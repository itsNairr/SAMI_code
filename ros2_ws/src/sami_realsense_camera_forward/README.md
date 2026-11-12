# Setup:
## This node uses 3 files:
realsense_camera_node.py
person_identify.py
twist_mux.yaml
## One time installs:
Pip install inference
Pip install pyrealsense2
## Do every time:
Source Ros2 in the SAMI directory
source /opt/ros/humble/setup.bash
Open terminal in the SAMI/ros2_ws directory run 
colcon build --packages-select sami_realsense_camera_forward
source install/setup.bash
## To run the program:
ros2 run sami_realsense_camera_forward camera

# Background information:
The Clearpath A200 husky has a .yaml file called twist_mux located in husky control config folder path which chooses what speed command will be sent to the robot. 

This is necessary as there are many components which can send different speeds/angles but one must be chosen to be sent to the motors

Speed is controlled through the cmd_vel command (naming convention is to add /cmd_vel for additional topics). Cmd_vel has a velocities for x,y,z and anuglar.

The mux is set up so that each different cmd_vel topic coming has a set priority which allows it to override other ones. For example, if you wanted to control your robot with the joystick but have the keyboard able to override it in emergencies you would give the keyboard cmd_vel topic a higher priority.

In addition there is a section called locks, this shuts down any movement of the Huskey, through a Boolean command of True and the huskey cannot move unless a False is sent to it to unlock it. For example, an Estop will lock all movement until it is reset. 

We will be adding /cmd_vel topics to both of the sections.
  
# realsense_camera_node.py

The realsense camera node has 2 publishers

stop_dist_publisher is a twist topic and publishes a 0 velocity and 0 angle command (stop) if any pixel in the depth camera is closer than 0.5 m. This has a priority of 20 which is higher than the keyboard or joystick commands so it will override them.

stop_person_publisher is a Boolean message and publishes a True command which locks/stops the robot from moving if the model identifies the object in front of it as a person.

Currently the program also locks the robot if the model identifies it as something other than a person, such as a garbage can. This will be modified in the future so that the robot can maneuver around an object if identified as such.

The publishers, camera, and Roboflow model are set up in the __init__ function.

The program uses the realsense pipeline to bring in images and enable it to receive data.
                                                 
# person_identify.py
The model uses roboflows generic model. This model identifies many common objects, importantly for this project it can accurately identify people when shown only their legs. This allows the camera to be mounted at a lower level without having full view of closer people.

https://docs.roboflow.com/models/supported-models/rf-detr 

A nano model was chosen as it allows for fast training and the lowest amount of computational power. SAMI’s applications currently require multiple models to be run at once, since the current computer only has 8 RAM lower computational power is an important consideration. In addition, since the robot is moving closer to a potential object as the previous image is processed it is important to have fast processing speed to reduce latency.

In the future, we may investigate a different model which only tracks people so that there is less data and computational powers required.

Confidence is set to 0.7 which was chosen to minimise false positives and produced correct responses. Increasing the confidence further may result in misidentify a person as an object which could create safety hazards. 

