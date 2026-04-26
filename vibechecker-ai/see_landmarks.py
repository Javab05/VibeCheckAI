import os
import sys
import numpy as np
from PIL import Image

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from cv.processor import extract_face, FaceData
    print("Successfully imported CV modules")
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def inspect_landmarks():
    test_path = os.path.join(current_dir, "test.jpg")
    
    if not os.path.exists(test_path):
        print(f"File not found: {test_path}")
        print("Please place a real face image named 'test.jpg' in the directory.")
        return

    print(f"Processing {test_path}...")
    result = extract_face(test_path)

    if result and isinstance(result, FaceData):
        print("\nFaceData object received successfully")
        print(f"Landmarks shape: {result.landmarks.shape}")
        
        # Display statistical summary of the landmarks
        lms = result.landmarks
        print("\nLandmark Coordinate Ranges:")
        print(f"  X: {lms[:, 0].min():.4f} to {lms[:, 0].max():.4f} (normalized)")
        print(f"  Y: {lms[:, 1].min():.4f} to {lms[:, 1].max():.4f} (normalized)")
        print(f"  Z: {lms[:, 2].min():.4f} to {lms[:, 2].max():.4f} (depth)")

        print("\nSample Data (First 5 Landmarks [X, Y, Z]):")
        for i in range(5):
            print(f"  {i}: {lms[i]}")
            
        print(f"\nTotal landmark count: {len(lms)}")
        print("Confirmed: Landmarks are stored as a (N, 3) NumPy array.")
    else:
        print("No face detected or wrong return type. Ensure 'test.jpg' contains a clear face.")

if __name__ == "__main__":
    inspect_landmarks()
