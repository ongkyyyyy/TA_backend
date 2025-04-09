from flask import Blueprint # type: ignore
from controllers.revenue_controller import RevenueController
from models.revenue import RevenueDB

def create_revenue_blueprint(app):
    revenue_bp = Blueprint("revenue", __name__)
    db = RevenueDB(app)
    controller = RevenueController(db)

    revenue_bp.add_url_rule("/revenues", "get_revenues", controller.get_revenues, methods=["GET"])
    revenue_bp.add_url_rule("/revenues/<revenue_id>", "get_revenue", controller.get_revenue, methods=["GET"])
    revenue_bp.add_url_rule("/revenues", "create_revenue", controller.create_revenue, methods=["POST"])
    revenue_bp.add_url_rule("/revenues/<revenue_id>", "edit_revenue", controller.edit_revenue, methods=["PUT"])
    revenue_bp.add_url_rule("/revenues/<revenue_id>", "remove_revenue", controller.remove_revenue, methods=["DELETE"])

    return revenue_bp
