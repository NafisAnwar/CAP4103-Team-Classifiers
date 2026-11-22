from pathlib import Path
from unittest.mock import patch
import json
import shutil
import tempfile
import unittest
from src.experiment_support import load_frozen_models
from src.files import ROOT, MANIFEST_NAMES, manifest_hashes, write_json


class FrozenModelGuardsTest(unittest.TestCase):  # group the regression checks and shared test fixtures for this component
    def setUp(self):  # prepare an isolated fixture before running the relevant regression checks
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.pointer = json.loads((ROOT / 'results/metrics/rq1_accepted.json').read_text())
        metadata = json.loads((ROOT / self.pointer['metadata']).read_text())
        names = ['results/metrics/rq1_accepted.json', self.pointer['metadata'], 'data/manifests/protocol_lock.json']
        names += ['data/manifests/' + name for name in MANIFEST_NAMES]
        names += list(metadata['source_sha256'].keys())  # copy source bytes so only the intended guard is triggered
        names += [(Path(self.pointer['metadata']).parent / name).as_posix() for name in self.pointer['score_sha256']]
        for name in names:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, path)
        self.metadata = metadata

    def assert_rejected_before_deserialization(self, message):  # support the deterministic test fixture and its assertions
        with patch('src.experiment_support.joblib.load') as load:
            with self.assertRaisesRegex(ValueError, message):
                load_frozen_models(self.root)
            load.assert_not_called()

    def test_metadata_tampering_is_rejected(self):  # verify that metadata tampering is rejected
        path = self.root / self.pointer['metadata']
        path.write_bytes(path.read_bytes() + b' ')
        self.assert_rejected_before_deserialization('metadata changed')

    def test_fresh_checkout_line_endings_pass_until_local_models_are_needed(self):  # verify that fresh checkout line endings pass until local models are needed
        for path in self.root.rglob('*'):
            if path.is_file() and path.suffix in ['.csv', '.json']:
                path.write_bytes(path.read_bytes().replace(b'\r\n', b'\n'))  # simulate the repository's lf checkout policy
        with patch('src.experiment_support.joblib.load') as load:
            with self.assertRaises(FileNotFoundError):
                load_frozen_models(self.root)  # all text guards pass before missing ignored models are reached
            load.assert_not_called()

    def test_a_refreshed_lock_cannot_replace_the_accepted_protocol(self):  # verify that a refreshed lock cannot replace the accepted protocol
        path = self.root / 'data/manifests/dataset_summary.json'
        path.write_bytes(path.read_bytes() + b' ')
        write_json(self.root / 'data/manifests/protocol_lock.json', {'schema_version': 1, 'manifest_sha256': manifest_hashes(self.root)})
        self.assert_rejected_before_deserialization('Frozen protocol changed')

    def test_feature_code_and_scores_are_checked(self):  # verify that feature code and scores are checked
        path = self.root / 'src/preprocessing.py'
        before = path.read_bytes()
        path.write_bytes(before + b'\n')
        self.assert_rejected_before_deserialization('implementation changed')
        path.write_bytes(before)
        path = self.root / Path(self.pointer['metadata']).parent / 'validation_scores.csv'
        path.write_bytes(path.read_bytes() + b'\n')
        self.assert_rejected_before_deserialization('scores changed')

    def test_model_bytes_are_checked_before_loading(self):  # verify that model bytes are checked before loading
        path = self.root / self.metadata['models']['face']['path']
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'broken model')
        self.assert_rejected_before_deserialization('face model changed')


if __name__ == '__main__':
    unittest.main()
