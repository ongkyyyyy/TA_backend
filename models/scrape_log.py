from .base_db import BaseDB

class ScrapeLog(BaseDB):
    def __init__(self):
        super().__init__()
        self.collection = self.db.scrape_log
