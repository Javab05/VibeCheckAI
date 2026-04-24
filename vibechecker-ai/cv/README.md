# Computer Vision / Feature Extraction — Aaron

Responsible for:
- MediaPipe face mesh integration
- Image preprocessing (resize, normalize)
- Landmark extraction pipeline

## Expected Output Format
TBD — Aaron to define what the pipeline returns (landmark array, tensor, etc.)
so Javaya can format it for model input.



### Notes:
* to test upload a `test.jpg` image in the root directory (`vibechecker-ai`)
* run this command in project root to visualize the face mapping:
```bash
* python -c "from cv.processor import show_face_mesh; show_face_mesh('test.jpg')"
```