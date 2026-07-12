import argparse
import json
import os
import time

import cv2
import mss
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument(
    '--noise-threshold',
    action='store',
    default=30,
    type=int,
    dest='noise_threshold',
    help='per-channel max value still treated as black (handles RDP/KVM compression noise)',
)
parser.add_argument(
    '--delay',
    action='store',
    default=3,
    type=int,
    help='seconds to wait before taking the screenshot',
)
args = parser.parse_args()

print(f'Taking screenshot in {args.delay} second(s) — switch to the target window now.')
for i in range(args.delay, 0, -1):
    print(f'  {i}...')
    time.sleep(1)

with mss.mss() as sct:
    monitor = sct.monitors[1]  # primary monitor (index 0 is the combined virtual screen)
    shot = sct.grab(monitor)
    img_bgr = cv2.cvtColor(np.array(shot), cv2.COLOR_BGRA2BGR)

print(f'Screenshot captured: {img_bgr.shape[1]}x{img_bgr.shape[0]} px')
os.makedirs('captures', exist_ok=True)
cv2.imwrite('captures/01_screenshot.png', img_bgr)

# Pixels where every channel is below the noise threshold are the (near-)black canvas.
# Everything else becomes white. This tolerates compression artefacts from RDP/IP KVM.
near_black = np.all(img_bgr < args.noise_threshold, axis=2)
binary = np.where(near_black, np.uint8(0), np.uint8(255))
cv2.imwrite('captures/02_threshold.png', binary)

# Invert so the canvas (black) becomes white — findContours finds white objects on black.
binary_inv = cv2.bitwise_not(binary)
contours, _ = cv2.findContours(binary_inv, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

if not contours:
    print('No contours found — try lowering --noise-threshold.')
else:
    best = max(contours, key=lambda c: cv2.boundingRect(c)[2] * cv2.boundingRect(c)[3])
    x, y, w, h = cv2.boundingRect(best)

    solidity = cv2.contourArea(best) / (w * h)
    if solidity < 0.95:
        print(f'Warning: largest region has solidity {solidity:.2f} — may not be rectangular.')

    debug = img_bgr.copy()
    cv2.drawContours(debug, [best], 0, (0, 255, 0), 2)
    cv2.rectangle(debug, (x, y), (x + w, y + h), (0, 0, 255), 2)
    cv2.imwrite('captures/03_contours.png', debug)

    coords = {'x': x, 'y': y, 'w': w, 'h': h}
    with open('coords.json', 'w') as f:
        json.dump(coords, f)
    print(f'Found bounding rectangle {w}x{h} at ({x}, {y}) — wrote coords.json')
