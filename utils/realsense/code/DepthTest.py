import pyrealsense2 as rs
import numpy as np
import cv2

#object that manages the flow of data from the camera
pipe = rs.pipeline()
#Create a config object, which is used to configure the camera for streaming
config = rs.config()

#Stream --> continous flow of data coming from the camera
#Image resolution 640 x 480, 8 bits per channel, and 30 FPS
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
#Depth is 16 bits per pixel, 30 FPS
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

#Create alignment object (is used later to align depth frames to color frames)
align = rs.align(rs.stream.color)

# Start streaming
pipe.start(config)

# Start measurement at centre of image, if mouse is not moved yet (we could pick any pos)
#x=640/2=320
mouse_x = 320
#y=480/2=240
mouse_y = 240

# Function that updates x and y when mouse moves
def mouse_position(event, x, y, flags, param):
    global mouse_x, mouse_y
#if the last event called was a mouse move event, update the mouse position
    if event == cv2.EVENT_MOUSEMOVE:
        mouse_x = x
        mouse_y = y


# Create window
cv2.namedWindow("RealSense Camera")

#Automatically when the mouse moves over the "RealSense Camera", OpenCV will call the mouse_position() function 
cv2.setMouseCallback("RealSense Camera", mouse_position)

try:
    while True:

        # Get a new set of frames from the camera
        frames = pipe.wait_for_frames()

        #Align the depth frame to color frame
        aligned_frame = align.process(frames)

        #Get the depth frame that is aligned to color frame
        depth_frame = aligned_frame.get_depth_frame()

        # Get the RGB/color frame that is aligned
        # Could also do color_frame = frames.get_color_frame()
        color_frame = aligned_frame.get_color_frame()

        # Make sure we actually received a frame, if we do not get them go back to the top of the loop
        if not color_frame or not depth_frame:
            continue

        # Convert RealSense frame into a NumPy array
        image = np.asanyarray(color_frame.get_data())

        #Grabs the depth value at the mouse position, and converts it to millimeters
        distance = depth_frame.get_distance(mouse_x, mouse_y)
        distance = distance * 1000  
        print("x:", mouse_x,
              "y:", mouse_y,
              "Depth:", distance, "mm")

        # Display it
        cv2.imshow("RealSense Camera", image)
        
        # Press space to close
        if cv2.waitKey(1) == ord(" "):
            break

finally:
    pipe.stop()
    cv2.destroyAllWindows()