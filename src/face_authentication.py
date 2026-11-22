from sklearn.decomposition import PCA
import numpy as np
from src.matching import TemplateMatcher
from src.preprocessing import validate_images


class FaceAuthenticator:  # represent grayscale facial images with enrollment-fitted eigenface features
    def __init__(self, n_components=32, seed=42):  # retain the candidate pca dimension and deterministic randomized solver seed
        self.n_components, self.seed = n_components, seed

    def fit(self, images, users):  # learn the pca basis and user centroids from enrollment images only
        images = validate_images(images)
        self.image_shape_ = images.shape[1:]
        vectors = images.reshape(len(images), -1).astype(np.float64)  # flatten each image into a pixel vector for the pca transform
        if not isinstance(self.n_components, int) or not 1 <= self.n_components < min(vectors.shape):
            raise ValueError('PCA components must be below enrollment sample and pixel counts')
        self.pca_ = PCA(n_components=self.n_components, svd_solver='randomized', random_state=self.seed)  # configure a seeded randomized principal component decomposition
        features = self.pca_.fit_transform(vectors)  # learn and apply the principal component basis on enrollment only
        self.matcher_ = TemplateMatcher().fit(features, users)  # create one cosine template per enrolled identity from the learned features
        self.classes_ = self.matcher_.classes_
        return self

    def score_matrix(self, images):  # transform unseen face images with frozen pca and score every enrolled identity
        if not hasattr(self, 'pca_'):
            raise ValueError('Face model is not fitted')
        images = validate_images(images)
        if images.shape[1:] != self.image_shape_:
            raise ValueError('Face probe dimensions differ from enrollment')
        features = self.pca_.transform(images.reshape(len(images), -1).astype(np.float64))  # reuse the learned face basis without fitting to probe pixels
        return self.matcher_.score_matrix(features)
