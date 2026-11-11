# Extract Video Frames

[ExtractVideoFrames.py](ExtractVideoFrames.py) saves video frames as JPEG images
at a chosen interval, starting at 0 seconds.

## Setup

Install OpenCV:

```bash
python3 -m pip install opencv-python
```

## Usage

Run from the repository root:

```bash
python3 utils/ExtractVideoFrames.py input.mp4 output_frames --interval 0.5
```

Replace `input.mp4` with your video path and `output_frames` with the destination
folder. Quote paths that contain spaces. The destination folder is created
automatically.

| Interval | Frames saved |
|----------|--------------|
| `1.0` | One frame every second |
| `0.5` | One frame every half-second |

You can also change `FRAME_INTERVAL_SECONDS` near the top of the script
(currently `0.5`). That value is used when `--interval` is omitted. The interval
must be greater than zero.

Images are named `input_frame_000000.jpg`, `input_frame_000001.jpg`, and so on,
using the video's filename as the prefix. Existing images are not overwritten;
use a different destination folder if those filenames already exist.
