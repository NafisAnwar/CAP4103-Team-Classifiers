import unittest
import numpy as np
from src.evaluation import Evaluator, evaluate_labeled


class EvaluationTest(unittest.TestCase):
    def test_perfect_separation_on_negative_and_positive_similarity_scales(self):
        for shift in [0, -10, 10]:
            metrics = Evaluator(np.array([0.8, 0.9]) + shift, np.array([0.1, 0.2]) + shift).metrics()
            self.assertEqual(metrics['eer'], 0)
            self.assertEqual(metrics['auc'], 1)

    def test_tied_scores_and_reversed_direction_are_visible(self):
        metrics = Evaluator([0.5, 0.5], [0.5, 0.5]).metrics()
        self.assertEqual(metrics['eer'], 0.5)
        self.assertEqual(metrics['auc'], 0.5)
        self.assertEqual(metrics['d_prime'], 0)
        reversed_metrics = Evaluator([0.1, 0.2], [0.8, 0.9]).metrics()
        self.assertEqual(reversed_metrics['score_direction_check'], 'reversed_means')
        self.assertEqual(reversed_metrics['auc'], 0)

    def test_invalid_inputs_fail(self):
        for genuine, impostor in [([], [1]), ([float('nan')], [1]), ([[1]], [0])]:
            with self.assertRaises(ValueError):
                Evaluator(genuine, impostor)
        with self.assertRaises(ValueError):
            evaluate_labeled([0.1, 0.3], [0, 2])
        with self.assertRaises(ValueError):
            evaluate_labeled([0.1, 0.3], [1, 1])


if __name__ == '__main__':
    unittest.main()
