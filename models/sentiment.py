from pymongo import MongoClient # type: ignore
from config import MONGO_URI

client = MongoClient(MONGO_URI)
db = client.hotelPerformance  

sentiment_collection = db.sentiments