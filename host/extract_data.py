import argparse
import hashlib
import json
import os
from operator import itemgetter

import cv2
import numpy as np


def blockify(image, width):
    h, w, _ = image.shape
    num_rows = h // width
    num_cols = w // width
    ret = []
    for r in range(num_rows):
        for c in range(num_cols):
            tally = []
            for i in image[r * width : (r + 1) * width]:
                for j in i[c * width : (c + 1) * width]:
                    tally.append(np.sum(j[:3]))
            ret.append(tally)
    return ret


def pyramid_weights(n):
    r = np.arange(n)
    d = np.minimum(r, r[::-1])
    p = np.minimum.outer(d, d)
    return p / p.sum()


def weigh_blocks(vals, width, sum_values=False):
    if width < 3:
        return vals
    p = pyramid_weights(width)
    num_elems = width * width
    ret = []
    for val in vals:
        res = np.multiply(np.array(val).reshape((width, width)), p).reshape(1, num_elems)
        if sum_values:
            ret.append(float(sum(sum(r) for r in res)))
        else:
            ret.extend(res)
    return ret


def combine_half_bytes(arr):
    pairs = zip(arr[::2], arr[1::2])
    return bytes((a << 4) + b for a, b in pairs)


def nearest_nibble(s, calib_sums):
    return min(range(16), key=lambda i: abs(calib_sums[i] - s))


def extract(image_path, coords_path, canvas_w, canvas_h, sq_width, out_dir, verify):
    print(f'processing {image_path}')
    img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise FileNotFoundError(f'could not read {image_path}')

    with open(coords_path) as f:
        coords = json.load(f)
    x, y, w, h = itemgetter('x', 'y', 'w', 'h')(coords)
    roi = img[y : y + h, x : x + w]

    roi = cv2.resize(roi, (canvas_w, canvas_h))

    blocks = blockify(roi, sq_width)
    weighted = weigh_blocks(blocks, sq_width, sum_values=True)

    num_cols = canvas_w // sq_width
    num_rows = canvas_h // sq_width
    num_data_blocks = (num_rows - 1) * num_cols

    data_weighted = weighted[:num_data_blocks]
    meta_weighted = weighted[num_data_blocks:]

    calib_sums = meta_weighted[:16]
    print(f'calibration nibbles: {[nearest_nibble(s, calib_sums) for s in calib_sums]}')

    byte_count_nibbles = [nearest_nibble(meta_weighted[16 + i], calib_sums) for i in range(4)]
    num_bytes = (byte_count_nibbles[0] << 12) | (byte_count_nibbles[1] << 8) | (byte_count_nibbles[2] << 4) | byte_count_nibbles[3]
    print(f'bytes on page: {num_bytes}')

    sha1_nibbles = [nearest_nibble(meta_weighted[20 + i], calib_sums) for i in range(40)]
    sha1_hex = ''.join(f'{n:x}' for n in sha1_nibbles)
    print(f'extracted SHA-1: {sha1_hex}')

    data_nibbles = [nearest_nibble(s, calib_sums) for s in data_weighted[: num_bytes * 2]]
    data_bytes = combine_half_bytes(data_nibbles)

    if verify:
        computed = hashlib.sha1(data_bytes).hexdigest()
        print(f'computed  SHA-1: {computed}')
        if computed != sha1_hex:
            print('WARNING: SHA-1 mismatch')
        else:
            print('SHA-1 OK')

    os.makedirs(out_dir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(image_path))[0]
    out_path = os.path.join(out_dir, f'block_{stem}_{sha1_hex[:16]}.bin')
    with open(out_path, 'wb') as f:
        f.write(data_bytes)
    print(f'wrote {len(data_bytes)} bytes to {out_path}')
    return out_path


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--image', required=True, help='path to capture PNG')
    parser.add_argument('--coords', default='coords.json', help='path to coords.json')
    parser.add_argument('--canvasWidth', type=int, default=1200)
    parser.add_argument('--canvasHeight', type=int, default=800)
    parser.add_argument('--blockSize', type=int, default=10)
    parser.add_argument('--outDir', default='.')
    parser.add_argument('--verify', action='store_true', default=False)
    args = parser.parse_args()
    extract(args.image, args.coords, args.canvasWidth, args.canvasHeight, args.blockSize, args.outDir, args.verify)
