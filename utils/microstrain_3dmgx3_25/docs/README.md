# LORD MicroStrain 3DM-GX3-25 IMU/AHRS

Driver, real-time 3D visualization, and ROS 2 Humble standalone node for the LORD MicroStrain 3DM-GX3-25 inertial sensor.

---

## Directory Structure

```
utils/microstrain_3dmgx3_25/
├── code/
│   ├── imu/
│   │   ├── __init__.py               # Package initialization
│   │   ├── driver.py                 # MIP serial protocol driver
│   │   ├── stream_cli.py             # CLI monitor implementation
│   │   └── ros_bridge.py             # ROS 2 Humble publisher node
│   ├── run_imu_cli.py                # CLI telemetry stream runner
│   ├── run_imu_desktop_visualizer.py # Matplotlib 3D orientation visualizer
│   └── run_ros2_node.py              # Standalone ROS 2 Humble node runner
├── docs/
│   ├── README.md                     # Sensor documentation
│   └── GAZEBO_ROS_INTEGRATION.md     # Gazebo simulation and URDF/SDF integration
└── experiments/                      # Sensor experiment notes and benchmarks
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

### 2. Desktop 3D Visualizer
Renders real-time 3D sensor orientation using unit quaternions and displays live telemetry strip charts.

```bash
python utils/microstrain_3dmgx3_25/code/run_imu_desktop_visualizer.py
```

* Coordinate axes: X = Red (Forward), Y = Green (Right), Z = Blue (Down).
* Strip charts: Euler angles and linear acceleration.

### 3. ROS 2 Humble Standalone Node
Publishes `/imu/data` (`sensor_msgs/msg/Imu`) and `/imu/mag` (`sensor_msgs/msg/MagneticField`) directly via `rclpy`:

```bash
# Run with default settings (auto-detected port, 50 Hz, frame: imu_link)
python utils/microstrain_3dmgx3_25/code/run_ros2_node.py

# Run with custom parameters
python utils/microstrain_3dmgx3_25/code/run_ros2_node.py --port COM4 --rate 100 --frame-id imu_link
```

Refer to [`GAZEBO_ROS_INTEGRATION.md`](GAZEBO_ROS_INTEGRATION.md) for matching Gazebo simulation URDF and SDF configurations.
