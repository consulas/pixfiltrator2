# Pixfiltrator 2

Exfiltrates data from a remote desktop by encoding it as pixels displayed on screen, then capturing and decoding it on the host.

## How It Works

The guest machine renders encoded data as images in a browser. The host machine captures those images via screen recording, then decodes them back into the original data.

## Setup

### Guest (Remote Desktop)

1. Copy the `guest/` folder onto the remote desktop.
2. Open `guest/client.html` in a browser on the remote desktop.

### Host

1. Install dependencies:
   ```bash
   pip install -r host/requirements.txt
   ```
2. Run `find_bounding_rect.py` to detect and save the screen region where the browser window is displaying:
   ```bash
   python3 host/find_bounding_rect.py
   ```
3. Run `capture.py` and press **Start** on the remote desktop to begin capturing frames:
   ```bash
   python3 host/capture.py
   ```
4. Once capture is complete, run `batch.py` to decode the captures into the output file:
   ```bash
   python3 host/batch.py
   ```
   Output is written to `host/output/`.

## Frame Format

Each frame encodes a chunk of data as pixels. The first 40 pixels (left to right, top row) are metadata:

| Pixels | Bytes | Purpose |
|--------|-------|---------|
| 1–16   | 48    | Color-coded frame index — each pixel encodes 3 bytes of color channel data used to identify the frame |
| 17–20  | 12    | Number of bytes in the image payload (encoded across 4 pixels, 3 bytes each) |
| 21–40  | 60    | SHA-1 hash of the frame payload (20 bytes, encoded across 20 pixels using the first byte of each pixel's RGB channels) |

The remaining pixels encode the raw payload data, 3 bytes per pixel (one per RGB channel).

## Scripts

Utilities for transferring this project between machines using git patches.

- **`scripts/create_patch.py`** — Creates a patch from a repo's full git history. Defaults to writing `scripts/output.patch`.
  ```bash
  python3 scripts/create_patch.py /path/to/repo [output.patch] [--from-commit HASH]
  ```
- **`scripts/apply_patch.py`** — Initializes a new repo at a destination path and applies the patch.
  ```bash
  python3 scripts/apply_patch.py output.patch /path/to/destination
  ```
