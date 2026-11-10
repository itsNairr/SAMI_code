from inference import get_model
from PIL import Image
import supervision as sv
import rclpy
from rclpy.node import Node
import pyrealsense2 as rs
import numpy as np
import cv2
 # Load once, then reuse for each camera frame.
model = get_model(model_id="rfdetr-seg-nano")
while(True):
    get_logger().info('Initializing RealSense camera...')
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
    frames = self.pipe.wait_for_frames()
    aligned_frames = self.align.process(frames)
    depth_frame = aligned_frames.get_depth_frame()
    color_frame = aligned_frames.get_color_frame()
    if not depth_frame or not color_frame:
        print("nothing")
    image = np.asanyarray(color_frame.get_data())
    # # get_distance returns metres; convert to millimetres
    # distance_mm = depth_frame.get_distance(
    #     self.mouse_x, self.mouse_y
    # ) * 1000.0
    cv2.imshow('RealSense Camera', image)
    cv2.waitKey(1)
    #image = Image.open("person.jpg").convert("RGB")
    prediction = model.infer(image, confidence=0.5)[0]
    detections = sv.Detections.from_inference(prediction)
    # Keep only people.
    names = model.class_names
    person_ids = [
        i for i, name in enumerate(names)
        if name == "person"
    ]
    people = detections[
        __import__("numpy").isin(detections.class_id, person_ids)
    ]
    # Each mask selects the pixels belonging to one person.
    if people.mask is not None:
        for person_index, mask in enumerate(people.mask):
            print(person_index, mask.shape, mask.sum())
            ys, xs = np.where(mask)
            print("X coordinates:", xs)
            print("Y coordinates:", ys)