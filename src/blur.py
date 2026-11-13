"""Face-only Gaussian blur; fitted models and normalization are never updated."""
from dataclasses import asdict
import hashlib
from pathlib import Path
import json
import joblib
import numpy as np
from scipy.ndimage import gaussian_filter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from src.datasets import dataset_images
from src.files import text_sha256, write_json, sha256
from src.fusion import accepted_scores, require_assets, index_rows
from src.matching import score_trials

DEFAULT_SIGMAS = (0.0, 0.5, 1.0, 2.0, 3.0)
MODE = 'reflect'
TRUNCATE = 4.0


def validate_sigmas(sigmas):
    values = tuple(float(s) for s in sigmas)
    if not values or values[0] != 0 or not np.isfinite(values).all() or any(s < 0 for s in values):
        raise ValueError('Finite nonnegative sigma levels must begin with zero')
    if list(values) != sorted(set(values)):
        raise ValueError('Sigma levels must be strictly increasing')
    return values


def blur_image(image, sigma):
    image = np.asarray(image)
    if image.ndim != 2 or not np.issubdtype(image.dtype, np.floating) or not np.isfinite(image).all():
        raise ValueError('Expected a finite grayscale floating-point image')
    if image.min() < 0 or image.max() > 1 or not np.isfinite(sigma) or sigma < 0:
        raise ValueError('Invalid image range or blur sigma')
    return image.copy() if sigma == 0 else gaussian_filter(image.copy(), sigma=sigma, mode=MODE, truncate=TRUNCATE)


def frozen_face_scores(model, images, trials, sigmas):
    sigmas = validate_sigmas(sigmas)
    before_model = joblib.hash(model)
    before_images = {key: hashlib.sha256(value.tobytes()).hexdigest() for key, value in images.items()}
    output = {}
    for sigma in sigmas:
        blurred = {key: blur_image(value, sigma) for key, value in images.items()}
        output[sigma] = score_trials(model, blurred, trials, 'face')
    if joblib.hash(model) != before_model:
        raise ValueError('Frozen face model changed during scoring')
    if before_images != {key: hashlib.sha256(value.tobytes()).hexdigest() for key,value in images.items()}:
        raise ValueError('Original face pixels changed during scoring')
    return output


def assert_equal_scores(actual, expected, fields, atol=0.0):
    a, b = index_rows(actual, fields), index_rows(expected, fields)
    if a.keys() != b.keys():
        raise ValueError('Condition keys differ')
    maximum = 0.0
    for key in a:
        if a[key]['is_genuine'] != b[key]['is_genuine']:
            raise ValueError('Condition labels differ')
        for field in fields:
            delta = abs(float(a[key][field]) - float(b[key][field]))
            maximum = max(maximum, delta)
            if delta > atol:
                raise ValueError(f'Condition scores differ for {field}; max allowed difference {atol}')
    return maximum


def prepare_plan(root, destination, sigmas=DEFAULT_SIGMAS):
    root, destination = Path(root), Path(destination)
    sigmas = validate_sigmas(sigmas)
    pointer, _, _, partitions, _, _ = accepted_scores(root)
    require_assets([root / 'data/raw/face/olivetti.npz'])
    images = dataset_images([r for r in partitions if r['modality'] == 'face'], 'validation', root)['face']
    if destination.exists():
        raise FileExistsError('Plan directory exists; use a fresh directory')
    selected = sorted(images)[:4]
    fig, axes = plt.subplots(len(selected), len(sigmas), figsize=(2*len(sigmas),2*len(selected)), squeeze=False)
    for i, key in enumerate(selected):
        for j, sigma in enumerate(sigmas):
            axes[i,j].imshow(blur_image(images[key],sigma),cmap='gray',vmin=0,vmax=1)
            axes[i,j].set_title(f'{key}, sigma {sigma:g}',fontsize=9)
            axes[i,j].axis('off')
    fig.suptitle('Validation-only blur inspection; no test images')
    fig.tight_layout()
    destination.mkdir(parents=True)
    preview = destination / 'validation_blur_preview.png'
    fig.savefig(preview,dpi=150)
    plt.close(fig)
    plan = {'schema_version': 1, 'sigmas': list(sigmas), 'sigma_units': 'original 64x64 face pixels',
            'mode': MODE, 'truncate': TRUNCATE, 'implementation': 'scipy.ndimage.gaussian_filter',
            'order': 'audited raw [0,1] face pixels -> blur -> frozen PCA -> frozen cosine templates',
            'selection_split': 'validation', 'sample_ids': selected,
            'sample_pixel_sha256': {k:hashlib.sha256(images[k].tobytes()).hexdigest() for k in selected},
            'baseline_id': pointer['run_id'], 'manifest_sha256': pointer['manifest_sha256'],
            'blur_code_sha256': sha256(root/'src/blur.py'),
            'preview_sha256': sha256(preview), 'reviewed': False, 'review_note': ''}
    write_json(destination/'blur_plan.json',plan)
    return destination/'blur_plan.json'


def load_plan(path, root, reviewed=True):
    path, root = Path(path), Path(root)
    plan = json.loads(path.read_text())
    pointer, _, _, partitions, _, _ = accepted_scores(root)
    if plan['schema_version'] != 1 or plan['selection_split'] != 'validation':
        raise ValueError('Plan must use validation images')
    validate_sigmas(plan['sigmas'])
    if plan['baseline_id'] != pointer['run_id'] or plan['manifest_sha256'] != pointer['manifest_sha256']:
        raise ValueError('Blur plan protocol differs')
    if plan['mode'] != MODE or plan['truncate'] != TRUNCATE or plan['blur_code_sha256'] != sha256(root/'src/blur.py'):
        raise ValueError('Blur implementation differs from the inspected plan')
    require_assets([root/'data/raw/face/olivetti.npz'])
    images = dataset_images([r for r in partitions if r['modality']=='face'], 'validation',root)['face']
    ids = plan['sample_ids']
    if not ids or len(ids)!=len(set(ids)) or not set(ids).issubset(images):
        raise ValueError('Plan contains invalid validation sample IDs')
    hashes = {k:hashlib.sha256(images[k].tobytes()).hexdigest() for k in ids}
    if hashes != plan['sample_pixel_sha256'] or sha256(path.parent/'validation_blur_preview.png') != plan['preview_sha256']:
        raise ValueError('Validation preview inputs or image changed')
    if reviewed and (plan['reviewed'] is not True or not plan['review_note'].strip()):
        raise ValueError('Inspect the validation preview and record a review before running held-out blur')
    return plan
