from pathlib import Path
import importlib.util
import unittest

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('verify_legacy', root / 'scripts/verify_legacy.py')
legacy_check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy_check)


class LegacyRegressionTest(unittest.TestCase):  # group the regression checks and shared test fixtures for this component
    def test_unchanged_ppa3_reproduces_counts_metrics_and_figures(self):  # verify that unchanged ppa3 reproduces counts metrics and figures
        result = legacy_check.verify()
        self.assertEqual(result['status'], 'passed')


if __name__ == '__main__':
    unittest.main()
