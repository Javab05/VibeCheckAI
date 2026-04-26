import torch
import torch.nn as nn

LANDMARK_FEATURE_SIZE = 10

class MultiModalEmotionCNN(nn.Module):
    def __init__(self, num_classes: int = 7, landmark_feature_size: int = LANDMARK_FEATURE_SIZE):
        super(MultiModalEmotionCNN, self).__init__()
        
        # Image branch: 1x48x48 grayscale -> 128-dim feature vector
        self.image_branch = nn.Sequential(
            # Layer 1: 48x48 -> 24x24
            nn.Conv2d(1, 32, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Dropout(0.25),
            
            # Layer 2: 24x24 -> 12x12
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Dropout(0.25),
            
            # Layer 3: 12x12 -> 6x6
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Dropout(0.25),
            
            # Classifier part of image branch
            nn.Flatten(),
            nn.Linear(128 * 6 * 6, 256), # 4608 -> 256
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(256, 128),
            nn.ReLU(inplace=True)
        )
        
        # Landmark branch: landmark_feature_size -> 64-dim feature vector
        self.landmark_branch = nn.Sequential(
            nn.Linear(landmark_feature_size, 128),
            nn.ReLU(inplace=True),
            nn.Linear(128, 64),
            nn.ReLU(inplace=True)
        )
        
        # Fusion and final classification
        self.fusion_classifier = nn.Sequential(
            nn.Linear(128 + 64, 64), # 192 -> 64
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(64, num_classes)
        )
        
        # Weight initialization
        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d) or isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight, nonlinearity='relu')
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

    def forward(self, image_tensor, landmark_tensor):
        img_features = self.image_branch(image_tensor)
        lm_features = self.landmark_branch(landmark_tensor)
        
        # Concatenate branches (Batch, 128) and (Batch, 64) -> (Batch, 192)
        combined = torch.cat((img_features, lm_features), dim=1)
        
        logits = self.fusion_classifier(combined)
        return logits

if __name__ == "__main__":
    # Sanity check
    num_classes = 7
    landmark_size = 10
    model = MultiModalEmotionCNN(num_classes=num_classes, landmark_feature_size=landmark_size)
    
    dummy_img = torch.randn(2, 1, 48, 48)
    dummy_lm = torch.randn(2, landmark_size)
    
    output = model(dummy_img, dummy_lm)
    print(f"Model Architecture:\n{model}")
    print(f"\nInput Shapes: Image {dummy_img.shape}, Landmarks {dummy_lm.shape}")
    print(f"Output Shape: {output.shape} (Expected [2, {num_classes}])")
    
    total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Total Trainable Params: {total_params:,}")
