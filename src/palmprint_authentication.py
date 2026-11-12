import numpy as np
from skimage.feature import hog, local_binary_pattern
from src.matching import TemplateMatcher
from src.preprocessing import validate_images


class PalmAuthenticator:
    def __init__(self, feature='hog'):
        if feature not in ['hog', 'lbp']:
            raise ValueError('Choose hog or lbp palm features')
        self.feature = feature

    def features(self, images):
        images = validate_images(images)
        if images.shape[1:] != (128, 128):
            raise ValueError('Expected 128x128 palm ROIs')
        features = []
        for image in images:
            if self.feature == 'hog':
                vector = hog(image, orientations=9, pixels_per_cell=(16, 16),
                             cells_per_block=(2, 2), block_norm='L2-Hys', transform_sqrt=True)
            else:
                codes = local_binary_pattern(np.rint(image * 255).astype(np.uint8), 16, 2, method='uniform')
                cells = []
                for y in range(0, 128, 32):
                    for x in range(0, 128, 32):
                        hist = np.bincount(codes[y:y + 32, x:x + 32].astype(int).ravel(), minlength=18)
                        cells.extend(np.sqrt(hist / hist.sum()))
                vector = np.asarray(cells)
            features.append(vector)
        return np.asarray(features)

    def fit(self, images, users):
        self.matcher_ = TemplateMatcher().fit(self.features(images), users)
        self.classes_ = self.matcher_.classes_
        return self

    def score_matrix(self, images):
        if not hasattr(self, 'matcher_'):
            raise ValueError('Palm model is not fitted')
        return self.matcher_.score_matrix(self.features(images))
