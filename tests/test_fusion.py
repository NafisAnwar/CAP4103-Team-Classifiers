from dataclasses import FrozenInstanceError, asdict
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from src.fusion import (Normalizer, fuse_scores, validate_coverage, asset_available,
                        require_assets, accepted_scores, completed_run)
from src.files import ROOT, read_csv, write_json
from src.experiment_support import RunArtifacts
from src.fusion_reporting import verify_metrics
from src.evaluation import evaluate_labeled


def fixtures(prefix='validation'):
    trials = [{'trial_id':f'{prefix}-{i}', 'claimed_user_id':f'u{i%2}', 'is_genuine':i%2}
              for i in range(4)]
    rows = [dict(r, face_score_raw=s, palm_score_raw=p) for r,s,p in
            zip(trials,[-.4,.2,.3,.8],[.1,.7,.2,.6])]
    return trials,rows


def normalizer():
    trials,rows=fixtures()
    return Normalizer.fit(rows,trials,split='validation',validation_sha256='fixture',baseline_id='fixture')


class FusionTest(unittest.TestCase):
    def test_population_zscore_and_no_test_clipping(self):
        norm=normalizer()
        _,rows=fixtures()
        for m in ['face','palm']:
            raw=np.array([r[m+'_score_raw'] for r in rows])
            np.testing.assert_allclose(norm.transform(raw,m),(raw-raw.mean())/raw.std(ddof=0))
            self.assertGreater(norm.transform([10],m)[0],1)

    def test_test_split_and_test_keys_cannot_fit(self):
        trials,rows=fixtures()
        with self.assertRaisesRegex(ValueError,'validation'):
            Normalizer.fit(rows,trials,split='test',validation_sha256='x',baseline_id='x')
        with self.assertRaisesRegex(ValueError,'validation'):
            Normalizer.fit(fixtures('test')[1],fixtures('test')[0],split='validation',validation_sha256='x',baseline_id='x')
        with self.assertRaisesRegex(ValueError,'split'):
            Normalizer.fit(fixtures('test')[1],trials,split='validation',validation_sha256='x',baseline_id='x')

    def test_fit_is_frozen_and_round_trips(self):
        norm=normalizer()
        with self.assertRaises(FrozenInstanceError):
            norm.face_mean=5
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'norm.json'
            norm.save(path,{'purpose':'synthetic test'})
            self.assertEqual(asdict(norm),asdict(Normalizer.load(path)))
            with self.assertRaises(FileExistsError):
                norm.save(path,{})

    def test_nonfinite_or_constant_parameters_fail(self):
        values=asdict(normalizer())
        for field,value in [('face_std',0),('palm_std',1e-14),('face_mean',float('nan'))]:
            with self.assertRaises(ValueError):
                Normalizer(**dict(values,**{field:value}))
        with self.assertRaises(ValueError):
            normalizer().transform([float('inf')],'face')

    def test_keyed_join_equal_weights_and_raw_preservation(self):
        trials,rows=fixtures()
        norm=normalizer()
        fused=fuse_scores(rows,list(reversed(rows)),norm,trials)
        self.assertEqual([r['face_score_raw'] for r in fused],[r['face_score_raw'] for r in rows])
        self.assertEqual([r['palm_score_raw'] for r in fused],[r['palm_score_raw'] for r in rows])
        for r in fused:
            self.assertEqual(r['fusion_score'],.5*r['face_score_normalized']+.5*r['palm_score_normalized'])

    def test_join_rejects_missing_duplicate_wrong_labels_and_nonfinite(self):
        trials,rows=fixtures()
        variants=[rows[:-1],rows+[rows[0]], [dict(rows[0],is_genuine=1)]+rows[1:],
                  [dict(rows[0],palm_score_raw=float('nan'))]+rows[1:]]
        for bad in variants:
            with self.assertRaises(ValueError):
                fuse_scores(rows,bad,normalizer(),trials)

    def test_coverage_rejects_matching_but_wrong_subset(self):
        trials,rows=fixtures()
        with self.assertRaises(ValueError):
            fuse_scores(rows[:-1],rows[:-1],normalizer(),trials)
        with self.assertRaises(ValueError):
            validate_coverage([dict(rows[0],is_genuine=.5)]+rows[1:],trials)

    def test_lfs_pointers_are_not_model_or_image_assets(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'face.joblib'
            self.assertFalse(asset_available(path))
            path.write_text('version https://git-lfs.github.com/spec/v1\noid sha256:000\nsize 10\n')
            self.assertFalse(asset_available(path))
            with self.assertRaisesRegex(FileNotFoundError,'LFS'):
                require_assets([path])
            path.write_bytes(b'actual bytes')
            self.assertTrue(asset_available(path))

    def test_accepted_score_counts_and_validation_parameters(self):
        pointer,_,_,_,trials,tables=accepted_scores()
        self.assertEqual(len(tables['validation']),3042)
        self.assertEqual(len(tables['test']),6084)
        norm=Normalizer.fit(tables['validation'],trials['validation'],split='validation',
                            validation_sha256=pointer['score_sha256']['validation_scores.csv'],
                            baseline_id=pointer['run_id'])
        self.assertEqual(norm.validation_count,3042)
        self.assertEqual(norm.face_mean,np.mean([r['face_score_raw'] for r in tables['validation']]))

    def test_exported_rq2_metrics_recompute_when_run_exists(self):
        pointer=ROOT/'results/metrics/rq2_latest.json'
        if not pointer.exists():
            self.skipTest('Run RQ2 to verify exported real scores')
        run_id=json.loads(pointer.read_text())['run_id']
        folder,metadata=completed_run(ROOT,run_id,'rq2')
        rows=read_csv(folder/'rq2_fusion_scores.csv')
        verify_metrics(rows,metadata['test_metrics'])
        norm=Normalizer.load(folder/'normalizer.json')
        _,_,_,_,trials,tables=accepted_scores()
        expected=fuse_scores(tables['test'],tables['test'],norm,trials['test'])
        for actual,wanted in zip(rows,expected):
            for field in ['face_score_raw','palm_score_raw','face_score_normalized','palm_score_normalized','fusion_score']:
                self.assertEqual(float(actual[field]),wanted[field])

    def test_rq2_pointer_does_not_change_rq1(self):
        provenance={'source_sha256':{},'manifest_sha256':{},'protocol_lock_sha256':'x',
                    'git_commit_at_run':None,'packages':{}}
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            original=root/'results/metrics/rq1_latest.json'
            write_json(original,{'run_id':'original'})
            before=original.read_bytes()
            with patch('src.experiment_support.capture_provenance',return_value=provenance):
                with RunArtifacts(root,'fusion',latest_name='rq2_latest.json') as run:
                    p=run.metrics_dir/'scores.csv'
                    p.write_text('score\n1\n')
                    run.complete({},[p])
            self.assertEqual(original.read_bytes(),before)
            self.assertTrue((root/'results/metrics/rq2_latest.json').exists())
        with self.assertRaises(ValueError):
            RunArtifacts(latest_name='../bad.json')


if __name__=='__main__':
    unittest.main()
