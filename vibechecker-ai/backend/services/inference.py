import sys
import os
from werkzeug.exceptions import BadRequest

# Add the project root to sys.path so we can use absolute imports for ml and database
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ml.inference_multimodal import MultiModalPredictor

# Instantiate the predictor once at the module level to load the model on import
predictor = MultiModalPredictor()

def run_inference(image) -> dict:
    """
    Run multimodal emotion prediction on an image.
    The function accepts a PIL image (or path/numpy array) and returns 
    the dict from predict() directly.
    
    Raises:
        BadRequest: 400 error if no face is detected.
    """
    result = predictor.predict(image)
    if result is None:
        raise BadRequest("No face detected in image.")
    return result
