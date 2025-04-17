from models.review import reviews_collection
from controllers.sentiments_controller import save_sentiment_analysis
from sentiment_analysis.sentiment_analysis import analyze_sentiment
from datetime import datetime
from langdetect import detect, LangDetectException # type: ignore
from bson import ObjectId # type: ignore

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

def get_all_reviews():
    pipeline = [
        {
            "$lookup": {
                "from": "hotels",
                "localField": "hotel_id",
                "foreignField": "_id",
                "as": "hotel_info"
            }
        },
        {
            "$unwind": {
                "path": "$hotel_info",
                "preserveNullAndEmptyArrays": True
            }
        },
        {
            "$project": {
                "_id": 0,
                "username": 1,
                "comment": 1,
                "rating": 1,
                "timestamp": 1,
                "hotel_name": "$hotel_info.hotel_name",
                "hotel_id": 1,
                "OTA": 1
            }
        }
    ]

    reviews = list(reviews_collection.aggregate(pipeline))
    return reviews
