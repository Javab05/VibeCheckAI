from flask import Blueprint, request, jsonify
from database.db import create_user

auth_routes = Blueprint("auth", __name__)

@auth_routes.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    user_id = create_user(username, password)

    return jsonify({"message": "User created", "user_id": user_id})