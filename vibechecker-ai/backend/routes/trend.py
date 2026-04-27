from flask import Blueprint, jsonify, abort
from database.db import get_db
from backend.services.trend_analysis import analyze_trend

trend_routes = Blueprint("trend", __name__)

@trend_routes.route("/<int:user_id>", methods=["GET"])
def get_trend(user_id):
    """
    Fetch the emotion trend analysis for a specific user.
    """
    db = get_db()
    try:
        result = analyze_trend(user_id, db)
        
        # If scores_analyzed is 0, return 404
        if result.get("scores_analyzed", 0) == 0:
            return jsonify({"error": "No vibe scores found for this user."}), 404
            
        return jsonify(result), 200
    finally:
        db.close()
