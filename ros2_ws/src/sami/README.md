# SAMI sensor subscriber

This ROS 2 Humble package runs the `sami_sensor_subscriber` node. It checks the
ROS graph every two seconds, subscribes to active published topics, and prints
a compact message sample from each topic at most once per second. New publishers
can start after the subscriber. Large image and scan arrays are summarized so
they do not flood the terminal.

The node skips `/rosout` and `/parameter_events`. It only reads and logs data:
it does not publish messages or start sensor drivers. The implementation is in
[sensor_subscriber.py](sami/sensor_subscriber.py), with message formatting in
[summary.py](sami/summary.py).

## Build and run

From the repository root:

```bash
source /opt/ros/humble/setup.bash
cd ros2_ws
colcon build --packages-select sami --symlink-install
source install/setup.bash
ros2 launch sami sami.launch.py
```

The [launch file](launch/sami.launch.py) starts only the subscriber. You can
also run it directly with `ros2 run sami sensor_subscriber`. Stop it with
`Ctrl+C`.

Start publishers in other terminals with ROS 2 and the workspace sourced. For
a quick check, publish a test message from another terminal:

```bash
source /opt/ros/humble/setup.bash
source ros2_ws/install/setup.bash
ros2 topic pub -r 2 /sami_demo std_msgs/msg/String "{data: hello}"
```

The subscriber should log that it is listening to `/sami_demo`, then print
`data=hello`. The Intel RealSense publisher can be started separately with
`ros2 run sami_realsense_camera realsense_camera` after building
[sami_realsense_camera](../sami_realsense_camera/); it needs `pyrealsense2` and
camera hardware.

## Future

- We will move our LiDAR analysis node from [sami_lidar](../sami_lidar/) into
  this package as another ROS node. The `lms1xx` hardware driver can remain a
  separate package.
- We may also move the RealSense camera publisher into this package later.
  Its `pyrealsense2` hardware dependency should remain optional for people who
  only need the subscriber.
