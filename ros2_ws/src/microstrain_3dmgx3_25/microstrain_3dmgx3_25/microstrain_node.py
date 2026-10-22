"""
ROS 2 Humble publisher node for LORD MicroStrain 3DM-GX3-25.

Publishes:
  - /imu/data (sensor_msgs/msg/Imu)
  - /imu/mag  (sensor_msgs/msg/MagneticField)
"""

import sys
from typing import Optional

# ROS 2 Humble imports
try:
    import rclpy
    from rclpy.node import Node
    from rclpy.qos import QoSHistoryPolicy, QoSProfile, QoSReliabilityPolicy
    from sensor_msgs.msg import Imu, MagneticField
    ROS2_AVAILABLE = True
except ImportError:
    ROS2_AVAILABLE = False

from .driver import MicroStrain3DMGX3Driver, IMUSample


class MicrostrainNode(Node if ROS2_AVAILABLE else object):
    """ROS 2 Humble node publishing 3DM-GX3-25 telemetry."""

    def __init__(self):
        super().__init__("microstrain_node")

        # Declare ROS 2 parameters
        self.declare_parameter("port", "")
        self.declare_parameter("baudrate", 115200)
        self.declare_parameter("rate", 50)
        self.declare_parameter("frame_id", "imu_link")
        self.declare_parameter("publish_mag", True)

        # Retrieve parameter values
        param_port = self.get_parameter("port").get_parameter_value().string_value
        param_baud = self.get_parameter("baudrate").get_parameter_value().integer_value
        self.rate_hz = self.get_parameter("rate").get_parameter_value().integer_value
        self.frame_id = self.get_parameter("frame_id").get_parameter_value().string_value
        self.publish_mag = self.get_parameter("publish_mag").get_parameter_value().bool_value

        # Sensor data QoS profile
        sensor_qos = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10,
        )

        # Create ROS 2 topic publishers
        self.imu_pub = self.create_publisher(Imu, "/imu/data", sensor_qos)
        if self.publish_mag:
            self.mag_pub = self.create_publisher(MagneticField, "/imu/mag", sensor_qos)

        # Static covariance values from hardware specifications
        self.orientation_covariance = [
            0.0001, 0.0,    0.0,
            0.0,    0.0001, 0.0,
            0.0,    0.0,    0.0001,
        ]
        self.angular_velocity_covariance = [
            0.00001, 0.0,     0.0,
            0.0,     0.00001, 0.0,
            0.0,     0.0,     0.00001,
        ]
        self.linear_acceleration_covariance = [
            0.0001, 0.0,    0.0,
            0.0,    0.0001, 0.0,
            0.0,    0.0,    0.0001,
        ]

        # Initialize hardware serial driver
        self.driver = MicroStrain3DMGX3Driver(
            port=param_port or None,
            baudrate=param_baud,
        )
        self.driver.connect()
        self.driver.add_callback(self.on_sample)
        self.driver.start_streaming(rate_hz=self.rate_hz)

        self.get_logger().info(
            f"Connected to 3DM-GX3-25 on {self.driver.port} at {self.rate_hz} Hz (frame: {self.frame_id})"
        )

    def on_sample(self, s: IMUSample):
        """Callback invoked on each received MIP sample."""
        now = self.get_clock().now().to_msg()

        # Construct Imu message
        imu_msg = Imu()
        imu_msg.header.stamp = now
        imu_msg.header.frame_id = self.frame_id

        # Orientation quaternion (x, y, z, w)
        imu_msg.orientation.x = s.quat_xyzw[0]
        imu_msg.orientation.y = s.quat_xyzw[1]
        imu_msg.orientation.z = s.quat_xyzw[2]
        imu_msg.orientation.w = s.quat_xyzw[3]
        imu_msg.orientation_covariance = self.orientation_covariance

        # Angular velocity (rad/s)
        imu_msg.angular_velocity.x = s.gyro_radps[0]
        imu_msg.angular_velocity.y = s.gyro_radps[1]
        imu_msg.angular_velocity.z = s.gyro_radps[2]
        imu_msg.angular_velocity_covariance = self.angular_velocity_covariance

        # Linear acceleration (m/s^2)
        imu_msg.linear_acceleration.x = s.accel_mps2[0]
        imu_msg.linear_acceleration.y = s.accel_mps2[1]
        imu_msg.linear_acceleration.z = s.accel_mps2[2]
        imu_msg.linear_acceleration_covariance = self.linear_acceleration_covariance

        self.imu_pub.publish(imu_msg)

        # Construct MagneticField message
        if self.publish_mag:
            mag_msg = MagneticField()
            mag_msg.header.stamp = now
            mag_msg.header.frame_id = self.frame_id
            mag_msg.magnetic_field.x = s.mag_tesla[0]
            mag_msg.magnetic_field.y = s.mag_tesla[1]
            mag_msg.magnetic_field.z = s.mag_tesla[2]
            self.mag_pub.publish(mag_msg)

    def destroy_node(self):
        """Release hardware serial port on shutdown."""
        if hasattr(self, "driver") and self.driver:
            self.driver.stop_streaming()
            self.driver.disconnect()
        super().destroy_node()


def main(args=None):
    """Entry point for ROS 2 Humble node."""
    if not ROS2_AVAILABLE:
        print("Error: rclpy not found. Install ROS 2 Humble to execute this node.", file=sys.stderr)
        sys.exit(1)

    rclpy.init(args=args)
    node = MicrostrainNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
