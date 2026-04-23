from flask import Blueprint, jsonify
from database.db import get_user_history

history_routes = Blueprint("history", __name__)

@history_routes.route("/<user_id>", methods=["GET"])
def history(user_id):
    history = get_user_history(user_id)
    return jsonify(history)