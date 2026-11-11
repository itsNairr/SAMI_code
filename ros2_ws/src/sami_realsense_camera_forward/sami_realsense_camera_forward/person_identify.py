
from inference import get_model
import supervision as sv
import numpy as np


class PersonIdentify:

    def __init__(self):

        # Load model ONCE
        #print("Loading person detection model...")

        self.model = get_model(
            model_id="rfdetr-seg-nano"
        )

        #print("Person detection model loaded!")

        # Find person class ID
        names = self.model.class_names

        self.person_ids = [
            i for i, name in enumerate(names)
            if name == "person"
        ]


    def identify(self, image):
        # # Run model on supplied camera image
        # prediction = self.model.infer(
        #     image,
        #     confidence=0.1  # Temporarily lower for debugging
        # )[0]

        # detections = sv.Detections.from_inference(prediction)

        # # Check whether anything was detected
        # if detections.class_id is None:
        #     print("No detections found", flush=True)
        #     return False

        # # Print all detected objects and their confidence
        # for i in range(len(detections)):

        #     class_id = int(detections.class_id[i])
        #     confidence = float(detections.confidence[i])

        #     class_name = self.model.class_names[class_id]

        #     print(
        #         f"Object: {class_name}, "
        #         f"Confidence: {confidence:.3f}",
        #         flush=True
        #     )

        # # Filter detections to people
        # people = np.isin(
        #     detections.class_id,
        #     self.person_ids
        # )

        # person_present = np.any(people)

        # print(f"Person present: {person_present}", flush=True)

        # return bool(person_present)

        print("new")

        # Run model on supplied camera image
        prediction = self.model.infer(
            image,
            confidence=0.7
        )[0]

        detections = sv.Detections.from_inference(prediction)

        #old stuff
        
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
                return True
        else:
            return False

                # # Find center pixel of the person
                # center_x = int(np.mean(xs))
                # center_y = int(np.mean(ys))

                # # Get depth at center pixel (metres)
                # distance = depth_frame.get_distance(
                #     center_x, center_y
                # )

                # print(
                #     f"Person {person_index} distance: "
                #     f"{distance:.2f} m"
                # )

    #     # # Check whether any detected class is a person
    #     # if detections.class_id is None:
    #     #     return False

    #     # people = np.isin(
    #     #     detections.class_id,
    #     #     self.person_ids
    #     # )

    #     person_present = np.any(people)

    #     return bool(person_present)
