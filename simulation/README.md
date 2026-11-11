# SAMI Simulation

Simulation workspace for the Clearpath Husky and its sensors.

## Layout

| Path | Description |
|------|-------------|
| `ros2_ws_sim/src/Camera_node_chloe_sim` | Forward Intel RealSense simulation distance and stop publisher |
| `ros2_ws_sim/src/microstrain_3dmgx3_25_sim` | Simulation MicroStrain 3DM-GX3-25 IMU node |
| `ros2_ws/src/sensors_sim_bringup` |  |
| `clearpath/robot.yaml` | Husky configuration settings and sensor setup |
| `run_sim.sh` | Executable file for starting up simulation |

## Gazebo Setup
Install Ubuntu 22.04 LTS
Intstall Ros2 Humble
Follow tutorial to setup offboard computer: 
- https://docs.clearpathrobotics.com/docs/ros2humble/ros/installation/offboard_pc/
- Stop after Step 0.5

Follow tutorial to install Clearpath Simulator:
- https://docs.clearpathrobotics.com/docs/ros2humble/ros/tutorials/simulator/install/
- Stop after running the first two commands in Step 0.3 shown below:
```bash
sudo apt update
sudo apt install ros-humble-clearpath-simulator
```

Check installation with following commands
```bash
ls /opt/ros/humble/share/clearpath_gz
ign gazebo --version
```

## Run Gazebo Simulation Warehouse World
Run commands below. Change setup_path to match your setup
```bash
source /opt/ros/humble/setup.bash
ros2 launch clearpath_gz simulation.launch.py setup_path:=/$HOME/<path_to_repo>/SAMI_code/simulation/clearpath
```

## Run Gazebo Simulation Pier World
### Run the run_sim.sh file
Run one time
```bash
chmod +x run_sim.sh
```
Run file
```bash
./run_sim.sh
```

## Running the Simulated Sensors
### One Time Setup - Build the Packages
```bash
source /opt/ros/humble/setup.bash
cd <path_to_repo>/SAMI_code/simulation/ros2_ws_sim
colcon build --symlink-install
source install/setup.bash
``` 
### Running the Sensors
With the simulation running, in a second terminal
```bash
source /opt/ros/humble/setup.bash
source <path_to_repo>/SAMI_code/simulation/ros2_ws_sim/install/setup.bash
ros2 launch sensors_sim_bringup sensors.launch.py
``` 