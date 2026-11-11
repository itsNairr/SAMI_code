
import rclpy
from rclpy.node import Node
import pyrealsense2 as rs
import numpy as np
import cv2
from std_msgs.msg import Float32
from geometry_msgs.msg import Twist
from . import person_identify

class RealSenseCameraNode(Node):
    def __init__(self):
        super().__init__('realsense_camera')
        self.depth_publisher = self.create_publisher(Float32, 'dist_away', 10)
        self.stop_dist_publisher = self.create_publisher(Twist, 'too_close_stop/cmd_vel', 10)
        self.stop_person_publisher = self.create_publisher(Twist, 'person_stop/cmd_vel', 10)
        
        self.person_detector = person_identify.PersonIdentify()
        
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

        # Update at approximately 30 FPS
        self.timer = self.create_timer(0.033, self.getDepth)
        print("hi")

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

            cv2.imshow('RealSense Camera', image)
            cv2.waitKey(1)
            raw_depth_image = np.asanyarray(depth_frame.get_data())
            #check if there is a pixel which is greater than 0 and less than 500
            has_close_object = np.any((raw_depth_image > 0) & (raw_depth_image < 500))
            if has_close_object:
                #also now need to check if its a person or not
                stop_msg = Twist()
                #stop forward/back motion
                stop_msg.linear.x = 0.0
                #stop rotational motion
                stop_msg.angular.z = 0.0
                self.stop_dist_publisher.publish(stop_msg)
                print("too close")
                
                person_present = self.person_detector.identify(image)
                if person_present:
                    stop_p_msg = Twist()
                    #stop forward/back motion
                    stop_p_msg.linear.x = 0.0
                    #stop rotational motion
                    stop_p_msg.angular.z = 0.0
                    self.stop_person_publisher.publish(stop_p_msg)
                    print("Stop its a person")
                else:
                    #trigger other code go around code
                    #publish go to other program
                    #for now we are just going to reverse a bit untill good
                    stop_p_msg = Twist()
                    #move backwards
                    stop_p_msg.linear.x = -0.5
                    #stop rotational motion
                    stop_p_msg.angular.z = 0.0
                    self.stop_person_publisher.publish(stop_p_msg)
                    print("reverse away from object")



                    #so if it's a person stop  if not reverse untill it is farter than 0.5 then execute the move around part or add obstacle to the path there  
     
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

        node = RealSenseCameraNode()
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
