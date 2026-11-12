from pathlib import Path
import csv
import json
import os
import tempfile
import hashlib

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_NAMES = ('config.json', 'dataset_summary.json', 'face_samples.csv', 'identity_mapping.csv',
                  'palm_samples.csv', 'palm_subject_counts.csv', 'partitions.csv', 'test_trials.csv',
                  'validation_trials.csv')


def write_csv(path, rows, fields=None):
    rows = list(rows)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or (list(rows[0]) if rows else [])
    if not fields:
        raise ValueError('CSV needs explicit field names when rows are empty')
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path):
    with Path(path).open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, indent=2, allow_nan=False) + '\n' #serialize first so bad values cannot damage an existing file
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name) #keep the temporary file on the same filesystem
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno()) #finish writing before replacing the old pointer or metadata
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True) #also clean up when replacement fails


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def text_sha256(path):
    data = Path(path).read_bytes().replace(b'\r\n', b'\n').replace(b'\r', b'\n') #git may change line endings on another checkout
    return hashlib.sha256(data).hexdigest()


def artifact_hash(path):
    return text_sha256(path) if Path(path).suffix.lower() in ['.csv', '.json', '.txt'] else sha256(path) #images and models keep exact byte hashes


def manifest_hashes(root=ROOT):
    folder = Path(root) / 'data/manifests'
    return {name: text_sha256(folder / name) for name in MANIFEST_NAMES} #the lock cannot include its own hash


def verify_manifest_hashes(expected, root=ROOT):
    actual = manifest_hashes(root)
    if actual != expected:
        changed = sorted(name for name in actual.keys() | expected.keys() if actual.get(name) != expected.get(name))
        raise ValueError(f'Frozen protocol changed: {changed}')
    return actual


def guard_manifest_rebuild(root, names, rebuild=False):
    folder = Path(root) / 'data/manifests'
    protected = set(names) | {'protocol_lock.json', 'config.json', 'partitions.csv'}
    if not rebuild and any((folder / name).exists() for name in protected):
        raise FileExistsError('Manifests already exist; use --rebuild only for an intentional protocol revision')
