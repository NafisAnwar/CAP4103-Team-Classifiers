
import unittest  # real frozen-face regression; palms are reused as accepted scores for rq3
from src.files import ROOT
from src.fusion import asset_available, accepted_scores
from src.datasets import dataset_images
from src.experiment_support import load_frozen_models
from src.matching import score_trials
from src.blur import assert_equal_scores
from src.evaluation import evaluate_labeled


class RestoredFaceTest(unittest.TestCase):  # group the regression checks and shared test fixtures for this component
    def test_restored_face_matches_all_accepted_validation_and_test_scores(self):  # verify that restored face matches all accepted validation and test scores
        pointer,metadata,_,partitions,trials,tables=accepted_scores()
        paths=[ROOT/'data/raw/face/olivetti.npz']+[ROOT/i['path'] for i in metadata['models'].values()]
        if not all(asset_available(p) for p in paths):
            self.skipTest('Actual Olivetti file and accepted frozen models are required')
        models,_=load_frozen_models()
        for split in ['validation','test']:
            faces=dataset_images([r for r in partitions if r['modality']=='face'],split)['face']
            actual=score_trials(models['face'],faces,trials[split],'face')
            self.assertLessEqual(assert_equal_scores(actual,tables[split],['face_score_raw'],atol=1e-12),1e-12)
            a=evaluate_labeled([r['face_score_raw'] for r in actual],[r['is_genuine'] for r in actual]).metrics()
            b=evaluate_labeled([r['face_score_raw'] for r in tables[split]],[r['is_genuine'] for r in tables[split]]).metrics()
            for field in ['eer','auc','d_prime']:
                self.assertAlmostEqual(a[field],b[field],places=12)


if __name__=='__main__':
    unittest.main()
