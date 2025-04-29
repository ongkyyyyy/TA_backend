from pymongo import MongoClient # type: ignore
from config import MONGO_URI

class DiagramDB:
    def __init__(self, app=None):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client.hotelPerformance
        self.hotels = self.db.hotels
        self.revenues = self.db.revenues
        self.reviews = self.db.reviews
        self.sentiments = self.db.sentiments

db = DiagramDB()