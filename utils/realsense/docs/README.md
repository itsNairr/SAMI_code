# Intel RealSense RGB-D Camera

Utilities and accuracy benchmark records for the Intel RealSense depth sensor.

---

## Directory Structure

```
utils/realsense/
├── code/
│   └── DepthTest.py             # Video streaming and interactive depth measurement script
├── docs/
│   └── README.md                # Camera documentation
└── experiments/
    └── DepthTestExperiment1     # Experiment 1 measurement records
```

---

## Usage

### Interactive Depth Measurement Test
Streams color and aligned depth frames, displaying depth values at the mouse cursor position.

```bash
python utils/realsense/code/DepthTest.py
```

* Hover the cursor over a pixel to inspect distance in millimeters.
* Press `q` to terminate the stream.
