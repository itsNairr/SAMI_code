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

        # Camera 0 forward camera
	Node(
	    package="my_robot_pkg_sim",
	    executable="camera_0",
	    name="camera_0_node",
	    parameters=[{
		"use_sim_time": True,
		"depth_topic": "/cpr_a200_0000/sensors/camera_0/depth/image",
	    }],
	    remappings=[
		("too_close_stop/cmd_vel", "/cpr_a200_0000/too_close_stop/cmd_vel"),
	    ],
	    output="screen",
	),
        # Camera 1 downward camera

        # Lidar
    ])
