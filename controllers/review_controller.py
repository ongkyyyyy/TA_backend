from models.review import reviews_collection
from controllers.sentiments_controller import save_sentiment_analysis
from sentiment_analysis.sentiment_analysis import analyze_sentiment
from datetime import datetime

def save_reviews(reviews):
    if not reviews:
        return {"message": "No reviews to save", "status": 400}

    filters = [{
        "username": r["username"],
        "comment": r["comment"],
        "timestamp": r["timestamp"],
        "hotel_name": r["hotel_name"],
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
    for r in reviews:
        key = f"{r['username']}-{r['comment']}-{r['timestamp']}-{r['hotel_name']}-{r['OTA']}"
        if key not in existing_keys:
            new_reviews.append(r)

    if not new_reviews:
        return {"message": "No new reviews to save", "status": 200, "inserted_ids": []}

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

    return {"message": "Reviews saved", "inserted_ids": result.inserted_ids, "status": 201}


def get_all_reviews():
    reviews = list(reviews_collection.find({}, {"_id": 0}))  
    return reviews
