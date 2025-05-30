from functools import wraps
from flask import request, jsonify # type: ignore
import jwt # type: ignore
from bson import ObjectId # type: ignore
from config import SECRET_KEY
from models.user import users_collection  # use the shared collection

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        token = None

        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        else:
            return jsonify({"error": "Authorization header missing or not Bearer token"}), 401

        if not token:
            return jsonify({"error": "Token is missing"}), 401

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")
            if not user_id:
                return jsonify({"error": "Invalid token payload: missing user_id"}), 401

            user = users_collection.find_one({"_id": ObjectId(user_id)})
            if not user:
                return jsonify({"error": "User not found"}), 404

            request.user = user

        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        except Exception as e:
            return jsonify({"error": f"Token processing error: {str(e)}"}), 500

        return f(*args, **kwargs)
    return decorated_function
