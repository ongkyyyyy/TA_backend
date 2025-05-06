import re
from flask import request, jsonify # type: ignore
from bson import ObjectId, regex # type: ignore

class HotelController:
    def __init__(self, db):
        self.db = db

    def create_hotel(self):
        data = request.json
        required_fields = ["hotel_name", "address", "city", "country"]

        if not all(field in data and data[field] for field in required_fields):
            return jsonify({"error": "Missing required field(s)"}), 400

        data.setdefault("agoda_link", "")
        data.setdefault("traveloka_link", "")
        data.setdefault("tripcom_link", "")
        data.setdefault("ticketcom_link", "")

        hotel_id = self.db.collection.insert_one(data).inserted_id
        return jsonify({"message": "Hotel created", "id": str(hotel_id)}), 201

    def get_hotels(self):

        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 15))
        skip = (page - 1) * limit

        hotels = []
        cursor = self.db.collection.find().skip(skip).limit(limit)
        total_count = self.db.collection.count_documents({})

        for hotel in cursor:
            hotel["_id"] = str(hotel["_id"])
            hotels.append(hotel)

        return jsonify({
            "data": hotels,
            "total": total_count,
            "page": page,
            "limit": limit
        })
        
    def get_hotels_dropdown(self):
        hotels = []
        for hotel in self.db.collection.find({}, {"hotel_name": 1}):
            hotels.append({
                "_id": str(hotel["_id"]),
                "hotel_name": hotel.get("hotel_name", "")
            })
        return jsonify(hotels)

    def get_hotel(self, hotel_id):
        try:
            hotel = self.db.collection.find_one({"_id": ObjectId(hotel_id)})
        except Exception:
            return jsonify({"error": "Invalid hotel ID"}), 400

        if not hotel:
            return jsonify({"error": "Hotel not found"}), 404

        hotel["_id"] = str(hotel["_id"])
        return jsonify(hotel)

    def update_hotel(self, hotel_id):
        data = request.json
        try:
            result = self.db.collection.update_one(
                {"_id": ObjectId(hotel_id)},
                {"$set": data}
            )
        except Exception:
            return jsonify({"error": "Invalid hotel ID"}), 400

        if result.matched_count == 0:
            return jsonify({"error": "Hotel not found"}), 404

        return jsonify({"message": "Hotel updated"}), 200

    def delete_hotel(self, hotel_id):
        try:
            hotel_obj_id = ObjectId(hotel_id)
        except Exception:
            return jsonify({"error": "Invalid hotel ID"}), 400

        hotel = self.db.collection.find_one({"_id": hotel_obj_id})
        if not hotel:
            return jsonify({"error": "Hotel not found"}), 404

        hotel_result = self.db.collection.delete_one({"_id": hotel_obj_id})

        revenue_result = self.db.revenues.delete_many({"hotel_id": hotel_obj_id})

        return jsonify({
            "message": "Hotel and associated revenues deleted successfully.",
            "hotel_deleted": hotel_result.deleted_count,
            "revenues_deleted": revenue_result.deleted_count
        }), 200
    
    def search_hotels(self):
        search_term = request.args.get("q")
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 15))
        skip = (page - 1) * limit

        query = {}
        if search_term:
            query = {
                "$or": [
                    {"hotel_name": {"$regex": re.escape(search_term), "$options": "i"}},
                    {"city": {"$regex": re.escape(search_term), "$options": "i"}},
                    {"country": {"$regex": re.escape(search_term), "$options": "i"}},
                    {"address": {"$regex": re.escape(search_term), "$options": "i"}}
                ]
            }

        hotels = []
        cursor = self.db.collection.find(query).skip(skip).limit(limit)
        total_count = self.db.collection.count_documents(query)

        for hotel in cursor:
            hotel["_id"] = str(hotel["_id"])
            hotels.append(hotel)

        return jsonify({
            "data": hotels,
            "total": total_count,
            "page": page,
            "limit": limit
        })

