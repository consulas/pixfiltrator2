import argparse
import os
import time

import mss
import mss.tools
import numpy as np


def mean_abs_diff(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.mean(np.abs(a.astype(np.int16) - b.astype(np.int16))))


def countdown(seconds: int) -> None:
    for i in range(seconds, 0, -1):
        print(f"{i}...")
        time.sleep(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Capture screenshots and keep only frames that differ enough from the previous saved frame."
    )
    parser.add_argument(
        "--outDir",
        default="captures",
        help="directory to save screenshots (default: captures)",
    )
    parser.add_argument(
        "--max",
        type=int,
        default=500,
        help="maximum number of captures to take (default: 500)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.25,
        help="seconds between capture attempts (default: 0.25)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=2.0,
        help="minimum mean absolute pixel difference (0-255) to keep a frame (default: 2.0)",
    )
    parser.add_argument(
        "--monitor",
        type=int,
        default=1,
        help="monitor index to capture (1=primary; 0=all monitors combined, default: 1)",
    )
    parser.add_argument(
        "--countdown",
        type=int,
        default=3,
        help="seconds to count down before starting (default: 3)",
    )
    args = parser.parse_args()

    os.makedirs(args.outDir, exist_ok=True)

    if args.countdown > 0:
        print(f"Starting capture in:")
        countdown(args.countdown)

    last_frame: np.ndarray | None = None
    saved = 0
    attempted = 0

    print(
        f"Capturing up to {args.max} frames to '{args.outDir}' "
        f"(threshold={args.threshold}, delay={args.delay}s). Ctrl-C to stop."
    )

    with mss.mss() as sct:
        monitors = sct.monitors
        if args.monitor >= len(monitors):
            raise SystemExit(
                f"Monitor {args.monitor} not found. Available: 0-{len(monitors)-1}"
            )
        region = monitors[args.monitor]
        print(f"Capturing monitor {args.monitor}: {region}")

        try:
            while attempted < args.max:
                shot = sct.grab(region)
                # BGRA -> drop alpha, keep BGR as uint8 array
                frame = np.array(shot)[:, :, :3]

                if last_frame is None or mean_abs_diff(frame, last_frame) >= args.threshold:
                    attempted += 1
                    saved += 1
                    fname = os.path.join(args.outDir, f"capture_{saved:05d}.png")
                    mss.tools.to_png(shot.rgb, shot.size, output=fname)
                    print(f"  saved {fname}")
                    last_frame = frame
                else:
                    attempted += 1

                time.sleep(args.delay)
        except KeyboardInterrupt:
            pass

    print(f"Done. {saved} frames saved out of {attempted} attempts.")
