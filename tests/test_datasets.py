import unittest
import numpy as np
from PIL import Image
from src.datasets import parse_palm_name
from src.preprocessing import crop_palm
from src.datasets import dataset_images
from unittest.mock import patch
import hashlib
import tempfile
from pathlib import Path


class DatasetTest(unittest.TestCase):  # group the regression checks and shared test fixtures for this component
    def test_shared_image_loader_checks_pixels_and_preserves_the_palm_crop(self):  # verify that shared image loader checks pixels and preserves the palm crop
        pixels = np.full((300, 260, 3), [180, 120, 95], dtype=np.uint8)
        face = np.zeros((1, 64, 64), dtype=np.float32)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / 'palm.png'
            Image.fromarray(pixels).save(path)
            rows = [{'modality': 'face', 'split': 'validation', 'original_sample_id': 'face',
                     'source_path_or_key': 'faces#0', 'pixel_sha256': hashlib.sha256(face[0].tobytes()).hexdigest()},
                    {'modality': 'palm', 'split': 'validation', 'original_sample_id': 'palm', 'source_path_or_key': 'palm.png',
                     'pixel_sha256': hashlib.sha256(str((260, 300)).encode() + pixels.tobytes()).hexdigest()}]
            with patch('src.datasets.load_faces', return_value=(face, np.array([0]))):
                images = dataset_images(rows, 'validation', root)
                np.testing.assert_array_equal(images['face']['face'], face[0])
                np.testing.assert_array_equal(images['palm']['palm'], crop_palm(Image.fromarray(pixels)))
                rows[1]['pixel_sha256'] = 'changed'
                with self.assertRaisesRegex(ValueError, 'changed since audit'):
                    dataset_images(rows, 'validation', root)  # a modified source never silently enters a later experiment

    def test_palm_labels_are_explicit(self):  # verify that palm labels are explicit
        self.assertEqual(parse_palm_name('032_S_R_19.JPG'), {'subject': '032', 'session': 'S', 'hand': 'R', 'number': '19'})
        with self.assertRaises(ValueError):
            parse_palm_name('unknown_19.JPG')

    def test_roi_rejects_missing_skin_and_crops_interior(self):  # verify that roi rejects missing skin and crops interior
        pixels = np.zeros((300, 260, 3), dtype=np.uint8)
        pixels[40:260, 30:230] = [180, 120, 95]
        roi = crop_palm(Image.fromarray(pixels))
        self.assertEqual(roi.shape, (128, 128))
        self.assertGreater(roi.min(), 0.3)
        with self.assertRaises(ValueError):
            crop_palm(Image.fromarray(np.zeros_like(pixels)))


if __name__ == '__main__':
    unittest.main()
