# ML Training / Classification — VibeChecker AI

Emotion recognition from facial images using a custom CNN trained on FER2013.

## Files

| File | Purpose |
|------|---------|
| `model.py` | `EmotionCNN` architecture + `load_model()` helper |
| `dataset.py` | FER2013 `DataLoader` with augmentation + class balancing |
| `train.py` | Full training loop with early stopping + checkpointing |
| `evaluate.py` | Test-set evaluation with per-class metrics + confusion matrix |
| `inference.py` | **Backend-facing API** — call `get_predictor()` from here |

## Setup

```bash
pip install torch torchvision pillow
```

## Training

1. Get FER2013 data from Javaya, placed as:
```
ml/data/
  train/angry/  train/disgust/  train/fear/  train/happy/
  train/sad/    train/surprise/ train/neutral/
  val/   ...
  test/  ...
```

2. Train:
```bash
cd ml/
python train.py
# With options:
python train.py --epochs 60 --batch-size 64 --lr 1e-3
# Resume from checkpoint:
python train.py --resume models/emotion_model_latest.pt
```

3. Evaluate:
```bash
python evaluate.py --checkpoint models/emotion_model_v1.0.pt --save-plot
```

## Backend Integration (Zem)

```python
from ml.inference import get_predictor

predictor = get_predictor()  # Loads model once at startup

result = predictor.predict_from_path("path/to/selfie.jpg")
# result = {
#   "emotion":       "happy",
#   "confidence":    0.82,
#   "scores":        {"angry": 0.02, "happy": 0.82, "sad": 0.04, ...},
#   "model_version": "v1.0"
# }

# Then store it:
from database.db import store_emotion_result
store_emotion_result(
    checkin_id=checkin.checkin_id,
    predicted_emotion=result["emotion"],
    confidence=result["confidence"],
    scores=result["scores"],
    model_version=result["model_version"],
)
```

## Model Checkpoints

Saved to `ml/models/` (git-ignored). Share via Google Drive.

- `emotion_model_v1.0.pt` — Best validation accuracy checkpoint
- `emotion_model_latest.pt` — Most recent epoch (for resuming)
- `training_log.csv` — Per-epoch loss/accuracy for plotting

## Expected Performance

FER2013 is a hard dataset (human accuracy ~65%). Target benchmarks:

| Metric | Target |
|--------|--------|
| Overall accuracy | 62–68% |
| Happy F1 | ~0.80 |
| Disgust F1 | ~0.40 (fewest samples) |
| Neutral F1 | ~0.65 |
