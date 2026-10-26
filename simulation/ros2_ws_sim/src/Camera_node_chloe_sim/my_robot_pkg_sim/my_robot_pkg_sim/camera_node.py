import rclpy
from rclpy.node import Node
# SIM: removed pyrealsense2 and cv2 imports
import numpy as np
import math                                                          # SIM: added
from sensor_msgs.msg import Image                                    # SIM: added
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy  # SIM: added
from std_msgs.msg import Float32
from geometry_msgs.msg import Twist

class CameraNode(Node):
    def __init__(self):
        super().__init__('camera_node')
        self.depth_publisher = self.create_publisher(Float32, 'dist_away', 10)
        self.stop_dist_publisher = self.create_publisher(Twist, 'too_close_stop/cmd_vel', 10)

        self.get_logger().info('Initializing simulated RealSense camera...')

        # SIM: replaced the RealSense pipeline/config/start/align with a depth subscription
        self.declare_parameter('depth_topic', '/cpr_a200_0000/sensors/camera_0/depth/image')
        depth_topic = self.get_parameter('depth_topic').value
        sensor_qos = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=5,
        )
        self.latest_depth = None
        self.create_subscription(Image, depth_topic, self.depth_callback, sensor_qos)

        # Initial mouse position
        self.mouse_x = 320
        self.mouse_y = 240

        # Update at approximately 30 FPS
        self.timer = self.create_timer(0.033, self.getDepth)

        self.get_logger().info('Simulated RealSense camera started successfully.')

    # SIM: new. Stores the newest depth frame from Gazebo
    def depth_callback(self, msg):
        self.latest_depth = msg

    # SIM: new. Stands in for depth_frame.get_distance(x, y) * 1000.0
    def get_distance_mm(self, msg, x, y):
        if msg.encoding == '32FC1':      # sim: float metres
            dtype, to_mm = np.float32, 1000.0
        elif msg.encoding == '16UC1':    # real camera: uint16 millimetres
            dtype, to_mm = np.uint16, 1.0
        else:
            self.get_logger().error(f'Unsupported depth encoding: {msg.encoding}')
            return 0.0
        dt = np.dtype(dtype).newbyteorder('>' if msg.is_bigendian else '<')
        arr = np.frombuffer(msg.data, dtype=dt).reshape(msg.height, msg.step // dt.itemsize)
        x = min(x, msg.width - 1)
        y = min(y, msg.height - 1)
        raw = float(arr[y, x])
        if not math.isfinite(raw):       # Gazebo uses inf/nan for no return
            return 0.0
        return raw * to_mm

    def getDepth(self):
        try:
            # SIM: replaced wait_for_frames() and align with the latest stored frame
            depth_msg = self.latest_depth
            if depth_msg is None:
                return
            self.latest_depth = None     # SIM: process each frame once

            # SIM: same result as before, in millimetres
            distance_mm = self.get_distance_mm(
                depth_msg, self.mouse_x, self.mouse_y
            )

            # SIM: removed cv2.imshow / cv2.waitKey
            if distance_mm > 0:
                dist_msg = Float32()
                dist_msg.data = float(distance_mm)
                self.depth_publisher.publish(dist_msg)
                if distance_mm <= 1200: #closer to objest than 0.5 meters stop
                    stop_msg = Twist()
                    #stop forward/back motion
                    stop_msg.linear.x = 0.0
                    #stop rotational motion
                    stop_msg.angular.z = 0.0
                    self.stop_dist_publisher.publish(stop_msg)

        except RuntimeError as e:
            self.get_logger().error(f'Depth frame error: {e}')

    # SIM: removed destroy_node (it only stopped the RealSense pipeline and closed cv2 windows)


def main(args=None):
    rclpy.init(args=args)
    node = None

    try:
        node = CameraNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except RuntimeError as e:
        print(f'Camera initialization/runtime error: {e}')
    finally:
        if node is not None:
            node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
