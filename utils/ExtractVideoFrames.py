"""Save video frames at an adjustable interval (default: one second).

Usage: python3 utils/ExtractVideoFrames.py input.mp4 output_frames --interval 0.5
Requires OpenCV (opencv-python).
"""
#Gemini was used to develop this script 

import argparse
import math
from pathlib import Path

import cv2


FRAME_INTERVAL_SECONDS = 0.5


def extract_frames(
    video_path: Path,
    destination: Path,
    interval_seconds: float = FRAME_INTERVAL_SECONDS,
) -> int:
    """Extract frames starting at 0 seconds and return the number saved."""
    if not math.isfinite(interval_seconds) or interval_seconds <= 0:
        raise ValueError("Frame interval must be a finite number greater than zero.")
    if not video_path.is_file():
        raise FileNotFoundError(f"Video file does not exist: {video_path}")

    capture = cv2.VideoCapture(str(video_path))
    try:
        if not capture.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        destination.mkdir(parents=True, exist_ok=True)
        count = 0
        while True:
            timestamp_seconds = count * interval_seconds
            if not capture.set(cv2.CAP_PROP_POS_MSEC, timestamp_seconds * 1000):
                raise OSError(f"Cannot seek to {timestamp_seconds:g} seconds in {video_path}")
            success, frame = capture.read()
            if not success:
                if count == 0:
                    raise ValueError(f"Video has no readable frames: {video_path}")
                break

            frame_path = destination / f"{video_path.stem}_frame_{count:06d}.jpg"
            if frame_path.exists():
                raise FileExistsError(f"Output already exists: {frame_path}")
            if not cv2.imwrite(str(frame_path), frame):
                raise OSError(f"Could not save frame: {frame_path}")
            count += 1

        return count
    finally:
        capture.release()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("video", type=Path, help="Input video file")
    parser.add_argument("destination", type=Path, help="Folder for extracted JPEGs")
    parser.add_argument(
        "--interval",
        type=float,
        default=FRAME_INTERVAL_SECONDS,
        help="Seconds between frames (default: %(default)s; use 0.5 for two per second)",
    )
    args = parser.parse_args()

    try:
        count = extract_frames(args.video, args.destination, args.interval)
    except (OSError, ValueError, cv2.error) as error:
        parser.exit(1, f"Error: {error}\n")
    print(f"Saved {count} frames to {args.destination}")


if __name__ == "__main__":
    main()
