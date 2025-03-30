from models.review import reviews_collection, sentiment_collection
from sentiment_analysis.sentiment_analysis import analyze_sentiment
from datetime import datetime

def save_reviews(reviews):
    if not reviews:
        return {"message": "No reviews to save", "status": 400}

    result = reviews_collection.insert_many(reviews)

    # Analyze sentiment for each inserted review
    sentiment_data = []
    for review, inserted_id in zip(reviews, result.inserted_ids):
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

    sentiment_response = save_sentiment_analysis(sentiment_data)

    return {
        "message": "Reviews and sentiment analysis saved successfully",
        "inserted_ids": result.inserted_ids,
        "sentiment_status": sentiment_response["status"],
        "count": len(result.inserted_ids),
        "status": 201
    }

def save_sentiment_analysis(sentiments):
    if not sentiments:
        return {"message": "No sentiment data to save", "status": 400}

    sentiment_collection.insert_many(sentiments)
    return {"message": "Sentiment analysis saved successfully", "status": 201}

def get_all_reviews():
    """Retrieve all reviews from MongoDB"""
    reviews = list(reviews_collection.find({}, {"_id": 0}))  
    return reviews
