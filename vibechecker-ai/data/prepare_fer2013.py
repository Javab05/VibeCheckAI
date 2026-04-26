"""Prepare FER2013 for VibeChecker AI (disgust dropped — 6 classes).

Reads data/raw/fer2013.csv and writes:
  - data/{train,val,test}/<emotion>/*.png   (PyTorch ImageFolder layout)
  - data/processed/{train,val,test}.npz     (compact numpy archives)

Split follows the CSV's Usage column:
    Training   -> train
    PublicTest -> val
    PrivateTest-> test

Label order (matches database/seed_db.py EMOTIONS):
    0 angry, 1 fear, 2 happy, 3 neutral, 4 sad, 5 surprise

Usage:
    python data/prepare_fer2013.py                 # default paths
    python data/prepare_fer2013.py --no-images     # skip PNG export (faster)
    python data/prepare_fer2013.py --input path/to.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np
from PIL import Image

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, **_kwargs):
        return iterable


IMG_SIZE = 48

# 6 classes, alphabetical (matches PyTorch ImageFolder auto-indexing)
EMOTIONS = ["angry", "fear", "happy", "neutral", "sad", "surprise"]

# FER2013 original labels → our new indices (disgust=1 is skipped)
_FER_NAMES = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]
LABEL_REMAP = {
    old: EMOTIONS.index(name)
    for old, name in enumerate(_FER_NAMES)
    if name != "disgust"
}

USAGE_TO_SPLIT = {
    "Training": "train",
    "PublicTest": "val",
    "PrivateTest": "test",
}


def parse_pixels(pixel_str: str) -> np.ndarray:
    """Space-separated pixel string -> (48, 48) uint8 array."""
    arr = np.array(pixel_str.split(), dtype=np.uint8)
    if arr.size != IMG_SIZE * IMG_SIZE:
        raise ValueError(f"Expected {IMG_SIZE * IMG_SIZE} pixels, got {arr.size}")
    return arr.reshape(IMG_SIZE, IMG_SIZE)


def prepare(input_csv: Path, data_dir: Path, export_images: bool) -> None:
    if not input_csv.exists():
        sys.exit(f"ERROR: input CSV not found at {input_csv}")

    buckets: dict[str, dict[str, list]] = {
        split: {"images": [], "labels": []} for split in USAGE_TO_SPLIT.values()
    }

    if export_images:
        for split in USAGE_TO_SPLIT.values():
            for emotion in EMOTIONS:
                (data_dir / split / emotion).mkdir(parents=True, exist_ok=True)

    written: dict[str, int] = {split: 0 for split in USAGE_TO_SPLIT.values()}
    skipped = 0

    with input_csv.open("r", newline="") as f:
        reader = csv.DictReader(f)
        for row in tqdm(reader, desc="Processing FER2013", unit="img"):
            split = USAGE_TO_SPLIT.get(row.get("Usage", "").strip())
            if split is None:
                skipped += 1
                continue

            try:
                old_label = int(row["emotion"])
                new_label = LABEL_REMAP.get(old_label)
                if new_label is None:  # disgust — skip
                    skipped += 1
                    continue
                img = parse_pixels(row["pixels"])
            except (ValueError, KeyError) as e:
                print(f"Skipping malformed row: {e}", file=sys.stderr)
                skipped += 1
                continue

            buckets[split]["images"].append(img)
            buckets[split]["labels"].append(new_label)

            if export_images:
                idx = written[split]
                out_path = data_dir / split / EMOTIONS[new_label] / f"{idx:05d}.png"
                Image.fromarray(img, mode="L").save(out_path)

            written[split] += 1

    processed_dir = data_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    print()
    print("Split summary:")
    print(f"  {'split':<6} {'total':>7}  " + "  ".join(f"{e:>8}" for e in EMOTIONS))
    for split, bucket in buckets.items():
        images = (
            np.stack(bucket["images"])
            if bucket["images"]
            else np.empty((0, IMG_SIZE, IMG_SIZE), dtype=np.uint8)
        )
        labels = np.array(bucket["labels"], dtype=np.int64)
        np.savez_compressed(processed_dir / f"{split}.npz", images=images, labels=labels)
        counts = np.bincount(labels, minlength=len(EMOTIONS))
        print(f"  {split:<6} {len(labels):>7}  " + "  ".join(f"{c:>8}" for c in counts))

    if skipped:
        print(f"\n(skipped {skipped} rows — disgust samples + any malformed data)")

    print()
    print(f"Wrote NumPy archives to:  {processed_dir}")
    if export_images:
        print(f"Wrote per-class PNGs to:  {data_dir}/{{train,val,test}}/<emotion>/")
    else:
        print("Skipped PNG export (--no-images).")


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    default_input = project_root / "data" / "raw" / "fer2013.csv"
    default_data_dir = project_root / "data"

    parser = argparse.ArgumentParser(description="Prepare FER2013 for VibeChecker AI.")
    parser.add_argument("--input", type=Path, default=default_input)
    parser.add_argument("--data-dir", type=Path, default=default_data_dir)
    parser.add_argument("--no-images", dest="export_images", action="store_false",
                        help="skip per-class PNG export")
    parser.set_defaults(export_images=True)
    args = parser.parse_args()

    prepare(args.input.resolve(), args.data_dir.resolve(), args.export_images)


if __name__ == "__main__":
    main()
