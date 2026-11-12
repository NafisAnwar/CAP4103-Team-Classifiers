import unittest
import numpy as np
from PIL import Image
from src.datasets import parse_palm_name
from src.preprocessing import crop_palm


class DatasetTest(unittest.TestCase):
    def test_palm_labels_are_explicit(self):
        self.assertEqual(parse_palm_name('032_S_R_19.JPG'), {'subject': '032', 'session': 'S', 'hand': 'R', 'number': '19'})
        with self.assertRaises(ValueError):
            parse_palm_name('unknown_19.JPG')

    def test_roi_rejects_missing_skin_and_crops_interior(self):
        pixels = np.zeros((300, 260, 3), dtype=np.uint8)
        pixels[40:260, 30:230] = [180, 120, 95]
        roi = crop_palm(Image.fromarray(pixels))
        self.assertEqual(roi.shape, (128, 128))
        self.assertGreater(roi.min(), 0.3)
        with self.assertRaises(ValueError):
            crop_palm(Image.fromarray(np.zeros_like(pixels)))


if __name__ == '__main__':
    unittest.main()
