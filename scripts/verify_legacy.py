from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import argparse
import shutil
import tempfile

root = Path(__file__).resolve().parents[1]


def verify(export=False):
    expected_hashes = json.loads((root / 'docs/legacy_source_hashes.json').read_text())
    for name, expected in expected_hashes.items():
        actual = hashlib.sha256((root / 'ppa3_legacy' / name).read_bytes()).hexdigest()
        if actual != expected:
            raise AssertionError(f'Original PPA3 file changed: {name}')
    env = dict(os.environ, PYTHONIOENCODING='utf-8', MPLBACKEND='Agg')
    with tempfile.TemporaryDirectory(prefix='cap4103_legacy_') as folder:
        temporary = Path(folder)
        for name in expected_hashes:
            shutil.copyfile(root / 'ppa3_legacy' / name, temporary / name) #the archived originals are never executed in place
        run = subprocess.run([sys.executable, '-B', str(temporary / 'main.py')],
                             cwd=temporary, env=env, capture_output=True, text=True,
                             encoding='utf-8', timeout=180, check=True)
        figures = ['roc_curve.png', 'det_curve.png', 'score_distribution_plot.png']
        if not all((temporary / 'plots' / name).is_file() for name in figures):
            raise AssertionError('Legacy figures were not generated')
        figure_bytes = {name: (temporary / 'plots' / name).read_bytes() for name in figures} #retain evidence after the temporary run ends
    print(run.stdout, end='')
    if run.stderr:
        print(run.stderr, file=sys.stderr, end='')
    expected = {'auc': ('ROC AUC', 0.7569), 'eer': ('Equal Error Rate', 0.2612),
                'd_prime': ('d-prime', 1.0973)}
    metrics = {}
    for key, (label, value) in expected.items():
        match = re.search(re.escape(label) + r': ([0-9.]+)', run.stdout)
        if not match or float(match.group(1)) != value:
            raise AssertionError(f'Legacy {label} did not reproduce {value}')
        metrics[key] = float(match.group(1))
    checks = ['Total samples: 375, identities: 20',
              'Training templates: 251; testing queries: 124',
              'Genuine scores: 124; impostor scores: 2356',
              'Matching probability matrix: (124, 20)']
    for text in checks:
        if text not in run.stdout:
            raise AssertionError(f'Missing expected legacy count: {text}')
    result = {'experiment': 'original_ppa3_caltech_landmarks_only', 'status': 'passed',
              'verified_at_utc': datetime.now(timezone.utc).isoformat(),
              'python': platform.python_version(), 'executable': sys.executable,
              'platform': platform.platform(), 'seed': 42,
              'counts': {'samples': 375, 'identities': 20, 'enrollment': 251,
                         'test': 124, 'genuine': 124, 'impostor': 2356},
              'metrics_rounded_4dp': metrics,
              'eer_method': 'original 500-point grid [-0.1, 1.1], closest FAR/FRR average',
              'packages': {name: version(name) for name in ['numpy', 'scipy', 'scikit-learn', 'matplotlib']},
              'source_sha256': expected_hashes,
               'figures_verified': figures, 'evidence_exported': export}
    if export:
        destination = root / 'results/metrics'
        destination.mkdir(parents=True, exist_ok=True)
        (destination / 'legacy_regression.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        (destination / 'legacy_stdout.txt').write_text(run.stdout, encoding='utf-8')
        for name, data in figure_bytes.items():
            path = root / 'ppa3_legacy/plots' / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data) #only the explicit export command updates saved evidence
    print('PASS: unchanged source, sample/claim counts, metrics and three generated figures')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--export', action='store_true', help='Replace saved legacy evidence after a successful check')
    verify(export=parser.parse_args().export)
