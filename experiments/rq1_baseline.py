from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
import argparse
import hashlib
import json
import platform
import re
import subprocess
import sys
import uuid
import joblib
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.datasets import load_faces
from src.evaluation import evaluate_labeled
from src.face_authentication import FaceAuthenticator
from src.files import ROOT, read_csv, write_csv, write_json
from src.matching import combine_raw_scores, score_trials
from src.palmprint_authentication import PalmAuthenticator
from src.trial_protocol import load_protocol


def dataset_images(partitions, split, root=ROOT):
    faces, _ = load_faces(root)
    result = {'face': {}, 'palm': {}}
    for row in partitions:
        if row['split'] != split:
            continue
        sample, modality = row['original_sample_id'], row['modality']
        if modality == 'face':
            image = faces[int(row['source_path_or_key'].rsplit('#', 1)[1])]
            digest = hashlib.sha256(image.tobytes()).hexdigest()
        else:
            from PIL import Image, ImageOps
            path = root / row['source_path_or_key']
            with Image.open(path) as source:
                pixels = ImageOps.exif_transpose(source).convert('RGB')
                digest = hashlib.sha256(str(pixels.size).encode() + pixels.tobytes()).hexdigest()
                from src.preprocessing import crop_palm
                image = crop_palm(pixels)
        if digest != row['pixel_sha256']:
            raise ValueError(f'Sample changed since audit: {sample}')
        result[modality][sample] = image
    return result


def enroll(model, images, rows, modality):
    enrollment = [row for row in rows if row['modality'] == modality and row['split'] == 'enrollment']
    model.fit(np.stack([images[modality][row['original_sample_id']] for row in enrollment]),
              [row['simulated_user_id'] for row in enrollment])
    model.fit_sample_ids_ = [row['original_sample_id'] for row in enrollment]
    return model


def score_and_evaluate(model, probes, trials, modality):
    rows = score_trials(model, probes[modality], trials, modality)
    evaluator = evaluate_labeled([row[f'{modality}_score_raw'] for row in rows],
                                 [row['is_genuine'] for row in rows])
    return rows, evaluator


def run(run_id=None):
    manifest = ROOT / 'data/manifests'
    config, partitions, trials = load_protocol()
    run_id = run_id or datetime.now(timezone.utc).strftime('rq1_%Y%m%dT%H%M%SZ_') + uuid.uuid4().hex[:6]
    if re.fullmatch(r'[A-Za-z0-9_-]+', run_id) is None:
        raise ValueError('Run ID must contain only letters, digits, underscores and hyphens')
    metrics_dir, figures_dir = ROOT / 'results/metrics' / run_id, ROOT / 'results/figures' / run_id
    if metrics_dir.exists() or figures_dir.exists():
        raise FileExistsError('Run already exists; choose a fresh ID to preserve results')
    metrics_dir.mkdir(parents=True)
    figures_dir.mkdir(parents=True)
    enrollment = dataset_images(partitions, 'enrollment')
    validation = dataset_images(partitions, 'validation')
    choices = {'face': [16, 32, 64], 'palm': ['hog', 'lbp']}
    selection, chosen, validation_scores = [], {}, {}
    for modality in ['face', 'palm']:
        best = None
        for setting in choices[modality]:
            model = FaceAuthenticator(setting, config['seed']) if modality == 'face' else PalmAuthenticator(setting)
            enroll(model, enrollment, partitions, modality)
            rows, evaluator = score_and_evaluate(model, validation, trials['validation'], modality)
            metrics = evaluator.metrics()
            selection.append({'modality': modality, 'setting': str(setting), 'validation_eer': metrics['eer'],
                              'validation_auc': metrics['auc'], 'score_direction_check': metrics['score_direction_check']})
            if metrics['score_direction_check'] == 'passed' and (best is None or metrics['eer'] < best):
                best, chosen[modality], validation_scores[modality] = metrics['eer'], model, rows
        if modality not in chosen:
            raise ValueError(f'No {modality} validation candidate has the expected score direction')
    write_csv(metrics_dir / 'validation_model_selection.csv', selection)
    write_csv(metrics_dir / 'validation_scores.csv', combine_raw_scores(validation_scores['face'], validation_scores['palm']))
    # choices are frozen before test image loading or scoring
    test = dataset_images(partitions, 'test')
    results, test_scores = [], {}
    model_dir = ROOT / 'data/processed/models' / run_id
    model_dir.mkdir(parents=True)
    for modality in ['face', 'palm']:
        rows, evaluator = score_and_evaluate(chosen[modality], test, trials['test'], modality)
        test_scores[modality] = rows
        metrics = evaluator.export(metrics_dir, figures_dir, f'rq1_{modality}')
        results.append(dict(metrics, modality=modality, subjects=config['subjects'], seed=config['seed']))
        joblib.dump(chosen[modality], model_dir / f'{modality}.joblib')
    write_csv(metrics_dir / 'rq1_baseline_scores.csv', combine_raw_scores(test_scores['face'], test_scores['palm']))
    write_csv(metrics_dir / 'rq1_summary.csv', results)
    source_paths = sorted([*ROOT.glob('src/*.py'), *ROOT.glob('experiments/*.py'), ROOT / 'scripts/download_data.py', ROOT / 'scripts/audit_data.py', ROOT / 'scripts/build_protocol.py'])
    try:
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
        dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip())
        source_dirty = bool(subprocess.check_output(['git', 'status', '--porcelain', '--', 'src', 'scripts', 'experiments', 'tests', 'configs', 'data/manifests', 'requirements.txt', 'requirements-lock.txt'], cwd=ROOT, text=True).strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        commit, dirty, source_dirty = None, True, True
    metadata = {'status': 'completed', 'run_id': run_id, 'created_at_utc': datetime.now(timezone.utc).isoformat(),
                'protocol': config, 'python': platform.python_version(), 'platform': platform.platform(),
                'packages': {name: version(name) for name in ['numpy', 'scipy', 'scikit-learn', 'scikit-image', 'matplotlib', 'pillow', 'joblib']},
                'git_commit_at_run': commit, 'git_worktree_dirty_at_run': dirty,
                'git_source_dirty_at_run': source_dirty,
                'source_sha256': {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in source_paths},
                'manifest_sha256': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(manifest.glob('*')) if path.is_file()},
                'models': {modality: {'path': (model_dir / f'{modality}.joblib').relative_to(ROOT).as_posix(),
                                      'sha256': hashlib.sha256((model_dir / f'{modality}.joblib').read_bytes()).hexdigest(),
                                      'fit_sample_ids': chosen[modality].fit_sample_ids_} for modality in chosen},
                'chosen_models': {'face_pca_components': chosen['face'].n_components,
                                  'palm_feature': chosen['palm'].feature, 'template_rule': 'mean unit enrollment vectors, normalized; cosine similarity'},
                'test_metrics': results,
                'limitations': ['Artificial identities link different real people.', 'No demographic fairness inference.',
                                'BMPD license metadata is Unknown; raw images remain local.',
                                'Heuristic palm ROI has no anatomical landmark or rotation alignment.',
                                'EER is descriptive on this held-out set, not a deployment threshold.']}
    write_json(metrics_dir / 'run_metadata.json', metadata)
    write_json(ROOT / 'results/metrics/rq1_latest.json', {'run_id': run_id, 'metadata': (metrics_dir / 'run_metadata.json').relative_to(ROOT).as_posix()})
    print(json.dumps({'run_id': run_id, 'chosen_models': metadata['chosen_models'], 'test_metrics': results}, indent=2))
    return metadata


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id')
    run(parser.parse_args().run_id)
