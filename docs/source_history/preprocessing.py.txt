from PIL import Image, ImageOps
import numpy as np
from scipy import ndimage


def crop_palm(source, size=128):
    if not isinstance(size, int) or size < 16:
        raise ValueError('ROI size must be an integer >= 16')
    image = ImageOps.exif_transpose(source).convert('RGB')
    small = image.copy()
    small.thumbnail((512, 512))
    rgb = np.asarray(small, dtype=np.float32) / 255
    red, green, blue = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    chroma_red = 0.5 + 0.5 * red - 0.418688 * green - 0.081312 * blue
    skin = (red > 0.12) & (chroma_red > 0.53) & (red > green) & (red > blue)
    skin = ndimage.binary_closing(skin, iterations=3)
    components, count = ndimage.label(skin)
    if count == 0:
        raise ValueError('No skin component detected')
    areas = np.bincount(components.ravel())
    areas[0] = 0
    mask = ndimage.binary_fill_holes(components == areas.argmax())
    distances = ndimage.distance_transform_edt(mask)
    cy, cx = np.unravel_index(distances.argmax(), distances.shape)
    radius = float(distances[cy, cx])
    if radius < 8:
        raise ValueError('Palm region is too small')
    sx, sy = image.width / small.width, image.height / small.height
    side = int(radius * min(sx, sy))
    left = max(0, min(image.width - side, int(cx * sx - side / 2)))
    top = max(0, min(image.height - side, int(cy * sy - side / 2)))
    if side < 64:
        raise ValueError('Palm crop has insufficient source resolution')
    roi = image.convert('L').crop((left, top, left + side, top + side)).resize((size, size), Image.Resampling.BILINEAR)
    return np.asarray(roi, dtype=np.float32) / 255


def palm_roi(path, size=128):
    with Image.open(path) as source:
        return crop_palm(source, size)


def validate_images(images):
    images = np.asarray(images, dtype=np.float32)
    if images.ndim != 3 or len(images) == 0 or not np.isfinite(images).all():
        raise ValueError('Expected nonempty finite grayscale images (n, height, width)')
    if images.min() < 0 or images.max() > 1:
        raise ValueError('Images must be scaled to [0, 1]')
    return images
