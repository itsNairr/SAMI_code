
from inference import get_model
from PIL import Image
import supervision as sv
import rclpy
from rclpy.node import Node
import pyrealsense2 as rs
import numpy as np
import cv2


class PersonIdentifyNode(Node):

    def __init__(self):
        super().__init__('person_avoid')

        # Initialize model once
        self.get_logger().info('Loading segmentation model...')
        self.model = get_model(model_id="rfdetr-seg-nano")

        # Initialize RealSense camera
        self.get_logger().info('Initializing RealSense camera...')

        self.pipe = rs.pipeline()
        config = rs.config()

        config.enable_stream(
            rs.stream.color, 640, 480, rs.format.bgr8, 30
        )

        config.enable_stream(
            rs.stream.depth, 640, 480, rs.format.z16, 30
        )

        self.pipe.start(config)

        # Align depth to color
        self.align = rs.align(rs.stream.color)

        # Run identify() every 0.1 seconds
        self.timer = self.create_timer(0.1, self.identify)


    def identify(self):

        try:
            # Retrieve camera frames
            frames = self.pipe.wait_for_frames()
            aligned_frames = self.align.process(frames)

            depth_frame = aligned_frames.get_depth_frame()
            color_frame = aligned_frames.get_color_frame()

            if not depth_frame or not color_frame:
                return

            # Convert color frame to numpy array
            image = np.asanyarray(color_frame.get_data())

            # Run segmentation model
            prediction = self.model.infer(
                image, confidence=0.5
            )[0]

            detections = sv.Detections.from_inference(prediction)

            # Identify person class IDs
            names = self.model.class_names

            person_ids = [
                i for i, name in enumerate(names)
                if name == "person"
            ]

            # Filter detections to only people
            people = detections[
                np.isin(detections.class_id, person_ids)
            ]

            # Process segmentation masks
            if people.mask is not None:

                for person_index, mask in enumerate(people.mask):

                    ys, xs = np.where(mask)

                    if len(xs) == 0:
                        continue

                    print(
                        f"Person {person_index}: "
                        f"{len(xs)} pixels"
                    )

                    # Find center pixel of the person
                    center_x = int(np.mean(xs))
                    center_y = int(np.mean(ys))

                    # Get depth at center pixel (metres)
                    distance = depth_frame.get_distance(
                        center_x, center_y
                    )

                    print(
                        f"Person {person_index} distance: "
                        f"{distance:.2f} m"
                    )
     
            # Display camera image
            cv2.imshow('RealSense Camera', image)
            cv2.waitKey(1)

        except RuntimeError as e:
            self.get_logger().error(
                f'RealSense frame error: {e}'
            )


    def destroy_node(self):

        # Stop camera before shutting down
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
        node = PersonIdentifyNode()
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
