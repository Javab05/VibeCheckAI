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
        print(f"FAILED: Expected BadRequest exception but got result: {result}")
    except Exception as e:
        print(f"Caught expected error: {e}")
        if "No face detected" in str(e):
            print("Confirmed: Exception message is correct.")

    # Test 3: Validate Multimodal Schema
    if os.path.exists(test_path):
        print("\nValidating result schema...")
        result = run_inference(test_path)
        required_keys = {"dominant_emotion", "confidence", "vibe_score", "scores", "model_version"}
        missing = required_keys - set(result.keys())
        if not missing:
            print("Success: All required multimodal keys present.")
        else:
            print(f"FAILED: Missing keys: {missing}")

if __name__ == "__main__":
    test_backend_integration()
