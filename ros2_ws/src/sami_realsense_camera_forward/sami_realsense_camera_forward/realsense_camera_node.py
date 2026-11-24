
import rclpy
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.signals import SignalHandlerOptions
import pyrealsense2 as rs
import numpy as np
import cv2
from std_msgs.msg import Float32
from std_msgs.msg import Bool
from geometry_msgs.msg import Twist
from . import person_identify
class RealSenseCameraNode(Node):
    def __init__(self):
        super().__init__('realsense_camera')
        self.depth_publisher = self.create_publisher(Float32, 'dist_away', 10)
        self.stop_dist_publisher = self.create_publisher(Twist, 'too_close_stop/cmd_vel', 10)
        self.stop_person_publisher = self.create_publisher(Bool, 'person_stop/cmd_vel', 10)
        
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
        # Align depth frames to the colour frame
        self.align = rs.align(rs.stream.color)
        # Update at approximately 30 FPS
        self.timer = self.create_timer(0.033, self.getDepth)
        self.get_logger().info('RealSense camera started successfully.')
    def getDepth(self):
        try:
            frames = self.pipe.wait_for_frames()
            aligned_frames = self.align.process(frames)
            depth_frame = aligned_frames.get_depth_frame()
            colour_frame = aligned_frames.get_color_frame()
            if not depth_frame or not colour_frame:
                return
            colour_img = np.asanyarray(colour_frame.get_data())
            depth_img = np.asanyarray(depth_frame.get_data())
            # cv2.imshow('RealSense Camera', image)
            # cv2.waitKey(1)
            #check if there is a pixel which is greater than 0 and less than 500
            has_close_object = np.any((depth_img > 0) & (depth_img < 1000))
            if has_close_object:
                #also now need to check if its a person or not
                stop_p_msg = Bool()
                #stop forward/back motion
                stop_p_msg.data = True
                self.stop_person_publisher.publish(stop_p_msg)
                print("too close")
    
                person_present = self.person_detector.identify(depth_img, colour_img)
                if person_present:
                    print("Stay stop its a person")
                else:
                    #trigger other code go around code
                    #publish go to other program
                    #for now we are just going to reverse a bit untill good
                    stop_p_msg = Bool()
                    #move backwards
                    stop_p_msg.data = False
                    self.stop_person_publisher.publish(stop_p_msg)
                    print("reverse away from object")
                    stop_msg = Twist()
                    #stop forward/back motion
                    stop_msg.linear.x = -0.3
                    #stop rotational motion
                    stop_msg.angular.z = 0.0
                    self.stop_dist_publisher.publish(stop_msg)
                    print("done reversing")

                    #so if it's a person stop  if not reverse untill it is farter than 0.5 then execute the move around part or add obstacle to the path there  
            else:
                #if person has moved now unlock 
                stop_p_msg = Bool()
                #move backwards
                stop_p_msg.data = False
                self.stop_person_publisher.publish(stop_p_msg)
                
        except RuntimeError as e:
            self.get_logger().error(f'RealSense frame error: {e}')
    def destroy_node(self):
        self.timer.cancel()
        try:
            if rclpy.ok():
                # Release the lock while ROS communications are still available.
                self.stop_person_publisher.publish(Bool(data=False))
                # Wait for delivery acknowledgment before destroying the publisher.
                if not self.stop_person_publisher.wait_for_all_acked(Duration(seconds=1.0)):
                    self.get_logger().warning('Timed out waiting for unlock acknowledgment')
        finally:
            if hasattr(self, 'pipe'):
                try:
                    self.pipe.stop()
                except RuntimeError:
                    pass
            cv2.destroyAllWindows()
            super().destroy_node()

def main(args=None):
    # Let Python handle Ctrl+C so the unlock is sent before ROS shuts down.
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)
    node = None
    try:
        node = RealSenseCameraNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except RuntimeError as e:
        print(f'Camera initialization/runtime error: {e}')
    finally:
        try:
            if node is not None:
                node.destroy_node()
        finally:
            if rclpy.ok():
                rclpy.shutdown()

if __name__ == '__main__':
    main()
