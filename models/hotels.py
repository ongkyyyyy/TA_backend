from pymongo import MongoClient # type: ignore
from config import MONGO_URI

class HotelsDB:
    def __init__(self, app=None):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client.hotelPerformance
        self.collection = self.db.hotels

hotels_collection = HotelsDB().collection