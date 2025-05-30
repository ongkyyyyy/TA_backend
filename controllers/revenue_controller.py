from flask import jsonify, request # type: ignore
from bson import ObjectId # type: ignore

class RevenueController:
    def __init__(self, db):
        self.db = db

    def get_revenues(self):
        try:
            revenues = self.db.get_all_revenues()
            return jsonify({"success": True, "data": revenues}), 200
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    def get_revenue(self, revenue_id):
        try:
            revenue = self.db.get_revenue_by_id(ObjectId(revenue_id))
            if revenue:
                return jsonify({"success": True, "data": revenue}), 200
            return jsonify({"success": False, "message": "Revenue not found"}), 404
        except Exception:
            return jsonify({"success": False, "message": "Invalid revenue ID format"}), 400

    def create_revenue(self):
        revenue_data = request.json

        if not revenue_data.get("hotel_id"):
            return jsonify({"success": False, "message": "hotel_id is required"}), 400

        hotel_id = revenue_data["hotel_id"]
        if not self.db.hotel_exists(hotel_id):
            return jsonify({"success": False, "message": "Hotel ID not found"}), 404

        try:
            processed_data = self.db.add_revenue(revenue_data)

            # Convert ObjectId fields to strings
            processed_data["_id"] = str(processed_data["_id"])
            processed_data["hotel_id"] = str(processed_data["hotel_id"])

            return jsonify({
                "success": True,
                "message": "Revenue added successfully",
                "data": processed_data
            }), 201
        except Exception as e:
            print("Error in create_revenue:", e)
            return jsonify({"success": False, "message": str(e)}), 500

    def edit_revenue(self, revenue_id):
        try:
            updated_data = request.json
            revenue_obj_id = ObjectId(revenue_id)

            update_status = self.db.update_revenue(revenue_obj_id, updated_data)

            if update_status == -1:
                return jsonify({"success": False, "message": "Revenue record not found"}), 404
            elif update_status == 0:
                return jsonify({"success": False, "message": "No matching fields found for update"}), 400
            else:
                updated_revenue = self.db.db.revenues.find_one({"_id": revenue_obj_id})
                
                if updated_revenue:
                    updated_revenue["_id"] = str(updated_revenue["_id"])
                    updated_revenue["hotel_id"] = str(updated_revenue["hotel_id"])

                return jsonify({
                    "success": True,
                    "message": "Revenue updated successfully",
                    "data": updated_revenue
                }), 200

        except Exception as e:
            print("Error:", e)
            return jsonify({"success": False, "message": "Invalid revenue ID format"}), 400

    def remove_revenue(self, revenue_id):
        try:
            deleted_count = self.db.delete_revenue(ObjectId(revenue_id))
            if deleted_count:
                return jsonify({"success": True, "message": "Revenue deleted successfully"}), 200
            return jsonify({"success": False, "message": "Revenue not found"}), 404
        except Exception:
            return jsonify({"success": False, "message": "Invalid revenue ID format"}), 400

    def get_revenues_by_hotel(self, hotel_id):
        if not self.db.hotel_exists(hotel_id):
            return jsonify({"success": False, "message": "Hotel ID not found"}), 404

        try:
            revenues = self.db.get_revenues_by_hotel(hotel_id)
            return jsonify({"success": True, "data": revenues}), 200
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
        
    def get_hotels_with_revenues(self):
        try:
            hotels_with_revenues = self.db.get_all_hotels_with_revenues()

            simplified_result = []
            for hotel in hotels_with_revenues:
                hotel_name = hotel.get("hotel_name", "Unknown Hotel")
                revenues = hotel.get("revenues", [])

                if revenues:
                    for rev in revenues:
                        rev["_id"] = str(rev["_id"])
                        rev["hotel_id"] = str(rev["hotel_id"])

                    simplified_result.append({
                        "name": hotel_name,
                        "revenues": revenues
                    })
            return jsonify({"success": True, "data": simplified_result}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500




