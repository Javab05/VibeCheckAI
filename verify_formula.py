import torch
import torch.nn.functional as F
import numpy as np

def verify():
    # Weights from the modified file
    vibe_weights = torch.tensor([30, 20, 45, 100, 70, 35, 75], dtype=torch.float32)
    
    # 1. Verify range [20, 100]
    print(f"Weights: {vibe_weights.tolist()}")
    print(f"Min weight: {torch.min(vibe_weights).item()}")
    print(f"Max weight: {torch.max(vibe_weights).item()}")
    
    # 2. Test with some distributions
    # Case: Happy dominant
    probs = torch.tensor([[0.05, 0.05, 0.05, 0.7, 0.05, 0.05, 0.05]])
    vibe_score = float(torch.sum(probs[0] * vibe_weights).item())
    print(f"Happy dominant (0.7) vibe score: {vibe_score:.2f}")
    
    # Case: Disgust dominant
    probs = torch.tensor([[0.05, 0.7, 0.05, 0.05, 0.05, 0.05, 0.05]])
    vibe_score = float(torch.sum(probs[0] * vibe_weights).item())
    print(f"Disgust dominant (0.7) vibe score: {vibe_score:.2f}")
    
    # Case: Neutral dominant
    probs = torch.tensor([[0.05, 0.05, 0.05, 0.05, 0.7, 0.05, 0.05]])
    vibe_score = float(torch.sum(probs[0] * vibe_weights).item())
    print(f"Neutral dominant (0.7) vibe score: {vibe_score:.2f}")

    # Case: Uniform
    probs = torch.ones((1, 7)) / 7.0
    vibe_score = float(torch.sum(probs[0] * vibe_weights).item())
    print(f"Uniform distribution vibe score: {vibe_score:.2f}")

    # Theoretical Min/Max
    # All weight on min weight index (disgust at index 1)
    probs_min = torch.zeros((1, 7))
    probs_min[0, 1] = 1.0
    score_min = float(torch.sum(probs_min[0] * vibe_weights).item())
    
    # All weight on max weight index (happy at index 3)
    probs_max = torch.zeros((1, 7))
    probs_max[0, 3] = 1.0
    score_max = float(torch.sum(probs_max[0] * vibe_weights).item())
    
    print(f"Theoretical Min: {score_min}")
    print(f"Theoretical Max: {score_max}")
    
    assert 20 <= score_min <= 100
    assert 20 <= score_max <= 100
    print("Range [20, 100] confirmed.")

if __name__ == "__main__":
    verify()
