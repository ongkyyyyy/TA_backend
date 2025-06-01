from .base_db import BaseDB

class Diagram(BaseDB):
    def __init__(self):
        super().__init__()
        self.hotels = self.db.hotels
        self.revenues = self.db.revenues
        self.reviews = self.db.reviews
        self.sentiments = self.db.sentiments