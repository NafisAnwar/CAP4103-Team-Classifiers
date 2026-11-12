from collections import Counter
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw
import hashlib
import re
import numpy as np
from src.files import ROOT, write_csv, write_json
from src.preprocessing import palm_roi, crop_palm

PALM_NAME = re.compile(r'(?P<subject>\d{3})_(?P<session>[FS])_(?P<hand>[LR])_(?P<number>\d+)\.JPG', re.I)


def parse_palm_name(name):
    match = PALM_NAME.fullmatch(Path(name).name)
    if match is None:
        raise ValueError(f'Unrecognized BMPD sample name: {name}')
    return match.groupdict()


def load_faces(root=ROOT):
    path = Path(root) / 'data/raw/face/olivetti.npz'
    if not path.exists():
        raise FileNotFoundError('Run scripts/download_data.py --modality face first')
    with np.load(path, allow_pickle=False) as data:
        images, labels = data['images'].copy(), data['labels'].copy()
    if images.shape != (400, 64, 64) or labels.shape != (400,):
        raise ValueError('Unexpected Olivetti array shapes')
    if not np.isfinite(images).all() or images.min() < 0 or images.max() > 1:
        raise ValueError('Invalid face pixels')
    return images, labels


def audit_datasets(root=ROOT):
    root = Path(root)
    images, labels = load_faces(root)
    faces, seen = [], {}
    for index, (image, label) in enumerate(zip(images, labels)):
        digest = hashlib.sha256(image.tobytes()).hexdigest()
        sample = f'face_{index:03d}'
        duplicate = seen.get(digest, '')
        seen.setdefault(digest, sample)
        faces.append({'sample_id': sample, 'subject_id': str(int(label)), 'array_index': index,
                      'pixel_sha256': digest, 'duplicate_of': duplicate,
                      'status': 'duplicate' if duplicate else 'usable'})
    palms, seen = [], {}
    paths = sorted((root / 'data/raw/palm/images').glob('*.JPG'))
    if not paths:
        raise FileNotFoundError('Run scripts/download_data.py --modality palm first')
    for path in paths:
        info = parse_palm_name(path.name)
        if info['hand'].upper() != 'R':
            raise ValueError('Only verified right palms are allowed')
        row = {'sample_id': path.stem, 'subject_id': info['subject'], 'session': info['session'],
               'hand': info['hand'], 'source_path': path.relative_to(root).as_posix(),
               'file_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
               'pixel_sha256': '', 'width': '', 'height': '', 'roi_std': '',
               'duplicate_of': '', 'status': 'usable'}
        try:
            with Image.open(path) as source:
                image = ImageOps.exif_transpose(source).convert('RGB')
                row['width'], row['height'] = image.size
                digest = hashlib.sha256(str(image.size).encode() + image.tobytes()).hexdigest()
                roi = crop_palm(image)
            row['pixel_sha256'] = digest
            prior = seen.get(digest)
            if prior:
                if prior['subject_id'] != row['subject_id']:
                    raise ValueError(f'Identical pixels under different subjects: {path.name}')
                row['duplicate_of'], row['status'] = prior['sample_id'], 'duplicate'
            else:
                seen[digest] = row
            row['roi_std'] = float(roi.std())
            if row['status'] == 'usable' and (min(image.size) < 128 or roi.std() < 0.02):
                row['status'] = 'low_contrast_or_resolution'
        except (OSError, SyntaxError, ValueError) as error:
            if 'different subjects' in str(error):
                raise
            row['status'] = f'decode_or_roi_error:{type(error).__name__}'
        palms.append(row)
        if len(palms) % 100 == 0:
            print(f'Audited palm images: {len(palms)}/{len(paths)}', flush=True)
    manifest = root / 'data/manifests'
    write_csv(manifest / 'face_samples.csv', faces)
    write_csv(manifest / 'palm_samples.csv', palms)
    counts = []
    for subject in sorted({row['subject_id'] for row in palms}):
        selected = [row for row in palms if row['subject_id'] == subject]
        usable = [row for row in selected if row['status'] == 'usable']
        counts.append({'subject_id': subject, 'downloaded': len(selected), 'usable_unique': len(usable),
                       'F': sum(row['session'] == 'F' for row in usable),
                       'S': sum(row['session'] == 'S' for row in usable)})
    write_csv(manifest / 'palm_subject_counts.csv', counts)
    summary = {'face': {'samples': len(faces), 'subjects': len(set(labels.tolist())),
                         'statuses': dict(Counter(row['status'] for row in faces))},
               'palm': {'samples': len(palms), 'subjects': len(counts),
                        'statuses': dict(Counter(row['status'] for row in palms))},
               'roi': {'size': 128, 'method': 'largest skin component, maximum-inscribed-circle interior square',
                       'skin_rule': 'R > 0.12, Cr > 0.53, R > G and R > B; closing and hole fill at <=512 pixels',
                       'crop_side': 'maximum distance to mask boundary, conservative central square'},
               'eligibility': 'unique decoded pixels; minimum source side 128; palm crop side >=64; ROI std >= 0.02',
               'bmpd_license_metadata': 'Unknown; public download, course-preapproved dataset; redistribution permission not established',
               'bmpd_source': 'https://www.kaggle.com/datasets/mahdieizadpanah/birjand-university-mobile-palmprint-databasebmpd',
               'olivetti_source': 'https://scikit-learn.org/stable/modules/generated/sklearn.datasets.fetch_olivetti_faces.html'}
    write_json(manifest / 'dataset_summary.json', summary)
    contact_sheets(root, palms)
    return summary, counts


def contact_sheets(root, rows):
    selected = []
    for subject in sorted({row['subject_id'] for row in rows}):
        for session in ['F', 'S']:
            candidates = [row for row in rows if row['subject_id'] == subject and row['session'] == session and row['status'] == 'usable']
            if candidates:
                selected.append(candidates[0])
    destination = root / 'data/processed/audit'
    destination.mkdir(parents=True, exist_ok=True)
    for page in range(0, len(selected), 20):
        canvas = Image.new('RGB', (1000, 900), 'white')
        draw = ImageDraw.Draw(canvas)
        for i, row in enumerate(selected[page:page + 20]):
            x, y = (i % 5) * 200, (i // 5) * 225
            with Image.open(root / row['source_path']) as image:
                image = ImageOps.exif_transpose(image).convert('RGB')
                image.thumbnail((95, 185))
                canvas.paste(image, (x, y + 25))
            roi = Image.fromarray((palm_roi(root / row['source_path']) * 255).astype(np.uint8)).resize((100, 100))
            canvas.paste(roi, (x + 98, y + 40))
            draw.text((x + 4, y + 4), row['sample_id'], fill='black')
        canvas.save(destination / f'palm_roi_audit_{page // 20 + 1:02d}.jpg')
