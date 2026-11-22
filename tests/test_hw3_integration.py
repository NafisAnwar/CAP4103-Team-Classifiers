import ast
import hashlib
import json
import unittest
from unittest.mock import patch
import numpy as np
from sklearn.metrics import roc_curve
from src.evaluation import Evaluator
from src.files import ROOT, read_csv


class HW3IntegrationTest(unittest.TestCase):  # group the regression checks and shared test fixtures for this component
    def test_original_hw3_numerical_methods_are_preserved(self):  # verify that original hw3 numerical methods are preserved
        original = (ROOT / 'docs/hw3_original.py.txt').read_bytes()
        self.assertEqual(hashlib.sha256(original).hexdigest(),
                         '35a1e1ea0448f3f4a64f9d353284928b8b2bb7e9395bf410e5807052bd5d43f4')

        def methods(source):  # support the deterministic test fixture and its assertions
            tree = ast.parse(source)
            cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'Evaluator')
            result = {}
            for node in cls.body:
                if isinstance(node, ast.FunctionDef):
                    if isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
                        node.body.pop(0)  # ignore only explanatory docstrings when comparing actual homework code
                    result[node.name] = ast.dump(node, include_attributes=False)
            return result

        old = methods(original)
        new = methods((ROOT / 'src/hw3_evaluator.py').read_bytes())
        for name in ['__init__', 'get_dprime', 'get_EER', 'compute_rates']:
            self.assertEqual(old[name], new[name], name)  # verify executable homework methods are unchanged

    def test_project_calls_hw3_with_full_empirical_thresholds(self):  # verify that project calls hw3 with full empirical thresholds
        genuine = np.array([-2.0, 0.0, 3.0, 3.0])
        impostor = np.array([-4.0, -2.0, 0.0, 1.0])
        evaluator = Evaluator(genuine, impostor)
        with patch.object(evaluator.hw3, 'compute_rates', wraps=evaluator.hw3.compute_rates) as rates:
            with patch.object(evaluator.hw3, 'get_dprime', wraps=evaluator.hw3.get_dprime) as dprime:
                result = evaluator.metrics()
                rates.assert_called_once()  # require the original homework calculations in the real metrics path
                dprime.assert_called_once()
        fpr, fnr, tpr, thresholds = evaluator.compute_rates()
        expected_fpr, expected_tpr, expected_thresholds = roc_curve(
            np.r_[np.ones(len(genuine)), np.zeros(len(impostor))],
            np.r_[genuine, impostor], drop_intermediate=False)
        np.testing.assert_array_equal(thresholds, expected_thresholds)
        np.testing.assert_allclose(fpr, expected_fpr, rtol=0, atol=1e-12)
        np.testing.assert_allclose(tpr, expected_tpr, rtol=0, atol=1e-12)
        np.testing.assert_allclose(fnr, 1 - expected_tpr, rtol=0, atol=1e-12)
        self.assertEqual(result['evaluation_source'], 'hw3_submitted_evaluator_empirical_thresholds')

    def test_degenerate_dprime_retains_existing_policy(self):  # verify that degenerate dprime retains existing policy
        self.assertIsNone(Evaluator([1, 1], [0, 0]).get_dprime())
        self.assertEqual(Evaluator([0, 0], [0, 0]).get_dprime(), 0)

    def test_all_twenty_saved_conditions_remain_reproducible(self):  # verify that all twenty saved conditions remain reproducible
        runs = [('rq1_main_verified_20261116', 'rq1_baseline_scores.csv'),
                ('rq2_main_verified_20261116', 'rq2_fusion_scores.csv'),
                ('rq3_main_verified_20261116', 'rq3_blur_scores.csv')]
        comparisons = 0
        for run, score_file in runs:
            folder = ROOT / 'results/metrics' / run
            rows = read_csv(folder / score_file)
            reference = json.loads((folder / 'run_metadata.json').read_text())['test_metrics']
            for expected in reference:
                modality = expected['modality']
                sigma = float(expected.get('blur_sigma', 0))
                with self.subTest(run=run, modality=modality, sigma=sigma):
                    selected = [row for row in rows if float(row.get('blur_sigma', 0)) == sigma]
                    field = 'fusion_score' if modality == 'fusion' else modality + '_score_raw'
                    genuine = [float(row[field]) for row in selected if row['is_genuine'] == '1']
                    impostor = [float(row[field]) for row in selected if row['is_genuine'] == '0']
                    actual = Evaluator(genuine, impostor).metrics()
                    for metric in ['eer', 'auc', 'd_prime']:
                        self.assertAlmostEqual(actual[metric], expected[metric], places=12)
                    self.assertEqual(actual['genuine_count'], expected['genuine_count'])
                    self.assertEqual(actual['impostor_count'], expected['impostor_count'])
                    comparisons += 1
        self.assertEqual(comparisons, 20)  # all research questions and blur conditions must be covered


if __name__ == '__main__':
    unittest.main()
