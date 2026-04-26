import os
import sys
import numpy as np
from PIL import Image

# Add current dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from ml.inference import get_predictor

def test_inference_pipeline():
    predictor = get_predictor()
    
    # Test 1: Real image (if test.jpg exists)
    test_path = "test.jpg"
    if os.path.exists(test_path):
        print(f"Testing full pipeline with {test_path}...")
        try:
            result = predictor.predict_from_path(test_path)
            print(f"Result: {result}")
        except Exception as e:
            print(f"Error during {test_path} prediction: {e}")
    else:
        print(f"File not found: {test_path}. Skipping real image test.")

    # Test 2: No face detected (Black image)
    print("\nTesting 'no_face_detected' error format...")
    try:
        black_array = np.zeros((480, 640, 3), dtype=np.uint8)
        result = predictor.predict_from_array(black_array)
        print(f"Result: {result}")
        
        # Validate error schema matches requirement
        expected_keys = {"error", "label", "confidence"}
        if all(k in result for k in expected_keys):
            print("Confirmed: Error response matches schema.")
        else:
            missing = expected_keys - set(result.keys())
            print(f"Warning: Missing keys in error response: {missing}")
    except Exception as e:
        print(f"Error during black image prediction: {e}")

if __name__ == "__main__":
    test_inference_pipeline()
