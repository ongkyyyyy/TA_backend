from models.sentiment import Sentiment  

sentiment_db = Sentiment()
sentiment_collection = sentiment_db.collection

def save_sentiment_analysis(sentiments):
    if not sentiments:
        return {"message": "No sentiment data to save", "status": 400}

    sentiment_collection.insert_many(sentiments)
    return {"message": "Sentiment analysis saved successfully", "status": 201}

def get_all_sentiments():
    sentiments = list(sentiment_collection.find({}, {"_id": 0}))  
    return sentiments