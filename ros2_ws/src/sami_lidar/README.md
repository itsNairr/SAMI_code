# SAMI LiDAR subscriber

The `lidar_subscriber` node reads `/scan` from the LMS1xx LiDAR driver. It checks
the area directly in front of the robot (within about 2 degrees of center)
for readings under 1 metre, then logs `Do not proceed` or `Proceed`. It does
not drive the robot or publish a new topic. See
[lidar_subscriber.py](sami_lidar/lidar_subscriber.py).

These commands use `~/capstone`, the location of this checkout. Replace it
with `~/SAMI` if that is where you cloned the repository. Set the LiDAR IP to
match your device; the example below uses `192.168.1.3` on port `2111`.

## Build once

```bash
cd ~/capstone/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select lms1xx sami_lidar --symlink-install
```

## Window 1: LiDAR driver

```bash
cd ~/capstone/ros2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 run lms1xx lms1xx --ros-args -p host:=192.168.1.3 -p port:=2111
```

Leave this running. It publishes the `/scan` topic.

## Window 2: Check the topic and run the subscriber

```bash
cd ~/capstone/ros2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 topic list
ros2 topic hz /scan
```

`ros2 topic list` shows available topics. `ros2 topic hz /scan` shows the
received scan rate; press `Ctrl+C` after checking it. Then run:

```bash
ros2 run sami_lidar lidar_subscriber
```

## Window 3: Visualize scans (optional)

```bash
cd ~/capstone/ros2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
rviz2
```

In RViz, set the fixed frame to `laser_link` and add a **LaserScan** display
using `/scan`.

## Quick commands

```bash
cd ~/capstone/ros2_ws/src/sami_lidar
cd ~/capstone/ros2_ws/src/LiDAR/lms1xx/src
ros2 topic echo /scan --once
```

The first two commands open the SAMI LiDAR package and LMS1xx driver source
directories. The last command prints one scan; run it from a terminal where
ROS 2 and the workspace have been sourced.
