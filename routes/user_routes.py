from flask import Blueprint  # type: ignore
from controllers.user_controller import UserController
from models.user import Users

def create_user_blueprint(app):
    user_bp = Blueprint("users", __name__)
    db = Users(app)
    controller = UserController(db)

    user_bp.add_url_rule("/register", "register", controller.register, methods=["POST"])
    user_bp.add_url_rule("/login", "login", controller.login, methods=["POST"])
    user_bp.add_url_rule("/logout", "logout", controller.logout, methods=["POST"])

    return user_bp
