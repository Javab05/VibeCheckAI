from flask import Blueprint, jsonify, request
from database.db import get_user_history
from datetime import datetime

history_routes = Blueprint("history", __name__)

@history_routes.route("/<user_id>", methods=["GET"])
def history(user_id):
    # Get season and year from query params or default to current
    now = datetime.now()
    season = request.args.get("season", get_current_season(now.month))
    season_year = int(request.args.get("season_year", now.year))

    checkins = get_user_history(int(user_id), season, season_year)

    return jsonify([
        {
            "checkin_id": c.checkin_id,
            "captured_at": c.captured_at,
            "season": c.season,
            "emotion": c.latest_result.predicted_emotion if c.latest_result else None,
            "confidence": c.latest_result.confidence if c.latest_result else None,
            "scores": c.latest_result.to_dict()["scores"] if c.latest_result else None,
        }
        for c in checkins
    ]), 200

def get_current_season(month):
    if month in (12, 1, 2): return "winter"
    if month in (3, 4, 5): return "spring"
    if month in (6, 7, 8): return "summer"
    return "fall"