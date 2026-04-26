import os
import sys
import numpy as np
from PIL import Image

# Add current dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from ml.inference_multimodal import MultiModalPredictor

def test_multimodal_inference():
    # Path to the new multimodal checkpoint
    checkpoint = "ml/models/multimodal_v1.0.pt"
    
    # Initialize predictor
    print(f"Initializing MultiModalPredictor with {checkpoint}...")
    try:
        predictor = MultiModalPredictor(checkpoint_path=checkpoint)
    except Exception as e:
        print(f"Failed to initialize predictor: {e}")
        return

    # Test 1: Real image (if test.jpg exists)
    test_path = "test.jpg"
    if os.path.exists(test_path):
        print(f"\nTesting multimodal pipeline with {test_path}...")
        try:
            img = Image.open(test_path)
            result = predictor.predict(img)
            if result:
                print(f"Prediction Result:")
                print(f"  Dominant Emotion: {result['dominant_emotion']}")
                print(f"  Confidence:       {result['confidence']:.4f}")
                print(f"  Vibe Score:       {result['vibe_score']:.2f}/100")
            else:
                print("No face detected in test image.")
        except Exception as e:
            print(f"Error during {test_path} prediction: {e}")
    else:
        print(f"\nFile not found: {test_path}. Skipping real image test.")

    # Test 2: No face detected (Black image)
    print("\nTesting 'no face' detection...")
    try:
        black_img = Image.fromarray(np.zeros((480, 640, 3), dtype=np.uint8))
        result = predictor.predict(black_img)
        if result is None:
            print("Confirmed: Predictor correctly returned None for black image.")
        else:
            print(f"Warning: Predictor returned a result for black image: {result}")
    except Exception as e:
        print(f"Error during black image prediction: {e}")

if __name__ == "__main__":
    test_multimodal_inference()
