from flask import request, jsonify 
from bson import ObjectId
import re
from datetime import datetime

class ScrapeLogController:
    def __init__(self, db):
        self.db = db 

    def create_scrape_log(self):
        data = request.json
        required_fields = ["hotel_id", "ota", "status", "total_reviews", "timestamp"]

        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing field: {field}"}), 400

        result = self.db.collection.insert_one(data)
        return jsonify({"message": "Scrape log created", "id": str(result.inserted_id)}), 201

    def get_scrape_logs(self):
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 15))
        skip = (page - 1) * limit

        ota = request.args.get("ota")
        status = request.args.get("status")
        start_date = request.args.get("start_date") 
        end_date = request.args.get("end_date")

        query = {}
        if ota:
            query["ota"] = ota
        if status:
            query["status"] = status

        if start_date or end_date:
            date_filter = {}
            if start_date:
                start_dt = datetime.strptime(start_date, "%d-%m-%Y")
                date_filter["$gte"] = start_dt
            if end_date:
                end_dt = datetime.strptime(end_date, "%d-%m-%Y").replace(hour=23, minute=59, second=59)
                date_filter["$lte"] = end_dt
            query["timestamp"] = date_filter

        cursor = (
            self.db.collection
            .find(query)
            .sort("timestamp", -1)
            .skip(skip)
            .limit(limit)
        )
        total = self.db.collection.count_documents(query)

        logs = []
        for log in cursor:
            log["_id"] = str(log["_id"])
            logs.append(log)

        return jsonify({
            "data": logs,
            "total": total,
            "page": page,
            "limit": limit
        })
    
    def get_scrape_log(self, log_id):
        try:
            log = self.db.collection.find_one({"_id": ObjectId(log_id)})
        except Exception:
            return jsonify({"error": "Invalid log ID"}), 400

        if not log:
            return jsonify({"error": "Scrape log not found"}), 404

        log["_id"] = str(log["_id"])
        return jsonify(log)

    def update_scrape_log(self, log_id):
        data = request.json
        try:
            result = self.db.collection.update_one({"_id": ObjectId(log_id)}, {"$set": data})
        except Exception:
            return jsonify({"error": "Invalid log ID"}), 400

        if result.matched_count == 0:
            return jsonify({"error": "Scrape log not found"}), 404

        return jsonify({"message": "Scrape log updated"}), 200

    def delete_scrape_log(self, log_id):
        try:
            result = self.db.collection.delete_one({"_id": ObjectId(log_id)})
        except Exception:
            return jsonify({"error": "Invalid log ID"}), 400

        if result.deleted_count == 0:
            return jsonify({"error": "Scrape log not found"}), 404

        return jsonify({"message": "Scrape log deleted"}), 200
