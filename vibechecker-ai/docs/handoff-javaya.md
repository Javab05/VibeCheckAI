# VibeChecker AI — Javaya's Handoff Document

**Owner:** Javaya
**Roles:** 3 (Database / Storage) + 6 (Data / ML Operations)
**Last updated:** 2026-04-18
**Status:** Database layer complete. Dataset prepared (6 classes). Self-owned polish items (get_season extract, np.fromstring fix, is_latest README note) shipped. Blocked on teammate inputs for next integration phase.

---

## Table of Contents

1. [What I built](#1-what-i-built)
2. [Architecture & data flow](#2-architecture--data-flow)
3. [File inventory](#3-file-inventory)
4. [Interconnection with each teammate](#4-interconnection-with-each-teammate)
5. [Timeline of work completed](#5-timeline-of-work-completed)
6. [Known issues & gotchas](#6-known-issues--gotchas)
7. [What's done](#7-whats-done)
8. [What's blocked (waiting on teammates)](#8-whats-blocked-waiting-on-teammates)
9. [What to do when teammates catch up](#9-what-to-do-when-teammates-catch-up)

---

## 1. What I built

### Role 3 — Database / Storage

A complete SQLite + SQLAlchemy data layer:

- Schema for 4 tables: `users`, `checkins`, `emotion_results`, `seasonal_summaries`
- Helper module (`db.py`) with CRUD, query, and aggregation functions the backend imports
- Bcrypt enforcement on user creation
- Re-inference support (model can run multiple times per selfie with full history)
- Weekly sadness trend query for frontend charts
- Configurable depression threshold
- Image storage convention (filesystem + path stored in DB)

### Role 6 — Data / ML Operations

A FER2013 dataset preparation pipeline:

- `prepare_fer2013.py` — parses the Kaggle CSV, splits into train/val/test, emits two output formats
- Per-class PNG folders (PyTorch `ImageFolder` compatible)
- Compact `.npz` numpy archives (fast loading during training)
- Dropped the `disgust` class (team decision — too imbalanced, not aligned with sadness-tracking goal)

---

## 2. Architecture & data flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER ACTION                                  │
│                 (uploads a daily selfie)                             │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  BACKEND (Zem)                                                       │
│  - Receives POST /checkin with image bytes                           │
│  - Writes image to storage/images/{user_id}/{date}.jpg               │
│  - Calls db.create_checkin() ──────────────────┐                     │
└────────────────────────────────────────────────┼────────────────────┘
                                                  │
                                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  DATABASE (Javaya)                                                   │
│  - checkins row inserted, returns Checkin ORM object                 │
└────────────────────────────────────────────────┬────────────────────┘
                                                  │
                                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  CV (Aaron)                                                          │
│  - Loads image from storage/images/...                               │
│  - Runs MediaPipe face mesh                                          │
│  - Outputs preprocessed face tensor                                  │
└────────────────────────────────────────────────┬────────────────────┘
                                                  │
                                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ML MODEL (Henry + Aaron)                                            │
│  - Trained on data I prepared (data/train/, data/val/, data/test/)   │
│  - Outputs 6-class softmax: [angry, fear, happy, neutral, sad, ...]  │
└────────────────────────────────────────────────┬────────────────────┘
                                                  │
                                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  BACKEND writes result                                               │
│  - db.store_emotion_result(checkin_id, predicted, conf, scores) ──┐  │
└───────────────────────────────────────────────────────────────────┼──┘
                                                                     │
                                                                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│  DATABASE (Javaya)                                                   │
│  - emotion_results row inserted with is_latest=1                     │
│  - Previous predictions (if any) demoted to is_latest=0              │
└────────────────────────────────────────────────┬────────────────────┘
                                                  │
                                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  DASHBOARD (vexonik + Nick, through Zem's API)                       │
│  - Calls db.get_weekly_sadness_trend() → line chart                  │
│  - Calls db.get_user_history() → photo + emotion gallery             │
│  - Calls db.update_seasonal_summary() → depression flag              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. File inventory

### Database layer (`database/`)

| File | Purpose |
|---|---|
| `models.py` | SQLAlchemy table definitions, `get_db()` session factory, `.to_dict()` helpers on every model |
| `db.py` | Public API — all helpers the backend imports. Contains `DEPRESSION_THRESHOLD = 0.3` |
| `init_db.py` | One-time setup: creates `vibechecker.db` and `storage/images/` directory |
| `seed_db.py` | Populates DB with 2 fake users + ~150 winter 2026 check-ins for testing |
| `README.md` | Quick reference for the database module |

### Data layer (`data/`)

| File / Dir | Purpose |
|---|---|
| `prepare_fer2013.py` | Parses FER2013 CSV → splits + writes PNG folders + .npz archives |
| `README.md` | Data pipeline documentation (label mapping, formats, usage) |
| `raw/fer2013.csv` | Symlink to downloaded CSV (gitignored) |
| `processed/*.npz` | Compact numpy archives for fast loading |
| `train/<emotion>/*.png` | ImageFolder-compatible training images |
| `val/<emotion>/*.png` | ImageFolder-compatible validation images |
| `test/<emotion>/*.png` | ImageFolder-compatible test images |

### Modified shared files

| File | What I changed |
|---|---|
| `requirements.txt` | Added `numpy`, `pillow`, `tqdm` for the data pipeline |

---

## 4. Interconnection with each teammate

### 4.1 — Backend (Zem)

**Zem is the #1 consumer of my code.** Every API route that touches data goes through `db.py`.

**How he imports:**
```python
from database.db import (
    create_user, get_user_by_email, get_user_by_id,
    create_checkin,
    store_emotion_result, get_emotion_result_history,
    get_user_history, get_weekly_sadness_trend,
    get_emotion_counts, get_dominant_emotion, get_average_scores,
    update_seasonal_summary,
)
```

**Conventions he needs to follow:**
1. **Bcrypt password BEFORE calling `create_user()`.**
   ```python
   import bcrypt
   hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
   user = create_user(username, email, hashed)
   ```
   If he passes a plaintext string, `create_user()` raises `ValueError`.

2. **All fetch/create functions return ORM objects.** Call `.to_dict()` before returning from API routes.
   ```python
   user = get_user_by_email(email)
   return jsonify(user.to_dict())   # password_hash is excluded automatically
   ```

3. **Aggregate functions return plain dicts/strings** (counts, averages, dominant, trend). These are JSON-safe already — no conversion needed.

4. **For dashboard queries, use `checkin.latest_result`:**
   ```python
   checkins = get_user_history(user_id=1, season="winter", season_year=2026)
   for c in checkins:
       data = c.to_dict()
       if c.latest_result:
           data["prediction"] = c.latest_result.to_dict()
       return data
   ```

5. **For re-running the model (e.g., v2 release), just call `store_emotion_result` again.** The function automatically demotes the old prediction to `is_latest=0`. No deletion needed.

6. **Saving images is the backend's responsibility, not mine.**
   - Backend writes to `storage/images/{user_id}/{YYYY-MM-DD}.jpg`
   - Backend passes that path string to `create_checkin(image_path=...)`
   - I only store the path string, never the image bytes

**What I need from Zem still:**
- Decision on the re-inference design (✅ answered: Option B — 1:many with is_latest)
- Decision on return type (✅ answered: ORM objects + .to_dict())
- Confirmation on whether he wants me to add any convenience helpers he didn't anticipate

---

### 4.2 — Computer Vision (Aaron)

**Aaron sits between the stored image and the ML model.** My involvement: his output becomes the model's input, and I might need to format it.

**Data flow:**
1. Backend writes image to `storage/images/{user_id}/{date}.jpg` — path in my DB
2. Aaron's code loads that file path (from `checkin.image_path` in my DB)
3. MediaPipe extracts face mesh landmarks
4. Aaron passes the processed data to the ML model

**What I give Aaron:**
- `data/train/<emotion>/*.png` — 48×48 grayscale PNGs if he wants to sanity-check his preprocessing on the training data
- The `image_path` field in the `checkins` table to know where the source image is

**What Aaron owes me (BLOCKED):**
- **Exact output format of his preprocessing pipeline.** Specifically:
  - Is it a NumPy array of 468 `(x, y, z)` landmark coordinates?
  - A cropped face image tensor of some size?
  - A combined structure with both?
  - What's the dtype (`float32`? `uint8`?) and shape?
- **What image formats/sizes his pipeline accepts as input.** (If a user uploads a 4K selfie, does his pipeline resize it, or do we need a pre-resize step?)

Once Aaron answers, I can write the bridge function that converts his output to the ML model's input tensor — but that also depends on Henry + Aaron's model input shape.

---

### 4.3 — ML Training (Henry + Aaron)

**They consume my prepared dataset** and produce model checkpoints the backend loads for inference.

**What I give them (ready now):**

Two loading paths, same data, pick whichever is convenient:

**Option 1 — NumPy (recommended for training loops):**
```python
import numpy as np
data = np.load("data/processed/train.npz")
images = data["images"]   # uint8 array, shape (28273, 48, 48)
labels = data["labels"]   # int64 array, shape (28273,), values 0-5
```

**Option 2 — PyTorch ImageFolder (drop-in DataLoader):**
```python
from torchvision.datasets import ImageFolder
from torchvision import transforms
train_ds = ImageFolder(
    "data/train",
    transform=transforms.Compose([
        transforms.Grayscale(num_output_channels=1),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5], std=[0.5]),
    ])
)
# train_ds.classes == ['angry', 'fear', 'happy', 'neutral', 'sad', 'surprise']
```

**Label order (CRITICAL — the model's softmax must match this order):**

| index | emotion  |
|------:|----------|
| 0     | angry    |
| 1     | fear     |
| 2     | happy    |
| 3     | neutral  |
| 4     | sad      |
| 5     | surprise |

This is alphabetical — matches PyTorch ImageFolder's default `class_to_idx`, so if they use ImageFolder, indices are correct automatically.

**Dataset stats (train/val/test):**
| split | total | angry | fear | happy | neutral | sad | surprise |
|---|---:|---:|---:|---:|---:|---:|---:|
| train | 28,273 | 3,995 | 4,097 | 7,215 | 4,965 | 4,830 | 3,171 |
| val | 3,533 | 467 | 496 | 895 | 607 | 653 | 415 |
| test | 3,534 | 491 | 528 | 879 | 626 | 594 | 416 |

**Class imbalance note:** `happy` has 1.8× more samples than `surprise`. Not as severe as disgust was, but still meaningful. Two options for handling this:
- Use a weighted `CrossEntropyLoss` — weights inversely proportional to class frequency
- Use a `WeightedRandomSampler` in the DataLoader

**How their checkpoint gets integrated:**
- Save trained model to `ml/models/emotion_model_vX.pt` (gitignored — share via Google Drive)
- Backend's inference endpoint loads the checkpoint and calls `db.store_emotion_result(..., model_version="v1.0")`
- Model version string goes straight into the DB — important for tracking which model made which prediction

**What they owe me (BLOCKED):**
- **Exact input shape the model expects.** 48×48×1 grayscale? 224×224×3 RGB after upscaling? This dictates whether my on-disk PNGs are used as-is or need a preprocessing step.
- **Output format confirmation.** Is it raw logits (need to softmax before storing), or already-softmaxed probabilities?
- **Accuracy target.** At what accuracy do they stop iterating? This affects whether I spend time on data augmentation or class balancing on my end.

---

### 4.4 — Frontend (vexonik + Nick)

**They don't touch my code directly** — all their data comes through Zem's API. But my query functions need to return data in a shape their chart library can plot.

**Data I already provide (ready for charts):**

**1. Weekly sadness trend line chart:**
```python
# db.get_weekly_sadness_trend(user_id, season, season_year)
# Returns:
[
  {"week": "2026-00", "avg_sadness": 0.19},
  {"week": "2026-01", "avg_sadness": 0.14},
  {"week": "2026-02", "avg_sadness": 0.17},
  ...
]
```
X-axis: week. Y-axis: avg_sadness (0.0–1.0). Perfect for a line chart.

**2. Daily photo + emotion history:**
```python
# db.get_user_history(user_id, season, season_year)
# Returns list of Checkin objects; Zem converts via .to_dict()
[
  {
    "checkin_id": 1,
    "image_path": "storage/images/1/2026-01-15.jpg",
    "captured_at": "2026-01-15T08:30:00",
    "prediction": {
      "predicted_emotion": "sad",
      "confidence": 0.72,
      "scores": {"angry": 0.03, "fear": 0.05, "happy": 0.10, "neutral": 0.10, "sad": 0.72, "surprise": 0.00},
      "model_version": "v1.0",
      "is_latest": 1
    }
  },
  ...
]
```
Can drive a calendar view, a photo gallery, or individual emotion breakdown pie charts.

**3. Seasonal summary card:**
```python
# db.update_seasonal_summary(user_id, season, season_year).to_dict()
# Returns:
{
  "season": "winter",
  "season_year": 2026,
  "total_checkins": 75,
  "avg_happiness": 0.18,
  "avg_sadness": 0.31,
  "dominant_emotion": "sad",
  "depression_flag": 1,
  "updated_at": "..."
}
```
Perfect for a dashboard summary card with a big depression_flag indicator.

**What I might still need from them:**
- **Preferred chart library** (Chart.js, Recharts, D3, etc.) — some libraries want different data shapes. I can reshape queries if needed.
- **Refresh cadence** — does the dashboard call `update_seasonal_summary()` on every page load, or should it run on a schedule (e.g., daily)? Affects whether I build a background job.
- **Timezone handling** — does "a day" mean UTC or the user's local time? Affects the weekly grouping logic.

---

## 5. Timeline of work completed

### Phase 1 — Initial exploration (starting point)
- Read the existing codebase: database/ already had schema + helpers + seed script written
- FER2013 dataset not yet processed; data/ directory didn't exist
- Confirmed scope: Database/Storage (Role 3) + Data/ML Ops (Role 6)

### Phase 2 — FER2013 dataset pipeline
1. Created `data/{raw,processed,train,val,test}/` with `.gitkeep` sentinels matching the existing `.gitignore`
2. Symlinked `~/Downloads/fer2013.csv` into `data/raw/`
3. Wrote `data/prepare_fer2013.py`:
   - Reads CSV, splits by `Usage` column (Training/PublicTest/PrivateTest)
   - Writes two output formats: PyTorch ImageFolder PNGs + compressed `.npz` archives
   - Processed all 35,887 rows in ~19 seconds
4. Wrote `data/README.md` with format documentation
5. Added `numpy`, `pillow`, `tqdm` to `requirements.txt`

### Phase 3 — Code cleanup
- Trimmed verbose comments across all 5 Python files (models, db, init_db, seed_db, prepare_fer2013)
- Dropped a misleading `try/except` in `get_db()` that was never reachable
- Kept one-line docstrings where useful; removed inline play-by-play comments

### Phase 4 — Teammate decision #1 (drop disgust → 6 classes)
- Asked Henry + Aaron whether to keep all 7 FER2013 emotions or drop the imbalanced `disgust` class (only 436 train samples)
- **Decision: drop disgust** (also aligns with the app's focus on sadness tracking)
- Updated `EMOTIONS` lists in `seed_db.py` and `prepare_fer2013.py` to alphabetical 6-class order
- Added a `LABEL_REMAP` dict in the prep script to skip label 1 (disgust) and remap the rest
- Deleted old disgust folders on disk
- Re-ran the prep: **28,273 train / 3,533 val / 3,534 test** (547 disgust samples skipped)

### Phase 5 — Teammate decision #2 (ORM objects + .to_dict())
- Asked Zem whether he wanted db.py helpers to return plain dicts, ORM objects, or both
- **Decision: ORM objects with `.to_dict()` helpers**
- Added `.to_dict()` method to all 4 model classes:
  - `User.to_dict()` — deliberately excludes `password_hash`
  - `EmotionResult.to_dict()` — auto-deserializes `scores_json` into a real Python dict
- Changed `get_user_history()` to return `list[Checkin]` with eager-loaded relationships (using `joinedload`)

### Phase 6 — Polish items (bcrypt, threshold constant, weekly trend)
- Added `DEPRESSION_THRESHOLD = 0.3` constant at top of `db.py`
- Added bcrypt guard in `create_user()` — raises `ValueError` if password_hash doesn't start with `$2b$`
- Added `get_weekly_sadness_trend()` — uses SQLite's `strftime` and `json_extract` to compute week-by-week averages for frontend charts

### Phase 7 — Re-inference architecture (Option B)
- Asked Zem whether to handle model reruns via in-place update (Option A) or full history with `is_latest` flag (Option B)
- **Decision: Option B — 1:many with `is_latest` flag**
- Added `is_latest` column to `EmotionResult`
- Split `Checkin.emotion_result` into two relationships:
  - `Checkin.latest_result` → single object (or None) where `is_latest=1` — for dashboards
  - `Checkin.emotion_results` → list of all predictions ever, newest first — for history/debugging
- Updated `store_emotion_result()` to demote old predictions to `is_latest=0` before inserting
- Added `get_emotion_result_history(checkin_id)` helper for full prediction history
- All aggregate queries now filter `is_latest == 1` (no double-counting)
- Updated index to `(checkin_id, is_latest)` for fast lookups

### Phase 8 — Self-owned polish items (done while blocked)
- Extracted `get_season()` into `db.py` so both `seed_db.py` and Zem's future check-in endpoint share a single source of truth (previously duplicated in seed only)
- Replaced the deprecated `np.fromstring(..., sep=" ")` in `prepare_fer2013.py` with `np.array(pixel_str.split(), dtype=np.uint8)` — silences the `DeprecationWarning` on NumPy 2.x
- Added an **is_latest flag heads-up** subsection to `database/README.md` so Zem cannot accidentally write aggregate queries that double-count historical predictions
- Verified everything still works: rebuilt DB, re-seeded (2 users + 145 check-ins), re-tested `parse_pixels` output shape

---

## 6. Known issues & gotchas

### 6.1 — DetachedInstanceError on relationships
**Risk:** If Zem accesses a relationship on a returned ORM object that wasn't eagerly loaded, SQLAlchemy tries to re-query through the closed session and raises `DetachedInstanceError`.

**Mitigation:** All my helpers that need relationships use `joinedload()` to force eager loading. If he adds new helpers, he needs to do the same.

**Example that works:**
```python
checkins = get_user_history(...)
for c in checkins:
    c.latest_result.predicted_emotion   # OK — joinedload pre-loaded it
```

**Example that would break:**
```python
user = get_user_by_id(1)
for c in user.checkins:   # DetachedInstanceError — not eager-loaded
    ...
```

### 6.2 — Timestamps stored as text
**Risk:** All timestamps are ISO 8601 strings, not SQLite's (non-existent) DATETIME type. Lexical sorting works because ISO 8601 is lexically sortable. But date arithmetic requires `strftime()`.

**Example I wrote:**
```python
week_col = func.strftime("%Y-%W", Checkin.captured_at)
```

**Gotcha for Zem:** He can't just compare `checkin.captured_at > yesterday` unless both are ISO strings.

### 6.3 — Password hashes bypass validation in seed_db.py
**Risk:** `seed_db.py` creates `User` objects directly via `db.add_all()`, bypassing the `create_user()` bcrypt guard. The placeholder strings (`"hashed_password_placeholder_1"`) aren't real bcrypt hashes.

**Impact:** Seeded users can't actually authenticate. That's fine for testing queries, but don't try to log in as "Javaya" / "TestUser" from the frontend — it won't work.

**If this matters later:** Replace placeholders with real bcrypt hashes:
```python
import bcrypt
password_hash = bcrypt.hashpw(b"testpass123", bcrypt.gensalt()).decode()
```

### 6.4 — SQLite single-writer limitation
**Risk:** SQLite only allows one writer at a time. If two backend API requests try to insert check-ins simultaneously, one might fail with `database is locked`.

**Probability for class project:** Very low. Demos and small user groups work fine.

**If it becomes an issue:** Enable WAL mode (`PRAGMA journal_mode=WAL`) or switch to PostgreSQL. The schema would port over with minor syntax tweaks.

### 6.5 — Season boundary logic is tricky
**Risk:** "Winter 2026" spans **December 2025 through February 2026**. The `season_year` field uses December rollover logic:
```python
season_year = 2026 if date.month <= 2 else 2025
```

**Where it lives:** `get_season(month)` is now exported from `database/db.py` (`seed_db.py` imports it too). Zem should use it directly:
```python
from database.db import get_season
season = get_season(now.month)
season_year = now.year + 1 if now.month == 12 else now.year  # winter rolls forward
```
The `season_year` rollover for December is **not** wrapped yet — left explicit because the backend may want to handle it differently in a timezone-aware way. Flag if we want that wrapped too.

### 6.6 — Image cleanup on account deletion
**Risk:** If a user deletes their account, do we:
- Cascade-delete their `checkins` and `emotion_results` rows? (FK cascade not set up yet)
- Delete their files from `storage/images/{user_id}/`?
- Soft-delete (keep DB rows with an `is_deleted` flag)?

**Current behavior:** None of the above. Deleting a user orphans their data.

**Decision needed with Zem** — see section 9.

### 6.7 — ~~`np.fromstring` is deprecated~~ (fixed)
**Resolved in Phase 8.** `prepare_fer2013.py` now uses `np.array(pixel_str.split(), dtype=np.uint8)`. No deprecation warning on NumPy 2.x. Retained as a section marker so section numbers don't shift.

### 6.8 — ImageFolder class ordering depends on alphabetical directory names
**Risk:** PyTorch `ImageFolder` auto-assigns label indices by sorting directory names alphabetically. My `EMOTIONS` list is alphabetical, so indices match. **But if someone adds a new emotion class later that isn't alphabetically at the end, all label indices shift** — and trained models would suddenly predict the wrong thing.

**Mitigation:** Either keep EMOTIONS alphabetical forever, or explicitly pass `class_to_idx={}` to ImageFolder. Document this in `data/README.md`. *(Already documented.)*

### 6.9 — The `vibechecker.db` file can get out of sync with the schema
**Risk:** If I change a model in `models.py` (add a column, rename something), the existing `vibechecker.db` file is **not automatically migrated**. Running `init_db.py` with `Base.metadata.create_all(engine)` only creates tables that don't exist — it doesn't alter existing ones.

**When this matters:** Every teammate needs to delete their local `vibechecker.db` and re-run `init_db.py + seed_db.py` after a schema change.

**Solution for later:** Set up Alembic migrations when the project matures. For a class project, just re-seed.

---

## 7. What's done

### Database layer
- [x] Schema design (users, checkins, emotion_results with `is_latest`, seasonal_summaries)
- [x] All CRUD helpers (create_user, create_checkin, store_emotion_result)
- [x] Query helpers (get_user_by_id, get_user_by_email, get_user_history)
- [x] Aggregate helpers (get_emotion_counts, get_dominant_emotion, get_average_scores)
- [x] Trend helper (get_weekly_sadness_trend) for frontend charts
- [x] History helper (get_emotion_result_history) for re-inference comparison
- [x] Seasonal summary auto-computation with depression_flag
- [x] Depression threshold as a named constant
- [x] Bcrypt enforcement in create_user
- [x] `.to_dict()` on all models (API-ready)
- [x] Indexes on all common query paths
- [x] init_db.py + seed_db.py + image storage dir creation
- [x] Comments cleaned up for readability
- [x] `get_season(month)` extracted into `db.py` — single source of truth for seed + backend
- [x] `is_latest` flag usage documented in `database/README.md` (heads-up for Zem on aggregate queries)

### Data / ML Ops
- [x] FER2013 downloaded and symlinked into `data/raw/`
- [x] `prepare_fer2013.py` script handling the full CSV → ImageFolder + npz pipeline
- [x] 6-class dataset (disgust dropped)
- [x] Standard FER2013 splits (28,273 / 3,533 / 3,534)
- [x] `data/README.md` with label mapping and usage examples
- [x] Deprecated `np.fromstring` replaced with `np.array(s.split(), ...)` in `prepare_fer2013.py`

### Documentation
- [x] Module docstrings on every file
- [x] `data/README.md`
- [x] `database/README.md`
- [x] This handoff document

---

## 8. What's blocked (waiting on teammates)

### Blocked by Aaron (CV)
- **MediaPipe output format specification.** I need to know exactly what shape/dtype Aaron's pipeline emits so I can write a preprocessing bridge between his code and the ML model's input layer.

### Blocked by Henry + Aaron (ML)
- **Model input shape confirmation.** If they want something other than raw 48×48 grayscale (e.g., upscaled 224×224 RGB), I may need to add a resize step to the training data pipeline.
- **Class imbalance strategy — their call.** Already told them to use `WeightedRandomSampler` or class-weighted loss if they need it. Waiting to see if they push back and ask me to pre-balance on disk.
- **Output format confirmation.** Logits or softmax probabilities? Affects whether Zem needs to apply softmax before calling `store_emotion_result`.

### Blocked by Zem (backend)
- **Image cleanup strategy on account deletion** — see section 6.6.
- **Chart data shape confirmation** — whether `get_weekly_sadness_trend()` needs to return a different format for the chart library the frontend picks.

### Blocked by vexonik + Nick (frontend)
- **Chart library choice** — affects ideal data shapes (if any change is needed).
- **Dashboard refresh cadence** — affects whether I build a scheduled summary job.
- **Timezone display preference** — affects the weekly grouping.

---

## 9. What to do when teammates catch up

### When Zem stands up his first API route
- [ ] **Write an integration test** that: creates a user, creates a check-in through Zem's endpoint, stores an emotion result, queries history, and updates the seasonal summary. End-to-end smoke test.
- [ ] **Verify the `image_path` string format** Zem uses matches what I store (`storage/images/{user_id}/{YYYY-MM-DD}.jpg`) or update my convention to match his.
- [x] ~~Extract `get_season()` into `db.py`~~ — done in Phase 8. Zem imports via `from database.db import get_season`.
- [ ] **Discuss image cleanup strategy** (gotcha 6.6) and implement the chosen approach:
  - If cascade delete: add `ondelete="CASCADE"` to ForeignKey columns and add filesystem cleanup in a user-delete helper
  - If soft delete: add `is_deleted` columns to users/checkins

### When Aaron defines his MediaPipe output format
- [ ] **Write a preprocessing bridge function** in either `cv/` or `ml/` that converts Aaron's output to the ML model's input tensor. Location depends on team preference — I'd suggest `cv/to_model_input.py`.
- [ ] **Test the bridge end-to-end** with a sample image: image → Aaron's preprocessing → my bridge → model input shape validation.

### When Henry + Aaron finalize model input shape
- [ ] **If they want 224×224 RGB upscaled:** add a `--target-size` flag to `prepare_fer2013.py` and regenerate the PNGs at that size. Keep 48×48 as default since that's FER2013's native resolution.
- [ ] **If they want class weights pre-computed:** add a `--compute-weights` flag that outputs `data/processed/class_weights.json` with inverse-frequency weights.

### When Henry + Aaron deliver a trained model checkpoint
- [ ] **Verify `store_emotion_result()` gets called correctly from their inference code** — correct label order, confidence in 0-1 range, all 6 emotions in `scores`.
- [ ] **Help set up experiment tracking** (Phase 4 of Role 6). Recommended minimum: a simple CSV log at `ml/experiments.csv` with columns `model_version, train_acc, val_acc, test_acc, hyperparams_json, date`. Can upgrade to MLflow / W&B if the team wants.
- [ ] **Run `update_seasonal_summary()` against real predictions** to sanity-check the 0.3 depression threshold — might need tuning once we see real model outputs.

### When vexonik + Nick start building charts
- [ ] **Ask which chart library they picked** and reshape query outputs if needed.
- [ ] **Add a daily granularity query** if weekly is too coarse for their line chart. Easy — swap `%Y-%W` for `%Y-%m-%d` in `get_weekly_sadness_trend`.
- [ ] **Add a "top N days" query** for callout cards ("Your saddest day was Jan 14th") if they want it.
- [ ] **Decide on refresh cadence** (gotcha 6.5 in role guide) and either:
  - Call `update_seasonal_summary()` on every dashboard load (simple, wasteful)
  - Or schedule it via a cron-style job (more complex, efficient)

### Ongoing (my responsibility)
- [x] ~~Fix deprecated `np.fromstring`~~ — done in Phase 8.
- [ ] **Replace seed_db.py password placeholders with real bcrypt hashes** when backend auth is ready.
- [ ] **Add edge-case handling:** duplicate daily submissions, missing images, timezone for "today".
- [ ] **Document the full data flow end-to-end** once integration is working — replace the ASCII diagram in section 2 with a real sequence diagram or screenshot.

---

## Quick-reference: commands every teammate should know

```bash
# One-time setup (each teammate does this on their machine)
pip install -r requirements.txt
cd database
python init_db.py     # creates vibechecker.db + storage/images/
python seed_db.py     # populates with fake users + check-ins

# FER2013 data prep (ML team only)
# 1. Download from Kaggle: https://www.kaggle.com/datasets/deadskull7/fer2013
# 2. Put CSV at data/raw/fer2013.csv
# 3. Run:
python data/prepare_fer2013.py              # full export (PNGs + npz)
python data/prepare_fer2013.py --no-images  # npz only (faster)

# Nuke and rebuild DB (after schema changes)
rm database/vibechecker.db
cd database && python init_db.py && python seed_db.py
```

---

## Contact

If anything in this doc is unclear or stops matching the code, ping Javaya directly. Questions about specific functions are faster than guesses.
