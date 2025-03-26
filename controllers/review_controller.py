from models.review import reviews_collection

def save_reviews(reviews):
    """Insert multiple reviews into MongoDB"""
    if not reviews:
        return {"message": "No reviews to save", "status": 400}
    
    reviews_collection.insert_many(reviews)
    return {"message": "Reviews saved successfully", "count": len(reviews), "status": 201}

def get_all_reviews():
    """Retrieve all reviews from MongoDB"""
    reviews = list(reviews_collection.find({}, {"_id": 0}))  
    return reviews
