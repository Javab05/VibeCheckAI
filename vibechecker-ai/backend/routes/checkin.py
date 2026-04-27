import os
import uuid
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from database.db import (
    create_checkin,
    store_emotion_result,
    set_face_features,
    get_season,
    update_seasonal_summary,
)
from services.inference import run_inference

checkin_routes = Blueprint("checkin", __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', '..', 'storage', 'images')

@checkin_routes.route("/upload", methods=["POST"])
def upload_checkin():
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400

    file = request.files["image"]
    user_id = request.form.get("user_id")

    if not user_id:
        return jsonify({"error": "No user_id provided"}), 400

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

    # Save check-in to DB
    checkin = create_checkin(
        user_id=int(user_id),
        image_path=image_path,
        captured_at=captured_at,
        season=season,
        season_year=season_year,
    )

    # Run ML model
    try:
        result = run_inference(image_path)
    except Exception as e:
        # Catch inference errors (like no face detected) and return as JSON
        return jsonify({"error": str(e)}), 400

    # Store result in DB
    scores = result["scores"]
    if "vibe_score" in result:
        scores["vibe_score"] = result["vibe_score"]

    store_emotion_result(
        checkin_id=checkin.checkin_id,
        predicted_emotion=result["emotion"],
        confidence=result["confidence"],
        scores=scores,
        model_version=result["model_version"],
    )

    # Persist Aaron's CV-derived facial features (if the inference dict
    # exposes them — keys are absent until ml/inference_multimodal.py is
    # updated to surface them, in which case this is a no-op).
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
        "emotion": result["emotion"],
        "dominant_emotion": result["dominant_emotion"],
        "confidence": result["confidence"],
        "scores": result["scores"],
        "model_version": result["model_version"],
        "vibe_score": result.get("vibe_score")
    }), 200