from PIL import Image, ImageOps
import numpy as np
from scipy import ndimage


def crop_palm(source, size=128):  # extract a central palm region using the interior of the largest detected skin component
    if not isinstance(size, int) or size < 16:
        raise ValueError('ROI size must be an integer >= 16')
    image = ImageOps.exif_transpose(source).convert('RGB')  # honor image orientation before estimating the palm region
    small = image.copy()
    small.thumbnail((512, 512))  # estimate the mask at a bounded resolution for faster segmentation
    rgb = np.asarray(small, dtype=np.float32) / 255  # normalize color values before applying the skin chroma rule
    red, green, blue = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    chroma_red = 0.5 + 0.5 * red - 0.418688 * green - 0.081312 * blue  # calculate a red chrominance channel to help distinguish skin from background
    skin = (red > 0.12) & (chroma_red > 0.53) & (red > green) & (red > blue)  # identify likely skin pixels with the fixed heuristic thresholds
    skin = ndimage.binary_closing(skin, iterations=3)  # close small holes and gaps in the segmented skin region
    components, count = ndimage.label(skin)  # separate disconnected candidate regions
    if count == 0:
        raise ValueError('No skin component detected')
    areas = np.bincount(components.ravel())
    areas[0] = 0  # exclude the background from the component size comparison
    mask = ndimage.binary_fill_holes(components == areas.argmax())  # keep the largest connected skin region and fill its internal holes
    distances = ndimage.distance_transform_edt(mask)  # measure the distance of every interior pixel to the mask boundary
    cy, cx = np.unravel_index(distances.argmax(), distances.shape)  # choose the most central interior point rather than the image center
    radius = float(distances[cy, cx])  # use the maximum interior distance as the conservative crop scale
    if radius < 8:
        raise ValueError('Palm region is too small')
    sx, sy = image.width / small.width, image.height / small.height  # map the downsampled mask coordinates back to the original resolution
    side = int(radius * min(sx, sy))  # define the square region in original source pixels
    left = max(0, min(image.width - side, int(cx * sx - side / 2)))
    top = max(0, min(image.height - side, int(cy * sy - side / 2)))
    if side < 64:
        raise ValueError('Palm crop has insufficient source resolution')
    roi = image.convert('L').crop((left, top, left + side, top + side)).resize((size, size), Image.Resampling.BILINEAR)  # crop, convert to grayscale and resize to the fixed descriptor input
    return np.asarray(roi, dtype=np.float32) / 255  # return normalized floating-point pixel intensities in the range zero to one


def palm_roi(path, size=128):  # open a local image and apply the same roi extraction used during the dataset audit
    with Image.open(path) as source:
        return crop_palm(source, size)


def validate_images(images):  # enforce finite grayscale batches with normalized pixel intensities
    images = np.asarray(images, dtype=np.float32)
    if images.ndim != 3 or len(images) == 0 or not np.isfinite(images).all():
        raise ValueError('Expected nonempty finite grayscale images (n, height, width)')
    if images.min() < 0 or images.max() > 1:
        raise ValueError('Images must be scaled to [0, 1]')
    return images
