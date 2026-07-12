import argparse
import glob
import os
import shutil
import tempfile

import extract_data


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--captureDir', default='captures/', help='directory containing capture_*.png files')
    parser.add_argument('--coords', default='coords.json', help='path to coords.json')
    parser.add_argument('--canvasWidth', type=int, default=1200)
    parser.add_argument('--canvasHeight', type=int, default=800)
    parser.add_argument('--blockSize', type=int, default=10)
    parser.add_argument('--outDir', default='output', help='temp directory for block files')
    parser.add_argument('--output', default='assembled.bin', help='final assembled output file')
    parser.add_argument('--verify', action='store_true', default=False)
    parser.add_argument('--debug', action='store_true', default=False)
    args = parser.parse_args()

    pattern = os.path.join(args.captureDir, 'capture_*.png')
    captures = sorted(glob.glob(pattern))
    if not captures:
        print(f'no captures found matching {pattern}')
        raise SystemExit(1)

    print(f'found {len(captures)} capture(s)')
    total_bytes = 0
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name
        for cap in captures:
            data = extract_data.extract(
                image_path=cap,
                coords_path=args.coords,
                canvas_w=args.canvasWidth,
                canvas_h=args.canvasHeight,
                sq_width=args.blockSize,
                out_dir=args.outDir,
                verify=args.verify,
                debug=args.debug,
            )
            tmp.write(data)
            total_bytes += len(data)

    os.makedirs(args.outDir, exist_ok=True)
    out_path = os.path.join(args.outDir, args.output)
    shutil.move(tmp_path, out_path)
    print(f'\nwrote {total_bytes} bytes to {out_path}')
