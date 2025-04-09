from pymongo import MongoClient
from config import MONGO_URI

client = MongoClient(MONGO_URI)
db = client.hotelPerformance  

reviews_collection = db.reviews
sentiment_collection = db.sentiments