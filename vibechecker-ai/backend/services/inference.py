import sys
import os

# Add ml folder to path so we can import from it
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'ml'))

from inference import get_predictor

def run_inference(image_path: str) -> dict:
    """
    Run emotion prediction on an image file.
    Returns a dict with emotion, confidence, scores, model_version.
    """
    predictor = get_predictor()
    result = predictor.predict_from_path(image_path)
    return result