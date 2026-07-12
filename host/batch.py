import argparse
import glob
import os

import extract_data


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--captureDir', default='captures/', help='directory containing capture_*.png files')
    parser.add_argument('--coords', default='coords.json', help='path to coords.json')
    parser.add_argument('--canvasWidth', type=int, default=1200)
    parser.add_argument('--canvasHeight', type=int, default=800)
    parser.add_argument('--blockSize', type=int, default=10)
    parser.add_argument('--outDir', default='out/', help='temp directory for block files')
    parser.add_argument('--output', default='assembled.bin', help='final assembled output file')
    parser.add_argument('--verify', action='store_true', default=False)
    args = parser.parse_args()

    pattern = os.path.join(args.captureDir, 'capture_*.png')
    captures = sorted(glob.glob(pattern))
    if not captures:
        print(f'no captures found matching {pattern}')
        raise SystemExit(1)

    print(f'found {len(captures)} capture(s)')
    block_files = []
    for cap in captures:
        block_path = extract_data.extract(
            image_path=cap,
            coords_path=args.coords,
            canvas_w=args.canvasWidth,
            canvas_h=args.canvasHeight,
            sq_width=args.blockSize,
            out_dir=args.outDir,
            verify=args.verify,
        )
        block_files.append(block_path)

    print(f'\nassembling {len(block_files)} block(s) into {args.output}')
    total_bytes = 0
    with open(args.output, 'wb') as out_f:
        for bf in block_files:
            with open(bf, 'rb') as in_f:
                data = in_f.read()
                out_f.write(data)
                total_bytes += len(data)

    print(f'wrote {total_bytes} bytes to {args.output}')
