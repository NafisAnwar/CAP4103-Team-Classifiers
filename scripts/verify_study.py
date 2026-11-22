# unified verification workflow for the three research questions

from pathlib import Path
import json
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from src.files import read_csv, sha256, text_sha256, artifact_hash
from src.fusion import accepted_scores


rq1_run = 'rq1_main_verified_20261116'
rq2_run = 'rq2_main_verified_20261116'
rq2_repeat = 'rq2_main_repeat_20261116'
rq3_run = 'rq3_main_verified_20261116'
rq3_repeat = 'rq3_main_repeat_20261116'


def run_python(arguments):
    subprocess.run(
        [sys.executable, '-B', *arguments],
        cwd=root,
        check=True
    )


def verify_rq1():
    pointer, _, _, _, _, _ = accepted_scores(root)

    folder = root / 'results' / 'metrics' / rq1_run

    metadata = json.loads(
        (folder / 'run_metadata.json').read_text()
    )

    status = json.loads(
        (folder / 'run_status.json').read_text()
    )

    for record in [metadata, status]:
        if record['status'] != 'completed' or record['run_id'] != rq1_run:
            raise ValueError('RQ1 verification run is incomplete or mismatched')

    for name, expected in pointer['score_sha256'].items():
        actual = text_sha256(folder / name)

        if actual != expected:
            raise ValueError(f'RQ1 score reproduction differs: {name}')

    for name, expected in metadata['artifact_sha256'].items():
        if artifact_hash(root / name) != expected:
            raise ValueError(f'RQ1 artifact changed: {name}')

    print('PASS: RQ1 validation and test scores match the accepted baseline')


def verify_palm_files():
    manifest = root / 'data' / 'manifests' / 'palm_samples.csv'
    samples = read_csv(manifest)

    if len(samples) != 812:
        raise ValueError('Unexpected palmprint manifest size')

    for sample in samples:
        image_path = root / sample['source_path']

        if not image_path.is_file():
            raise FileNotFoundError(image_path)

        if sha256(image_path) != sample['file_sha256']:
            raise ValueError(
                f'Palmprint file changed or is not hydrated: {image_path}'
            )

    print(f'PASS: all {len(samples)} raw palmprint file hashes')


def main():
    output = Path(tempfile.mkdtemp(prefix='cap4103_study_verification_'))

    print('\nCAP4103 Study Verification', flush=True)
    print('Verifying the recorded experimental results.', flush=True)

    print('\n[1/5] RQ1 baseline integrity', flush=True)
    verify_rq1()

    print('\n[2/5] Raw palmprint dataset integrity', flush=True)
    verify_palm_files()

    print('\n[3/5] Automated tests and PPA3 regression', flush=True)

    test_command = (
        "import sys, unittest; "
        "suite = unittest.defaultTestLoader.discover('tests'); "
        "result = unittest.TextTestRunner(verbosity=2).run(suite); "
        "sys.exit(0 if result.wasSuccessful() "
        "and result.testsRun == 61 and not result.skipped else 1)"
    )

    run_python(['-c', test_command])

    print('\n[4/5] RQ2 fusion repeatability', flush=True)

    run_python([
        'scripts/verify_fusion.py',
        '--first', rq2_run,
        '--second', rq2_repeat,
        '--output', str(output / 'rq2_repeatability.json')
    ])

    print('\n[5/5] RQ2 and RQ3 experimental audit', flush=True)

    run_python([
        'scripts/review_submission.py',
        '--rq2-run', rq2_run,
        '--rq3-run', rq3_run,
        '--repeat-run', rq3_repeat,
        '--output', str(output / 'score_audit')
    ])

    print('\nPASS: all study verification checks completed')
    print(f'Verification outputs: {output}')
    print('Existing experimental results remain unchanged.')


if __name__ == '__main__':
    main()
