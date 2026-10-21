# SAMI

ROS 2 Humble workspace for the Clearpath Husky and its sensors.

## Layout

| Path | Description |
|------|-------------|
| `ros2_ws/src/husky` | Husky ROS 2 packages (`husky_base`, `husky_control`, ...) |
| `ros2_ws/src/microstrain_3dmgx3_25` | MicroStrain 3DM-GX3-25 IMU node |
| `simulation/` | Clearpath simulation config |
| `utils/` | Standalone sensor utilities (RealSense, IMU) |

## Build

```bash
source /opt/ros/humble/setup.bash
cd ros2_ws
colcon build --symlink-install
source install/setup.bash
```

## Launch the Husky base

Connect the Husky serial adapter (on WSL2, attach it with `usbipd` first).
The driver uses `/dev/ttyUSB0` (set in
`ros2_ws/src/husky/husky_description/urdf/husky_macro.urdf.xacro`), so make
sure it is readable:

```bash
ls -l /dev/ttyUSB0
sudo chmod 666 /dev/ttyUSB0   # if you get "Failed to open serial port"
```

Then launch:

```bash
ros2 launch husky_base base.launch.py
```

Success looks like:

```
[HuskyHardware]: System Successfully started!
Configured and activated husky_velocity_controller
Configured and activated joint_state_broadcaster
```

## Drive with the keyboard

Install the teleop package once:

```bash
sudo apt install ros-humble-teleop-twist-keyboard
```

In a **second terminal** (with the workspace sourced), while the base launch is
running:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

The `twist_mux` node already subscribes to `/cmd_vel`, so no remapping is needed.

### Keys

```
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

The Husky is capped at 1.0 m/s (`max_speed` in the URDF). Start slow
(`z`/`x` a few times) and keep the robot on blocks or in an open area for the
first test. Press `Ctrl+C` to quit the teleop node (the robot stops after the
0.5 s mux timeout).

## Troubleshooting

- **`Unable to open /dev/ttyUSB0`**: the adapter is not attached to WSL or lacks
  permissions. Check `lsusb` and `ls /dev/ttyUSB*`, then `chmod` as above.
- **Robot does not move**: confirm `ros2 topic echo /cmd_vel` shows messages
  while you press keys, and that both controllers were activated in the launch
  output.
