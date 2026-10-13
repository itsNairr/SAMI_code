"""
ROS 2 Humble standalone node for LORD MicroStrain 3DM-GX3-25.

Publishes:
  - /imu/data (sensor_msgs/msg/Imu)
  - /imu/mag  (sensor_msgs/msg/MagneticField)
"""

import argparse
import sys
import time
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


class MicrostrainRos2HumbleNode(Node if ROS2_AVAILABLE else object):
    """ROS 2 Humble node publishing MicroStrain 3DM-GX3-25 telemetry."""

    def __init__(
        self,
        port: Optional[str] = None,
        baudrate: int = 115200,
        rate: int = 50,
        frame_id: str = "imu_link",
        publish_mag: bool = True,
    ):
        super().__init__("microstrain_3dmgx3_25_node")

        # Declare ROS 2 parameters
        self.declare_parameter("port", port or "")
        self.declare_parameter("baudrate", baudrate)
        self.declare_parameter("rate", rate)
        self.declare_parameter("frame_id", frame_id)
        self.declare_parameter("publish_mag", publish_mag)

        # Retrieve parameter values
        param_port = self.get_parameter("port").get_parameter_value().string_value or port
        param_baud = self.get_parameter("baudrate").get_parameter_value().integer_value
        self.rate_hz = self.get_parameter("rate").get_parameter_value().integer_value
        self.frame_id = self.get_parameter("frame_id").get_parameter_value().string_value
        self.publish_mag = self.get_parameter("publish_mag").get_parameter_value().bool_value

        # Standard sensor data QoS profile
        sensor_qos = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10,
        )

        # Publishers
        self.imu_pub = self.create_publisher(Imu, "/imu/data", sensor_qos)
        if self.publish_mag:
            self.mag_pub = self.create_publisher(MagneticField, "/imu/mag", sensor_qos)

        # Covariance matrices based on 3DM-GX3-25 specifications
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

        # Initialize hardware driver
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
        """Callback invoked on each received MIP IMUSample."""
        now = self.get_clock().now().to_msg()

        # Construct sensor_msgs/msg/Imu
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

        # Construct sensor_msgs/msg/MagneticField
        if self.publish_mag:
            mag_msg = MagneticField()
            mag_msg.header.stamp = now
            mag_msg.header.frame_id = self.frame_id
            mag_msg.magnetic_field.x = s.mag_tesla[0]
            mag_msg.magnetic_field.y = s.mag_tesla[1]
            mag_msg.magnetic_field.z = s.mag_tesla[2]
            self.mag_pub.publish(mag_msg)

    def destroy_node(self):
        """Stops sensor stream and releases hardware port on shutdown."""
        if self.driver:
            self.driver.stop_streaming()
            self.driver.disconnect()
        super().destroy_node()


def main(args=None):
    """Main execution function for standalone ROS 2 Humble node."""
    if not ROS2_AVAILABLE:
        print("Error: rclpy not found. Install ROS 2 Humble to execute this node.", file=sys.stderr)
        sys.exit(1)

    # CLI argument parsing
    parser = argparse.ArgumentParser(description="MicroStrain 3DM-GX3-25 ROS 2 Humble Node")
    parser.add_argument("--port", type=str, default="", help="Serial port (default: auto-detect)")
    parser.add_argument("--baudrate", type=int, default=115200, help="Baud rate (default: 115200)")
    parser.add_argument("--rate", type=int, default=50, help="Publish rate in Hz (default: 50)")
    parser.add_argument("--frame-id", type=str, default="imu_link", help="TF frame ID (default: imu_link)")
    parser.add_argument("--no-mag", action="store_true", help="Disable magnetic field publishing")

    parsed, unknown = parser.parse_known_args(args=sys.argv[1:])

    rclpy.init(args=unknown)
    node = MicrostrainRos2HumbleNode(
        port=parsed.port or None,
        baudrate=parsed.baudrate,
        rate=parsed.rate,
        frame_id=parsed.frame_id,
        publish_mag=not parsed.no_mag,
    )
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
