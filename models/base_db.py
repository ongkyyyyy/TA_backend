from pymongo import MongoClient  # type: ignore
from config import MONGO_URI

class BaseDB:
    def __init__(self, db_name="hotelPerformance"):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[db_name]