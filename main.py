import argparse
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
MODES = ('verify', 'rq1', 'rq2', 'rq3', 'full', 'download', 'tests', 'setup')
MENU = {
    '1': ('verify', 'Verify submitted results without downloading datasets'),
    '2': ('rq1', 'Reproduce RQ1: individual authentication'),
    '3': ('rq2', 'Reproduce RQ2: baseline and score-level fusion'),
    '4': ('full', 'Reproduce RQ3: complete study including facial blur'),
    '5': ('download', 'Download the authorized original datasets'),
    '6': ('tests', 'Run all automated tests'),
    '0': (None, 'Exit'),
}


def project_root(base=HERE):
    base = Path(base).resolve()
    candidate = base / 'project'  # the submission keeps implementation folders under one directory
    if (candidate / 'scripts/reproduce_full.py').is_file():
        return candidate
    if (base / 'scripts/reproduce_full.py').is_file():
        return base  # the development checkout retains its existing paths
    raise FileNotFoundError('Project implementation is missing. Extract the entire submission ZIP.')


def dependency_issues(root):
    problems = []
    for line in (root / 'requirements-lock.txt').read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        name, expected = line.strip().split('==', 1)
        try:
            actual = version(name)
        except PackageNotFoundError:
            actual = 'not installed'
        if actual != expected:
            problems.append(f'{name}: expected {expected}, found {actual}')
    return problems


def setup(root):
    if sys.prefix == sys.base_prefix:
        raise RuntimeError('Use RUN_PROJECT.cmd or activate a Python 3.13 virtual environment before setup.')
    if sys.version_info[:2] != (3, 13):
        raise RuntimeError('Python 3.13 is required for the pinned project environment.')
    if dependency_issues(root):
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', str(root / 'requirements-lock.txt')],
                       cwd=root, check=True)  # install only when the pinned environment is incomplete
    subprocess.run([sys.executable, '-m', 'pip', 'check'], cwd=root, check=True)
    remaining = dependency_issues(root)
    if remaining:
        raise RuntimeError('Pinned dependency check failed: ' + '; '.join(remaining))
    print('PASS: Pinned Python environment is ready.', flush=True)


def mode_command(mode, root, data_root):
    if mode == 'verify':
        command = ['scripts/verify_package.py']
        if (root / '.git').exists():
            command.append('--repository')  # a development checkout has no submission checksum manifest
        return command
    if mode in ('rq1', 'rq2', 'rq3', 'full'):
        through = 'rq3' if mode == 'full' else mode
        return ['scripts/reproduce_full.py', '--through', through, '--data-root', str(data_root)]
    if mode == 'download':
        return ['scripts/download_data.py', '--modality', 'both']
    if mode == 'tests':
        return ['-m', 'unittest', 'discover', '-s', 'tests', '-v']
    raise ValueError(f'Unknown execution mode: {mode}')


def execute(mode, root, data_root=None):
    if mode == 'setup':
        setup(root)
        return
    if sys.version_info[:2] != (3, 13):
        raise RuntimeError('Use Python 3.13 with the supplied pinned dependencies.')
    problems = dependency_issues(root)
    if problems:
        raise RuntimeError('Run RUN_PROJECT.cmd or main.py setup first. ' + '; '.join(problems))
    command = mode_command(mode, root, data_root or root)
    subprocess.run([sys.executable, '-B', *command], cwd=root, check=True)  # use the same interpreter for every experiment


def menu(root, data_root=None):
    while True:
        print('\nCAP4103 | TEAM CLASSIFIERS')
        print('Face and Palmprint Biometric Authentication')
        for key, (_, label) in MENU.items():
            print(f'[{key}] {label}')
        try:
            choice = input('Select an option: ').strip()
        except EOFError:
            return 0  # allow noninteractive terminals to exit without hanging
        if choice not in MENU:
            print('Please enter one of the listed numbers.')
            continue
        mode = MENU[choice][0]
        if mode is None:
            return 0
        try:
            execute(mode, root, data_root)
        except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as error:
            print(f'FAILED: {error}', file=sys.stderr)


def main(argv=None):
    parser = argparse.ArgumentParser(description='CAP4103 biometric experiment launcher')
    parser.add_argument('mode', nargs='?', choices=MODES, help='omit to open the interactive menu')
    parser.add_argument('--data-root', type=Path, help='directory containing data/raw for independent reproduction')
    args = parser.parse_args(argv)
    try:
        root = project_root()
        data_root = args.data_root.resolve() if args.data_root else None
        if args.mode is None:
            return menu(root, data_root)
        if data_root is not None and args.mode not in ('rq1', 'rq2', 'rq3', 'full'):
            parser.error('--data-root applies only to image-level reproduction')
        execute(args.mode, root, data_root)
        return 0
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as error:
        print(f'FAILED: {error}', file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('\nCancelled.')
        return 130


if __name__ == '__main__':
    raise SystemExit(main())
