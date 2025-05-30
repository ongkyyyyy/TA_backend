from flask import Blueprint
from controllers.review_controller import ReviewController

def create_review_blueprint(app):
    review_bp = Blueprint("reviews", __name__)
    controller = ReviewController()

    review_bp.add_url_rule("/scrape/<source>", view_func=controller.scrape_reviews, methods=["POST"])
    review_bp.add_url_rule("/reviews", view_func=controller.receive_reviews, methods=["POST"])
    review_bp.add_url_rule("/reviews", view_func=controller.fetch_reviews, methods=["GET"])

    return review_bp
