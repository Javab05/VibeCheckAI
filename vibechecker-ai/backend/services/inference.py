import sys
import os

# Add the project root to sys.path so we can use absolute imports for ml and database
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ml.inference import EmotionPredictor

# Instantiate the predictor once at the module level to load the model on import
predictor = EmotionPredictor()

def run_inference(image) -> dict:
    """
    Run emotion prediction on an image (path, array, or PIL Image).
    Returns the prediction result dict as-is from the EmotionPredictor.
    """
    return predictor.predict(image)
