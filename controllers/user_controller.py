import jwt
import datetime
from flask import request, jsonify  # type: ignore
from werkzeug.security import generate_password_hash, check_password_hash  # type: ignore
from bson import ObjectId
from config import SECRET_KEY

class UserController:
    def __init__(self, db):
        self.db = db

    def register(self):
        data = request.json
        if not data.get("username") or not data.get("password"):
            return jsonify({"error": "Username and password are required"}), 400

        if self.db.collection.find_one({"username": data["username"]}):
            return jsonify({"error": "Username already exists"}), 409

        hashed_pw = generate_password_hash(data["password"])
        user_id = self.db.collection.insert_one({
            "username": data["username"],
            "password": hashed_pw
        }).inserted_id

        return jsonify({"message": "User registered", "id": str(user_id)}), 201

    def login(self):
        data = request.json
        user = self.db.collection.find_one({"username": data.get("username")})
        if not user or not check_password_hash(user["password"], data.get("password", "")):
            return jsonify({"error": "Invalid username or password"}), 401

        token = jwt.encode({
            "user_id": str(user["_id"]),
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, SECRET_KEY, algorithm="HS256")

        return jsonify({"token": token}), 200

    def logout(self):
        # Token removal is client-side
        return jsonify({"message": "Logged out successfully"}), 200
