# microstrain_3dmgx3_25

ROS 2 Humble driver and publisher node for the LORD MicroStrain 3DM-GX3-25 inertial sensor.

---

## Published Topics

* `/imu/data` (`sensor_msgs/msg/Imu`): Orientation quaternion, angular velocity (rad/s), linear acceleration (m/s^2).
* `/imu/mag` (`sensor_msgs/msg/MagneticField`): 3-axis magnetic field vector (Tesla).

---

## Parameters

* `port` (`string`, default: `""`): Serial port name (empty string enables auto-detection).
* `baudrate` (`int`, default: `115200`): Serial baud rate.
* `rate` (`int`, default: `50`): Data streaming and publish frequency in Hz.
* `frame_id` (`string`, default: `"imu_link"`): TF frame identifier for header.
* `publish_mag` (`bool`, default: `true`): Toggle publishing magnetometer vector.

---

## Build and Run

### 1. Build Package
From the root of `ros2_ws`:
```bash
colcon build --packages-select microstrain_3dmgx3_25
source install/setup.bash
```

### 2. Run Node
```bash
# Run with default parameters
ros2 run microstrain_3dmgx3_25 microstrain_node

# Run with parameter overrides
ros2 run microstrain_3dmgx3_25 microstrain_node --ros-args -p port:=COM4 -p rate:=100 -p frame_id:=imu_link
```
