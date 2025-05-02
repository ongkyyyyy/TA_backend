from flask import Blueprint  # type: ignore
from controllers.diagram_controller import get_revenue_sentiment_diagram

def create_diagram_blueprint(app):
    diagram_bp = Blueprint("diagrams", __name__)

    diagram_bp.add_url_rule(
        "/diagram/revenue-sentiment",
        "diagram_revenue_sentiment",
        get_revenue_sentiment_diagram,
        methods=["GET"]
    )

    return diagram_bp
