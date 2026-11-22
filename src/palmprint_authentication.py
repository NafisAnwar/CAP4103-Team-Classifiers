import numpy as np
from skimage.feature import hog, local_binary_pattern
from src.matching import TemplateMatcher
from src.preprocessing import validate_images


class PalmAuthenticator:  # extract palm texture features and compare enrolled identity templates
    def __init__(self, feature='hog'):  # retain the selected candidate descriptor for validation model selection
        if feature not in ['hog', 'lbp']:
            raise ValueError('Choose hog or lbp palm features')
        self.feature = feature

    def features(self, images):  # encode normalized palm crops with hog or the alternative local binary pattern descriptor
        images = validate_images(images)
        if images.shape[1:] != (128, 128):
            raise ValueError('Expected 128x128 palm ROIs')
        features = []
        for image in images:
            if self.feature == 'hog':  # evaluate the validated hog candidate or its lbp alternative
                vector = hog(image, orientations=9, pixels_per_cell=(16, 16),
                             cells_per_block=(2, 2), block_norm='L2-Hys', transform_sqrt=True)  # use nine orientation bins and normalized overlapping hog blocks
            else:
                codes = local_binary_pattern(np.rint(image * 255).astype(np.uint8), 16, 2, method='uniform')  # encode neighborhood texture with uniform circular lbp codes
                cells = []
                for y in range(0, 128, 32):
                    for x in range(0, 128, 32):
                        hist = np.bincount(codes[y:y + 32, x:x + 32].astype(int).ravel(), minlength=18)  # summarize local texture frequencies within each spatial cell
                        cells.extend(np.sqrt(hist / hist.sum()))  # apply square-root histogram normalization before concatenation
                vector = np.asarray(cells)
            features.append(vector)  # keep descriptor ordering aligned with the corresponding input images
        return np.asarray(features)

    def fit(self, images, users):  # enroll user centroids from extracted palm features
        self.matcher_ = TemplateMatcher().fit(self.features(images), users)  # enroll the palm feature vectors under their mapped user labels
        self.classes_ = self.matcher_.classes_
        return self

    def score_matrix(self, images):  # score probe descriptors against the frozen enrollment templates
        if not hasattr(self, 'matcher_'):
            raise ValueError('Palm model is not fitted')
        return self.matcher_.score_matrix(self.features(images))
