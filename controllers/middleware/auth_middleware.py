from functools import wraps
from flask import request, jsonify
import jwt
from bson import ObjectId
from config import SECRET_KEY
from models.user import UsersDB

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(">>> token_required activated")

        # Get token from the Authorization header
        auth_header = request.headers.get("Authorization", "")
        token = None

        # Validate Bearer token format
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        else:
            return jsonify({"error": "Authorization header missing or not Bearer token"}), 401

        if not token:
            return jsonify({"error": "Token is missing"}), 401

        try:
            # Decode token
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")
            if not user_id:
                return jsonify({"error": "Invalid token payload: missing user_id"}), 401

            # Check if user exists
            user = UsersDB().collection.find_one({"_id": ObjectId(user_id)})
            if not user:
                return jsonify({"error": "User not found"}), 404

            # Attach user info to the request object
            request.user = user

        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        except Exception as e:
            return jsonify({"error": f"Token processing error: {str(e)}"}), 500

        return f(*args, **kwargs)
    return decorated_function
