import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from src.files import ROOT


entry = ROOT / 'main.py' if (ROOT / 'main.py').is_file() else ROOT.parent / 'main.py'
spec = importlib.util.spec_from_file_location('cap4103_master', entry)
master = importlib.util.module_from_spec(spec)
spec.loader.exec_module(master)


class MasterTest(unittest.TestCase):  # group the regression checks and shared test fixtures for this component
    def test_repository_and_submission_layouts(self):  # verify that repository and submission layouts
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            with self.assertRaises(FileNotFoundError):
                master.project_root(base)
            for root in [base, base / 'project']:
                (root / 'scripts').mkdir(parents=True)
                (root / 'scripts/reproduce_full.py').touch()
                self.assertEqual(master.project_root(base), root)

    def test_modes_dispatch_with_prerequisites_and_package_integrity(self):  # verify that modes dispatch with prerequisites and package integrity
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.assertEqual(master.mode_command('verify', root, root), ['scripts/verify_package.py'])
            (root / '.git').mkdir()
            self.assertEqual(master.mode_command('verify', root, root), ['scripts/verify_package.py', '--repository'])
            for mode in ['rq1', 'rq2', 'rq3', 'full']:
                expected = 'rq3' if mode == 'full' else mode
                self.assertEqual(master.mode_command(mode, root, root),
                                 ['scripts/reproduce_full.py', '--through', expected, '--data-root', str(root)])
            self.assertEqual(master.mode_command('download', root, root), ['scripts/download_data.py', '--modality', 'both'])
            self.assertEqual(master.mode_command('tests', root, root), ['-m', 'unittest', 'discover', '-s', 'tests', '-v'])

    def test_execution_uses_same_python_and_propagates_failure(self):  # verify that execution uses same python and propagates failure
        with patch.object(master.sys, 'version_info', (3, 13, 2)):
            with patch.object(master, 'dependency_issues', return_value=[]):
                with patch.object(master.subprocess, 'run', side_effect=subprocess.CalledProcessError(7, 'test')) as run:
                    with self.assertRaises(subprocess.CalledProcessError):
                        master.execute('rq2', ROOT, ROOT)
                    run.assert_called_once_with([master.sys.executable, '-B', 'scripts/reproduce_full.py',
                                                 '--through', 'rq2', '--data-root', str(ROOT)], cwd=ROOT, check=True)

    def test_missing_dependencies_prevent_execution(self):  # verify that missing dependencies prevent execution
        with patch.object(master.sys, 'version_info', (3, 13, 2)):
            with patch.object(master, 'dependency_issues', return_value=['numpy: missing']):
                with patch.object(master.subprocess, 'run') as run:
                    with self.assertRaisesRegex(RuntimeError, 'setup first'):
                        master.execute('verify', ROOT)
                    run.assert_not_called()

    def test_menu_handles_invalid_selection_and_failed_action(self):  # verify that menu handles invalid selection and failed action
        with patch('builtins.input', side_effect=['invalid', '1', '0']):
            with patch.object(master, 'execute', side_effect=RuntimeError('expected failure')) as execute:
                with patch('builtins.print') as output:
                    self.assertEqual(master.menu(ROOT), 0)
                    execute.assert_called_once_with('verify', ROOT, None)
                    output.assert_any_call('Please enter one of the listed numbers.')
                    output.assert_any_call('FAILED: expected failure', file=master.sys.stderr)


if __name__ == '__main__':
    unittest.main()
