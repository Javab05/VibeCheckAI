# VibeCheckAI — API Contract

**Owner:** Javaya (Role 3 — Database) + Zem (Role 1 — Backend)
**Consumers:** Carlo (Role 2 — Frontend), Henry/Aaron (Role 5 — ML)
**Status:** Draft. Endpoints exist but several have bugs — see § [Known Bugs](#known-bugs).

This is the source of truth for every request/response shape between the Expo
frontend and the Flask backend. If the frontend or backend disagrees with a
shape here, fix the code — don't re-edit this doc without a team discussion.

---

## Conventions

- **Base URL (dev):** `http://<LAN-IP>:5000` — e.g. `http://192.168.1.10:5000`.
  Expo runs on the phone, so `localhost` from the laptop is not reachable;
  use the machine's LAN IP. (Zem: `flask run --host 0.0.0.0` to bind all interfaces.)
- **Content type:** `application/json` for every endpoint except
  `POST /checkin/upload`, which is `multipart/form-data`.
- **Confidence + scores:** floats in the range `0.0–1.0`. (The frontend currently
  shows `0–100` — it is responsible for the ×100 conversion on display.)
- **Timestamps:** ISO-8601 strings in UTC (e.g. `"2026-01-15T14:32:11"`).
- **Seasons:** one of `"winter"`, `"spring"`, `"summer"`, `"fall"`.
  `season_year` is the calendar year the season *ends in* — December 2025 → February 2026 is all `season="winter", season_year=2026`.
- **Emotions (6 classes, disgust dropped):** `angry`, `fear`, `happy`, `neutral`, `sad`, `surprise`.
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

**Response 200**
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
- `400` — missing fields
- `401 {"error": "Invalid Password"}`
- `404 {"error": "User not found"}`

---

### `POST /checkin/upload`
Upload a daily selfie, run inference, and persist the result.

**Request** (`multipart/form-data`)
| field     | type | notes                          |
|-----------|------|--------------------------------|
| `user_id` | str  | from login response            |
| `image`   | file | JPEG/PNG, front-facing selfie  |

**Response 200**
```json
{
  "checkin_id": 42,
  "predicted_emotion": "sad",
  "confidence": 0.62,
  "scores": {
    "angry":    0.04,
    "fear":     0.11,
    "happy":    0.05,
    "neutral":  0.14,
    "sad":      0.62,
    "surprise": 0.04
  },
  "model_version": "v1.0",
  "captured_at": "2026-01-15T14:32:11",
  "season": "winter",
  "season_year": 2026
}
```

**Errors**
- `400` — missing `user_id` or `image`
- `413` — image too large (Zem: set `MAX_CONTENT_LENGTH`)
- `500` — inference failure

**Server responsibilities**
1. Save the file to `storage/images/<user_id>/<timestamp>.jpg`.
2. Call `run_inference(path)` → `(predicted_emotion, confidence, scores_dict)`.
3. `create_checkin(user_id, image_path, captured_at, season, season_year)` — derive `season`/`season_year` from `datetime.utcnow()` via `db.get_season()`.
4. `store_emotion_result(checkin_id, predicted_emotion, confidence, scores, model_version)`.
5. Return the shape above.

---

### `GET /history/<user_id>?season=<season>&season_year=<year>`
All check-ins for a user in one season, newest prediction attached.

**Query params**
- `season` — required, one of `winter|spring|summer|fall`
- `season_year` — required, int

**Response 200**
```json
[
  {
    "checkin_id": 42,
    "user_id": 1,
    "image_path": "storage/images/1/2026-01-15.jpg",
    "captured_at": "2026-01-15T14:32:11",
    "season": "winter",
    "season_year": 2026,
    "latest_result": {
      "result_id": 71,
      "checkin_id": 42,
      "predicted_emotion": "sad",
      "confidence": 0.62,
      "scores": { "angry": 0.04, "fear": 0.11, "happy": 0.05, "neutral": 0.14, "sad": 0.62, "surprise": 0.04 },
      "model_version": "v1.0",
      "is_latest": 1,
      "processed_at": "2026-01-15T14:32:12"
    }
  }
]
```

Empty list `[]` if the user has no check-ins for that season.
`latest_result` may be `null` for a check-in whose inference hasn't completed yet.

---

### `GET /history/<user_id>/trend?season=<season>&season_year=<year>` *(proposed)*
Week-by-week average sadness for the trend chart on the home screen.
Backed by `db.get_weekly_sadness_trend()`.

**Response 200**
```json
[
  { "week": "2026-01", "avg_sadness": 0.23 },
  { "week": "2026-02", "avg_sadness": 0.31 }
]
```

Week key format is `YYYY-WW` (ISO year + week number). Zem: add the route.

---

### `GET /history/<user_id>/summary?season=<season>&season_year=<year>` *(proposed)*
Aggregated seasonal summary. Backed by `db.update_seasonal_summary()`.

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
  "updated_at": "2026-02-28T23:59:00"
}
```

`depression_flag` is 1 iff `avg_sadness > DEPRESSION_THRESHOLD` (currently `0.3`, see `db.py`).

---

## Frontend ↔ Backend shape reconciliation

Carlo's `frontend/app/(tabs)/home.tsx` currently hardcodes:

```ts
const MOCK_RESULT = {
  sadScore: 62,       // 0–100
  level: 'Moderate',
  levelColor: COLORS.moodLow,
  confidence: 87,     // 0–100
  signals: [...],
};
```

Backend does **not** return any of those fields directly. The frontend must
convert the real response into UI shape locally:

| UI field      | Source                                                         |
|---------------|----------------------------------------------------------------|
| `sadScore`    | `Math.round(scores.sad * 100)`                                 |
| `confidence`  | `Math.round(confidence * 100)`                                 |
| `level`       | derived from `sadScore`: `<30 Low`, `30–60 Moderate`, `>60 High` |
| `levelColor`  | same derivation → theme color                                  |
| `signals`     | **not provided by the API.** Either: (a) drop from UI, (b) derive client-side from the top-3 non-dominant emotions, or (c) add an optional `signals: string[]` field to the response once Aaron's CV pipeline can produce them. Decide with Carlo + Aaron. |

---

## CORS

Expo dev server runs on `http://localhost:19006` (web) or a LAN URL on device.
Browser fetches from a different origin than the Flask server → preflight fails without CORS.

**Fix (Zem, in `backend/flaskApp.py`):**
```python
from flask_cors import CORS
app = Flask(__name__)
CORS(app)  # dev: wide open. Tighten before shipping.
```

`flask-cors` is in `requirements.txt` as of branch `javaya/flask-cors-integration`.

---

## Known bugs

These are blocking the integration tests in `tests/test_integration.py`.
Tracking here so Zem has one checklist.

| # | File                         | Line | Bug                                                                                      |
|---|------------------------------|------|------------------------------------------------------------------------------------------|
| 1 | `backend/routes/auth.py`     | 28   | `user_id = create_user(...)` — `create_user()` returns a `User`, not an int. Use `.user_id`. |
| 2 | `backend/routes/auth.py`     | 64   | `user.id` doesn't exist. Column is `user.user_id`.                                       |
| 3 | `backend/routes/checkin.py`  | 13   | `create_checkin(user_id)` called with 1 arg; helper needs `(user_id, image_path, captured_at, season, season_year)`. |
| 4 | `backend/routes/checkin.py`  | 19   | `store_emotion_result(checkin_id, emotion)` called with 2 args; helper needs `(checkin_id, predicted_emotion, confidence, scores, model_version)`. |
| 5 | `backend/routes/checkin.py`  | 9-10 | `file` is read from the request but never saved to disk. Needs `file.save(<path>)`.       |
| 6 | `backend/routes/history.py`  | 7    | `get_user_history(user_id)` called with 1 arg; helper needs `(user_id, season, season_year)`. Endpoint also needs to accept `?season=&season_year=` query params. |

Plus the ML-side reminder: `ml/model.py` still has 7 classes (includes disgust).
Henry needs to drop to 6 classes to match what the DB/seed and this contract assume.

---

## Versioning

No `/v1/` prefix yet — pre-alpha. When we ship, freeze this doc as `api-contract-v1.md`
and any breaking change gets `/v2/` routes in parallel.
