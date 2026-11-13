"""Validation-only, persistent z-score normalization and keyed equal-weight fusion."""
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import re
import numpy as np
from src.files import ROOT, read_csv, write_json, text_sha256, sha256, verify_manifest_hashes
from src.trial_protocol import load_protocol

VERSION = 'validation_all_claims_zscore_v1'
KEYS = ('trial_id', 'claimed_user_id')
RQ2_FIELDS = ['trial_id', 'claimed_user_id', 'is_genuine', 'face_score_raw', 'palm_score_raw',
              'face_score_normalized', 'palm_score_normalized', 'fusion_score', 'normalization_version']
RQ3_FIELDS = ['blur_sigma'] + RQ2_FIELDS[:-1]


def asset_available(path):
    path = Path(path)
    if not path.is_file():
        return False
    with path.open('rb') as stream:
        return not stream.read(128).startswith(b'version https://git-lfs.github.com/spec/v1')


def require_assets(paths):
    missing = [str(p) for p in paths if not asset_available(p)]
    if missing:
        raise FileNotFoundError('Actual data/model bytes are missing or are Git LFS pointers. '
                                'Run git lfs pull in an authorized clone or obtain the actual files. '
                                'First unavailable paths: ' + ', '.join(missing[:3]))


def index_rows(rows, score_fields=()):
    index = {}
    for original in rows:
        row = dict(original)
        key = tuple(row[k] for k in KEYS)
        if not all(isinstance(k, str) and k for k in key) or key in index:
            raise ValueError('Blank or duplicate trial/claim key')
        if str(row['is_genuine']) not in {'0', '1'}:
            raise ValueError('Labels must be binary integers')
        row['is_genuine'] = int(row['is_genuine'])
        for field in score_fields:
            row[field] = float(row[field])
            if not np.isfinite(row[field]):
                raise ValueError('Nonfinite score')
        index[key] = row
    if not index:
        raise ValueError('Empty score table')
    return index


def validate_coverage(rows, trials, fields=('face_score_raw', 'palm_score_raw')):
    actual, expected = index_rows(rows, fields), index_rows(trials)
    if actual.keys() != expected.keys():
        raise ValueError('Score keys do not exactly cover the requested split')
    for key in expected:
        if actual[key]['is_genuine'] != expected[key]['is_genuine']:
            raise ValueError('Score truth labels differ from the protocol')
    return [actual[key] for key in sorted(actual)]


def accepted_scores(root=ROOT):
    root = Path(root)
    pointer = json.loads((root / 'results/metrics/rq1_accepted.json').read_text())
    metadata_path = root / pointer['metadata']
    if text_sha256(metadata_path) != pointer['metadata_sha256']:
        raise ValueError('Accepted metadata changed')
    metadata = json.loads(metadata_path.read_text())
    if metadata['status'] != 'completed' or metadata['run_id'] != pointer['run_id']:
        raise ValueError('Accepted run is incomplete or mismatched')
    verify_manifest_hashes(pointer['manifest_sha256'], root)
    config, partitions, trials = load_protocol(root)
    if config != metadata['protocol']:
        raise ValueError('Accepted protocol differs')
    for name in ['src/preprocessing.py', 'src/face_authentication.py',
                 'src/palmprint_authentication.py', 'src/matching.py']:
        if sha256(root / name) != metadata['source_sha256'][name]:
            raise ValueError('Accepted feature or matching implementation changed')
    tables = {}
    for split, name in [('validation', 'validation_scores.csv'), ('test', 'rq1_baseline_scores.csv')]:
        path = metadata_path.parent / name
        if text_sha256(path) != pointer['score_sha256'][name]:
            raise ValueError('Accepted scores changed')
        tables[split] = validate_coverage(read_csv(path), trials[split])
    return pointer, metadata, config, partitions, trials, tables


@dataclass(frozen=True)
class Normalizer:
    face_mean: float
    face_std: float
    palm_mean: float
    palm_std: float
    validation_sha256: str
    baseline_id: str
    validation_count: int
    normalization_version: str = VERSION

    def __post_init__(self):
        values = [self.face_mean, self.face_std, self.palm_mean, self.palm_std]
        if not np.isfinite(values).all() or min(self.face_std, self.palm_std) <= 1e-12:
            raise ValueError('Nonfinite or constant/near-constant validation scores')
        if self.normalization_version != VERSION or self.validation_count < 2:
            raise ValueError('Unknown normalization version or invalid sample count')

    @classmethod
    def fit(cls, rows, validation_trials, *, split, validation_sha256, baseline_id):
        if split != 'validation' or any(not r['trial_id'].startswith('validation-') for r in validation_trials):
            raise ValueError('Normalizer fitting is restricted to validation')
        rows = validate_coverage(rows, validation_trials)
        values = {m: np.array([r[m + '_score_raw'] for r in rows]) for m in ['face', 'palm']}
        return cls(float(values['face'].mean()), float(values['face'].std(ddof=0)),
                   float(values['palm'].mean()), float(values['palm'].std(ddof=0)),
                   validation_sha256, baseline_id, len(rows))

    def transform(self, values, modality):
        if modality not in ['face', 'palm']:
            raise ValueError('Unknown modality')
        values = np.asarray(values, dtype=float)
        if not np.isfinite(values).all():
            raise ValueError('Nonfinite scores')
        result = (values - getattr(self, modality + '_mean')) / getattr(self, modality + '_std')
        if not np.isfinite(result).all():
            raise ValueError('Nonfinite normalized scores')
        return result

    def save(self, path, provenance):
        path = Path(path)
        if path.exists():
            raise FileExistsError('Normalizer already exists; do not overwrite frozen parameters')
        write_json(path, {'parameters': asdict(self), 'provenance': provenance,
                          'definition': '(raw_score - validation_mean) / validation_population_std',
                          'fitting_population': 'all validation claims; no label balancing',
                          'clipping': 'none; unbounded higher-is-better scores'})

    @classmethod
    def load(cls, path):
        return cls(**json.loads(Path(path).read_text())['parameters'])


def fuse_scores(face_rows, palm_rows, normalizer, trials):
    faces = index_rows(face_rows, ['face_score_raw'])
    palms = index_rows(palm_rows, ['palm_score_raw'])
    if faces.keys() != palms.keys():
        raise ValueError('Modality keys differ')
    rows = []
    for key in sorted(faces):
        a, b = faces[key], palms[key]
        if a['is_genuine'] != b['is_genuine']:
            raise ValueError('Modality labels differ')
        face = float(normalizer.transform(a['face_score_raw'], 'face'))
        palm = float(normalizer.transform(b['palm_score_raw'], 'palm'))
        rows.append({'trial_id': key[0], 'claimed_user_id': key[1], 'is_genuine': a['is_genuine'],
                     'face_score_raw': a['face_score_raw'], 'palm_score_raw': b['palm_score_raw'],
                     'face_score_normalized': face, 'palm_score_normalized': palm,
                     'fusion_score': 0.5 * face + 0.5 * palm,
                     'normalization_version': normalizer.normalization_version})
    return validate_coverage(rows, trials, RQ2_FIELDS[3:-1])


def completed_run(root, run_id, experiment):
    root = Path(root)
    if re.fullmatch(r'[A-Za-z0-9_-]+', run_id) is None:
        raise ValueError('Invalid run ID')
    folder = root / 'results/metrics' / run_id
    metadata = json.loads((folder / 'run_metadata.json').read_text())
    status = json.loads((folder / 'run_status.json').read_text())
    if any(x['status'] != 'completed' or x['run_id'] != run_id for x in [metadata, status]):
        raise ValueError('Run is not completed')
    if metadata['experiment'] != experiment:
        raise ValueError('Wrong experiment type')
    from src.files import artifact_hash
    for name, expected in metadata['artifact_sha256'].items():
        if artifact_hash(root / name) != expected:
            raise ValueError('Completed artifact changed: ' + name)
    return folder, metadata
