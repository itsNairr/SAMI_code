
from inference import get_model
import supervision as sv
import numpy as np
import cv2
class PersonIdentify:
    def __init__(self):
        # Load model ONCE
        self.model = get_model(
            model_id="rfdetr-seg-nano"
        )

        # Find person class ID
        names = self.model.class_names
        self.person_ids = [
            i for i, name in enumerate(names)
            if name == "person"
        ]
        self.mask_annotator = sv.MaskAnnotator()
        self.label_annotator = sv.LabelAnnotator()
    def identify(self, depth_img, colour_img):
        print("hi")
        #pre process mask anyhting further than 0.5m away
        depth_mask = (depth_img >0) & (depth_img <= 1000)#to set mask distance
        filtered_img = colour_img.copy()
        filtered_img[~depth_mask] = 0 #sets all pixels farther than 0.5m to black

        # Run model on supplied camera image
        prediction = self.model.infer(
            filtered_img,
            confidence=0.4
        )[0]
        detections = sv.Detections.from_inference(prediction)
        print("Total detections:", len(detections))
        print("Masks available:", detections.mask is not None)
        # Create labels
        labels = []
        for i in range(len(detections)):
            class_id = detections.class_id[i]
            class_name = self.model.class_names[class_id]
            confidence = detections.confidence[i]
            if class_name == "person":
                category = "PERSON"
            else:
                category = "OBJECT"
            label = f"{category}: {class_name} ({confidence:.2f})"
            labels.append(label)
    #show the image with segments
        annotated_image = self.mask_annotator.annotate(
            scene=filtered_img.copy(),
            detections=detections
        )
        # Draw labels over masks
        annotated_image = self.label_annotator.annotate(
            scene=annotated_image,
            detections=detections,
            labels=labels
        )
        cv2.imshow("Filtered Segmentation", annotated_image)
        cv2.waitKey(1)
        
    # Identify person class IDs
        # names = self.model.class_names
        # person_ids = [
        #     i for i, name in enumerate(names)
        #     if name == "person"
        # ]
        # # Filter detections to only people
        # people = detections[
        #     np.isin(detections.class_id, person_ids)
        # ]
        # # Process segmentation masks
        # if people.mask is not None:
        #     for person_index, mask in enumerate(people.mask):
        #         ys, xs = np.where(mask)
        #         if len(xs) == 0:
        #             continue
        #         print(
        #             f"Person {person_index}: "
        #             f"{len(xs)} pixels"
        #         )
        #         return True
        # else:
        #     return False
        people = detections[
            np.isin(detections.class_id, self.person_ids)
        ]
        if len(people) > 0:
            return True
        return False
