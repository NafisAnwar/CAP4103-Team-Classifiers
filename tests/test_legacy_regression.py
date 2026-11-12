from pathlib import Path
import importlib.util
import unittest

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('verify_legacy', root / 'scripts/verify_legacy.py')
legacy_check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy_check)


class LegacyRegressionTest(unittest.TestCase):
    def test_unchanged_ppa3_reproduces_counts_metrics_and_figures(self):
        result = legacy_check.verify()
        self.assertEqual(result['status'], 'passed')


if __name__ == '__main__':
    unittest.main()
