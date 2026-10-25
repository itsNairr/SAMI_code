"""
ROS 2 Humble simulation node for the MicroStrain 3DM-GX3-25.

Instead of reading the serial driver, this node subscribes to the simulated
Gazebo IMU and republishes it using the same message layout, covariances and
topics as the hardware node.

Publishes:
  - /imu/data (sensor_msgs/msg/Imu)
  - /imu/mag  (sensor_msgs/msg/MagneticField)  [optional, synthetic]
"""

import sys

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSHistoryPolicy, QoSProfile, QoSReliabilityPolicy
from sensor_msgs.msg import Imu, MagneticField


class MicrostrainNode(Node):
    """Republishes the simulated IMU as if it came from the 3DM-GX3-25."""

    def __init__(self):
        super().__init__("microstrain_node")

        # Parameters (rate, frame_id, publish_mag are kept from the hardware node)
        self.declare_parameter("input_topic", "/a200_0000/sensors/imu_0/raw/imu")
        self.declare_parameter("imu_topic", "/imu/data")
        self.declare_parameter("mag_topic", "/imu/mag")
        self.declare_parameter("rate", 0)  # Hz, 0 = publish every sim message
        self.declare_parameter("frame_id", "imu_0_link")
        self.declare_parameter("publish_mag", False)
        # Synthetic magnetic field in Tesla (Gazebo's IMU has no magnetometer)
        self.declare_parameter("mag_field", [2.0e-5, 0.0, -4.0e-5])

        input_topic = self.get_parameter("input_topic").value
        imu_topic = self.get_parameter("imu_topic").value
        mag_topic = self.get_parameter("mag_topic").value
        self.rate_hz = self.get_parameter("rate").value
        self.frame_id = self.get_parameter("frame_id").value
        self.publish_mag = self.get_parameter("publish_mag").value
        self.mag_field = list(self.get_parameter("mag_field").value)

        sensor_qos = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10,
        )

        self.imu_pub = self.create_publisher(Imu, imu_topic, sensor_qos)
        if self.publish_mag:
            self.mag_pub = self.create_publisher(MagneticField, mag_topic, sensor_qos)

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

        self._last_pub_ns = None

        # Subscribe to the raw simulated IMU (best effort receives from
        # either reliable or best-effort publishers)
        self.create_subscription(Imu, input_topic, self.on_sim_imu, sensor_qos)

        self.get_logger().info(
            f"Sim IMU: {input_topic} -> {imu_topic} (frame: {self.frame_id})"
        )

    def on_sim_imu(self, s: Imu):
        """Callback invoked for each simulated IMU message."""
        stamp_ns = s.header.stamp.sec * 1_000_000_000 + s.header.stamp.nanosec

        # Optional throttle, using sim time from the message stamp
        if self.rate_hz and self.rate_hz > 0:
            period_ns = int(1e9 / self.rate_hz)
            if self._last_pub_ns is not None and stamp_ns - self._last_pub_ns < period_ns:
                return
            self._last_pub_ns = stamp_ns

        imu_msg = Imu()
        imu_msg.header.stamp = s.header.stamp
        imu_msg.header.frame_id = self.frame_id

        # Orientation quaternion
        imu_msg.orientation = s.orientation
        imu_msg.orientation_covariance = self.orientation_covariance

        # Angular velocity (rad/s)
        imu_msg.angular_velocity = s.angular_velocity
        imu_msg.angular_velocity_covariance = self.angular_velocity_covariance

        # Linear acceleration (m/s^2). Gazebo already reports m/s^2,
        # so the hardware node's g -> m/s^2 conversion is not needed.
        imu_msg.linear_acceleration = s.linear_acceleration
        imu_msg.linear_acceleration_covariance = self.linear_acceleration_covariance

        self.imu_pub.publish(imu_msg)

        if self.publish_mag:
            mag_msg = MagneticField()
            mag_msg.header.stamp = s.header.stamp
            mag_msg.header.frame_id = self.frame_id
            mag_msg.magnetic_field.x = self.mag_field[0]
            mag_msg.magnetic_field.y = self.mag_field[1]
            mag_msg.magnetic_field.z = self.mag_field[2]
            self.mag_pub.publish(mag_msg)


def main(args=None):
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
