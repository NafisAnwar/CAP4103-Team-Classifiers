from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.request import Request, urlopen
from zipfile import ZipFile
import argparse
import io
import json
import re
import struct
import time
import zlib

ROOT = Path(__file__).resolve().parents[1]
BMPD = 'https://www.kaggle.com/api/v1/datasets/'
REF = 'mahdieizadpanah/birjand-university-mobile-palmprint-databasebmpd'
NAME = re.compile(r'(?P<subject>\d{3})_(?P<session>[FS])_(?P<hand>[LR])_(?P<number>\d+)\.JPG', re.I)


def fetch_range(url, start, end):  # retrieve a specific archive byte range with bounded retries and length checks
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers={'Range': f'bytes={start}-{end}'}), timeout=90) as response:
                if response.status != 206 or not response.headers.get('Content-Range', '').startswith(f'bytes {start}-{end}/'):
                    raise ValueError('Server did not honor the requested byte range')
                data = response.read(end - start + 2)
            if len(data) != end - start + 1:
                raise ValueError('Incomplete or oversized archive byte range')
            return data
        except (OSError, ValueError):
            if attempt == 2:
                raise
            time.sleep(attempt + 1)


class RemoteArchive(io.RawIOBase):  # expose a remote zip as a seekable stream without downloading unrelated images
    def __init__(self, url, size):  # track the archive endpoint, byte length and current read position
        self.url, self.size, self.pos = url, size, 0

    def seekable(self):  # advertise random access for the zip reader
        return True

    def seek(self, offset, whence=0):  # translate zip offsets to positions in the remote archive
        self.pos = offset if whence == 0 else self.pos + offset if whence == 1 else self.size + offset
        if self.pos < 0:
            raise ValueError('Negative seek')
        return self.pos

    def tell(self):  # return the current byte position
        return self.pos

    def read(self, count=-1):  # retrieve only the requested bytes and advance the stream position
        count = min(self.size - self.pos, count if count >= 0 else self.size)
        if count <= 0:
            return b''
        data = fetch_range(self.url, self.pos, self.pos + count - 1)
        self.pos += count
        return data


def extract_member(block, base_offset, info):  # decode the selected zip member and verify its declared size and crc
    offset = info.header_offset - base_offset
    if block[offset:offset + 4] != b'PK\x03\x04':
        raise ValueError('Invalid local zip header')
    name_size, extra_size = struct.unpack_from('<HH', block, offset + 26)
    start = offset + 30 + name_size + extra_size
    compressed = block[start:start + info.compress_size]
    if info.compress_type == 8:
        data = zlib.decompress(compressed, -15)
    elif info.compress_type == 0:
        data = compressed
    else:
        raise ValueError(f'Unsupported compression: {info.compress_type}')
    if len(data) != info.file_size or zlib.crc32(data) != info.CRC:
        raise ValueError(f'Archive integrity failure: {info.filename}')
    return data


def download_bmpd(workers=4):  # retrieve right-palm captures and verify their archive entries
    destination = ROOT / 'data/raw/palm'
    destination.mkdir(parents=True, exist_ok=True)
    with urlopen(BMPD + 'view/' + REF, timeout=40) as response:
        metadata = json.load(response)
    (destination / 'kaggle_metadata.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    with urlopen(Request(BMPD + 'download/' + REF, headers={'Range': 'bytes=0-0'}), timeout=60) as response:
        if response.status != 206:
            raise ValueError('Archive does not support partial downloads')
        size = int(response.headers['Content-Range'].split('/')[-1])
        url = response.geturl()
    with ZipFile(RemoteArchive(url, size)) as archive:
        entries = archive.infolist()
    inventory = [{'name': item.filename, 'bytes': item.file_size, 'crc32': item.CRC} for item in entries]
    (destination / 'archive_inventory.json').write_text(json.dumps(inventory, indent=2), encoding='utf-8')
    groups = {}
    for index, info in enumerate(entries):
        match = NAME.fullmatch(Path(info.filename).name)
        if match and match['hand'].upper() == 'R':
            groups.setdefault((match['subject'], match['session']), []).append((index, info))

    def download_group(items):  # download and validate one subject-session group, reusing intact local files
        paths = [(destination / 'images' / Path(info.filename).name, info) for _, info in items]
        if all(path.exists() and path.stat().st_size == info.file_size and zlib.crc32(path.read_bytes()) == info.CRC for path, info in paths):
            return len(paths)
        start = items[0][1].header_offset
        last_index = items[-1][0]
        end = entries[last_index + 1].header_offset - 1 if last_index + 1 < len(entries) else archive.start_dir - 1
        block = fetch_range(url, start, end)
        for path, info in paths:
            data = extract_member(block, start, info)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        return len(paths)

    completed = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        pending = [pool.submit(download_group, items) for items in groups.values()]
        for future in as_completed(pending):
            completed += future.result()
            print(f'BMPD right-palm files verified: {completed}', flush=True)
    print(f'Archive entries: {len(entries)}; right-palm images: {completed}; license metadata: {metadata.get("licenseName")}', flush=True)


def download_faces():  # retrieve the canonical unshuffled olivetti dataset and save normalized arrays
    import numpy as np
    from sklearn.datasets import fetch_olivetti_faces
    destination = ROOT / 'data/raw/face'
    destination.mkdir(parents=True, exist_ok=True)
    faces = fetch_olivetti_faces(data_home=destination, shuffle=False)
    np.savez_compressed(destination / 'olivetti.npz', images=faces.images, labels=faces.target)
    print(f'Olivetti images: {faces.images.shape}; subjects: {len(np.unique(faces.target))}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--modality', choices=['face', 'palm', 'both'], default='both')
    args = parser.parse_args()
    if args.modality in ['face', 'both']:
        download_faces()
    if args.modality in ['palm', 'both']:
        download_bmpd()
