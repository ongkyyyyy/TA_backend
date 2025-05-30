from flask import Blueprint, request, jsonify  # type: ignore
from controllers.sentiments_controller import get_all_sentiments

def create_sentiment_blueprint(app):
    sentiments_bp = Blueprint("sentiments", __name__)

    @sentiments_bp.route("/sentiments", methods=["GET"])
    def get_sentiments():
        sentiments = get_all_sentiments()
        return jsonify({"reviews": sentiments})

    return sentiments_bp
