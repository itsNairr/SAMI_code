from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        # IMU
        Node(
            package="microstrain_3dmgx3_25_sim",
            executable="microstrain_node",
            parameters=[{
                "use_sim_time": True,
                "input_topic": "/cpr_a200_0000/sensors/imu_0/data",
                "imu_topic": "/imu/data",
                "frame_id": "imu_0_link",
                "publish_mag": False,
            }],
            output="screen",
        ),

        # Camera 0 (add once Camera_node_chloe_sim is done)

        # Camera 1

        # Lidar
    ])
