from models.review import reviews_collection
from controllers.sentiments_controller import save_sentiment_analysis
from sentiment_analysis.sentiment_analysis import analyze_sentiment
from models.sentiment import sentiment_collection
from datetime import datetime
from langdetect import detect, LangDetectException # type: ignore
from bson import ObjectId # type: ignore
from flask import request # type: ignore
import re

def save_reviews(reviews, hotel_id=None):  
    if not reviews:
        return {"message": "No reviews to save", "status": 400}

    filters = [{
        "username": r["username"],
        "comment": r["comment"],
        "timestamp": r["timestamp"],
        "hotel_name": r.get("hotel_name", ""),
        "OTA": r["OTA"]
    } for r in reviews]

    existing = reviews_collection.find({"$or": filters}, {
        "username": 1, "comment": 1, "timestamp": 1, "hotel_name": 1, "OTA": 1
    })

    existing_keys = {
        f"{r['username']}-{r['comment']}-{r['timestamp']}-{r['hotel_name']}-{r['OTA']}"
        for r in existing
    }

    new_reviews = []
    non_id_count = 0

    for r in reviews:
        key = f"{r['username']}-{r['comment']}-{r['timestamp']}-{r['hotel_name']}-{r['OTA']}"
        if key not in existing_keys:
            comment = r.get("comment", "")
            try:
                if detect(comment) != 'id':
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
            "status": 200,
            "inserted_ids": [],
            "skipped_non_id": non_id_count
        }

    result = reviews_collection.insert_many(new_reviews)
    sentiment_data = []

    for review, inserted_id in zip(new_reviews, result.inserted_ids):
        comment = review.get("comment", "")
        sentiment, pos_count, neg_count = analyze_sentiment(comment)
        sentiment_data.append({
            "review_id": inserted_id,
            "comment": comment,
            "sentiment": sentiment,
            "positive_score": pos_count,
            "negative_score": neg_count,
            "created_at": datetime.utcnow()
        })

    save_sentiment_analysis(sentiment_data)

    return {
        "message": f"Reviews saved. Skipped {non_id_count} non-Indonesian reviews.",
        "inserted_ids": result.inserted_ids,
        "status": 201,
        "skipped_non_id": non_id_count
    }

def prepare_unicode_friendly_regex(text):
    safe_text = re.escape(text)
    safe_text = safe_text.replace('', '[\u200B-\u200D\uFEFF]?')
    return re.compile(safe_text, re.IGNORECASE)

def get_all_reviews():
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
    hotel_id = request.args.get('hotel_id')

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

    if hotel_id:
        try:
            early_match_conditions.append({"hotel_id": ObjectId(hotel_id)})
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
                "hotel_id": 1,
                "OTA": 1,
                "sentiment": "$sentiment_info.sentiment",
                "positive_score": "$sentiment_info.positive_score",
                "negative_score": "$sentiment_info.negative_score",
            }
        },
        {"$skip": skip},
        {"$limit": per_page}
    ]

    reviews = list(reviews_collection.aggregate(pipeline))
    return reviews