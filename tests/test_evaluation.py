import unittest
import numpy as np
import tempfile
import json
from pathlib import Path
from unittest.mock import patch
from src.evaluation import Evaluator, evaluate_labeled


class EvaluationTest(unittest.TestCase):  # group the regression checks and shared test fixtures for this component
    def test_custom_fusion_description_is_used_in_metrics_and_plot(self):  # verify that custom fusion description is used in metrics and plot
        evaluator = evaluate_labeled([0.9, 0.8, 0.2, 0.1], [1, 1, 0, 0],
                                     score_type='equal_weight_normalized_fusion', score_label='Normalized fusion score')
        with tempfile.TemporaryDirectory() as folder:
            with patch('matplotlib.axes.Axes.set_xlabel', autospec=True) as label:
                evaluator.export(Path(folder), Path(folder), 'fusion')
                self.assertTrue(any(call.args[1] == 'Normalized fusion score' for call in label.call_args_list))
            saved = json.loads((Path(folder) / 'fusion_metrics.json').read_text())
        self.assertEqual(saved['score_type'], 'equal_weight_normalized_fusion')
        self.assertEqual(saved['eer'], 0)

    def test_perfect_separation_on_negative_and_positive_similarity_scales(self):  # verify that perfect separation on negative and positive similarity scales
        for shift in [0, -10, 10]:
            metrics = Evaluator(np.array([0.8, 0.9]) + shift, np.array([0.1, 0.2]) + shift).metrics()
            self.assertEqual(metrics['eer'], 0)
            self.assertEqual(metrics['auc'], 1)

    def test_tied_scores_and_reversed_direction_are_visible(self):  # verify that tied scores and reversed direction are visible
        metrics = Evaluator([0.5, 0.5], [0.5, 0.5]).metrics()
        self.assertEqual(metrics['eer'], 0.5)
        self.assertEqual(metrics['auc'], 0.5)
        self.assertEqual(metrics['d_prime'], 0)
        reversed_metrics = Evaluator([0.1, 0.2], [0.8, 0.9]).metrics()
        self.assertEqual(reversed_metrics['score_direction_check'], 'reversed_means')
        self.assertEqual(reversed_metrics['auc'], 0)

    def test_invalid_inputs_fail(self):  # verify that invalid inputs fail
        for genuine, impostor in [([], [1]), ([float('nan')], [1]), ([[1]], [0])]:
            with self.assertRaises(ValueError):
                Evaluator(genuine, impostor)
        with self.assertRaises(ValueError):
            evaluate_labeled([0.1, 0.3], [0, 2])
        with self.assertRaises(ValueError):
            evaluate_labeled([0.1, 0.3], [1, 1])


if __name__ == '__main__':
    unittest.main()
