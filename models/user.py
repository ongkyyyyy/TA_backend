from pymongo import MongoClient  # type: ignore
from config import MONGO_URI

client = MongoClient(MONGO_URI)
db = client.hotelPerformance
users_collection = db.users  

class UsersDB:
    def __init__(self, app=None):
        self.client = client
        self.db = db
        self.collection = users_collection
