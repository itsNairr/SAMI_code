# LORD MicroStrain 3DM-GX3-25 IMU/AHRS

Driver, data logging, real-time 3D visualization, and ROS 2 Humble standalone node for the LORD MicroStrain 3DM-GX3-25 inertial sensor.

---

## Directory Structure

```
utils/microstrain_3dmgx3_25/
├── code/
│   ├── imu/
│   │   ├── __init__.py               # Package initialization
│   │   ├── driver.py                 # MIP serial protocol driver
│   │   ├── logger.py                 # CSV and NumPy data logger
│   │   ├── stream_cli.py             # CLI monitor implementation
│   │   └── ros_bridge.py             # ROS 2 Humble publisher node
│   ├── run_imu_cli.py                # CLI telemetry stream runner
│   ├── run_imu_logger.py             # Standalone data logger runner
│   ├── run_imu_desktop_visualizer.py # Matplotlib 3D orientation visualizer
│   └── run_ros2_node.py              # Standalone ROS 2 Humble node runner
├── docs/
│   ├── README.md                     # Sensor documentation
│   └── GAZEBO_ROS_INTEGRATION.md     # Gazebo simulation and URDF/SDF integration
└── experiments/
    └── logs/                         # Default directory for recorded CSV and NPZ files
```

---

## Usage

### 1. Telemetry CLI Streamer
Displays real-time Euler angles, acceleration, and angular rates in the console.

```bash
python utils/microstrain_3dmgx3_25/code/run_imu_cli.py
```

Parameters:
* `--rate <Hz>`: Sampling frequency (default: 50 Hz).
* `--port <COM>`: Serial port (default: auto-detected).

### 2. Data Logger
Records timestamped sensor data to CSV and compressed NumPy (`.npz`) formats. Output files default to `experiments/logs/`.

```bash
# Record for 10 seconds at 50 Hz:
python utils/microstrain_3dmgx3_25/code/run_imu_logger.py --duration 10 --rate 50 --npz

# Continuous logging to a specified path:
python utils/microstrain_3dmgx3_25/code/run_imu_logger.py --out utils/microstrain_3dmgx3_25/experiments/logs/my_run.csv
```

Recorded channels:
* `timestamp_s`, `dt_s`
* `roll_deg`, `pitch_deg`, `yaw_deg`, `roll_rad`, `pitch_rad`, `yaw_rad`
* `quat_w`, `quat_x`, `quat_y`, `quat_z`
* `accel_x_g`, `accel_y_g`, `accel_z_g`, `accel_x_mps2`, `accel_y_mps2`, `accel_z_mps2`
* `gyro_x_degps`, `gyro_y_degps`, `gyro_z_degps`, `gyro_x_radps`, `gyro_y_radps`, `gyro_z_radps`
* `mag_x_gauss`, `mag_y_gauss`, `mag_z_gauss`, `mag_x_tesla`, `mag_y_tesla`, `mag_z_tesla`

### 3. Desktop 3D Visualizer
Renders real-time 3D sensor orientation using unit quaternions and displays live telemetry strip charts.

```bash
python utils/microstrain_3dmgx3_25/code/run_imu_desktop_visualizer.py
```

* Coordinate axes: X = Red (Forward), Y = Green (Right), Z = Blue (Down).
* Strip charts: Euler angles and linear acceleration.

### 4. ROS 2 Humble Standalone Node
Publishes `/imu/data` (`sensor_msgs/msg/Imu`) and `/imu/mag` (`sensor_msgs/msg/MagneticField`) directly via `rclpy`:

```bash
# Run with default settings (auto-detected port, 50 Hz, frame: imu_link)
python utils/microstrain_3dmgx3_25/code/run_ros2_node.py

# Run with custom parameters
python utils/microstrain_3dmgx3_25/code/run_ros2_node.py --port COM4 --rate 100 --frame-id imu_link
```

Refer to [`GAZEBO_ROS_INTEGRATION.md`](GAZEBO_ROS_INTEGRATION.md) for matching Gazebo simulation URDF and SDF configurations.
