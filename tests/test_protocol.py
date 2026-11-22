from pathlib import Path
import tempfile
import unittest
from src.files import write_csv, read_csv, write_json, manifest_hashes
from src.trial_protocol import build_protocol, validate_partitions, validate_trials, make_trials, load_protocol
from src.datasets import audit_datasets


class ProtocolTest(unittest.TestCase):  # group the regression checks and shared test fixtures for this component
    def setUp(self):  # prepare an isolated fixture before running the relevant regression checks
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)
        faces, palms = [], []
        for subject in range(3):
            for number in range(10):
                faces.append({'subject_id': str(subject), 'sample_id': f'face_{subject}_{number}',
                              'status': 'usable', 'array_index': subject * 10 + number,
                              'pixel_sha256': f'face_{subject}_{number}'})
                palms.append({'subject_id': f'{subject:03d}', 'sample_id': f'palm_{subject}_{number}',
                              'session': 'F' if number < 6 else 'S', 'hand': 'R',
                              'status': 'usable', 'source_path': f'data/raw/palm/{subject}_{number}.JPG',
                              'pixel_sha256': f'palm_{subject}_{number}'})
        write_csv(self.root / 'data/manifests/face_samples.csv', faces)
        write_csv(self.root / 'data/manifests/palm_samples.csv', palms)
        write_csv(self.root / 'data/manifests/palm_subject_counts.csv', [{'subject_id': 'fixture'}])
        write_json(self.root / 'data/manifests/dataset_summary.json', {'fixture': True})
        self.addCleanup(self.folder.cleanup)

    def test_seeded_manifest_is_repeatable_and_session_separated(self):  # verify that seeded manifest is repeatable and session separated
        config = build_protocol(self.root)
        path = self.root / 'data/manifests/partitions.csv'
        first = path.read_bytes()
        build_protocol(self.root, rebuild=True)  # an intentional repeat has to say it will replace the protocol
        self.assertEqual(first, path.read_bytes())
        self.assertEqual(config['trial_counts'], {'validation': 18, 'test': 36})
        rows = read_csv(path)
        self.assertTrue(all(row['session_if_available'] == 'S' for row in rows if row['modality'] == 'palm' and row['split'] == 'test'))

    def test_duplicate_pixels_across_splits_are_rejected(self):  # verify that duplicate pixels across splits are rejected
        build_protocol(self.root)
        rows = read_csv(self.root / 'data/manifests/partitions.csv')
        faces = [row for row in rows if row['modality'] == 'face']
        faces[5]['pixel_sha256'] = faces[0]['pixel_sha256']
        with self.assertRaises(ValueError):
            validate_partitions(rows)

    def test_claim_labels_missing_rows_and_wrong_split_are_rejected(self):  # verify that claim labels missing rows and wrong split are rejected
        build_protocol(self.root)
        rows = read_csv(self.root / 'data/manifests/partitions.csv')
        trials = make_trials(rows, 'test')
        validate_trials(trials, rows, 'test')
        for invalid in [trials[:-1], [trials[0]] + trials[1:-1] + [trials[0]]]:
            with self.assertRaises(ValueError):
                validate_trials(invalid, rows, 'test')
        trials[0]['is_genuine'] = 1 - trials[0]['is_genuine']
        with self.assertRaises(ValueError):
            validate_trials(trials, rows, 'test')

    def test_mapping_or_palm_session_corruption_is_rejected(self):  # verify that mapping or palm session corruption is rejected
        build_protocol(self.root)
        load_protocol(self.root)
        path = self.root / 'data/manifests/identity_mapping.csv'
        mapping = read_csv(path)
        mapping[0]['face_subject_id'] = 'incorrect'
        write_csv(path, mapping)
        with self.assertRaises(ValueError):
            load_protocol(self.root)
        rows = read_csv(self.root / 'data/manifests/partitions.csv')
        next(row for row in rows if row['modality'] == 'palm')['session_if_available'] = 'wrong'
        with self.assertRaises(ValueError):
            validate_partitions(rows)

    def test_existing_audit_and_protocol_require_explicit_rebuild(self):  # verify that existing audit and protocol require explicit rebuild
        with self.assertRaises(FileExistsError):
            audit_datasets(self.root)  # this must fail before trying to read any raw data
        build_protocol(self.root)
        before = manifest_hashes(self.root)
        with self.assertRaises(FileExistsError):
            build_protocol(self.root)
        self.assertEqual(before, manifest_hashes(self.root))

    def test_even_structurally_valid_manifest_edits_break_the_lock(self):  # verify that even structurally valid manifest edits break the lock
        build_protocol(self.root)
        path = self.root / 'data/manifests/partitions.csv'
        rows = read_csv(path)
        rows[0]['source_path_or_key'] = 'changed_source'
        write_csv(path, rows)
        validate_partitions(rows)  # structural checks alone would accept this change
        with self.assertRaisesRegex(ValueError, 'Frozen protocol changed'):
            load_protocol(self.root)


if __name__ == '__main__':
    unittest.main()
