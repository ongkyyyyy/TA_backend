from .base_db import BaseDB

class RevenueDB(BaseDB):
    def __init__(self):
        super().__init__()
        self.collection = self.db.revenues
        self.hotels = self.db.hotels 
