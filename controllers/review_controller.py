import os
import subprocess
from bson import ObjectId # type: ignore
from flask import request, jsonify, current_app # type: ignore
from datetime import datetime
from models.hotels import Hotels
from models.review import Reviews
from controllers.scrape_log_controller import ScrapeLogController
from sentiment_analysis.sentiment_analysis import analyze_sentiment
from controllers.sentiments_controller import save_sentiment_analysis
from langdetect import detect, LangDetectException # type: ignore
import subprocess
import re
import requests # type: ignore

def prepare_unicode_friendly_regex(text):
    safe_text = re.escape(text)
    safe_text = safe_text.replace('', '[\u200B-\u200D\uFEFF]?')
    return re.compile(safe_text, re.IGNORECASE)

class ReviewController:
    def __init__(self):
        self.hotels_collection = Hotels().collection
        self.reviews_collection = Reviews().collection
    
    def save_reviews(self, reviews, hotel_id=None):
        if not reviews:
            return {"message": "No reviews to save", "status": 400, "inserted_ids": []}

        filters = [{
            "username": r["username"],
            "comment": r["comment"],
            "timestamp": r["timestamp"],
            "hotel_name": r.get("hotel_name", ""),
            "OTA": r["OTA"]
        } for r in reviews]

        existing = self.reviews_collection.find({"$or": filters})
        existing_keys = {
            f"{r['username']}-{r['comment']}-{r['timestamp']}-{r['hotel_name']}-{r['OTA']}"
            for r in existing
        }

        new_reviews = []
        non_id_count = 0

        for r in reviews:
            key = f"{r['username']}-{r['comment']}-{r['timestamp']}-{r['hotel_name']}-{r['OTA']}"
            if key not in existing_keys:
                try:
                    if detect(r.get("comment", "")) != 'id':
                        non_id_count += 1
                        continue
                except LangDetectException:
                    non_id_count += 1
                    continue

                if hotel_id:
                    r["hotel_id"] = ObjectId(hotel_id)
                new_reviews.append(r)

        if not new_reviews:
            return {
                "message": f"No new Indonesian reviews to save. Skipped {non_id_count} non-Indonesian reviews.",
                "inserted_ids": [],
                "status": 200
            }

        result = self.reviews_collection.insert_many(new_reviews)

        sentiment_data = []
        for review, inserted_id in zip(new_reviews, result.inserted_ids):
            sentiment, pos, neg = analyze_sentiment(review.get("comment", ""))
            sentiment_data.append({
                "review_id": inserted_id,
                "comment": review.get("comment", ""),
                "sentiment": sentiment,
                "positive_score": pos,
                "negative_score": neg,
                "created_at": datetime.utcnow()
            })

        save_sentiment_analysis(sentiment_data)

        return {
            "message": f"Reviews saved. Skipped {non_id_count} non-Indonesian reviews.",
            "inserted_ids": result.inserted_ids,
            "status": 201
        }

    def scrape_reviews(self, source):
        data = request.json
        hotel_id = data.get("hotel_id")

        if not hotel_id:
            return jsonify({"error": "hotel_id is required"}), 400

        try:
            hotel_id_obj = ObjectId(hotel_id)
        except Exception as e:
            return jsonify({"error": f"Invalid hotel_id format: {str(e)}"}), 400

        hotel = self.hotels_collection.find_one({"_id": hotel_id_obj})
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

        try:
            SCRAPER_API = "https://scraper-ashy-one.vercel.app"
            response = requests.get(
                f"{SCRAPER_API}/api/{source}",
                params={"url": hotel_url, "hotel_id": hotel_id},
                timeout=120
            )

            if response.status_code != 200:
                return jsonify({"error": response.json().get("error", "Scraping failed")}), 500

            return jsonify({
                "message": f"{source} scraping completed. Data has been sent to /reviews endpoint.",
                "stdout": response.json().get("output", "")
            }), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def receive_reviews(self):
        data = request.json
        reviews = data.get("reviews", [])
        hotel_id = data.get("hotel_id")
        ota = data.get("ota", "unknown")

        now = datetime.utcnow()
        scrape_log_data = {
            "hotel_id": hotel_id,
            "ota": ota,
            "timestamp": now, 
            "total_reviews": len(reviews),
            "note": "",
        }

        db = current_app.scrape_log_db
        log_controller = ScrapeLogController(db)

        try:
            result = self.save_reviews(reviews, hotel_id)
            inserted_ids = result.get("inserted_ids", [])

            scrape_log_data["status"] = "success"
            scrape_log_data["total_reviews"] = len(inserted_ids)

            if inserted_ids:
                scrape_log_data["note"] = f"Scraping successful, {len(inserted_ids)} new reviews inserted."
            else:
                scrape_log_data["note"] = "Scraping succeeded but no new reviews were inserted (possibly duplicates)."

            log_controller.create_scrape_log(scrape_log_data)

            return jsonify({
                "message": result["message"],
                "inserted_ids": [str(_id) for _id in inserted_ids],
                "status": result["status"],
                "note": scrape_log_data["note"]
            }), result["status"]

        except Exception as e:
            scrape_log_data["status"] = "error"
            scrape_log_data["note"] = f"Error occurred: {str(e)}"

            log_controller.create_scrape_log(scrape_log_data)

            return jsonify({
                "message": "Internal server error",
                "error": str(e),
                "note": scrape_log_data["note"]
            }), 500
    
    def get_all_reviews(self):
        page = int(request.args.get('page', 1))
        per_page = 15
        skip = (page - 1) * per_page

        search_query = request.args.get('search', '').strip()
        sentiment_filter = request.args.get('sentiment')
        min_rating = request.args.get('min_rating', type=float)
        max_rating = request.args.get('max_rating', type=float)
        ota_filter = request.args.get('ota')
        min_date = request.args.get('min_date')
        max_date = request.args.get('max_date')

        hotel_ids_param = request.args.get('hotel_id')
        early_match_conditions = []

        if min_rating is not None or max_rating is not None:
            rating_filter = {}
            if min_rating is not None:
                rating_filter["$gte"] = min_rating
            if max_rating is not None:
                rating_filter["$lte"] = max_rating
            early_match_conditions.append({"rating": rating_filter})

        if ota_filter:
            early_match_conditions.append({"OTA": ota_filter})

        if hotel_ids_param:
            try:
                hotel_ids = [ObjectId(hid) for hid in hotel_ids_param.split(',') if hid]
                early_match_conditions.append({"hotel_id": {"$in": hotel_ids}})
            except Exception:
                pass

        pipeline = []

        if early_match_conditions:
            pipeline.append({"$match": {"$and": early_match_conditions}})

        pipeline.append({
            "$addFields": {
                "timestamp_date": {
                    "$dateFromString": {
                        "dateString": "$timestamp",
                        "format": "%d-%m-%Y",
                        "onError": None,
                        "onNull": None
                    }
                }
            }
        })

        pipeline.append({
            "$match": {
                "timestamp_date": {"$ne": None}
            }
        })

        if min_date or max_date:
            date_filter = {}
            if min_date:
                date_filter["$gte"] = datetime.strptime(min_date, "%d-%m-%Y")
            if max_date:
                date_filter["$lte"] = datetime.strptime(max_date, "%d-%m-%Y")
            pipeline.append({"$match": {"timestamp_date": date_filter}})

        pipeline.append({
            "$lookup": {
                "from": "sentiments",
                "localField": "_id",
                "foreignField": "review_id",
                "as": "sentiment_info"
            }
        })
        pipeline.append({
            "$unwind": {
                "path": "$sentiment_info",
                "preserveNullAndEmptyArrays": True
            }
        })

        post_lookup_conditions = []

        if search_query:
            regex = prepare_unicode_friendly_regex(search_query)
            post_lookup_conditions.append({
                "$or": [
                    {"username": {"$regex": regex}},
                    {"comment": {"$regex": regex}},
                    {"hotel_name": {"$regex": regex}}
                ]
            })

        if sentiment_filter:
            post_lookup_conditions.append({
                "sentiment_info.sentiment": sentiment_filter.lower()
            })

        if post_lookup_conditions:
            pipeline.append({"$match": {"$and": post_lookup_conditions}})

        pipeline += [
            {"$sort": {"timestamp_date": -1}},
            {
                "$project": {
                    "_id": 0,
                    "username": 1,
                    "comment": 1,
                    "rating": 1,
                    "timestamp": 1,
                    "hotel_name": 1,
                    "OTA": 1,
                    "sentiment": "$sentiment_info.sentiment",
                    "positive_score": "$sentiment_info.positive_score",
                    "negative_score": "$sentiment_info.negative_score",
                    "hotel_id": { "$toString": "$hotel_id" } 
                }
            },
            {"$skip": skip},
            {"$limit": per_page}
        ]

        return list(self.reviews_collection.aggregate(pipeline))
    
    def fetch_reviews(self):
        return jsonify({"reviews": self.get_all_reviews()})