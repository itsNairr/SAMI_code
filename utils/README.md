# Utilities

## Setup

Install the Python dependencies:

```bash
python3 -m pip install opencv-python numpy
```

## Extract Video Frames

[ExtractVideoFrames.py](ExtractVideoFrames.py) saves video frames as JPEG images
at a chosen interval, starting at 0 seconds.

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

## Convert a Dataset to YOLO Segmentation Format

[ConvertDataSet.py](ConvertDataSet.py) converts images and their crack masks into
YOLO polygon labels, then saves them in training and validation folders.

Prepare an image folder and a matching mask folder. Each mask must share its
image's filename stem: for example, `crack_001.jpg` needs `crack_001.png` or
`crack_001.bmp` in the mask folder. Images can be PNG, JPG, JPEG, or BMP. Masks
should match the image dimensions, with nonzero pixels marking cracks and zero
pixels marking the background.

Edit the configuration block near the top of the script:

```python
SRC_IMAGES_DIR = "./data/images/"
SRC_MASKS_DIR = "./data/masks/"
OUTPUT_DATASET_DIR = "./yolo_dataset/"
TRAIN_SPLIT = 0.8  # 80% training, 20% validation
CLASS_ID = 0      # Crack class ID
```

Run from the repository root; no command-line arguments are needed:

```bash
python3 utils/ConvertDataSet.py
```

Relative paths in the configuration are resolved from the folder where you run
the command. The script creates this output structure:

```text
yolo_dataset/
├── images/
│   ├── train/
│   └── val/
└── labels/
    ├── train/
    └── val/
```

Each copied image gets a matching `.txt` label containing one polygon per line:
`class_id x1 y1 x2 y2 ...`, with coordinates normalized to the mask width and
height. Images with missing or unreadable masks are skipped. Contours with an
area below 5 pixels are ignored, and images with no remaining contours are also
skipped. Use a fresh output folder for each conversion to keep runs separate.
