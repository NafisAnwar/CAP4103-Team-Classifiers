from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from src.blur import blur_image, validate_sigmas, frozen_face_scores, assert_equal_scores
from src.fusion import Normalizer, fuse_scores
from src.evaluation import evaluate_labeled
from src.files import ROOT


class FixedModel:
    def __init__(self):
        self.classes_=np.array(['a','b'])
        self.templates_=np.array([[1,0,0,0],[0,0,0,1]],dtype=float)

    def fit(self,*args):
        raise AssertionError('Blur scoring must never fit')

    def score_matrix(self,images):
        return images.reshape(len(images),-1)@self.templates_.T


def fixture():
    images={'one':np.array([[.9,.1],[.1,.2]]),'two':np.array([[.1,.2],[.3,.8]])}
    trials=[dict(trial_id=f't{i}{claim}',claimed_user_id=claim,is_genuine=int(true==claim),
                 simulated_true_user=true,face_test_sample_id=sample,palm_test_sample_id='p'+sample)
            for i,(sample,true) in enumerate([('one','a'),('two','b')]) for claim in ['a','b']]
    return images,trials


class BlurTest(unittest.TestCase):
    def test_sigma_zero_is_exact_copy_with_original_dtype(self):
        image=fixture()[0]['one'].astype(np.float32)
        actual=blur_image(image,0)
        np.testing.assert_array_equal(image,actual)
        self.assertEqual(actual.dtype,image.dtype)
        self.assertFalse(np.shares_memory(actual,image))

    def test_positive_blur_preserves_shape_range_and_input(self):
        image=fixture()[0]['one']
        before=image.copy()
        result=blur_image(image,1)
        self.assertEqual(result.shape,image.shape)
        self.assertTrue(np.all((result>=0)&(result<=1)))
        self.assertLess(result.std(),image.std())
        np.testing.assert_array_equal(image,before)

    def test_invalid_sigmas_and_pixels_rejected(self):
        for sigmas in [[],[1],[0,0],[0,-1],[0,float('inf')],[0,2,1]]:
            with self.assertRaises(ValueError):
                validate_sigmas(sigmas)
        for image in [np.zeros((2,2,3)),np.full((2,2),float('nan')),np.full((2,2),2.),np.zeros((2,2),dtype=int)]:
            with self.assertRaises(ValueError):
                blur_image(image,1)

    def test_frozen_model_and_original_arrays_unchanged(self):
        model=FixedModel()
        images,trials=fixture()
        original={k:v.copy() for k,v in images.items()}
        templates=model.templates_.copy()
        with patch.object(FixedModel,'fit',side_effect=AssertionError('refit')) as fit:
            rows=frozen_face_scores(model,images,trials,[0,1,2])
            fit.assert_not_called()
        self.assertEqual(len(rows[0]),len(trials))
        np.testing.assert_array_equal(templates,model.templates_)
        for key in images:
            np.testing.assert_array_equal(images[key],original[key])
        self.assertNotEqual(rows[0][0]['face_score_raw'],rows[1][0]['face_score_raw'])

    def test_sigma_zero_fusion_and_palm_invariance(self):
        images,trials=fixture()
        scores=frozen_face_scores(FixedModel(),images,trials,[0,1,2])
        palms=[dict(r,palm_score_raw=.7 if r['is_genuine'] else .2) for r in scores[0]]
        norm=Normalizer(.3,.2,.4,.3,'fixture','fixture',4)
        clear=fuse_scores(scores[0],palms,norm,trials)
        original_params=repr(norm)
        palm_eers=[]
        for sigma in scores:
            rows=fuse_scores(scores[sigma],list(reversed(palms)),norm,trials)
            assert_equal_scores(rows,clear,['palm_score_raw','palm_score_normalized'])
            if sigma==0:
                assert_equal_scores(rows,clear,['face_score_raw','face_score_normalized','fusion_score'])
            palm_eers.append(evaluate_labeled([r['palm_score_raw'] for r in rows],[r['is_genuine'] for r in rows]).metrics()['eer'])
        self.assertEqual(len(set(palm_eers)),1)
        self.assertEqual(repr(norm),original_params)

    def test_score_equality_checks_keys_labels_and_values(self):
        images,trials=fixture()
        rows=frozen_face_scores(FixedModel(),images,trials,[0])[0]
        assert_equal_scores(rows,list(reversed(rows)),['face_score_raw'])
        bad=[dict(rows[0],face_score_raw=rows[0]['face_score_raw']+.1)]+rows[1:]
        with self.assertRaises(ValueError):
            assert_equal_scores(rows,bad,['face_score_raw'])
        with self.assertRaises(ValueError):
            assert_equal_scores(rows,rows[:-1],['face_score_raw'])

    def test_synthetic_rq3_orchestration_exports_and_checks_metrics(self):
        import shutil
        from experiments.rq3_blur import run
        from src.fusion import accepted_scores
        from src.files import write_json, read_csv
        pointer=ROOT/'results/metrics/rq2_latest.json'
        if not pointer.exists():
            self.skipTest('Run RQ2 first to supply the orchestration fixture')
        rq2_id=json.loads(pointer.read_text())['run_id']
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'repo'
            shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('__pycache__','.git','raw','processed'))
            original=accepted_scores(root)[-1]['test']
            sweeps={sigma:[dict(r,face_score_raw=r['face_score_raw']-.2*sigma) for r in original]
                    for sigma in [0.,1.]}
            plan_path=root/'synthetic_plan.json'
            plan={'sigmas':[0.,1.], 'purpose':'synthetic orchestration fixture, not research'}
            write_json(plan_path,plan)
            models={'face':FixedModel(),'palm':FixedModel()}
            with patch('experiments.rq3_blur.require_assets'), \
                 patch('experiments.rq3_blur.load_frozen_models',return_value=(models,{})), \
                 patch('experiments.rq3_blur.load_plan',return_value=plan), \
                 patch('experiments.rq3_blur.dataset_images',return_value={'face':fixture()[0]}), \
                 patch('experiments.rq3_blur.frozen_face_scores',return_value=sweeps):
                result=run(rq2_id,plan_path,'synthetic_orchestration_only',root=root)
            self.assertEqual(result['status'],'completed')
            self.assertEqual(len(result['test_metrics']),6)
            self.assertFalse(result['face_model_refitted'])
            rows=read_csv(root/'results/metrics/synthetic_orchestration_only/rq3_blur_scores.csv')
            self.assertEqual(len(rows),2*6084)
            self.assertTrue((root/'results/figures/synthetic_orchestration_only/rq3_comparison.png').exists())

    def test_sigma_zero_tolerance_is_tight(self):
        images,trials=fixture()
        rows=frozen_face_scores(FixedModel(),images,trials,[0])[0]
        small=[dict(r,face_score_raw=r['face_score_raw']+1e-14) for r in rows]
        self.assertLess(assert_equal_scores(rows,small,['face_score_raw'],atol=1e-12),1e-12)
        large=[dict(r,face_score_raw=r['face_score_raw']+1e-8) for r in rows]
        with self.assertRaises(ValueError):
            assert_equal_scores(rows,large,['face_score_raw'],atol=1e-12)

    def test_actual_rq3_stops_before_outputs_when_lfs_unresolved(self):
        from src.fusion import asset_available
        from experiments.rq3_blur import run
        pointer=ROOT/'results/metrics/rq2_latest.json'
        face=ROOT/'data/raw/face/olivetti.npz'
        if not pointer.exists():
            self.skipTest('This intake guard applies to a source-only LFS checkout after RQ2')
        rq2_id=json.loads(pointer.read_text())['run_id']
        with patch('experiments.rq3_blur.require_assets', side_effect=FileNotFoundError('Git LFS pointers')), \
             patch('experiments.rq3_blur.RunArtifacts') as artifacts:
            with self.assertRaisesRegex(FileNotFoundError,'LFS'):
                run(rq2_id,'unused_plan.json',root=ROOT)
            artifacts.assert_not_called()


if __name__=='__main__':
    unittest.main()
