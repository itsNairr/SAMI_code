#Gemini was used to develop the script 
import cv2
import os
import random
import shutil
import numpy as np

# ================= CONFIGURATION =================
SRC_IMAGES_DIR = "path/to/concrete3k/images/"   # Raw source images
SRC_MASKS_DIR = "path/to/concrete3k/masks/"     # Raw source pixel masks
OUTPUT_DATASET_DIR = "./yolo_dataset/"          # Where to save the output dataset
TRAIN_SPLIT = 0.8                               # 80% train, 20% validation
CLASS_ID = 0                                    # Class 0 for 'crack'
# =================================================

# Setup the YOLO directory structure
subdirs = [
    "images/train", "images/val",
    "labels/train", "labels/val"
]
for subdir in subdirs:
    os.makedirs(os.path.join(OUTPUT_DATASET_DIR, subdir), exist_ok=True)

# Find all matching files
image_extensions = ('.png', '.jpg', '.jpeg', '.bmp')
image_files = [f for f in os.listdir(SRC_IMAGES_DIR) if f.lower().endswith(image_extensions)]

# Shuffle for random train/val allocation
random.seed(42)
random.shuffle(image_files)

split_idx = int(len(image_files) * TRAIN_SPLIT)
train_files = image_files[:split_idx]
val_files = image_files[split_idx:]

def process_file_set(files, split_type):
    for filename in files:
        base_name = os.path.splitext(filename)[0]

        # Paths
        img_src_path = os.path.join(SRC_IMAGES_DIR, filename)
        # Assuming mask shares the same base name, adjust extension if masks are specifically .png/.bmp
        mask_src_path = os.path.join(SRC_MASKS_DIR, f"{base_name}.png") 
        if not os.path.exists(mask_src_path):
            mask_src_path = os.path.join(SRC_MASKS_DIR, f"{base_name}.bmp")
            if not os.path.exists(mask_src_path):
                continue # Skip if mask is missing

        # Read the mask in grayscale
        mask = cv2.imread(mask_src_path, cv2.IMREAD_GRAYSCALE)
        if mask is None:
            continue

        h, w = mask.shape

        # Find external contours of the cracks
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Prepare label output line entries
        polygon_lines = []
        for contour in contours:
            # Filter out tiny noise contours (less than 5 pixels area)
            if cv2.contourArea(contour) < 5:
                continue

            # Flatten contour array to a 2D shape: [[x1, y1], [x2, y2], ...]
            polygon = contour.reshape(-1, 2)

            # Normalize coordinates relative to image width and height
            normalized_poly = polygon / [w, h]

            # Format as: x1 y1 x2 y2 x3 y3...
            poly_string = " ".join([f"{coord[0]:.6f} {coord[1]:.6f}" for coord in normalized_poly])
            polygon_lines.append(f"{CLASS_ID} {poly_string}\n")

        # Only copy image and save label if polygons were successfully extracted
        if polygon_lines:
            # Copy Image
            img_dest_path = os.path.join(OUTPUT_DATASET_DIR, "images", split_type, filename)
            shutil.copy(img_src_path, img_dest_path)

            # Save YOLO Text Label
            label_dest_path = os.path.join(OUTPUT_DATASET_DIR, "labels", split_type, f"{base_name}.txt")
            with open(label_dest_path, "w") as f:
                f.writelines(polygon_lines)

print("Processing training split...")
process_file_set(train_files, "train")

print("Processing validation split...")
process_file_set(val_files, "val")

print(f"Dataset successfully created at: {os.path.abspath(OUTPUT_DATASET_DIR)}")