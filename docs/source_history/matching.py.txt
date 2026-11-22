import numpy as np


def unit_vectors(features):
    features = np.asarray(features, dtype=float)
    if features.ndim != 2 or not len(features) or not np.isfinite(features).all():
        raise ValueError('Expected a nonempty finite feature matrix')
    norms = np.linalg.norm(features, axis=1, keepdims=True)
    if np.any(norms <= 1e-12):
        raise ValueError('Zero feature vector cannot define cosine similarity')
    return features / norms


class TemplateMatcher:
    def fit(self, features, users):
        features = unit_vectors(features)
        users = np.asarray(users, dtype=str)
        if users.shape != (len(features),) or len(np.unique(users)) < 2:
            raise ValueError('Need one identity per sample and at least two identities')
        self.classes_ = np.unique(users)
        self.templates_ = unit_vectors(np.array([features[users == user].mean(axis=0) for user in self.classes_]))
        return self

    def score_matrix(self, features):
        if not hasattr(self, 'templates_'):
            raise ValueError('Matcher is not fitted')
        features = unit_vectors(features)
        if features.shape[1] != self.templates_.shape[1]:
            raise ValueError('Probe and enrollment feature dimensions differ')
        return np.clip(features @ self.templates_.T, -1, 1)


def score_trials(model, samples, trials, modality):
    if modality not in ['face', 'palm'] or not trials:
        raise ValueError('Need face/palm trials')
    keys = [(row['trial_id'], row['claimed_user_id']) for row in trials]
    if len(set(keys)) != len(keys) or len({row['trial_id'] for row in trials}) != len(trials):
        raise ValueError('Duplicate claim or trial keys')
    field = f'{modality}_test_sample_id'
    probes = sorted({row[field] for row in trials})
    if set(probes) != set(samples):
        raise ValueError('Probe images must match the manifest exactly')
    matrix = model.score_matrix(np.stack([samples[key] for key in probes]))
    classes = list(model.classes_)
    if matrix.shape != (len(probes), len(classes)) or not np.isfinite(matrix).all():
        raise ValueError('Invalid score matrix')
    probe_index, class_index = {key: i for i, key in enumerate(probes)}, {key: i for i, key in enumerate(classes)}
    rows = []
    for row in trials:
        claim = row['claimed_user_id']
        if claim not in class_index or int(row['is_genuine']) != int(row['simulated_true_user'] == claim):
            raise ValueError('Unknown claim or inconsistent genuine label')
        rows.append({'trial_id': row['trial_id'], 'claimed_user_id': claim,
                     'is_genuine': int(row['is_genuine']),
                     f'{modality}_score_raw': float(matrix[probe_index[row[field]], class_index[claim]])})
    return rows


def combine_raw_scores(face_rows, palm_rows):
    def index_rows(rows):
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
        joined.append(row)
    return joined
