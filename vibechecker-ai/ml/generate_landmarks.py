import os
import sys
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from PIL import Image

def main():
    # Paths relative to this script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    no_face_log = os.path.join(base_dir, "no_face.txt")
    
    # Check for train directory
    train_dir = os.path.join(data_dir, "train")
    if not os.path.exists(train_dir):
        print(f"Error: Training directory not found at {train_dir}")
        sys.exit(1)

    # Check for model file in multiple locations
    model_path_ml = os.path.join(base_dir, "face_landmarker.task")
    model_path_cv = os.path.join(os.path.dirname(base_dir), "cv", "face_landmarker.task")
    
    if os.path.exists(model_path_ml):
        model_path = model_path_ml
    elif os.path.exists(model_path_cv):
        model_path = model_path_cv
        print(f"Using model found at {model_path}")
    else:
        print(f"Error: MediaPipe model file not found at {model_path_ml} or {model_path_cv}")
        sys.exit(1)

    # Initialize FaceLandmarker
    base_options = python.BaseOptions(model_asset_path=model_path)
    options = vision.FaceLandmarkerOptions(
        base_options=base_options,
        output_face_blendshapes=False,
        output_facial_transformation_matrixes=False,
        num_faces=1
    )

    target_dirs = ["train", "test", "val"]
    
    total_processed = 0
    total_no_face = 0
    
    with vision.FaceLandmarker.create_from_options(options) as detector:
        with open(no_face_log, "a") as log_file:
            for sub_dir in target_dirs:
                current_path = os.path.join(data_dir, sub_dir)
                if not os.path.exists(current_path):
                    print(f"Skipping {sub_dir} as it does not exist.")
                    continue

                print(f"Processing directory: {current_path}")
                
                for root, _, files in os.walk(current_path):
                    for file in files:
                        if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                            img_path = os.path.join(root, file)
                            npy_path = os.path.splitext(img_path)[0] + ".npy"

                            # Skip if .npy already exists
                            if os.path.exists(npy_path):
                                continue

                            try:
                                # Load image and ensure RGB (MediaPipe requirement)
                                pil_img = Image.open(img_path).convert("RGB")
                                numpy_img = np.array(pil_img)
                                image = mp.Image(image_format=mp.ImageFormat.SRGB, data=numpy_img)
                                
                                # Detect landmarks
                                detection_result = detector.detect(image)
                                
                                if detection_result.face_landmarks:
                                    # Extract landmarks (478, 3)
                                    landmarks = detection_result.face_landmarks[0]
                                    coords = np.array([[lm.x, lm.y, lm.z] for lm in landmarks], dtype=np.float32)
                                    np.save(npy_path, coords)
                                else:
                                    # No face detected
                                    np.save(npy_path, np.array([]))
                                    log_file.write(f"{img_path}\n")
                                    log_file.flush()
                                    total_no_face += 1
                                    
                                total_processed += 1
                                
                                if total_processed % 500 == 0:
                                    print(f"Progress: {total_processed} images processed, {total_no_face} no-face detected.")
                                    
                            except Exception as e:
                                print(f"Error processing {img_path}: {e}")

    print(f"Finished! Total processed: {total_processed}, Total no-face: {total_no_face}")
    print(f"No-face paths logged to {no_face_log}")

if __name__ == "__main__":
    main()
