import torch
import torch.nn.functional as F
import numpy as np
from PIL import Image
from pathlib import Path
import os
import sys

# Import components
from ml.model_multimodal import MultiModalEmotionCNN, LANDMARK_FEATURE_SIZE
from cv.processor import extract_face, FaceData

# Flag: cv/processor.py's extract_face returns a FaceData object (with .face_image and .landmarks) 
# instead of a raw tuple (cropped_pil, landmarks). Implementation below handles the dataclass.

class MultiModalPredictor:
    def __init__(self, checkpoint_path="vibechecker-ai/ml/models/best_multimodal.pt"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.classes = ["angry", "disgust", "fear", "happy", "neutral", "sad", "surprise"]
        
        # Vibe score weights matching the class order above
        # happy=100, surprise=70, neutral=50, fear=30, sad=20, angry=10, disgust=5
        self.vibe_weights = torch.tensor([10, 5, 30, 100, 50, 20, 70], dtype=torch.float32).to(self.device)
        
        # Initialize model
        self.model = MultiModalEmotionCNN(num_classes=7, landmark_feature_size=LANDMARK_FEATURE_SIZE).to(self.device)
        
        # Load checkpoint
        if os.path.exists(checkpoint_path):
            checkpoint = torch.load(checkpoint_path, map_location=self.device)
            if 'model_state' in checkpoint:
                self.model.load_state_dict(checkpoint['model_state'])
            else:
                self.model.load_state_dict(checkpoint)
        else:
            print(f"Warning: Checkpoint not found at {checkpoint_path}")
            
        self.model.eval()
        
        # Image transformation
        self.transform = transforms = torch.nn.Sequential(
            # Note: We'll use PIL/Numpy for initial prep as in train.py, 
            # but this defines the logic.
        )
        
    def _dist(self, p1, p2):
        return np.linalg.norm(p1 - p2)

    def _calculate_ear(self, lm, indices):
        p1, p2, p3, p4, p5, p6 = [lm[i] for i in indices]
        return (self._dist(p2, p6) + self._dist(p3, p5)) / (2.0 * self._dist(p1, p4) + 1e-6)

    def _get_landmark_features(self, lm):
        features = []
        # Same indices and formulas as in train.py
        L_EAR_IDX = [33, 160, 158, 133, 153, 144]
        R_EAR_IDX = [362, 385, 387, 263, 373, 380]
        
        l_ear = self._calculate_ear(lm, L_EAR_IDX)
        r_ear = self._calculate_ear(lm, R_EAR_IDX)
        
        features.append(l_ear) # 1
        features.append(r_ear) # 2
        
        mar = self._dist(lm[13], lm[14]) / (self._dist(lm[61], lm[291]) + 1e-6)
        features.append(mar) # 3
        
        left_eye_center_y = (lm[33][1] + lm[133][1]) / 2.0
        features.append(left_eye_center_y - lm[70][1]) # 4
        
        right_eye_center_y = (lm[362][1] + lm[263][1]) / 2.0
        features.append(right_eye_center_y - lm[300][1]) # 5
        
        v = lm[291] - lm[61]
        features.append(np.degrees(np.arctan2(v[1], v[0]))) # 6
        
        f_ratio = self._dist(lm[234], lm[454]) / (self._dist(lm[10], lm[152]) + 1e-6)
        features.append(f_ratio) # 7
        
        face_height = self._dist(lm[10], lm[152]) + 1e-6
        features.append(self._dist(lm[1], lm[152]) / face_height) # 8
        
        sym_pairs = [(33, 263), (61, 291), (70, 300), (133, 362), (159, 386)]
        sym_diffs = [abs((1.0 - lm[i][0]) - lm[j][0]) for i, j in sym_pairs]
        features.append(np.mean(sym_diffs)) # 9
        
        features.append((l_ear + r_ear) / 2.0) # 10
        
        return torch.tensor(features, dtype=torch.float32).unsqueeze(0).to(self.device)

    def predict(self, image: Image.Image):
        # 1. Extract face and landmarks
        face_data = extract_face(image)
        if face_data is None:
            return None
            
        # 2. Image transformation
        # face_data.face_image is already 48x48 grayscale from processor.py
        # Apply the rest of the transform: ToTensor -> Normalize
        img_tensor = np.array(face_data.face_image.convert("L")) / 255.0
        img_tensor = (img_tensor - 0.5) / 0.5
        img_tensor = torch.tensor(img_tensor, dtype=torch.float32).unsqueeze(0).unsqueeze(0).to(self.device)
        
        # 3. Landmark features
        lm_tensor = self._get_landmark_features(face_data.landmarks)
        
        # 4. Inference
        with torch.no_grad():
            logits = self.model(img_tensor, lm_tensor)
            probs = F.softmax(logits, dim=1)
            
        # 5. Results computation
        conf, idx = torch.max(probs, 1)
        conf = round(float(conf.item()), 4)
        dominant_emotion = self.classes[idx.item()]
        
        # vibe_score: weighted sum of softmax probabilities
        vibe_score = float(torch.sum(probs[0] * self.vibe_weights).item())
        
        return {
            "vibe_score": vibe_score,
            "dominant_emotion": dominant_emotion,
            "confidence": conf
        }

if __name__ == "__main__":
    # Test stub
    predictor = MultiModalPredictor()
    # If test.jpg exists in root, run a quick test
    test_img_path = "vibechecker-ai/test.jpg"
    if os.path.exists(test_img_path):
        img = Image.open(test_img_path)
        res = predictor.predict(img)
        print(f"Test Result: {res}")
