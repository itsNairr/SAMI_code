"""Start the SAMI sensor subscriber."""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(package='sami', executable='sensor_subscriber', output='screen'),
    ])
