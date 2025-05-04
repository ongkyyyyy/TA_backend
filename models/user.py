from pymongo import MongoClient  # type: ignore
from config import MONGO_URI

class UsersDB:
    def __init__(self, app=None):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client.hotelPerformance
        self.collection = self.db.users

users_collection = UsersDB().collection
