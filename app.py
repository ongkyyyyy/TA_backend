from flask import Flask # type: ignore
from config import MONGO_URI
from routes.revenue_routes import create_revenue_blueprint
from routes.review_routes import create_review_blueprint 
from routes.sentiment_routes import create_sentiment_blueprint
from routes.hotel_routes import create_hotel_blueprint
from routes.diagram_routes import create_diagram_blueprint
from routes.user_routes import create_user_blueprint
from routes.scrape_log_routes import create_scrape_log_blueprint
from flask_cors import CORS # type: ignore
from apscheduler.schedulers.background import BackgroundScheduler # type: ignore
from scheduler.review_scraper_scheduler import run_scraping_for_all_hotels
from models.scrape_log import ScrapeLog
import os
port = int(os.environ.get("PORT", 8000))

app = Flask(__name__)
app.scrape_log_db = ScrapeLog()
CORS(app, supports_credentials=True)
app.config["MONGO_URI"] = MONGO_URI

revenue_bp = create_revenue_blueprint(app)
app.register_blueprint(revenue_bp)

reviews_bp = create_review_blueprint(app)
app.register_blueprint(reviews_bp)  

sentiments_bp = create_sentiment_blueprint(app)
app.register_blueprint(sentiments_bp)

hotels_bp = create_hotel_blueprint(app)
app.register_blueprint(hotels_bp)

diagram_bp = create_diagram_blueprint(app)
app.register_blueprint(diagram_bp)

user_bp = create_user_blueprint(app)
app.register_blueprint(user_bp)

scrape_log_bp = create_scrape_log_blueprint(app)
app.register_blueprint(scrape_log_bp)

if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_scraping_for_all_hotels,
        trigger='cron',
        hour=1,
        minute=0,
        id='run_scraping_for_all_hotels',
        misfire_grace_time=30,
        replace_existing=True  
    )
    scheduler.start()

    app.run(host="0.0.0.0", port=port)
