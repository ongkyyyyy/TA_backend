from pymongo import MongoClient
from config import MONGO_URI

class ScrapeLogDB:
    def __init__(self, app=None):
        client = MongoClient(MONGO_URI)
        db = client.hotelPerformance
        self.collection = db.scrape_log
