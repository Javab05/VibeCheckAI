from flask import Blueprint, request, jsonify
from database.db import create_checkin, store_emotion_result
from services.inference import run_inference

checkin_routes = Blueprint("checkin", __name__)

@checkin_routes.route("/upload", methods=["POST"])
def upload_checkin():
    file = request.files["image"]
    user_id = request.form.get("user_id")

    # Save check-in
    checkin_id = create_checkin(user_id)

    # Run ML model
    emotion = run_inference(file)

    # Store result
    store_emotion_result(checkin_id, emotion)

    return jsonify({
        "checkin_id": checkin_id,
        "emotion": emotion
    })