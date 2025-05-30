from .base_db import BaseDB

class ScrapeLogDB(BaseDB):
    def __init__(self):
        super().__init__()
        self.collection = self.db.scrape_log
