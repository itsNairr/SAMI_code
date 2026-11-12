import rclpy # allows the script to communciate with ROS2
import numpy as np
from rclpy.node import Node
from sensor_msgs.msg import LaserScan #message type that i published by LMS1xx
from rclpy.qos import qos_profile_sensor_data #provides the communication settings 
from geometry_msgs.msg import Twist
from sensor_msgs.msg import PointCloud2
from std_msgs.msg import Header


#an attibute is a variable that belons to an object

class LidarSubscriber(Node):     # use the functionality of node 

    def __init__(self): #anytime you create a clas ie ___= LidarSubsriber(), this section will run
        super().__init__("lidar_subscriber") #create node
        
                                        # message type, topic name, function to run when the data arrives, communication settings 
        self.subscription=self.create_subscription(LaserScan, '/scan', 
                                                    self.scan_callback, qos_profile_sensor_data)
        self.stop_dist_LiDAR_publisher = self.create_publisher(Twist, 'LiDAR_stop/cmd_vel', 10)
        #self.depth_publisher = self.create_publisher(PointCloud2, 'LiDAR_points', 10)
    
        #call self.scan_callback anytime new data arrives and give it the message 

    def scan_callback(self,msg):
        distance = np.array(msg.ranges)
        number_of_measurements_array = np.arange(len(distance))
        angle = msg.angle_min + number_of_measurements_array * msg.angle_increment
        cartesian_coord = np.zeros((len(distance), 2))
        cartesian_coord[:,0]=distance*np.cos(angle) #x
        cartesian_coord[:,1]=distance*np.sin(angle) #y

        #points_3d = [[x, y, 0.0] for x, y in cartesian_coord]
        #LiDAR_coord=PointCloud2()
        #LiDAR_msg=LiDAR_coord.create_cloud_xyz32(header, points_3d)

        count=0
        for i in range(len(distance)):
            if np.deg2rad(-2) < angle[i] < np.deg2rad(2):
                if distance[i]<1:
                    count += 1
                    #self.get_logger().info(f'LiDAR Distance:{distance[i]} Angle: {np.rad2deg(angle[i])}')
                    
        if count > 0:
            self.get_logger().info(f'Do not proceed')
            #also now need to check if its a person or not
            stop_msg = Twist()
            #stop forward/back motion
            stop_msg.linear.x = 0.0
            #stop rotational motion
            stop_msg.angular.z = 0.0
            self.stop_dist_LiDAR_publisher.publish(stop_msg)
        elif count == 0:
            self.get_logger().info(f'Proceed')
        
        # for i in range(len(distance)):
        #     if np.deg2rad(-2) < angle[i] < np.deg2rad(2):
        #         self.get_logger().info(f'Angle: {np.rad2deg(angle[i]):.2f}°, Distance: {distance[i]:.3f} m')


        # self.get_logger().info(f'Total measurements: {len(distance)}')
        # self.get_logger().info(f'Range min: {msg.range_min}')
        # self.get_logger().info(f'Range max: {msg.range_max}')

        # negative = distance[angle < 0]
        # positive = distance[angle > 0]

        # self.get_logger().info(
        #     f'Negative valid: {np.sum(negative > 0)}/{len(negative)}, '
        #     f'Positive valid: {np.sum(positive > 0)}/{len(positive)}')
        # self.get_logger().info(f'Number of data points: {len(distance)})')

def main(args=None):
    rclpy.init(args=args) #initializes ROS 2 

    node = LidarSubscriber() #create object for node

    rclpy.spin(node) #keeps the node running and available when running

    node.destroy_node() #when the node stops shutdown properly 
    rclpy.shutdown()


if __name__ == '__main__':
    main()