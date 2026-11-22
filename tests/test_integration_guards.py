from unittest.mock import patch
import unittest
from src.evaluation import evaluate_labeled
from src.files import ROOT
from src.fusion import accepted_scores, completed_run, Normalizer
from src.fusion_reporting import verify_metrics


class IntegrationGuardsTest(unittest.TestCase):  # group the regression checks and shared test fixtures for this component
    def test_metric_audit_rejects_missing_or_duplicate_systems(self):  # verify that metric audit rejects missing or duplicate systems
        rows = [{'is_genuine': label, 'face_score_raw': score, 'palm_score_raw': score,
                 'fusion_score': score} for label, score in [(1, .9), (1, .8), (0, .2), (0, .1)]]
        metrics = evaluate_labeled([.9, .8, .2, .1], [1, 1, 0, 0]).metrics()
        summary = [dict(metrics, modality=name) for name in ['face', 'palm', 'fusion']]
        verify_metrics(rows, summary)
        for invalid in [[], summary[:2], [summary[0], summary[0], summary[2]]]:
            with self.assertRaisesRegex(ValueError, 'exactly once'):
                verify_metrics(rows, invalid)

    def test_blur_rejects_parameters_not_fitted_on_accepted_validation(self):  # verify that blur rejects parameters not fitted on accepted validation
        from dataclasses import replace
        from experiments.rq3_blur import run
        pointer, _, _, _, trials, tables = accepted_scores()
        fitted = Normalizer.fit(tables['validation'], trials['validation'], split='validation',
                                validation_sha256=pointer['score_sha256']['validation_scores.csv'], baseline_id=pointer['run_id'])
        with patch('experiments.rq3_blur.Normalizer.load', return_value=replace(fitted, face_mean=fitted.face_mean+.1)), \
             patch('experiments.rq3_blur.RunArtifacts') as artifacts:
            with self.assertRaisesRegex(ValueError, 'validation-only fit'):
                run('rq2_main_verified_20261116', 'not_needed.json')
            artifacts.assert_not_called()  # bad parameters fail before any held-out image loading or output creation


if __name__ == '__main__':
    unittest.main()
