from pathlib import Path
from unittest.mock import patch
import json
import tempfile
import unittest
from src.experiment_support import RunArtifacts
from src.files import write_json, text_sha256, sha256


class RunArtifactsTest(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.pointer = self.root / 'results/metrics/rq1_latest.json'
        write_json(self.pointer, {'run_id': 'old'})
        self.before = self.pointer.read_bytes()
        self.provenance = {'source_sha256': {'src/example.py': 'one'}, 'manifest_sha256': {},
                           'protocol_lock_sha256': 'lock', 'git_commit_at_run': 'commit', 'packages': {}}

    def status(self, name):
        return json.loads((self.root / 'results/metrics' / name / 'run_status.json').read_text())['status']

    def test_exception_is_recorded_and_latest_is_unchanged(self):
        with patch('src.experiment_support.capture_provenance', return_value=self.provenance):
            with self.assertRaisesRegex(RuntimeError, 'interrupted'):
                with RunArtifacts(self.root, 'broken') as run:
                    self.assertEqual(self.status('broken'), 'running')
                    raise RuntimeError('interrupted') #simulate failure after output folders exist
        self.assertEqual(self.status('broken'), 'failed')
        self.assertEqual(self.before, self.pointer.read_bytes())

    def test_model_only_collision_is_rejected_without_other_outputs(self):
        (self.root / 'data/processed/models/existing').mkdir(parents=True)
        with self.assertRaises(FileExistsError):
            with RunArtifacts(self.root, 'existing'):
                self.fail('collision must be rejected before entering')
        self.assertFalse((self.root / 'results/metrics/existing').exists())

    def test_source_changes_and_missing_artifacts_prevent_completion(self):
        changed = dict(self.provenance, source_sha256={'src/example.py': 'two'})
        for name, end in [('changed', changed), ('missing', self.provenance)]:
            with patch('src.experiment_support.capture_provenance', side_effect=[self.provenance, end]):
                with self.assertRaises(ValueError):
                    with RunArtifacts(self.root, name) as run:
                        run.complete({}, [run.metrics_dir / 'absent.csv'])
            self.assertEqual(self.status(name), 'failed')
            self.assertEqual(self.before, self.pointer.read_bytes())

    def test_completed_run_publishes_artifact_hashes_and_latest(self):
        with patch('src.experiment_support.capture_provenance', return_value=self.provenance):
            with RunArtifacts(self.root, 'good') as run:
                artifact = run.metrics_dir / 'scores.csv'
                artifact.write_text('score\n0.5\n')
                metadata = run.complete({}, [artifact])
        self.assertEqual(self.status('good'), 'completed')
        self.assertEqual(json.loads(self.pointer.read_text())['run_id'], 'good')
        self.assertIn('results/metrics/good/scores.csv', metadata['artifact_sha256'])

    def test_atomic_json_failure_preserves_existing_file_and_cleans_temporary(self):
        before_files = set(self.pointer.parent.iterdir())
        with patch('src.files.os.replace', side_effect=OSError('simulated disk error')):
            with self.assertRaises(OSError):
                write_json(self.pointer, {'run_id': 'new'})
        self.assertEqual(self.before, self.pointer.read_bytes())
        self.assertEqual(before_files, set(self.pointer.parent.iterdir()))

    def test_pointer_publication_failure_marks_metadata_failed(self):
        def write_or_fail(path, value):
            if path == self.pointer:
                raise OSError('pointer publication failed')
            write_json(path, value)
        with patch('src.experiment_support.capture_provenance', return_value=self.provenance):
            with patch('src.experiment_support.write_json', side_effect=write_or_fail):
                with self.assertRaises(OSError):
                    with RunArtifacts(self.root, 'unpublished') as run:
                        artifact = run.metrics_dir / 'scores.csv'
                        artifact.write_text('score\n0.5\n')
                        run.complete({}, [artifact])
        self.assertEqual(self.status('unpublished'), 'failed')
        saved = json.loads((run.metrics_dir / 'run_metadata.json').read_text())
        self.assertEqual(saved['status'], 'failed')
        self.assertEqual(self.before, self.pointer.read_bytes())

    def test_text_hash_allows_only_line_ending_changes(self):
        path = self.root / 'scores.csv'
        path.write_bytes(b'score\r\n0.5\r\n')
        expected, raw = text_sha256(path), sha256(path)
        path.write_bytes(b'score\n0.5\n')
        self.assertEqual(text_sha256(path), expected)
        self.assertNotEqual(sha256(path), raw)
        path.write_bytes(b'score\n0.6\n')
        self.assertNotEqual(text_sha256(path), expected)


if __name__ == '__main__':
    unittest.main()
