from flask import Blueprint, request, jsonify
from datetime import datetime
import subprocess
import os
from controllers.review_controller import save_reviews, get_all_reviews
from sentiment_analysis.sentiment_analysis import analyze_sentiment

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
                capture_output=True,
                encoding='utf-8',
                errors='replace'  
            )
            if result.returncode != 0:
                return jsonify({"error": result.stderr}), 500

            return jsonify({"message": "Traveloka scraping triggered successfully", "output": result.stdout})
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
                capture_output=True,
                encoding='utf-8',
                errors='replace'  
            )
            if result.returncode != 0:
                return jsonify({"error": result.stderr}), 500

            return jsonify({"message": "Ticket.com scraping triggered successfully", "output": result.stdout})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        
    @review_bp.route("/agoda_scrape", methods=["POST"])
    def scrape_agoda_reviews():
        data = request.json
        hotel_url = data.get("url")

        if not hotel_url:
            return jsonify({"error": "Hotel URL is required"}), 400
        
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        SCRIPT_PATH = os.path.join(backend_dir, "scraper", "agoda_scrape_reviews.js")

        if not os.path.exists(SCRIPT_PATH):
            return jsonify({"error": f"Script not found at {SCRIPT_PATH}"}), 500

        try:
            result = subprocess.run(
                ["node", SCRIPT_PATH, hotel_url],
                text=True,
                capture_output=True,
                encoding='utf-8',
                errors='replace'  
            )
            if result.returncode != 0:
                return jsonify({"error": result.stderr}), 500

            return jsonify({"message": "Agoda scraping triggered successfully", "output": result.stdout})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        
    @review_bp.route("/tripcom_scrape", methods=["POST"])
    def scrape_tripcom_reviews():
        data = request.json
        hotel_url = data.get("url")

        if not hotel_url:
            return jsonify({"error": "Hotel URL is required"}), 400
        
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        SCRIPT_PATH = os.path.join(backend_dir, "scraper", "tripcom_scrape_reviews.js")

        if not os.path.exists(SCRIPT_PATH):
            return jsonify({"error": f"Script not found at {SCRIPT_PATH}"}), 500

        try:
            result = subprocess.run(
                ["node", SCRIPT_PATH, hotel_url],
                text=True,
                capture_output=True,
                encoding='utf-8',
                errors='replace'  
            )
            if result.returncode != 0:
                return jsonify({"error": result.stderr}), 500

            return jsonify({"message": "Trip.com scraping triggered successfully", "output": result.stdout})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @review_bp.route("/reviews", methods=["POST"])
    def receive_reviews():
            data = request.json.get("reviews", [])
            saved_reviews = save_reviews(data)

            if not saved_reviews.get("inserted_ids"):
                return jsonify({"error": "Failed to save reviews"}), 500

            inserted_ids = saved_reviews["inserted_ids"]
            sentiment_results = []
            
            for review, review_id in zip(data, inserted_ids):
                text = review.get("comment", "")
                sentiment, pos_count, neg_count = analyze_sentiment(text)

                sentiment_results.append({
                    "review_id": str(review_id), 
                    "comment": text,
                    "sentiment": sentiment,
                    "positive_score": pos_count,
                    "negative_score": neg_count,
                    "created_at": datetime.utcnow()
                })

            return jsonify({
                "message": "Reviews and sentiment analysis processed successfully",
                "sentiment_results": sentiment_results,
                "status": 201
            }), 201
            
    @review_bp.route("/reviews", methods=["GET"])
    def fetch_reviews():
        reviews = get_all_reviews()
        return jsonify({"reviews": reviews})

    return review_bp
