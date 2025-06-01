from flask import Blueprint  # type: ignore
from controllers.revenue_controller import RevenueController
from models.revenue import RevenueDB
from controllers.middleware.auth_middleware import token_required

def create_revenue_blueprint(app):
    revenue_bp = Blueprint("revenue", __name__)
    db = RevenueDB()
    controller = RevenueController(db)

    revenue_bp.add_url_rule("/revenues", "get_revenues", token_required(controller.get_revenues), methods=["GET"])
    revenue_bp.add_url_rule("/revenues", "create_revenue", token_required(controller.create_revenue), methods=["POST"])
    revenue_bp.add_url_rule("/revenues/<revenue_id>", "edit_revenue", token_required(controller.edit_revenue), methods=["PUT"])
    revenue_bp.add_url_rule("/revenues/<revenue_id>", "remove_revenue", token_required(controller.remove_revenue), methods=["DELETE"])
    
    return revenue_bp
