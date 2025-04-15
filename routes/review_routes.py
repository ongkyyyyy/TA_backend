from flask import Blueprint, request, jsonify # type: ignore
from datetime import datetime
import subprocess
import os
from controllers.review_controller import save_reviews, get_all_reviews
from sentiment_analysis.sentiment_analysis import analyze_sentiment
from models.hotels import hotels_collection
from bson import ObjectId 

def create_review_blueprint(app):
    review_bp = Blueprint("reviews", __name__)
    
    @review_bp.route("/scrape/<source>", methods=["POST"])
    def scrape_reviews(source):
        data = request.json
        hotel_id = data.get("hotel_id")

        if not hotel_id:
            return jsonify({"error": "hotel_id is required"}), 400
        
        try:
            hotel_id_obj = ObjectId(hotel_id)
        except Exception as e:
            return jsonify({"error": f"Invalid hotel_id format: {str(e)}"}), 400

        hotel = hotels_collection.find_one({"_id": ObjectId(hotel_id_obj)})
        if not hotel:
            return jsonify({"error": "Hotel not found"}), 404

        source_map = {
            "traveloka": hotel.get("traveloka_link"),
            "ticketcom": hotel.get("ticketcom_link"),
            "agoda": hotel.get("agoda_link"),
            "tripcom": hotel.get("tripcom_link"),
        }

        hotel_url = source_map.get(source)
        if not hotel_url:
            return jsonify({"error": f"{source} link is not available for this hotel"}), 400

        script_map = {
            "traveloka": "scrape_reviews.js",
            "ticketcom": "ticketcom_scrape_reviews.js",
            "agoda": "agoda_scrape_reviews.js",
            "tripcom": "tripcom_scrape_reviews.js",
        }

        script_file = script_map.get(source)
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        script_path = os.path.join(backend_dir, "scraper", script_file)

        if not os.path.exists(script_path):
            return jsonify({"error": f"Script not found at {script_path}"}), 500

        try:
            result = subprocess.run(
                ["node", script_path, hotel_url, hotel_id],
                text=True,
                capture_output=True,
                encoding='utf-8',
                errors='replace'
            )
            if result.returncode != 0:
                return jsonify({"error": result.stderr}), 500

            return jsonify({
                "message": f"{source} scraping completed. Data has been sent to /reviews endpoint.",
                "stdout": result.stdout
            }), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

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
        data = request.json
        reviews = data.get("reviews", [])
        hotel_id = data.get("hotel_id") 

        result = save_reviews(reviews, hotel_id)

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
