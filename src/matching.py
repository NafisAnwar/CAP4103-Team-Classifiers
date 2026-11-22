import numpy as np


def unit_vectors(features):  # normalize nonzero feature vectors so dot products represent cosine similarity
    features = np.asarray(features, dtype=float)
    if features.ndim != 2 or not len(features) or not np.isfinite(features).all():
        raise ValueError('Expected a nonempty finite feature matrix')
    norms = np.linalg.norm(features, axis=1, keepdims=True)  # calculate each feature vector magnitude before cosine normalization
    if np.any(norms <= 1e-12):
        raise ValueError('Zero feature vector cannot define cosine similarity')
    return features / norms  # scale each nonzero feature vector to unit length


class TemplateMatcher:  # enroll one normalized mean feature template for each simulated identity
    def fit(self, features, users):  # create a deterministic template matrix ordered by enrolled user identifier
        features = unit_vectors(features)
        users = np.asarray(users, dtype=str)
        if users.shape != (len(features),) or len(np.unique(users)) < 2:
            raise ValueError('Need one identity per sample and at least two identities')
        self.classes_ = np.unique(users)  # establish a stable column order for enrolled identities
        self.templates_ = unit_vectors(np.array([features[users == user].mean(axis=0) for user in self.classes_]))  # average normalized enrollment vectors by identity and renormalize each centroid
        return self

    def score_matrix(self, features):  # compute all probe-to-template cosine similarities without refitting
        if not hasattr(self, 'templates_'):
            raise ValueError('Matcher is not fitted')
        features = unit_vectors(features)
        if features.shape[1] != self.templates_.shape[1]:
            raise ValueError('Probe and enrollment feature dimensions differ')
        return np.clip(features @ self.templates_.T, -1, 1)  # compute cosine similarities as matrix dot products bounded to the valid range


def score_trials(model, samples, trials, modality):  # extract the requested claimed-identity score for each manifest trial
    if modality not in ['face', 'palm'] or not trials:
        raise ValueError('Need face/palm trials')
    keys = [(row['trial_id'], row['claimed_user_id']) for row in trials]
    if len(set(keys)) != len(keys) or len({row['trial_id'] for row in trials}) != len(trials):
        raise ValueError('Duplicate claim or trial keys')
    field = f'{modality}_test_sample_id'
    probes = sorted({row[field] for row in trials})  # score each distinct probe once rather than repeating feature extraction for every claim
    if set(probes) != set(samples):
        raise ValueError('Probe images must match the manifest exactly')
    matrix = model.score_matrix(np.stack([samples[key] for key in probes]))  # calculate the complete probe-by-enrolled-user similarity matrix
    classes = list(model.classes_)
    if matrix.shape != (len(probes), len(classes)) or not np.isfinite(matrix).all():
        raise ValueError('Invalid score matrix')
    probe_index, class_index = {key: i for i, key in enumerate(probes)}, {key: i for i, key in enumerate(classes)}  # map explicit sample and identity keys to the correct matrix coordinates
    rows = []
    for row in trials:
        claim = row['claimed_user_id']  # select the alleged enrolled identity, not the highest-scoring identity
        if claim not in class_index or int(row['is_genuine']) != int(row['simulated_true_user'] == claim):
            raise ValueError('Unknown claim or inconsistent genuine label')
        rows.append({'trial_id': row['trial_id'], 'claimed_user_id': claim,
                     'is_genuine': int(row['is_genuine']),
                     f'{modality}_score_raw': float(matrix[probe_index[row[field]], class_index[claim]])})
    return rows


def combine_raw_scores(face_rows, palm_rows):  # join modality scores by claim keys while preserving the raw values
    def index_rows(rows):  # prevent repeated claim keys from hiding mismatched modality rows
        index = {(row['trial_id'], row['claimed_user_id']): row for row in rows}
        if len(index) != len(rows):
            raise ValueError('Duplicate score key')
        return index
    faces, palms = index_rows(face_rows), index_rows(palm_rows)
    if not faces or faces.keys() != palms.keys():
        raise ValueError('Modality score keys differ')
    joined = []
    for key, face in faces.items():
        palm = palms[key]
        if int(face['is_genuine']) != int(palm['is_genuine']):
            raise ValueError('Modality ground-truth labels differ')
        row = dict(face, palm_score_raw=palm['palm_score_raw'])
        if not np.isfinite([row['face_score_raw'], row['palm_score_raw']]).all():
            raise ValueError('Nonfinite matching score')
        joined.append(row)  # retain one aligned genuine or impostor row with both raw modality scores
    return joined
