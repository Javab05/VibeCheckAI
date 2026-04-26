# Computer Vision / Feature Extraction — Aaron

Responsible for:
- MediaPipe face mesh integration
- Image preprocessing (resize, normalize)
- Landmark extraction pipeline

## Expected Output Format
Example outcome of real image:
```json
{'emotion': 'neutral', 'confidence': 0.7179, 'scores': {'angry': 0.0861, 'disgust': 0.0032, 'fear': 0.0498, 'happy': 0.0155, 'neutral': 0.7179, 'sad': 0.12, 'surprise': 0.0075}, 'model_version': 'v1.0'}
```



### Notes:
* to test upload a `test.jpg` image in the root directory (`vibechecker-ai`)
* run this command in project root to visualize the face mapping:
```bash
* python -c "from cv.processor import show_face_mesh; show_face_mesh('test.jpg')"
```
* to check for confidence rating testing on an image execute the follow command in root with `test.jpg`
```bash
python -c "
from ml.inference import EmotionPredictor

predictor = EmotionPredictor()
result = predictor.predict('test.jpg')
print('Real prediction:', result)
"
```