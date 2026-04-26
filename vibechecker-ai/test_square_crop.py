
import os
import sys
import numpy as np
from PIL import Image

# 1. Setup paths so we can import from the local cv module
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from cv.processor import extract_face
    print("Successfully imported extract_face from cv.processor")
except ImportError as e:
    print(f"Import Error: {e}")
    print("Ensure you are running this script from the 'vibechecker-ai' directory.")
    sys.exit(1)

def run_test():
    # 2. Locate a test image
    test_image_path = os.path.join(current_dir, "test.jpg")
    
    if os.path.exists(test_image_path):
        print(f"Using existing test image: {test_image_path}")
        img_input = test_image_path
    else:
        print("test.jpg not found, creating a 640x480 landscape dummy image...")
        # Create a dummy image with a white area
        dummy_data = np.zeros((480, 640, 3), dtype=np.uint8)
        dummy_data[100:300, 200:400] = [255, 255, 255] 
        img_input = dummy_data

    # 3. Execute the extraction
    print("Running face extraction (initializing MediaPipe)...")
    try:
        result = extract_face(img_input)
        
        if result:
            print("SUCCESS")
            print(f"Output Dimensions: {result.size[0]}x{result.size[1]}")
            
            # Save the result so you can inspect it
            output_path = os.path.join(current_dir, "crop_result.png")
            result.save(output_path)
            print(f"Result saved to: {output_path}")
            
            if result.size == (48, 48):
                print("Confirmed: Correct aspect ratio and resolution.")
            else:
                print(f"Warning: Unexpected size: {result.size}")
        else:
            print("No face detected. Try using a real photo of a face named 'test.jpg'.")
            
    except Exception as e:
        print(f"An error occurred during execution: {e}")
        print("Note: There may be an issue with the local MediaPipe installation or environment.")

if __name__ == "__main__":
    run_test()
