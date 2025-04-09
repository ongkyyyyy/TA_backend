from flask import Flask
from config import MONGO_URI
from routes.revenue_routes import create_revenue_blueprint
from routes.review_routes import create_review_blueprint 
from routes.sentiment_routes import create_sentiment_blueprint

app = Flask(__name__)
app.config["MONGO_URI"] = MONGO_URI

revenue_bp = create_revenue_blueprint(app)
app.register_blueprint(revenue_bp)

reviews_bp = create_review_blueprint(app)
app.register_blueprint(reviews_bp)  

sentiments_bp = create_sentiment_blueprint(app)
app.register_blueprint(sentiments_bp)

if __name__ == "__main__":
    app.run(debug=False)
