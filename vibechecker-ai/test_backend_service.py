import os
import sys
import numpy as np

# Add the project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.services.inference import run_inference

def test_backend_integration():
    print("Testing backend service integration...")
    
    # Test 1: Real image
    test_path = "test.jpg"
    if os.path.exists(test_path):
        print(f"Processing {test_path}...")
        try:
            result = run_inference(test_path)
            print(f"Success Result: {result}")
        except Exception as e:
            print(f"Error during {test_path} processing: {e}")
    else:
        print(f"File not found: {test_path}. Skipping real image test.")
    
    # Test 2: No face detected
    print("\nTesting no-face detection...")
    try:
        black_array = np.zeros((480, 640, 3), dtype=np.uint8)
        result = run_inference(black_array)
        print(f"Error Result: {result}")
        
        # Validate schema
        expected_keys = {"error", "label", "confidence"}
        if all(k in result for k in expected_keys):
            print("Confirmed: Error response matches required schema.")
    except Exception as e:
        print(f"Error during black image processing: {e}")

if __name__ == "__main__":
    test_backend_integration()
