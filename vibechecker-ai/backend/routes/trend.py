from flask import Blueprint, jsonify, request
from database.db import get_db
from services.trend_analysis import analyze_trend

trend_routes = Blueprint("trend", __name__)

@trend_routes.route("/<int:user_id>", methods=["GET"])
def get_trend(user_id):
    """
    Fetch the emotion trend analysis for a specific user.
    Optional query parameter: ?year=YYYY
    """
    year_param = request.args.get("year")
    year = int(year_param) if year_param and year_param.isdigit() else None
    
    db = get_db()
    try:
        result = analyze_trend(user_id, db, year=year)
        
        # If scores_analyzed is 0, return 404
        if result.get("scores_analyzed", 0) == 0:
            return jsonify({"error": "No vibe scores found for this user."}), 404
            
        return jsonify(result), 200
    finally:
        db.close()
