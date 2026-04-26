import os
import sys
import time
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, random_split
from torchvision import transforms
from PIL import Image
from pathlib import Path

# Import the model
from model_multimodal import MultiModalEmotionCNN, LANDMARK_FEATURE_SIZE

# Indices for landmark calculations
# Left EAR: 33, 160, 158, 133, 153, 144
# Right EAR: 362, 385, 387, 263, 373, 380
LEFT_EAR_IDX = [33, 160, 158, 133, 153, 144]
RIGHT_EAR_IDX = [362, 385, 387, 263, 373, 380]

def dist(p1, p2):
    return np.linalg.norm(p1 - p2)

def calculate_ear(lm, indices):
    # EAR = (dist(p2,p6) + dist(p3,p5)) / (2 * dist(p1,p4))
    p1, p2, p3, p4, p5, p6 = [lm[i] for i in indices]
    return (dist(p2, p6) + dist(p3, p5)) / (2.0 * dist(p1, p4) + 1e-6)

class MultiModalDataset(Dataset):
    def __init__(self, root_dir, transform=None):
        self.root_dir = Path(root_dir)
        self.transform = transform
        self.samples = []
        
        # FER2013 emotion labels (ensure consistent order)
        self.classes = ["angry", "disgust", "fear", "happy", "neutral", "sad", "surprise"]
        self.class_to_idx = {cls: i for i, cls in enumerate(self.classes)}
        
        print(f"Loading dataset from {root_dir}...")
        for emotion in self.classes:
            emotion_dir = self.root_dir / emotion
            if not emotion_dir.exists():
                continue
                
            for img_file in emotion_dir.glob("*"):
                if img_file.suffix.lower() in [".jpg", ".jpeg", ".png"]:
                    npy_file = img_file.with_suffix(".npy")
                    if npy_file.exists():
                        try:
                            landmarks = np.load(npy_file)
                            if landmarks.shape == (478, 3):
                                self.samples.append((img_file, npy_file, self.class_to_idx[emotion]))
                        except Exception:
                            continue
        print(f"Loaded {len(self.samples)} valid samples.")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path, npy_path, label = self.samples[idx]
        
        # Image branch
        image = Image.open(img_path).convert("L")
        if self.transform:
            image = self.transform(image)
            
        # Landmark branch
        lm = np.load(npy_path)
        
        # Feature Extraction
        features = []
        
        # 1. Left EAR
        l_ear = calculate_ear(lm, LEFT_EAR_IDX)
        features.append(l_ear)
        
        # 2. Right EAR
        r_ear = calculate_ear(lm, RIGHT_EAR_IDX)
        features.append(r_ear)
        
        # 3. MAR: dist(lm[13], lm[14]) / dist(lm[61], lm[291])
        mar = dist(lm[13], lm[14]) / (dist(lm[61], lm[291]) + 1e-6)
        features.append(mar)
        
        # 4. Left brow raise: left_eye_center_y - lm[70]_y
        # Use mean of indices 33, 133 for eye center
        left_eye_center_y = (lm[33][1] + lm[133][1]) / 2.0
        features.append(left_eye_center_y - lm[70][1])
        
        # 5. Right brow raise: right_eye_center_y - lm[300]_y
        # Use mean of indices 362, 263 for eye center
        right_eye_center_y = (lm[362][1] + lm[263][1]) / 2.0
        features.append(right_eye_center_y - lm[300][1])
        
        # 6. Mouth corner angle: degrees(arctan2) of vector from lm[61] to lm[291]
        v = lm[291] - lm[61]
        angle = np.degrees(np.arctan2(v[1], v[0]))
        features.append(angle)
        
        # 7. Face width-to-height ratio: dist(lm[234], lm[454]) / dist(lm[10], lm[152])
        f_ratio = dist(lm[234], lm[454]) / (dist(lm[10], lm[152]) + 1e-6)
        features.append(f_ratio)
        
        # 8. Nose-to-chin normalized: dist(lm[1], lm[152]) / face_height
        face_height = dist(lm[10], lm[152]) + 1e-6
        n2c = dist(lm[1], lm[152]) / face_height
        features.append(n2c)
        
        # 9. Symmetry: mean absolute diff of mirrored x-coords
        # Mirrored x = 1 - x
        sym_pairs = [(33, 263), (61, 291), (70, 300), (133, 362), (159, 386)]
        sym_diffs = []
        for i, j in sym_pairs:
            # MediaPipe coords are normalized 0-1
            # Mirror lm[i].x and compare to lm[j].x
            mirrored_x = 1.0 - lm[i][0]
            sym_diffs.append(abs(mirrored_x - lm[j][0]))
        features.append(np.mean(sym_diffs))
        
        # 10. Mean of EAR
        features.append((l_ear + r_ear) / 2.0)
        
        landmark_tensor = torch.tensor(features, dtype=torch.float32)
        
        return image, landmark_tensor, label

def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on device: {device}")
    
    # Paths
    base_dir = Path(__file__).parent
    data_dir = base_dir / "data" / "train"
    model_dir = base_dir / "models"
    best_model_path = model_dir / "best_multimodal.pt"
    pretrained_path = model_dir / "emotion_model_v1.0.pt"
    
    if not data_dir.exists():
        print(f"Error: Data directory not found at {data_dir}")
        sys.exit(1)
        
    # Transforms
    transform = transforms.Compose([
        transforms.Grayscale(num_output_channels=1),
        transforms.Resize((48, 48)),
        transforms.ToTensor(),
        transforms.Normalize(mean=(0.5,), std=(0.5,))
    ])
    
    # Dataset and Split
    full_dataset = MultiModalDataset(data_dir, transform=transform)
    val_size = int(0.1 * len(full_dataset))
    train_size = len(full_dataset) - val_size
    train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size])
    
    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True, num_workers=4, pin_memory=True)
    val_loader = DataLoader(val_dataset, batch_size=64, shuffle=False, num_workers=4, pin_memory=True)
    
    # Model
    model = MultiModalEmotionCNN(num_classes=7, landmark_feature_size=LANDMARK_FEATURE_SIZE).to(device)
    
    # Warm Start
    if pretrained_path.exists():
        print(f"Loading pretrained weights from {pretrained_path}...")
        pretrained_state = torch.load(pretrained_path, map_location=device)
        if "model_state_dict" in pretrained_state:
            pretrained_state = pretrained_state["model_state_dict"]
            
        current_state = model.state_dict()
        matched_layers = 0
        skipped_layers = 0
        
        for name, param in pretrained_state.items():
            # Remap to image_branch
            new_name = "image_branch." + name
            if new_name in current_state and current_state[new_name].shape == param.shape:
                current_state[new_name].copy_(param)
                matched_layers += 1
            else:
                skipped_layers += 1
        model.load_state_dict(current_state)
        print(f"Warm start complete: {matched_layers} layers matched, {skipped_layers} layers skipped.")
    
    # Training Config
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=1e-3)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=3, factor=0.5)
    
    best_val_loss = float("inf")
    
    print("\nStarting Training...")
    for epoch in range(30):
        start_time = time.time()
        
        # Train
        model.train()
        train_loss = 0.0
        for images, landmarks, labels in train_loader:
            images, landmarks, labels = images.to(device), landmarks.to(device), labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(images, landmarks)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item() * images.size(0)
        
        train_loss /= len(train_loader.dataset)
        
        # Validation
        model.eval()
        val_loss = 0.0
        correct = 0
        with torch.no_grad():
            for images, landmarks, labels in val_loader:
                images, landmarks, labels = images.to(device), landmarks.to(device), labels.to(device)
                outputs = model(images, landmarks)
                loss = criterion(outputs, labels)
                val_loss += loss.item() * images.size(0)
                
                _, predicted = torch.max(outputs, 1)
                correct += (predicted == labels).sum().item()
                
        val_loss /= len(val_loader.dataset)
        val_acc = correct / len(val_loader.dataset)
        
        scheduler.step(val_loss)
        
        elapsed = time.time() - start_time
        print(f"Epoch {epoch+1:02d}/30 | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.4f} | {elapsed:.1f}s")
        
        # Checkpoint
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save({
                'epoch': epoch,
                'model_state': model.state_dict(),
                'label_map': full_dataset.classes
            }, best_model_path)
            print(f"  --> Saved best model to {best_model_path}")

    print("\nTraining Complete.")

if __name__ == "__main__":
    main()
