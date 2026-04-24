import os
import cv2
import numpy as np
from PIL import Image
from typing import Optional, Union
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.vision import drawing_utils
from mediapipe.tasks.python.vision import drawing_styles
import matplotlib.pyplot as plt

def _to_rgb_numpy(image: Union[str, np.ndarray, Image.Image]) -> np.ndarray:
    """
    Normalizes input to a HxWx3 RGB NumPy array.
    """
    if isinstance(image, str):
        if not os.path.exists(image):
            raise FileNotFoundError(f"Image path not found: {image}")
        img = cv2.imread(image)
        if img is None:
            raise FileNotFoundError(f"Could not read image at path: {image}")
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    if isinstance(image, Image.Image):
        return np.array(image.convert("RGB"))

    if isinstance(image, np.ndarray):
        if image.ndim == 2:
            return cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        if image.ndim == 3:
            if image.shape[2] == 4:
                return cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
            if image.shape[2] == 3:
                return image
        raise TypeError(f"Unsupported numpy array shape: {image.shape}")

    raise TypeError(f"Unsupported input type: {type(image)}")


def extract_face(image_input):
    # 1. Convert input to numpy array
    rgb_numpy_array = _to_rgb_numpy(image_input)
    height, width, _ = rgb_numpy_array.shape

    # 2. Setup MediaPipe path and options
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(current_dir, 'face_landmarker.task')

    base_options = python.BaseOptions(model_asset_path=model_path)
    options = vision.FaceLandmarkerOptions(
        base_options=base_options,
        output_face_blendshapes=False,  # We don't need blendshapes if we just want the crop
        output_facial_transformation_matrixes=False,
        num_faces=1
    )

    # 3. Create detector and run
    with vision.FaceLandmarker.create_from_options(options) as landmarker:
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_numpy_array)
        detection_result = landmarker.detect(mp_image)

        # 4. If a face is found, crop and format it
        if len(detection_result.face_landmarks) > 0:
            face_landmarks = detection_result.face_landmarks[0]

            # Find the edges of the face (bounding box)
            x_coords = [landmark.x for landmark in face_landmarks]
            y_coords = [landmark.y for landmark in face_landmarks]

            # Convert normalized coordinates (0.0 - 1.0) to actual pixel values
            x_min, x_max = int(min(x_coords) * width), int(max(x_coords) * width)
            y_min, y_max = int(min(y_coords) * height), int(max(y_coords) * height)

            # Add a 10% margin so we don't cut off the chin/forehead (standard for AI models)
            margin_x = int((x_max - x_min) * 0.1)
            margin_y = int((y_max - y_min) * 0.1)

            x_min = max(0, x_min - margin_x)
            x_max = min(width, x_max + margin_x)
            y_min = max(0, y_min - margin_y)
            y_max = min(height, y_max + margin_y)

            # Crop the numpy array
            face_crop = rgb_numpy_array[y_min:y_max, x_min:x_max]

            # Convert to PIL Image, make Grayscale ('L'), and resize to 48x48
            pil_img = Image.fromarray(face_crop)
            gray_img = pil_img.convert('L')
            final_img = gray_img.resize((48, 48))

            return final_img
        else:
            print("No face detected.")
            return None


def show_face_mesh(image_input):
    """Detects a face and displays the full MediaPipe wireframe mapping on screen."""
    # 1. Convert input
    rgb_numpy_array = _to_rgb_numpy(image_input)

    # 2. Setup model
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(current_dir, 'face_landmarker.task')
    base_options = python.BaseOptions(model_asset_path=model_path)
    options = vision.FaceLandmarkerOptions(base_options=base_options, num_faces=1)

    # 3. Detect
    with vision.FaceLandmarker.create_from_options(options) as landmarker:
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_numpy_array)
        detection_result = landmarker.detect(mp_image)

        # 4. Draw the results
        if len(detection_result.face_landmarks) > 0:
            annotated_image = np.copy(rgb_numpy_array)

            for face_landmarks in detection_result.face_landmarks:
                # Draw the full web (tesselation)
                drawing_utils.draw_landmarks(
                    image=annotated_image,
                    landmark_list=face_landmarks,
                    connections=vision.FaceLandmarksConnections.FACE_LANDMARKS_TESSELATION,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=drawing_styles.get_default_face_mesh_tesselation_style())

                # Draw the prominent outlines (eyes, lips, face shape)
                drawing_utils.draw_landmarks(
                    image=annotated_image,
                    landmark_list=face_landmarks,
                    connections=vision.FaceLandmarksConnections.FACE_LANDMARKS_CONTOURS,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=drawing_styles.get_default_face_mesh_contours_style())

            # 5. Pop open a window to show the image
            plt.figure(figsize=(8, 8))
            plt.imshow(annotated_image)
            plt.axis('off')  # Hide axes
            plt.title("MediaPipe Face Mapping")
            plt.show()
        else:
            print("No face detected to map.")