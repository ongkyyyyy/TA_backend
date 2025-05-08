from flask import Blueprint, request, jsonify # type: ignore
from datetime import datetime
import subprocess
import os
from controllers.review_controller import save_reviews, get_all_reviews
from controllers.scrape_log_controller import ScrapeLogController
from sentiment_analysis.sentiment_analysis import analyze_sentiment
from models.hotels import hotels_collection
from bson import ObjectId  # type: ignore
from flask import current_app

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

    @review_bp.route("/reviews", methods=["POST"])
    def receive_reviews():
        data = request.json
        reviews = data.get("reviews", [])
        hotel_id = data.get("hotel_id")
        ota = data.get("ota", "unknown")

        now = datetime.utcnow()

        scrape_log_data = {
            "hotel_id": hotel_id,
            "ota": ota,
            "scrape_date": now.strftime("%d-%m-%y"),
            "timestamp": now,
            "total_reviews": len(reviews),
            "note": "",  # Add a note field initially
        }

        db = current_app.scrape_log_db
        log_controller = ScrapeLogController(db)

        try:
            result = save_reviews(reviews, hotel_id)
            inserted_ids = result.get("inserted_ids", [])

            if inserted_ids:
                # Success, reviews inserted
                scrape_log_data["status"] = "success"
                scrape_log_data["total_reviews"] = len(inserted_ids)
                scrape_log_data["note"] = f"Scraping successful, {len(inserted_ids)} new reviews inserted."
            else:
                # Success, but no new reviews inserted
                scrape_log_data["status"] = "success"
                scrape_log_data["note"] = "Scraping succeeded but no new reviews were inserted (possibly duplicates)."

            with current_app.test_request_context(json=scrape_log_data):
                log_controller.create_scrape_log()

            return jsonify({
                "message": result["message"],
                "inserted_ids": [str(_id) for _id in inserted_ids],
                "status": result["status"],
                "note": scrape_log_data["note"]
            }), result["status"]

        except Exception as e:
            scrape_log_data["status"] = "error"
            scrape_log_data["note"] = f"Error occurred: {str(e)}"

            with current_app.test_request_context(json=scrape_log_data):
                log_controller.create_scrape_log()

            return jsonify({"message": "Internal server error", "error": str(e), "note": scrape_log_data["note"]}), 500
            
    @review_bp.route("/reviews", methods=["GET"])
    def fetch_reviews():
        reviews = get_all_reviews()
        return jsonify({"reviews": reviews})

    return review_bp
