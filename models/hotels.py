from .base_db import BaseDB

class Hotels(BaseDB):
    def __init__(self):
        super().__init__()
        self.collection = self.db.hotels
        self.revenues = self.db.revenues 
