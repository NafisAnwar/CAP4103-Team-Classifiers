import unittest
import numpy as np
from src.matching import TemplateMatcher, score_trials, combine_raw_scores
from src.face_authentication import FaceAuthenticator
from src.palmprint_authentication import PalmAuthenticator


class MatchingTest(unittest.TestCase):
    def test_sorted_classes_and_claim_lookup_independent_of_probe_order(self):
        matcher = TemplateMatcher().fit([[0, 1], [0, 0.9], [1, 0], [0.9, 0]], ['b', 'b', 'a', 'a'])
        self.assertEqual(list(matcher.classes_), ['a', 'b'])
        np.testing.assert_allclose(matcher.score_matrix([[1, 0], [0, 1]]), [[1, 0], [0, 1]])
        class Adapter:
            classes_ = matcher.classes_
            def score_matrix(self, images):
                return matcher.score_matrix(images.reshape(len(images), -1))
        trials = [{'trial_id': 'one', 'claimed_user_id': 'b', 'simulated_true_user': 'a', 'is_genuine': 0, 'face_test_sample_id': 'z'},
                  {'trial_id': 'two', 'claimed_user_id': 'a', 'simulated_true_user': 'a', 'is_genuine': 1, 'face_test_sample_id': 'z'}]
        rows = score_trials(Adapter(), {'z': np.array([[1, 0]])}, trials, 'face')
        self.assertEqual([row['face_score_raw'] for row in rows], [0, 1])
        with self.assertRaises(ValueError):
            score_trials(Adapter(), {}, trials, 'face')

    def test_paired_raw_scores_join_on_keys_and_reject_corruption(self):
        face = [{'trial_id': str(i), 'claimed_user_id': 'a', 'is_genuine': i % 2, 'face_score_raw': 0.1 * i} for i in range(4)]
        palm = [{k: v for k, v in row.items() if k != 'face_score_raw'} | {'palm_score_raw': row['face_score_raw'] + 0.2} for row in reversed(face)]
        rows = combine_raw_scores(face, palm)
        np.testing.assert_allclose([row['palm_score_raw'] for row in rows], [0.2, 0.3, 0.4, 0.5])
        with self.assertRaises(ValueError):
            combine_raw_scores(face, palm[:-1])
        with self.assertRaises(ValueError):
            combine_raw_scores(face, palm + palm[:1])
        palm[0]['is_genuine'] = 1 - palm[0]['is_genuine']
        with self.assertRaises(ValueError):
            combine_raw_scores(face, palm)

    def test_face_model_is_repeatable_and_scoring_does_not_refit(self):
        rng = np.random.default_rng(42)
        images = rng.random((12, 8, 8), dtype=np.float32)
        labels = ['b'] * 6 + ['a'] * 6
        one, two = FaceAuthenticator(4).fit(images, labels), FaceAuthenticator(4).fit(images, labels)
        before = one.pca_.components_.copy()
        score = one.score_matrix(images[:2])
        np.testing.assert_allclose(score, two.score_matrix(images[:2]))
        np.testing.assert_allclose(score[0], one.score_matrix(images[:1])[0], rtol=1e-10, atol=1e-10)
        np.testing.assert_array_equal(before, one.pca_.components_)
        self.assertEqual(score.shape, (2, 2))
        with self.assertRaises(ValueError):
            one.score_matrix(images[:, :4, :4])
        with self.assertRaises(ValueError):
            FaceAuthenticator(12).fit(images, labels)

    def test_palm_feature_dimensions_and_finite_scoring(self):
        images = np.random.default_rng(42).random((4, 128, 128), dtype=np.float32)
        for feature, dimension in [('hog', 1764), ('lbp', 288)]:
            model = PalmAuthenticator(feature).fit(images, ['a', 'a', 'b', 'b'])
            self.assertEqual(model.features(images[:1]).shape, (1, dimension))
            self.assertTrue(np.isfinite(model.score_matrix(images[:1])).all())
        with self.assertRaises(ValueError):
            TemplateMatcher().fit([[0, 0], [1, 0]], ['a', 'b'])


if __name__ == '__main__':
    unittest.main()
