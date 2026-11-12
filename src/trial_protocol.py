from collections import Counter
from pathlib import Path
import json
import numpy as np
from src.files import ROOT, read_csv, write_csv, write_json, guard_manifest_rebuild, manifest_hashes, verify_manifest_hashes


def validate_partitions(rows):
    if not rows:
        raise ValueError('No partition rows')
    samples, pixels, users = set(), set(), set()
    for row in rows:
        if row['modality'] not in ['face', 'palm'] or not row['pixel_sha256']:
            raise ValueError('Unknown modality or missing image hash')
        if row['modality'] == 'palm' and (row['palm_hand_if_applicable'] != 'R' or row['session_if_available'] != ('S' if row['split'] == 'test' else 'F')):
            raise ValueError('Palm hand or session conflicts with the fixed protocol')
        key = row['modality'], row['original_sample_id'] #one sample can belong to only one partition
        digest = row['modality'], row['pixel_sha256'] #renaming a copied image must not hide leakage
        if key in samples or digest in pixels:
            raise ValueError('Repeated sample or decoded image pixels across partitions')
        if row['split'] not in ['enrollment', 'validation', 'test']:
            raise ValueError('Unknown split')
        samples.add(key)
        pixels.add(digest)
        users.add(row['simulated_user_id'])
    for modality in ['face', 'palm']:
        originals = set()
        for user in users:
            group = [row for row in rows if row['modality'] == modality and row['simulated_user_id'] == user]
            splits = {row['split'] for row in group}
            if splits != {'enrollment', 'validation', 'test'}:
                raise ValueError('Each mapped user needs all three splits in each modality')
            subjects = {row['original_subject_id'] for row in group}
            if len(subjects) != 1 or subjects & originals:
                raise ValueError('Each simulated user must map to one distinct source subject per modality')
            originals.update(subjects)


def make_trials(partitions, split):
    if split not in ['validation', 'test']:
        raise ValueError('Claims may use validation or test probes only')
    validate_partitions(partitions)
    users = sorted({row['simulated_user_id'] for row in partitions})
    if len(users) < 2:
        raise ValueError('At least two enrolled users required')
    trials = []
    for user in users:
        probes = {}
        for modality in ['face', 'palm']:
            probes[modality] = sorted([row['original_sample_id'] for row in partitions if row['modality'] == modality
                                      and row['simulated_user_id'] == user and row['split'] == split])
        if not probes['face'] or len(probes['face']) != len(probes['palm']):
            raise ValueError('Both modalities need the same nonzero probe count')
        for index, (face, palm) in enumerate(zip(probes['face'], probes['palm'])):
            for claim in users:
                trials.append({'trial_id': f'{split}-{user}-p{index:02d}-{claim}',
                               'simulated_true_user': user, 'face_test_sample_id': face,
                               'palm_test_sample_id': palm, 'claimed_user_id': claim,
                               'is_genuine': int(user == claim), 'pair_index': index})
    return trials


def validate_trials(trials, partitions, split):
    expected = make_trials(partitions, split) #compare against every genuine and impostor claim
    fields = list(expected[0])
    key = lambda row: tuple(str(row[field]) for field in fields)
    if len(trials) != len(expected) or {key(row) for row in trials} != {key(row) for row in expected}:
        raise ValueError('Trial manifest has duplicate, missing, relabeled or wrong-split claims')


def load_protocol(root=ROOT):
    manifest = Path(root) / 'data/manifests'
    lock = json.loads((manifest / 'protocol_lock.json').read_text(encoding='utf-8'))
    verify_manifest_hashes(lock['manifest_sha256'], root) #check bytes before trusting labels or trial counts
    config = json.loads((manifest / 'config.json').read_text())
    partitions = read_csv(manifest / 'partitions.csv')
    validate_partitions(partitions)
    mapping = read_csv(manifest / 'identity_mapping.csv')
    users = sorted({row['simulated_user_id'] for row in partitions})
    if len(users) != config['subjects'] or len(mapping) != len(users):
        raise ValueError('Mapped subject count conflicts with configuration')
    actual_mapping = set()
    for user in users:
        subjects = {}
        for modality in ['face', 'palm']:
            rows = [row for row in partitions if row['simulated_user_id'] == user and row['modality'] == modality]
            if dict(Counter(row['split'] for row in rows)) != config['split_per_modality_per_user']:
                raise ValueError('Per-user partition counts conflict with configuration')
            subjects[modality] = rows[0]['original_subject_id']
        actual_mapping.add((user, subjects['face'], subjects['palm']))
    expected_mapping = {(row['simulated_user_id'], row['face_subject_id'], row['palm_subject_id']) for row in mapping}
    if actual_mapping != expected_mapping:
        raise ValueError('Identity mapping conflicts with partition labels')
    trials = {split: read_csv(manifest / f'{split}_trials.csv') for split in ['validation', 'test']}
    for split in trials:
        validate_trials(trials[split], partitions, split)
        if len(trials[split]) != config['trial_counts'][split]:
            raise ValueError('Claim count conflicts with configuration')
    return config, partitions, trials


def build_protocol(root=ROOT, seed=42, max_users=40, rebuild=False):
    root = Path(root)
    guard_manifest_rebuild(root, ['identity_mapping.csv', 'validation_trials.csv', 'test_trials.csv'], rebuild)
    face_rows = [row for row in read_csv(root / 'data/manifests/face_samples.csv') if row['status'] == 'usable']
    palm_rows = [row for row in read_csv(root / 'data/manifests/palm_samples.csv') if row['status'] == 'usable']
    face_users = sorted({row['subject_id'] for row in face_rows}, key=int)
    face_users = [user for user in face_users if sum(row['subject_id'] == user for row in face_rows) >= 10]
    palm_users = sorted({row['subject_id'] for row in palm_rows})
    palm_users = [user for user in palm_users if all(sum(row['subject_id'] == user and row['session'] == session for row in palm_rows) >= count
                                                  for session, count in [('F', 6), ('S', 4)])]
    count = min(len(face_users), len(palm_users), max_users)
    if count < 2:
        raise ValueError('Insufficient eligible subjects for the predeclared 4/2/4 session-aware protocol')
    rng = np.random.default_rng(seed) #keep identity mapping and sample selection reproducible
    face_users = rng.permutation(face_users)[:count]
    palm_users = rng.permutation(palm_users)[:count]
    mapping, partitions = [], []
    for index, (face_id, palm_id) in enumerate(zip(face_users, palm_users)):
        user = f'user_{index:03d}'
        mapping.append({'simulated_user_id': user, 'face_subject_id': str(face_id), 'palm_subject_id': str(palm_id)})
        selected_faces = [row for row in face_rows if row['subject_id'] == face_id]
        selected_faces = [selected_faces[i] for i in rng.permutation(len(selected_faces))[:10]]
        pools = {session: [row for row in palm_rows if row['subject_id'] == palm_id and row['session'] == session] for session in ['F', 'S']}
        first = [pools['F'][i] for i in rng.permutation(len(pools['F']))[:6]]
        second = [pools['S'][i] for i in rng.permutation(len(pools['S']))[:4]] #the second session is held out for testing
        for modality, samples in [('face', selected_faces), ('palm', first + second)]:
            for sample_index, row in enumerate(samples):
                split = 'enrollment' if sample_index < 4 else 'validation' if sample_index < 6 else 'test'
                partitions.append({'modality': modality, 'simulated_user_id': user,
                                   'original_subject_id': row['subject_id'], 'original_sample_id': row['sample_id'],
                                   'palm_hand_if_applicable': row.get('hand', ''),
                                   'session_if_available': row.get('session', ''), 'split': split,
                                   'source_path_or_key': row.get('source_path', 'data/raw/face/olivetti.npz#' + row.get('array_index', '')),
                                   'pixel_sha256': row['pixel_sha256']})
    validate_partitions(partitions)
    manifest = root / 'data/manifests'
    write_csv(manifest / 'identity_mapping.csv', mapping)
    write_csv(manifest / 'partitions.csv', partitions)
    for split in ['validation', 'test']:
        write_csv(manifest / f'{split}_trials.csv', make_trials(partitions, split))
    config = {'seed': seed, 'subjects': count, 'mapping': 'artificial_between_different_people',
              'split_per_modality_per_user': {'enrollment': 4, 'validation': 2, 'test': 4},
              'palm_session_policy': 'F enrollment/validation; S test, distinct decoded pixels',
              'palm_subject_eligibility': 'at least 6 unique usable F and 4 unique usable S captures',
              'face_session_policy': 'dataset provides no session labels; seeded within-subject split',
              'enrollment_fit_only': True, 'normalization_fit_split': 'validation',
              'trial_counts': {split: len(make_trials(partitions, split)) for split in ['validation', 'test']}}
    write_json(manifest / 'config.json', config)
    write_json(manifest / 'protocol_lock.json', {'schema_version': 1, 'hash_format': 'sha256_text_lf_binary_raw_v1',
                                               'manifest_sha256': manifest_hashes(root)}) #freeze this complete study bundle
    return config
