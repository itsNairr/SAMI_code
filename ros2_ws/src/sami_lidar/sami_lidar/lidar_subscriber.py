import rclpy # allows the script to communciate with ROS2
import numpy as np
from rclpy.node import Node
from sensor_msgs.msg import LaserScan #message type that i published by LMS1xx
from rclpy.qos import qos_profile_sensor_data #provides the communication settings 

#an attibute is a variable that belons to an object

class LidarSubscriber(Node):     # use the functionality of node 

    def __init__(self): #anytime you create a clas ie ___= LidarSubsriber(), this section will run
        super().__init__("lidar_subscriber") #create node
        
                                        # message type, topic name, function to run when the data arrives, communication settings 
        self.subscription=self.create_subscription(LaserScan, '/scan', 
                                                    self.scan_callback, qos_profile_sensor_data)
        #call self.scan_callback anytime new data arrives and give it the message 


        #msgs.range - holds the distances (hyp of all the values) (meters)
        #msgs.angle_min - hold the start angles (which is -135 degrees,or  -2.356194496154785 )
        #msgs.agnle_increment - angle between measurents (rad)
        #angle_min is constant that is the starting angle, then we add angle_increment (0.5), 
        #times the measuremnet number away from the minimum
        #example if 0 is the minimu, angle 4 would be 0+4*0.5= 2 degrees  

    #the lidar starts at -135 degrees or -3pi/4 rad

    def scan_callback(self,msg):
        distance = np.array(msg.ranges)
        number_of_measurements_array = np.arange(len(distance))
        angle = msg.angle_min + number_of_measurements_array * msg.angle_increment
        cartesian_coord = np.zeros((len(distance), 2))
        cartesian_coord[:,0]=distance*np.cos(angle) #x
        cartesian_coord[:,1]=distance*np.sin(angle) #y

        count=0
        for i in range(len(distance)):
            if np.deg2rad(-2) < angle[i] < np.deg2rad(2):
                if distance[i]<5:
                    count += 1
                    self.get_logger().info(f'LiDAR Distance:{distance[i]} Angle: {angle[i]}')
                    
        if count > 0:
            self.get_logger().info(f'Do not proceed')
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