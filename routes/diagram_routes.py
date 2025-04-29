from flask import Blueprint  # type: ignore
from controllers.diagram_controller import get_revenue_diagram_data, get_reviews_sentiments

def create_diagram_blueprint(app):
    diagram_bp = Blueprint("diagrams", __name__)

    diagram_bp.add_url_rule(
        "/diagram/revenue/<hotel_id>", 
        "diagram_revenue", 
        get_revenue_diagram_data, 
        methods=["GET"]
    )

    diagram_bp.add_url_rule(
        "/diagram/review-sentiment/<hotel_id>", 
        "diagram_review_sentiment", 
        get_reviews_sentiments, 
        methods=["GET"]
    )

    return diagram_bp
