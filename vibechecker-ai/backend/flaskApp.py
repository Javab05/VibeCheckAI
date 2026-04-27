import sys, os
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add vibechecker-ai to path so database and ml folders can be found
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from flask import Flask, request, jsonify
from flask_cors import CORS
from routes.auth import auth_routes
from routes.checkin import checkin_routes
from routes.history import history_routes
from routes.trend import trend_routes
from services.inference import run_inference
from database.db import create_checkin, store_emotion_result, get_season, update_seasonal_summary, set_face_features
from PIL import Image

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'storage', 'images')

app.register_blueprint(auth_routes, url_prefix="/auth")
app.register_blueprint(checkin_routes, url_prefix="/checkin")
app.register_blueprint(history_routes, url_prefix="/history")
app.register_blueprint(trend_routes, url_prefix="/trend")

@app.route("/inference", methods=["POST"])
def inference():
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400
    
    user_id = request.form.get("user_id")
    if not user_id:
        return jsonify({"error": "No user_id provided"}), 400

    file = request.files["image"]
    
    # Save image to storage
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    filename = f"{uuid.uuid4()}.jpg"
    image_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(image_path)

    # Get current date info for season
    now = datetime.now(timezone.utc)
    captured_at = now.isoformat()
    season = get_season(now.month)
    season_year = now.year

    try:
        # Save check-in to DB
        checkin = create_checkin(
            user_id=int(user_id),
            image_path=image_path,
            captured_at=captured_at,
            season=season,
            season_year=season_year,
        )

        # Run ML model
        result = run_inference(image_path)
        
        # Store result in DB
        scores = result.get("scores", {})
        if "vibe_score" in result:
            scores["vibe_score"] = result["vibe_score"]

        store_emotion_result(
            checkin_id=checkin.checkin_id,
            predicted_emotion=result["emotion"],
            confidence=result["confidence"],
            scores=scores,
            model_version=result["model_version"],
        )

        # Persist derived facial features
        set_face_features(
            checkin_id=checkin.checkin_id,
            ear=result.get("ear"),
            mar=result.get("mar"),
            brow_raise=result.get("brow_raise"),
            mouth_angle=result.get("mouth_angle"),
        )

        # Update seasonal summary
        update_seasonal_summary(int(user_id), season, season_year)

        return jsonify({
            "checkin_id": checkin.checkin_id,
            "vibe_score": result.get("vibe_score"),
            "emotion": result.get("emotion"),
            "dominant_emotion": result.get("dominant_emotion"),
            "confidence": result.get("confidence"),
            "scores": result.get("scores"),
            "model_version": result.get("model_version")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/")
def home():
    return {
        "status": "ok",
        "service": "VibeCheckAI backend",
        "message": "API is running"
    }

@app.route("/ping")
def ping():
    return {"status": "ok"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)