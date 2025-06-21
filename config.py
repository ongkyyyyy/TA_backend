# MONGO_URI = "mongodb+srv://williamongkywow:williamongkywow@clusterta.poz3g.mongodb.net/hotelPerformance"
# SECRET_KEY = "supersecretkey_987654321"
import os

MONGO_URI = os.environ.get("MONGODB_URI")
SECRET_KEY = os.environ.get("SECRET_KEY")
