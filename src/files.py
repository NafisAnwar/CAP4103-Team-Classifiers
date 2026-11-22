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
COMMENT_ONLY_SOURCE_TRANSITIONS = {  # allow only the four exact source versions proven equivalent to the accepted historical model code
    'src/preprocessing.py': ('aa957e84dbc2abe4c9780d8d2915f1b8516cb6f4f8434612b0bbf8998515f081',
                             '42a703005a7c0d7abe214c8c7b746693ddc0dd3bc79155488eb3b12fdf5bc0ef'),
    'src/face_authentication.py': ('69870835e09ac349faf1dda96e5e88143c75503fbc708b3defb139e456a9cb03',
                                   '7b9b50966579da9c0c32ddbff06d9dc3008d5f88530ba3cd9998c2cb422a3ecb'),
    'src/palmprint_authentication.py': ('f098c52b9b20b03f1542f62069dbe07541b5c5b27137d4948c75ee4ee1604f23',
                                        'e46a507cfdcfe3aa4424c70d7819f299dc667229ceb10646e8e6de171aa86f3f'),
    'src/matching.py': ('6d1ba7b72e68f6d899d9419f6666018c237e677f822621d77c92076f4ab77e02',
                        'c127e626557a05473e1920b752769b58d83acd9c826cf0deb4df8c9a812daf5e'),
}


def write_csv(path, rows, fields=None):  # export rows with a consistent explicit column schema
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


def read_csv(path):  # read score or manifest rows by column name rather than position
    with Path(path).open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


def write_json(path, value):  # publish valid json atomically to protect existing experiment records
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, indent=2, allow_nan=False) + '\n'  # serialize first so bad values cannot damage an existing file
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)  # keep the temporary file on the same filesystem
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())  # finish writing before replacing the old pointer or metadata
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)  # also clean up when replacement fails


def sha256(path):  # fingerprint the exact stored bytes for immutable binary evidence
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_hash_matches(root, name, expected):  # accept only exact source bytes or a specifically audited comment-only transition
    actual = sha256(Path(root) / name)
    return actual == expected or COMMENT_ONLY_SOURCE_TRANSITIONS.get(name) == (expected, actual)


def text_sha256(path):  # normalize line endings before hashing portable textual artifacts
    data = Path(path).read_bytes().replace(b'\r\n', b'\n').replace(b'\r', b'\n')  # git may change line endings on another checkout
    return hashlib.sha256(data).hexdigest()


def artifact_hash(path):  # select the appropriate byte or normalized text hash for each artifact
    return text_sha256(path) if Path(path).suffix.lower() in ['.csv', '.json', '.txt'] else sha256(path)  # images and models keep exact byte hashes


def manifest_hashes(root=ROOT):  # hash the fixed set of dataset and trial manifests
    folder = Path(root) / 'data/manifests'
    return {name: text_sha256(folder / name) for name in MANIFEST_NAMES}  # the lock cannot include its own hash


def verify_manifest_hashes(expected, root=ROOT):  # reject any change to the frozen experiment protocol
    actual = manifest_hashes(root)
    if actual != expected:
        changed = sorted(name for name in actual.keys() | expected.keys() if actual.get(name) != expected.get(name))
        raise ValueError(f'Frozen protocol changed: {changed}')
    return actual


def guard_manifest_rebuild(root, names, rebuild=False):  # prevent accidental replacement of an accepted study manifest
    folder = Path(root) / 'data/manifests'
    protected = set(names) | {'protocol_lock.json', 'config.json', 'partitions.csv'}
    if not rebuild and any((folder / name).exists() for name in protected):
        raise FileExistsError('Manifests already exist; use --rebuild only for an intentional protocol revision')
