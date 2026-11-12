from pathlib import Path
import hashlib
import json
import unittest
import joblib
import numpy as np
from src.files import ROOT, read_csv
from src.evaluation import evaluate_labeled
from src.trial_protocol import load_protocol
from src.datasets import load_faces
from src.preprocessing import palm_roi


@unittest.skipUnless((ROOT / 'results/metrics/rq1_latest.json').exists(), 'Local RQ1 outputs required')
class ExperimentIntegrityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pointer = json.loads((ROOT / 'results/metrics/rq1_latest.json').read_text())
        cls.metadata = json.loads((ROOT / pointer['metadata']).read_text())
        cls.folder = (ROOT / pointer['metadata']).parent
        cls.config, cls.partitions, cls.trials = load_protocol()
        cls.rows = read_csv(cls.folder / 'rq1_baseline_scores.csv')

    def test_exported_scores_exactly_cover_the_manifest_and_reproduce_metrics(self):
        expected = {(row['trial_id'], row['claimed_user_id'], int(row['is_genuine'])) for row in self.trials['test']}
        actual = {(row['trial_id'], row['claimed_user_id'], int(row['is_genuine'])) for row in self.rows}
        self.assertEqual(len(self.rows), len(expected))
        self.assertEqual(actual, expected)
        labels = [int(row['is_genuine']) for row in self.rows]
        for saved in self.metadata['test_metrics']:
            scores = [float(row[f'{saved["modality"]}_score_raw']) for row in self.rows]
            calculated = evaluate_labeled(scores, labels).metrics()
            for field in ['eer', 'auc', 'd_prime']:
                self.assertAlmostEqual(calculated[field], saved[field], places=12)

    @unittest.skipUnless((ROOT / 'data/raw/face/olivetti.npz').exists(), 'Download datasets and run RQ1 to check local models')
    def test_frozen_models_use_only_enrollment_and_reproduce_a_probe(self):
        for modality, model_info in self.metadata['models'].items():
            enrollment = {row['original_sample_id'] for row in self.partitions if row['modality'] == modality and row['split'] == 'enrollment'}
            self.assertEqual(set(model_info['fit_sample_ids']), enrollment)
            path = ROOT / model_info['path']
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), model_info['sha256'])
            model = joblib.load(path)
            self.assertEqual(set(model.fit_sample_ids_), enrollment)
            trial = self.trials['test'][0]
            sample = trial[f'{modality}_test_sample_id']
            row = next(row for row in self.partitions if row['modality'] == modality and row['original_sample_id'] == sample)
            if modality == 'face':
                faces, _ = load_faces()
                image = faces[int(row['source_path_or_key'].rsplit('#', 1)[1])]
            else:
                image = palm_roi(ROOT / row['source_path_or_key'])
            matrix = model.score_matrix(np.stack([image]))[0]
            expected = {row['claimed_user_id']: float(row[f'{modality}_score_raw']) for row in self.rows if row['trial_id'].startswith('test-' + trial['simulated_true_user'] + '-p00-')}
            np.testing.assert_allclose(matrix, [expected[claim] for claim in model.classes_], rtol=1e-10, atol=1e-10)


if __name__ == '__main__':
    unittest.main()
