from flask import Blueprint, request, jsonify
import subprocess
import os
from controllers.review_controller import save_reviews, get_all_reviews

def create_review_blueprint(app):
    review_bp = Blueprint("reviews", __name__)

    @review_bp.route("/traveloka_scrape", methods=["POST"])
    def scrape_traveloka_reviews():
        data = request.json
        hotel_url = data.get("url")

        if not hotel_url:
            return jsonify({"error": "Hotel URL is required"}), 400
        
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        SCRIPT_PATH = os.path.join(backend_dir, "scraper", "scrape_reviews.js")

        if not os.path.exists(SCRIPT_PATH):
            return jsonify({"error": f"Script not found at {SCRIPT_PATH}"}), 500

        try:
            result = subprocess.run(
                ["node", SCRIPT_PATH, hotel_url],
                text=True,
                capture_output=True
            )
            if result.returncode != 0:
                return jsonify({"error": result.stderr}), 500

            return jsonify({"message": "Scraping triggered successfully", "output": result.stdout})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        
    @review_bp.route("/ticketcom_scrape", methods=["POST"])
    def scrape_ticketcom_reviews():
        data = request.json
        hotel_url = data.get("url")

        if not hotel_url:
            return jsonify({"error": "Hotel URL is required"}), 400
        
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        SCRIPT_PATH = os.path.join(backend_dir, "scraper", "ticketcom_scrape_reviews.js")

        if not os.path.exists(SCRIPT_PATH):
            return jsonify({"error": f"Script not found at {SCRIPT_PATH}"}), 500

        try:
            result = subprocess.run(
                ["node", SCRIPT_PATH, hotel_url],
                text=True,
                capture_output=True
            )
            if result.returncode != 0:
                return jsonify({"error": result.stderr}), 500

            return jsonify({"message": "Scraping triggered successfully", "output": result.stdout})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @review_bp.route("/reviews", methods=["POST"])
    def receive_reviews():
        data = request.json.get("reviews", [])
        response = save_reviews(data)
        return jsonify(response), response["status"]

    @review_bp.route("/reviews", methods=["GET"])
    def fetch_reviews():
        reviews = get_all_reviews()
        return jsonify({"reviews": reviews})

    return review_bp
