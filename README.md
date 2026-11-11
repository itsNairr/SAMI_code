# SAMI

## Contents

- [Repository Layout](#repository-layout)
- [Requirements](#requirements)
- [Build](#build)
- [Launch the Husky Base](#launch-the-husky-base)
- [Sensor Nodes](#sensor-nodes)
- [Monitor Topics with SAMI](#monitor-topics-with-sami)
- [MicroStrain Data](#microstrain-data)
- [Drive with the Keyboard](#drive-with-the-keyboard)
- [Simulation](#simulation)
- [Utilities and Dataset Preparation](#utilities-and-dataset-preparation)
- [Troubleshooting](#troubleshooting)

## Repository Layout

| Path | Description |
|------|-------------|
| [ros2_ws/src/husky/](ros2_ws/src/husky/) | Husky base driver, controllers, localization, robot description, and teleoperation |
| [ros2_ws/src/LiDAR/lms1xx/](ros2_ws/src/LiDAR/lms1xx/) | SICK LMS1xx LiDAR driver |
| [ros2_ws/src/sami_lidar/](ros2_ws/src/sami_lidar/) | LiDAR obstacle analysis and logging |
| [ros2_ws/src/microstrain_3dmgx3_25/](ros2_ws/src/microstrain_3dmgx3_25/) | MicroStrain 3DM-GX3-25 IMU driver and publisher |
| [ros2_ws/src/sami_realsense_camera_forward/](ros2_ws/src/sami_realsense_camera_forward/) | RealSense depth processing, person segmentation, and stop requests |
| [ros2_ws/src/sami/](ros2_ws/src/sami/) | SAMI topic monitor and launch entry point |
| [simulation/](simulation/) | Clearpath/Gazebo configuration, pier world, and simulated sensor adapters |
| [utils/](utils/) | Video frame extraction, YOLO dataset conversion, and standalone sensor tools |

## Requirements

- ROS 2 Humble, Python 3, `colcon`, and the ROS dependencies for the packages you
  build. The simulation setup targets Ubuntu 22.04 LTS.
- For hardware operation, connect the Husky and the sensors you intend to use;
  configure serial permissions and the LiDAR network connection.
- Install component-specific Python dependencies in the environment used to run
  that component:

| Component | Python dependencies |
|-----------|---------------------|
| RealSense camera and person detection | `pyrealsense2`, `numpy`, `opencv-python`, `inference`, `supervision` |
| MicroStrain driver and standalone visualizer | `pyserial`; the visualizer also uses `numpy` and `matplotlib` |
| Video extraction and dataset conversion | `opencv-python`, `numpy` |

The camera also needs access to the configured `rfdetr-seg-nano` model and a
graphical display for its preview window. For Clearpath/Gazebo installation,
follow the [simulation setup guide](simulation/README.md).

## Build

From the repository root:

```bash
source /opt/ros/humble/setup.bash
cd ros2_ws
colcon build --symlink-install
source install/setup.bash
```

To build only the sensor subscriber and RealSense publisher, use
`colcon build --packages-select sami sami_realsense_camera_forward --symlink-install`
from `ros2_ws` instead of building the full workspace.

For each new hardware terminal, start at the repository root and source both
ROS 2 and the built workspace before running the commands below:

```bash
source /opt/ros/humble/setup.bash
source ros2_ws/install/setup.bash
```

## Launch the Husky Base

Connect the Husky serial adapter (on WSL2, attach it with `usbipd` first).
The driver uses `/dev/ttyUSB0`, configured in the
[Husky URDF](ros2_ws/src/husky/husky_description/urdf/husky_macro.urdf.xacro).
Make sure your user has read and write access to the device:

```bash
ls -l /dev/ttyUSB0
```

Then launch:

```bash
ros2 launch husky_base base.launch.py
```

Success looks like:

```text
[HuskyHardware]: System Successfully started!
Configured and activated husky_velocity_controller
Configured and activated joint_state_broadcaster
```

## Sensor Nodes

Start the components you need in separate sourced terminals:

| Component | Command |
|-----------|---------|
| RealSense camera | `ros2 run sami_realsense_camera_forward camera` |
| LMS1xx LiDAR driver | `ros2 launch lms1xx LMS1xx.launch.py` |
| LiDAR obstacle analysis | `ros2 run sami_lidar lidar_subscriber` |
| MicroStrain IMU | `ros2 run microstrain_3dmgx3_25 microstrain_node` |

Set the LiDAR host and port to match your sensor in
[lms_111.yaml](ros2_ws/src/LiDAR/lms1xx/config/lms_111.yaml). The LiDAR analysis
node reads `/scan` and logs whether the area directly ahead is clear; it does
not send drive commands. See the [LiDAR guide](ros2_ws/src/sami_lidar/README.md)
for connection and visualization instructions.

The RealSense node checks depth for nearby objects, runs person segmentation
when an object is close, and publishes stop requests and a boolean motion lock.
The current implementation asserts the lock for close objects whether or not
they are identified as people. It displays camera frames locally rather than
publishing raw image topics.

The main hardware sensor topics are:

| Topic | Message type | Purpose |
|-------|--------------|---------|
| `/scan` | `sensor_msgs/msg/LaserScan` | LiDAR range measurements |
| `/imu/data` | `sensor_msgs/msg/Imu` | Orientation, angular velocity, and acceleration |
| `/imu/mag` | `sensor_msgs/msg/MagneticField` | Magnetic field vector |
| `/too_close_stop/cmd_vel` | `geometry_msgs/msg/Twist` | Camera request for zero velocity |
| `/person_stop/cmd_vel` | `std_msgs/msg/Bool` | Camera motion lock; `true` blocks lower-priority commands |

The camera declares a `/dist_away` publisher, but the current implementation
does not publish distance samples on it.

## Monitor Topics with SAMI

[sami.launch.py](ros2_ws/src/sami/launch/sami.launch.py) starts the read-only
SAMI sensor subscriber. Start sensor publishers separately; the monitor
discovers publishers that are already running or start later:

```bash
ros2 launch sami sami.launch.py
```

The subscriber listens to all discoverable published application topics,
including `/scan`, `/imu/data`, and camera topics. It prints one compact sample
per topic per second so image and scan payloads do not flood the terminal.
ROS bookkeeping topics (`/rosout` and `/parameter_events`) are excluded. The
subscriber only reads topics; it never sends drive commands. To run just the node:

```bash
ros2 run sami sensor_subscriber
```

See the [SAMI package README](ros2_ws/src/sami/README.md) for a test publisher
example and future package plans.

## MicroStrain Data

The MicroStrain 3DM-GX3-25 hardware node publishes `/imu/data`
(`sensor_msgs/msg/Imu`) with orientation as a quaternion, angular velocity in
rad/s, and acceleration in m/s^2. It also publishes `/imu/mag`
(`sensor_msgs/msg/MagneticField`) with the magnetic field in tesla. The default
requested sampling rate is 50 Hz, with messages labelled `imu_link`.

See the [MicroStrain README](ros2_ws/src/microstrain_3dmgx3_25/README.md)
for the published fields, timestamps, covariance values, unit-conversion
equations, quaternion component ordering, and sampling-rate equation.

## Drive with the Keyboard

Install the teleop package once:

```bash
sudo apt install ros-humble-teleop-twist-keyboard
```

In a **second terminal** (with the workspace sourced), while the base launch is
running:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

The `twist_mux` node subscribes to `/cmd_vel`, so no remapping is needed.
Camera stops have higher priority than keyboard commands, and the boolean
camera lock is configured in
[twist_mux.yaml](ros2_ws/src/husky/husky_control/config/twist_mux.yaml).

### Keys

```text
   u    i    o
   j    k    l
   m    ,    .
```

| Key | Action |
|-----|--------|
| `i` | Forward |
| `,` | Backward |
| `j` | Rotate left |
| `l` | Rotate right |
| `u` / `o` | Forward + turn left / right |
| `m` / `.` | Backward + turn left / right |
| `k` | Stop |
| `q` / `z` | Increase / decrease all speeds by 10% |
| `w` / `x` | Increase / decrease linear speed by 10% |
| `e` / `c` | Increase / decrease angular speed by 10% |

The Husky is capped at 1.0 m/s in the
[URDF](ros2_ws/src/husky/husky_description/urdf/husky_macro.urdf.xacro) and
[controller configuration](ros2_ws/src/husky/husky_control/config/control.yaml).
Start slow
(`z`/`x` a few times) and keep the robot on blocks or in an open area for the
first test. Press `Ctrl+C` to quit the teleop node (the robot stops after the
0.5 s controller command timeout).

## Simulation

The simulation uses Clearpath/Gazebo with a Husky, a custom pier world, and
camera and IMU adapter nodes. Follow the
[simulation README](simulation/README.md) to install the simulator and choose
the warehouse or pier world.

After setup, start the custom pier world from the repository root:

```bash
bash simulation/run_sim.sh
```

In a second terminal, build the simulation packages once and launch the sensor
adapters:

```bash
source /opt/ros/humble/setup.bash
cd simulation/ros2_ws_sim
colcon build --symlink-install
source install/setup.bash
ros2 launch sensors_sim_bringup sensors.launch.py
```

Robot and sensor placement are configured in
[robot.yaml](simulation/clearpath/robot.yaml). Simulated sensor topic mappings
and namespaces are configured in
[sensors.launch.py](simulation/ros2_ws_sim/src/sensors_sim_bringup/launch/sensors.launch.py).

## Utilities and Dataset Preparation

| Tool | Purpose |
|------|---------|
| [ExtractVideoFrames.py](utils/ExtractVideoFrames.py) | Save video frames as JPEGs at a configurable interval, such as every 1 or 0.5 seconds |
| [ConvertDataSet.py](utils/ConvertDataSet.py) | Convert images and crack masks into YOLO segmentation labels with training and validation folders |
| [RealSense utilities](utils/realsense/docs/README.md) | Interactive depth measurements and sensor experiment records |
| [MicroStrain utilities](utils/microstrain_3dmgx3_25/docs/README.md) | Standalone IMU telemetry and 3D orientation visualization |

See the [utilities README](utils/README.md) for installation, video extraction
commands, adjustable intervals, and dataset input/output configuration. The
frame extractor and dataset converter can run independently of ROS 2.

## Troubleshooting

- **ROS package not found**: build the package and source ROS 2 plus the correct
  hardware or simulation workspace in the current terminal.
- **`Unable to open /dev/ttyUSB0`**: the adapter is not attached to WSL or lacks
  permissions. Check `lsusb`, the device path, and your user's read/write access.
- **No LiDAR scans**: check the sensor network connection and host/port in
  [lms_111.yaml](ros2_ws/src/LiDAR/lms1xx/config/lms_111.yaml), then inspect
  `ros2 topic hz /scan`.
- **Camera startup errors**: check RealSense attachment, Python dependencies,
  model availability, and access to a graphical display.
- **Robot does not move**: confirm `ros2 topic echo /cmd_vel` shows messages
  while you press keys, and that both controllers were activated in the launch
  output. Check `/person_stop/cmd_vel` and other mux locks if sensor nodes are
  running.
