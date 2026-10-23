
import rclpy
from rclpy.node import Node
import pyrealsense2 as rs
import numpy as np
import cv2
from std_msgs.msg import Float32
from geometry_msgs.msg import Twist

class CameraNode(Node):
    def __init__(self):
        super().__init__('camera_node')
        self.depth_publisher = self.create_publisher(Float32, 'dist_away', 10)
        self.stop_dist_publisher = self.create_publisher(Twist, 'too_close_stop/cmd_vel', 10)
        
        self.get_logger().info('Initializing RealSense camera...')

        # Create the RealSense pipeline and configuration
        self.pipe = rs.pipeline()
        config = rs.config()

        config.enable_stream(
            rs.stream.color, 640, 480, rs.format.bgr8, 30
        )
        config.enable_stream(
            rs.stream.depth, 640, 480, rs.format.z16, 30
        )

        # Start the camera
        self.pipe.start(config)

        # Align depth frames to the color frame
        self.align = rs.align(rs.stream.color)

        # Initial mouse position
        self.mouse_x = 320
        self.mouse_y = 240

        # Update at approximately 30 FPS
        self.timer = self.create_timer(0.033, self.getDepth)

        self.get_logger().info('RealSense camera started successfully.')

    def getDepth(self):
        try:
            frames = self.pipe.wait_for_frames()
            aligned_frames = self.align.process(frames)

            depth_frame = aligned_frames.get_depth_frame()
            color_frame = aligned_frames.get_color_frame()

            if not depth_frame or not color_frame:
                return

            image = np.asanyarray(color_frame.get_data())

            # get_distance returns metres; convert to millimetres
            distance_mm = depth_frame.get_distance(
                self.mouse_x, self.mouse_y
            ) * 1000.0

            cv2.imshow('RealSense Camera', image)
            cv2.waitKey(1)
            if distance_mm > 0:
                dist_msg = Float32()
                dist_msg.data = float(distance_mm)
                self.depth_publisher.publish(dist_msg)
                if distance_mm <= 500: #closer to objest than 0.5 meters stop
                    stop_msg = Twist()
                    #stop forward/back motion
                    stop_msg.linear.x = 0.0
                    #stop rotational motion
                    stop_msg.angular.z = 0.0
                    self.stop_dist_publisher.publish(stop_msg)

        except RuntimeError as e:
            self.get_logger().error(f'RealSense frame error: {e}')

    def destroy_node(self):
        # Stop the camera when the ROS node shuts down
        if hasattr(self, 'pipe'):
            try:
                self.pipe.stop()
            except RuntimeError:
                pass

        cv2.destroyAllWindows()
        super().destroy_node()


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
