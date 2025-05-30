from flask import Blueprint # type: ignore
from controllers.diagram_controller import get_revenue_sentiment_diagram
from controllers.middleware.auth_middleware import token_required

def create_diagram_blueprint(app):
    diagram_bp = Blueprint("diagrams", __name__)

    diagram_bp.add_url_rule(
        "/diagram/revenue-sentiment",
        "diagram_revenue_sentiment",
        token_required(get_revenue_sentiment_diagram),
        methods=["GET"]
    )

    return diagram_bp