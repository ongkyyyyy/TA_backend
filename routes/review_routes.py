from flask import Blueprint, request, jsonify # type: ignore
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
                errors='replace',
                check=True
            )
            if result.returncode != 0:
                return jsonify({"error": result.stderr}), 500
            
            with open("agoda_scrape_stdout.log", "w", encoding="utf-8") as f_out:
                f_out.write(result.stdout)
            with open("agoda_scrape_stderr.log", "w", encoding="utf-8") as f_err:
                f_err.write(result.stderr)

            print("🟢 STDOUT:\n", result.stdout)
            print("🔴 STDERR:\n", result.stderr)


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
        result = save_reviews(data)

        if not result.get("inserted_ids"):
            return jsonify({"message": result["message"]}), result["status"]

        return jsonify({
            "message": result["message"],
            "inserted_ids": [str(_id) for _id in result["inserted_ids"]],
            "status": result["status"]
        }), result["status"]
            
    @review_bp.route("/reviews", methods=["GET"])
    def fetch_reviews():
        reviews = get_all_reviews()
        return jsonify({"reviews": reviews})

    return review_bp
