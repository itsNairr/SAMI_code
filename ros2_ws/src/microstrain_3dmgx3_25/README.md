# microstrain_3dmgx3_25

ROS 2 Humble driver and publisher node for the LORD MicroStrain 3DM-GX3-25 inertial sensor.

---

## Published Topics

The hardware node publishes one message per received sensor sample. The default
requested rate is **50 Hz**, and `/imu/mag` is enabled by default
(`publish_mag:=false` disables that topic).

| Topic | Message type | Fields | Data and units |
|-------|--------------|--------|----------------|
| `/imu/data` | `sensor_msgs/msg/Imu` | `orientation.{x,y,z,w}` | Sensor-provided orientation quaternion; dimensionless |
| `/imu/data` | `sensor_msgs/msg/Imu` | `angular_velocity.{x,y,z}` | Angular velocity about each sensor axis, rad/s |
| `/imu/data` | `sensor_msgs/msg/Imu` | `linear_acceleration.{x,y,z}` | Scaled accelerometer readings, m/s^2 |
| `/imu/mag` | `sensor_msgs/msg/MagneticField` | `magnetic_field.{x,y,z}` | Magnetic field along each sensor axis, tesla (T) |

Both messages include `header.frame_id` (default: `imu_link`) and
`header.stamp`, set to the current ROS clock time in the sample callback rather
than a timestamp from the sensor. Components retain the sensor's axis convention;
setting `frame_id` labels the data and does not rotate it. The node applies no
gravity compensation to the accelerometer readings.

The IMU message also includes these fixed 3 x 3 covariance matrices, stored in
row-major order. `I_3` is the identity matrix, so all off-diagonal entries are zero.

| Field | Matrix | Units |
|-------|--------|-------|
| `orientation_covariance` | `0.0001 * I_3` | rad^2 |
| `angular_velocity_covariance` | `0.00001 * I_3` | (rad/s)^2 |
| `linear_acceleration_covariance` | `0.0001 * I_3` | (m/s^2)^2 |

These are constants in the node, not estimates calculated from incoming samples.
`magnetic_field_covariance` remains at its default all-zero value; the node does
not supply a magnetic-field uncertainty estimate.

The driver also reads roll, pitch, and yaw from the sensor and stores both radians
and degrees in each sample. Those Euler angles are available to the standalone
utilities but are not published as separate ROS fields or topics.

## Equations Used

The conversions below are implemented in
[`driver.py`](microstrain_3dmgx3_25/driver.py). The field-to-topic mapping is in
[`microstrain_node.py`](microstrain_3dmgx3_25/microstrain_node.py).

### Sensor values to ROS units

For each axis `i` in `x, y, z`, acceleration is converted from g to m/s^2,
and magnetic field is converted from gauss to tesla:

```text
a_i [m/s^2] = a_i [g] * 9.80665
B_i [T]     = B_i [gauss] * 10^-4
omega_i [rad/s] = sensor gyro_i [rad/s]
```

For example, `1 g` becomes `9.80665 m/s^2`, and `0.5 gauss` becomes
`0.00005 T`. Gyroscope values already use rad/s and are copied directly.

The sensor supplies its quaternion in scalar-first order `(q0, q1, q2, q3)`.
The driver reorders the components for ROS:

```text
(w, x, y, z) = (q0, q1, q2, q3)
ROS (x, y, z, w) = (q1, q2, q3, q0)
```

Orientation comes directly from the sensor. The Python driver does not calculate
it by integrating angular velocity or fusing the accelerometer and magnetometer.

For the standalone CLI and visualizer, the driver also converts Euler angles and
angular velocity to degrees:

```text
angle [deg]       = angle [rad] * 180 / pi
omega_i [deg/s]   = omega_i [rad/s] * 180 / pi
```

The ROS messages continue to use quaternion orientation and rad/s angular velocity.

### Requested sampling rate

The driver queries the sensor base rate, with a fallback of `1000 Hz`, and uses
integer decimation to configure the stream:

```text
f_request = max(1, min(rate, 500))
d         = max(1, floor(f_base / f_request))
f_stream  = f_base / d
```

Here `rate` is the requested rate in Hz, `d` is the decimation factor, and
`f_stream` is the nominal configured sensor rate. With a `1000 Hz` base rate,
the default `50 Hz` request gives `d = 20`. Requests that do not divide the base
rate exactly can produce a different nominal rate. The node publishes from
sample callbacks rather than a separate timer.

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
