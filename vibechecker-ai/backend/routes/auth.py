from flask import Blueprint, request, jsonify
from database.db import create_user, get_user_by_email
import bcrypt

auth_routes = Blueprint("auth", __name__)

#-----------------------
#       Register       -
#-----------------------

@auth_routes.route("/register", methods=["POST"])
def register():
    data = request.json

    username = data.get("username")
    email = data["email"]
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({"Error": "Missing Fields"}), 400


    password_hash = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    user_id = create_user(username, email, password_hash)

    return jsonify({
        "message": "User created",
        "user_id": user_id
        })

#-----------------------
#       LOGIN          -
#-----------------------
@auth_routes.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Missing Fields"}), 400
    
    #find user in DB
    user = get_user_by_email(email)

    if not user:
        return jsonify({"error": "User not found"}), 404
    
    #Verify password
    is_valid = bcrypt.checkpw(
        password.encode("utf-8"),
        user.password_hash.encode("utf-8")
    )

    if not is_valid:
        return jsonify({"error": "Invalid Password"}), 401
    
    return jsonify({
        "message": "Login Successful",
        "user_id": user.id
    }), 200