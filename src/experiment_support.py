from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
import json
import platform
import re
import subprocess
import uuid
import joblib
import numpy as np
from src.evaluation import evaluate_labeled
from src.files import ROOT, manifest_hashes, sha256, text_sha256, artifact_hash, verify_manifest_hashes, write_json, source_hash_matches
from src.matching import score_trials
from src.trial_protocol import load_protocol


def enroll(model, images, rows, modality):  # fit features and templates exclusively from the enrollment partition
    selected = [row for row in rows if row['modality'] == modality and row['split'] == 'enrollment']
    model.fit(np.stack([images[modality][row['original_sample_id']] for row in selected]),
              [row['simulated_user_id'] for row in selected])  # validation and test images never enter this fit
    model.fit_sample_ids_ = [row['original_sample_id'] for row in selected]
    return model


def score_and_evaluate(model, probes, trials, modality):  # match probes against claimed identities and evaluate their binary labels
    rows = score_trials(model, probes[modality], trials, modality)  # keep claim lookup independent of row order
    evaluator = evaluate_labeled([row[f'{modality}_score_raw'] for row in rows], [row['is_genuine'] for row in rows])
    return rows, evaluator


def capture_provenance(root=ROOT):  # record exact source, manifest, environment and git state before execution
    root = Path(root)
    sources = sorted({path for folder in ['src', 'scripts', 'experiments', 'tests']
                      for path in (root / folder).glob('*.py')} |
                     {path for path in [root / 'requirements.txt', root / 'requirements-lock.txt'] if path.is_file()})
    try:
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()
        status = ['git', '--no-optional-locks', 'status', '--porcelain']
        dirty = bool(subprocess.check_output(status, cwd=root, text=True).strip())
        source_dirty = bool(subprocess.check_output(status + ['--', 'src', 'scripts', 'experiments', 'tests',
                                 'data/manifests', 'requirements.txt', 'requirements-lock.txt'], cwd=root, text=True).strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        commit, dirty, source_dirty = None, True, True
    return {'hash_format': 'sha256_text_lf_binary_raw_v1',
            'source_sha256': {path.relative_to(root).as_posix(): text_sha256(path) for path in sources},
            'manifest_sha256': manifest_hashes(root),
            'protocol_lock_sha256': text_sha256(root / 'data/manifests/protocol_lock.json'),
            'git_commit_at_run': commit, 'git_worktree_dirty_at_run': dirty, 'git_source_dirty_at_run': source_dirty,
            'python': platform.python_version(), 'platform': platform.platform(),
            'packages': {name: version(name) for name in ['numpy', 'scipy', 'scikit-learn', 'scikit-image', 'matplotlib', 'pillow', 'joblib']}}


class RunArtifacts:  # manage a unique run directory and publish only completed experimental evidence
    def __init__(self, root=ROOT, run_id=None, latest_name='rq1_latest.json'):  # reserve names for metrics, figures and frozen model artifacts
        if latest_name not in {'rq1_latest.json', 'rq2_latest.json', 'rq3_latest.json'}:
            raise ValueError('Unknown latest pointer name')
        self.latest_name = latest_name
        self.root = Path(root)
        self.run_id = run_id or datetime.now(timezone.utc).strftime('rq1_%Y%m%dT%H%M%SZ_') + uuid.uuid4().hex[:6]
        if re.fullmatch(r'[A-Za-z0-9_-]+', self.run_id) is None:
            raise ValueError('Run ID must contain only letters, digits, underscores and hyphens')
        self.metrics_dir = self.root / 'results/metrics' / self.run_id
        self.figures_dir = self.root / 'results/figures' / self.run_id
        self.model_dir = self.root / 'data/processed/models' / self.run_id
        self.completed = False

    def __enter__(self):  # reject output collisions and record the starting input hashes
        folders = [self.metrics_dir, self.figures_dir, self.model_dir]
        if any(path.exists() for path in folders):
            raise FileExistsError('Run already exists; choose a fresh ID to preserve all results and models')
        self.provenance = capture_provenance(self.root)  # capture inputs before creating experiment outputs
        self.started = datetime.now(timezone.utc).isoformat()
        self.metrics_dir.mkdir(parents=True)  # reserve this run name before creating its other destinations
        try:
            self._status('running')
            self.figures_dir.mkdir(parents=True)
            self.model_dir.mkdir(parents=True)
        except BaseException as error:
            self._status('failed', error_type=type(error).__name__, error=str(error))
            raise
        return self

    def _status(self, status, **details):  # persist the run lifecycle and starting provenance even when execution fails
        write_json(self.metrics_dir / 'run_status.json', {'run_id': self.run_id, 'status': status,
                   'started_at_utc': self.started, 'updated_at_utc': datetime.now(timezone.utc).isoformat(),
                   'input_provenance': self.provenance, **details})  # failed runs keep their starting inputs too

    def complete(self, metadata, required_paths):  # verify input stability and all required artifacts before publishing the latest pointer
        current = capture_provenance(self.root)
        for field in ['source_sha256', 'manifest_sha256', 'protocol_lock_sha256', 'git_commit_at_run', 'packages']:
            if current[field] != self.provenance[field]:
                raise ValueError(f'Experiment inputs changed while running: {field}')
        if not required_paths or any(not path.is_file() or path.stat().st_size == 0 for path in required_paths):
            raise ValueError('Cannot complete a run with missing or empty artifacts')
        metadata.update(self.provenance)  # save the inputs that existed at the start
        metadata.update(status='completed', run_id=self.run_id, started_at_utc=self.started,
                        created_at_utc=datetime.now(timezone.utc).isoformat(),
                        artifact_sha256={path.relative_to(self.root).as_posix(): artifact_hash(path) for path in required_paths})
        path = self.metrics_dir / 'run_metadata.json'
        write_json(path, metadata)
        self._status('completed')
        write_json(self.root / 'results/metrics' / self.latest_name,
                   {'run_id': self.run_id, 'metadata': path.relative_to(self.root).as_posix()})  # publish only verified complete runs
        self.completed = True
        return metadata

    def __exit__(self, kind, error, traceback):  # mark interrupted or incomplete runs failed without concealing the exception
        if not self.completed:
            path = self.metrics_dir / 'run_metadata.json'
            if path.is_file():
                metadata = json.loads(path.read_text(encoding='utf-8'))
                metadata['status'] = 'failed'
                write_json(path, metadata)  # a failed pointer publication must not leave completed metadata behind
            self._status('failed', error_type=kind.__name__ if kind else 'IncompleteRun',
                         error=str(error) if error else 'Run exited without completing artifact checks')
        return False


def load_frozen_models(root=ROOT, model_run_id=None):  # validate accepted metadata and model bytes before loading enrolled templates
    root = Path(root)
    if model_run_id is not None and re.fullmatch(r'[A-Za-z0-9_-]+', model_run_id) is None:
        raise ValueError('Model run ID contains invalid characters')
    pointer = json.loads((root / 'results/metrics/rq1_accepted.json').read_text(encoding='utf-8'))
    path = root / pointer['metadata']
    if text_sha256(path) != pointer['metadata_sha256']:
        raise ValueError('Accepted baseline metadata changed')
    metadata = json.loads(path.read_text(encoding='utf-8'))
    if metadata['status'] != 'completed' or metadata['run_id'] != pointer['run_id']:
        raise ValueError('Accepted baseline is not a completed matching run')
    verify_manifest_hashes(pointer['manifest_sha256'], root)  # the historical metadata keeps its original windows byte hashes
    config, partitions, _ = load_protocol(root)
    if config != metadata['protocol']:
        raise ValueError('Accepted baseline protocol configuration changed')
    for name in ['src/preprocessing.py', 'src/face_authentication.py', 'src/palmprint_authentication.py', 'src/matching.py']:
        if not source_hash_matches(root, name, metadata['source_sha256'][name]):  # retain exact hash enforcement for frozen feature and matching code
            raise ValueError(f'Frozen model feature or matching implementation changed: {name}')
    for name, digest in pointer['score_sha256'].items():
        if text_sha256(path.parent / name) != digest:
            raise ValueError(f'Accepted baseline scores changed: {name}')
    models = {}
    for modality in ['face', 'palm']:
        info = metadata['models'][modality]
        path = root / info['path'] if model_run_id is None else root / 'data/processed/models' / model_run_id / f'{modality}.joblib'
        if sha256(path) != info['sha256']:
            raise ValueError(f'Frozen {modality} model changed')  # a fresh reproduction must match the accepted model bytes too
        expected = [row['original_sample_id'] for row in partitions if row['modality'] == modality and row['split'] == 'enrollment']
        if info['fit_sample_ids'] != expected:
            raise ValueError('Frozen model enrollment IDs conflict with protocol')
        models[modality] = joblib.load(path)  # only load the local artifact after checking its recorded hash
        if models[modality].fit_sample_ids_ != expected or list(models[modality].classes_) != sorted({row['simulated_user_id'] for row in partitions}):
            raise ValueError('Loaded model identities conflict with protocol')
    return models, metadata
