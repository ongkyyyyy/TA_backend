from .base_db import BaseDB

class Sentiment(BaseDB):
    def __init__(self):
        super().__init__()
        self.collection = self.db.sentiments