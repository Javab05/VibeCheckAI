# VibeCheckAI — API Contract

**Owner:** Javaya (Role 3 — Database) + Zem (Role 1 — Backend)
**Consumers:** Carlo (Role 2 — Frontend), Henry/Aaron (Role 5 — ML)
**Status:** Live. Frontend ↔ backend integration shipped via PRs #8–#11.

This is the source of truth for every request/response shape between the Expo
frontend and the Flask backend. If the frontend or backend disagrees with a
shape here, fix the code — don't re-edit this doc without a team discussion.

---

## Conventions

- **Base URL (dev):** the Expo client auto-resolves `http://<LAN-IP>:5000` from
  `Constants.expoConfig.hostUri` (see `frontend/constants/api.ts`). Flask is
  bound to `0.0.0.0:5000` so phones on the same Wi-Fi can reach it.
- **Content type:** `application/json` for every endpoint except
  `POST /checkin/upload`, which is `multipart/form-data`.
- **Confidence + scores:** floats in the range `0.0–1.0`. Frontend converts
  to 0–100 for display.
- **Vibe score:** 0–100 integer-ish float. Computed server-side as a
  weighted sum of the softmax probabilities (`happy=100, surprise=70,
  neutral=50, fear=30, sad=20, angry=10, disgust=5`). Higher = more positive vibe.
- **Timestamps:** ISO-8601 strings in UTC (e.g. `"2026-01-15T14:32:11+00:00"`).
- **Seasons:** one of `"winter"`, `"spring"`, `"summer"`, `"fall"`.
  `season_year` is the calendar year the season *ends in* — December 2025 →
  February 2026 is all `season="winter", season_year=2026`.
- **Emotions:** the model currently emits **7 classes** —
  `angry`, `disgust`, `fear`, `happy`, `neutral`, `sad`, `surprise`.
  ⚠️ This conflicts with the team's prior decision to drop disgust; pending
  resolution between Henry's training set and Javaya's `prepare_fer2013.py`.
- **Errors:** JSON body `{"error": "human message"}` with a non-2xx status.

---

## Endpoints

### `GET /` — health root
**Response 200**
```json
{ "status": "ok", "service": "VibeCheckAI backend", "message": "API is running" }
```

### `GET /ping` — simple health
**Response 200**
```json
{ "status": "ok" }
```

---

### `POST /auth/register`
Create a new user. Password is hashed server-side with bcrypt before storage.

**Request**
```json
{
  "username": "javaya",
  "email": "javaya@example.com",
  "password": "plaintext-password"
}
```

**Response 201**
```json
{ "message": "User created", "user_id": 1 }
```

**Errors**
- `400 {"error": "Missing Fields"}` — any of username/email/password absent.
- `409 {"error": "Email already registered"}` — *to be added by Zem; currently raises 500.*

---

### `POST /auth/login`
Verify credentials.

**Request**
```json
{ "email": "javaya@example.com", "password": "plaintext-password" }
```

**Response 200**
```json
{ "message": "Login Successful", "user_id": 1 }
```

**Errors**
- `400 {"error": "Missing Fields"}`
- `401 {"error": "Invalid Password"}`
- `404 {"error": "User not found"}`

---

### `POST /checkin/upload`
Upload a daily selfie, run multimodal inference, and persist the result.

**Request** (`multipart/form-data`)
| field     | type | notes                          |
|-----------|------|--------------------------------|
| `user_id` | str  | from login/register response   |
| `image`   | file | JPEG/PNG, front-facing selfie  |

**Response 200**
```json
{
  "checkin_id": 42,
  "emotion": "sad",
  "confidence": 0.62,
  "scores": {
    "angry":    0.04,
    "disgust":  0.00,
    "fear":     0.11,
    "happy":    0.05,
    "neutral":  0.14,
    "sad":      0.62,
    "surprise": 0.04
  },
  "model_version": "multimodal_v1.0",
  "vibe_score": 32.7
}
```

**Errors**
- `400 {"error": "No image provided"}`
- `400 {"error": "No user_id provided"}`
- `400 {"error": "No face detected in image."}` — MediaPipe couldn't find a face
- `500` — inference failure

**Server pipeline**
1. Save the file to `storage/images/<uuid>.jpg`.
2. `cv.processor.extract_face(image)` → `(face_image_48x48_grayscale, landmarks_478x3)` or `None`.
3. `ml.inference_multimodal.MultiModalPredictor.predict()` — fuses the cropped image with 10 derived landmark features (eye-aspect ratio, mouth-aspect ratio, head tilt, face symmetry, etc.) and returns the dict above.
4. `db.create_checkin(user_id, image_path, captured_at, season, season_year)` — `season`/`season_year` derived from `datetime.now(UTC)` via `db.get_season()`.
5. `db.store_emotion_result(checkin_id, emotion, confidence, scores, model_version)` — old predictions for the same checkin get demoted to `is_latest=0`.
6. `db.update_seasonal_summary(user_id, season, season_year)` — recomputes aggregates.

---

### `GET /history/<user_id>?season=<season>&season_year=<year>`
All check-ins for a user in one season, with the latest prediction flattened onto each row.

**Query params** (both optional — default to current season/year)
- `season` — one of `winter|spring|summer|fall`
- `season_year` — int

**Response 200**
```json
[
  {
    "checkin_id": 42,
    "captured_at": "2026-01-15T14:32:11+00:00",
    "season": "winter",
    "emotion": "sad",
    "confidence": 0.62,
    "scores": { "angry": 0.04, "disgust": 0.00, "fear": 0.11, "happy": 0.05, "neutral": 0.14, "sad": 0.62, "surprise": 0.04 }
  }
]
```

Empty list `[]` if the user has no check-ins for that season.
`emotion`/`confidence`/`scores` will be `null` for a check-in whose inference failed.

> ⚠️ The shape was historically nested under `latest_result` (matching `Checkin.to_dict()` + `EmotionResult.to_dict()`). The current implementation flattens for frontend convenience. If anyone adds new fields, mirror them at the top level — don't reintroduce the wrapper without coordinating with Carlo.

---

### `GET /history/<user_id>/trend?season=<season>&season_year=<year>` *(proposed — not yet routed)*
Week-by-week average sadness for the trend chart.
Backed by `db.get_weekly_sadness_trend()`.

**Response 200**
```json
[
  { "week": "2026-01", "avg_sadness": 0.23 },
  { "week": "2026-02", "avg_sadness": 0.31 }
]
```

Week key format is `YYYY-WW` (ISO year + week number). Zem: add the route when the dashboard needs it.

---

### `GET /history/<user_id>/summary?season=<season>&season_year=<year>` *(proposed — not yet routed)*
Aggregated seasonal summary. Backed by `db.update_seasonal_summary()` (already invoked on every check-in upload, so the row exists).

**Response 200**
```json
{
  "summary_id": 3,
  "user_id": 1,
  "season": "winter",
  "season_year": 2026,
  "total_checkins": 78,
  "avg_happiness": 0.18,
  "avg_sadness": 0.34,
  "dominant_emotion": "sad",
  "depression_flag": 1,
  "updated_at": "2026-02-28T23:59:00+00:00"
}
```

`depression_flag` is 1 iff `avg_sadness > DEPRESSION_THRESHOLD` (currently `0.3`, see `db.py`).

---

## Frontend ↔ Backend shape mapping

The frontend's UI fields are derived from the backend response. Mapping:

| UI field                     | Source                                                              |
|------------------------------|---------------------------------------------------------------------|
| `vibeScore` (0–100)          | response `vibe_score` directly (already 0–100)                      |
| `sadScore` (0–100)           | `Math.round(scores.sad * 100)` — if you want to keep showing it     |
| `confidence` (0–100)         | `Math.round(confidence * 100)`                                      |
| `level`                      | derived from `vibe_score` or `sadScore` thresholds (UI's call)      |
| `levelColor`                 | derived from `level`                                                |
| `signals`                    | not provided. Drop, or derive client-side from top-3 non-dominant emotions. |

**`vibe_score` is the headline number** the frontend should lean on now that
the multimodal model produces it directly. It's already in 0–100 space and
incorporates all 7 emotion probabilities, so it's a richer signal than `scores.sad` alone.

---

## CORS

Wide-open in dev:
```python
from flask_cors import CORS
app = Flask(__name__)
CORS(app)
```
Tighten to specific origins before shipping.

---

## Known bugs

✅ All 6 backend route bugs from the original draft of this doc are fixed
(PRs #8–#11). Tests in `tests/test_integration.py` need to be reconciled
with the new response shapes — they currently encode the old assumptions.

**Open questions / pending decisions:**
- **Disgust class.** Model still emits 7 classes including `disgust`, but the prep
  pipeline (`data/prepare_fer2013.py`) drops it. Henry to confirm direction.
- **Landmark persistence.** `cv.processor.extract_face()` produces 478 raw
  landmarks per face but the pipeline only consumes 10 derived features and
  discards the rest. Aaron + Javaya to decide whether to add a `face_landmarks`
  table for re-analysis purposes.
- **Email-collision register.** `/auth/register` doesn't yet return 409 on
  duplicate emails — it raises a 500 from the unique-constraint violation.

---

## Versioning

No `/v1/` prefix yet — pre-alpha. When we ship, freeze this doc as `api-contract-v1.md`
and any breaking change gets `/v2/` routes in parallel.
