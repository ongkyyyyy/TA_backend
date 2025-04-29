from flask import jsonify
from bson import ObjectId
from datetime import datetime
from models.diagram import db

def get_revenue_diagram_data(hotel_id: str):
    revenues = list(db.revenues.find({"hotel_id": ObjectId(hotel_id)}).sort("date", 1))

    revenue_data = {
        "dates": [],
        "room_revenue": [],
        "restaurant_revenue": [],
        "other_revenue": [],
        "nett_revenue": [],
        "gross_revenue": [],
        "grand_total_revenue": []
    }

    for rev in revenues:
        revenue_data["dates"].append(rev["date"])
        revenue_data["room_revenue"].append(rev["room_details"]["total_room_revenue"])
        revenue_data["restaurant_revenue"].append(rev["restaurant"]["total_restaurant_revenue"])
        revenue_data["other_revenue"].append(rev["other_revenue"]["total_other_revenue"])
        revenue_data["nett_revenue"].append(rev["nett_revenue"])
        revenue_data["gross_revenue"].append(rev["gross_revenue"])
        revenue_data["grand_total_revenue"].append(rev["grand_total_revenue"])

    return jsonify(revenue_data)

def get_reviews_sentiments(hotel_id: str):
    reviews = list(db.reviews.find({"hotel_id": ObjectId(hotel_id)}).sort("timestamp", 1))
    
    sentiment_map = {s["review_id"]: s for s in db.sentiments.find({
        "review_id": {"$in": [r["_id"] for r in reviews]}
    })}

    result = {
        "dates": [],
        "ratings": [],
        "positive": [],
        "neutral": [],
        "negative": [],
    }

    for review in reviews:
        date_str = review["timestamp"]
        result["dates"].append(date_str)
        result["ratings"].append(review["rating"])

        sentiment = sentiment_map.get(review["_id"])
        if sentiment:
            if sentiment["sentiment"] == "positive":
                result["positive"].append(1)
                result["neutral"].append(0)
                result["negative"].append(0)
            elif sentiment["sentiment"] == "neutral":
                result["positive"].append(0)
                result["neutral"].append(1)
                result["negative"].append(0)
            else:
                result["positive"].append(0)
                result["neutral"].append(0)
                result["negative"].append(1)
        else:
            result["positive"].append(0)
            result["neutral"].append(1)
            result["negative"].append(0)

    return jsonify(result)
