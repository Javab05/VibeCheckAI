# Data / ML Ops — Javaya

FER2013 dataset preparation for VibeChecker AI.
All 7 FER2013 emotion classes are kept (team decision, Apr 2026):
the multimodal model weights disgust lower in the vibe-score formula
and Aaron's landmark mapping uses the full label set.

## Layout
```
data/
├── raw/               # fer2013.csv goes here (gitignored)
├── processed/         # train.npz, val.npz, test.npz (gitignored)
├── train/             # train/<emotion>/*.png  (gitignored)
├── val/               # val/<emotion>/*.png    (gitignored)
└── test/              # test/<emotion>/*.png   (gitignored)
```

## Prepare the dataset

1. Download FER2013 from Kaggle: https://www.kaggle.com/datasets/deadskull7/fer2013
2. Put (or symlink) the CSV at `data/raw/fer2013.csv`.
3. From the project root, run:
   ```bash
   python data/prepare_fer2013.py
   ```
   Add `--no-images` to skip the per-class PNG export (faster; only writes `.npz`).

The script splits by the CSV's `Usage` column:
- `Training` → `data/train/` and `data/processed/train.npz`
- `PublicTest` → `data/val/` and `data/processed/val.npz`
- `PrivateTest` → `data/test/` and `data/processed/test.npz`

## Label mapping
| index | emotion  |
|------:|----------|
| 0     | angry    |
| 1     | disgust  |
| 2     | fear     |
| 3     | happy    |
| 4     | neutral  |
| 5     | sad      |
| 6     | surprise |

Alphabetical order — matches PyTorch `ImageFolder` auto-indexing and
`database/seed_db.py` (`EMOTIONS`). The ML model's softmax output
emits scores in this same order.

## Formats

### For the ML team (Henry + Aaron)
- **Fast path — `.npz` archives** (recommended for training):
  ```python
  import numpy as np
  data = np.load("data/processed/train.npz")
  images = data["images"]   # uint8 (N, 48, 48)
  labels = data["labels"]   # int64 (N,)
  ```
- **Easy path — PyTorch `ImageFolder`** (drop-in dataloader):
  ```python
  from torchvision.datasets import ImageFolder
  train_ds = ImageFolder("data/train", transform=...)
  # train_ds.classes == ['angry', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise']
  ```

### For the CV team (Aaron)
The per-class PNGs under `data/train/<emotion>/` are raw 48x48 grayscale. If MediaPipe
face mesh needs a different size or 3-channel input, add preprocessing in `cv/` —
don't modify the on-disk dataset.

## Regenerating
The output dirs are gitignored, so each team member needs to run `prepare_fer2013.py`
once on their own machine after dropping the CSV into `data/raw/`.
