from flask import jsonify, request  # type: ignore
from bson import ObjectId  # type: ignore
from datetime import datetime

class RevenueController:
    def __init__(self, db):
        self.db = db

    def calculate_revenue(self, data):
        try:
            data = self.normalize_revenue_data(data)

            room_lodging = float(data.get("room_lodging", 0))
            rebate_discount = float(data.get("rebate_discount", 0))
            total_room_revenue = room_lodging - rebate_discount

            breakfast = float(data.get("breakfast", 0))
            restaurant_food = float(data.get("restaurant_food", 0))
            restaurant_beverage = float(data.get("restaurant_beverage", 0))
            total_restaurant_revenue = breakfast + restaurant_food + restaurant_beverage

            other_room_revenue = float(data.get("other_room_revenue", 0))
            telephone = float(data.get("telephone", 0))
            business_center = float(data.get("business_center", 0))
            other_income = float(data.get("other_income", 0))
            spa_therapy = float(data.get("spa_therapy", 0))
            misc = float(data.get("misc", 0))
            allowance_other = float(data.get("allowance_other", 0))
            total_other_revenue = (
                other_room_revenue + telephone + business_center +
                other_income + spa_therapy + misc - allowance_other
            )

            nett_revenue = total_room_revenue + total_restaurant_revenue + total_other_revenue
            service_charge = nett_revenue * 0.10
            government_tax = nett_revenue * 0.11
            gross_revenue = nett_revenue + service_charge + government_tax

            ap_restaurant = float(data.get("ap_restaurant", 0))
            tips = float(data.get("tips", 0))
            grand_total_revenue = gross_revenue + ap_restaurant + tips

            active_rooms = int(data.get("active_rooms", 0))
            room_available = int(data.get("room_available", 0))
            house_use = int(data.get("house_use", 0))
            complimentary = int(data.get("complimentary", 0))
            rooms_occupied = int(data.get("rooms_occupied", 0))
            rooms_sold = int(data.get("rooms_sold", 0))
            guests_in_house = int(data.get("guests_in_house", 0))

            vacant_rooms = room_available - rooms_occupied if room_available > 0 else 0
            occupancy = (rooms_occupied / room_available) * 100 if room_available > 0 else 0
            average_room_rate = total_room_revenue / rooms_sold if rooms_sold > 0 else 0

            data.update({
                "room_details": {
                    "room_lodging": room_lodging,
                    "rebate_discount": rebate_discount,
                    "total_room_revenue": round(total_room_revenue, 2)
                },
                "restaurant": {
                    "breakfast": breakfast,
                    "restaurant_food": restaurant_food,
                    "restaurant_beverage": restaurant_beverage,
                    "total_restaurant_revenue": round(total_restaurant_revenue, 2)
                },
                "other_revenue": {
                    "other_room_revenue": other_room_revenue,
                    "telephone": telephone,
                    "business_center": business_center,
                    "other_income": other_income,
                    "spa_therapy": spa_therapy,
                    "misc": misc,
                    "allowance_other": allowance_other,
                    "total_other_revenue": round(total_other_revenue, 2)
                },
                "nett_revenue": round(nett_revenue, 2),
                "service_charge": round(service_charge, 2),
                "government_tax": round(government_tax, 2),
                "gross_revenue": round(gross_revenue, 2),
                "ap_restaurant": ap_restaurant,
                "tips": tips,
                "grand_total_revenue": round(grand_total_revenue, 2),
                "room_stats": {
                    "active_rooms": active_rooms,
                    "room_available": room_available,
                    "house_use": house_use,
                    "complimentary": complimentary,
                    "rooms_occupied": rooms_occupied,
                    "rooms_sold": rooms_sold,
                    "guests_in_house": guests_in_house,
                    "vacant_rooms": vacant_rooms,
                    "occupancy": round(occupancy, 2),
                    "average_room_rate": round(average_room_rate, 2)
                }
            })

            return data

        except Exception as e:
            raise ValueError(f"Error in calculating revenue: {str(e)}")

    def get_revenues(self):

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        skip = (page - 1) * per_page

        hotel_ids_param = request.args.get('hotel_id') or request.args.get('hotel_ids')
        min_date = request.args.get('min_date')
        max_date = request.args.get('max_date')
        sort_by = request.args.get('sort_by', 'date')
        sort_order = int(request.args.get('sort_order', -1))
        min_revenue = request.args.get('minRevenue')
        max_revenue = request.args.get('maxRevenue')
        min_occupancy = request.args.get('minOccupancy')
        max_occupancy = request.args.get('maxOccupancy')

        pipeline = []
        match_conditions = []

        if hotel_ids_param:
            try:
                hotel_ids = [ObjectId(hid.strip()) for hid in hotel_ids_param.split(',') if hid.strip()]
                if hotel_ids:
                    match_conditions.append({"hotel_id": {"$in": hotel_ids}})
            except Exception:
                pass

        if min_date or max_date:
            try:
                date_filter = {}
                if min_date:
                    date_filter["$gte"] = datetime.strptime(min_date, "%d-%m-%Y")
                if max_date:
                    date_filter["$lte"] = datetime.strptime(max_date, "%d-%m-%Y")
                match_conditions.append({
                    "$expr": {
                        "$and": [
                            {"$gte": [{"$dateFromString": {"dateString": "$date", "format": "%d-%m-%Y"}}, date_filter.get("$gte", datetime.min)]},
                            {"$lte": [{"$dateFromString": {"dateString": "$date", "format": "%d-%m-%Y"}}, date_filter.get("$lte", datetime.max)]}
                        ]
                    }
                })
            except Exception:
                pass

        try:
            revenue_conditions = {}
            if min_revenue:
                revenue_conditions["$gte"] = float(min_revenue)
            if max_revenue:
                revenue_conditions["$lte"] = float(max_revenue)
            if revenue_conditions:
                match_conditions.append({"grand_total_revenue": revenue_conditions})
        except ValueError:
            pass

        try:
            occupancy_conditions = {}
            if min_occupancy:
                occupancy_conditions["$gte"] = float(min_occupancy)
            if max_occupancy:
                occupancy_conditions["$lte"] = float(max_occupancy)
            if occupancy_conditions:
                match_conditions.append({"room_stats.occupancy": occupancy_conditions})
        except ValueError:
            pass

        if match_conditions:
            pipeline.append({"$match": {"$and": match_conditions}})

        pipeline += [
            {
                "$lookup": {
                    "from": "hotels",
                    "localField": "hotel_id",
                    "foreignField": "_id",
                    "as": "hotel_info"
                }
            },
            {
                "$unwind": {
                    "path": "$hotel_info",
                    "preserveNullAndEmptyArrays": True
                }
            },
            {
                "$addFields": {
                    "hotel_name": "$hotel_info.hotel_name"
                }
            },
            {
                "$project": {
                    "hotel_info": 0
                }
            }
        ]

        if sort_by == "date":
            pipeline.append({
                "$addFields": {
                    "parsed_date": {
                        "$dateFromString": {
                            "dateString": "$date",
                            "format": "%d-%m-%Y",
                            "onError": None,
                            "onNull": None
                        }
                    }
                }
            })
            pipeline.append({"$sort": {"parsed_date": sort_order}})
        elif sort_by == "revenue":
            pipeline.append({"$sort": {"grand_total_revenue": sort_order}})
        else:
            pipeline.append({
                "$addFields": {
                    "parsed_date": {
                        "$dateFromString": {
                            "dateString": "$date",
                            "format": "%d-%m-%Y",
                            "onError": None,
                            "onNull": None
                        }
                    }
                }
            })
            pipeline.append({"$sort": {"parsed_date": -1}})

        pipeline.append({"$skip": skip})
        pipeline.append({"$limit": per_page})

        try:
            results = list(self.db.collection.aggregate(pipeline))

            for item in results:
                item["_id"] = str(item["_id"])
                if "hotel_id" in item:
                    item["hotel_id"] = str(item["hotel_id"])

            count_filter = {"$and": match_conditions} if match_conditions else {}
            total = self.db.collection.count_documents(count_filter)

            response = {
                "success": True,
                "data": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "total_pages": (total + per_page - 1) // per_page,
                    "data": results
                }
            }
            return jsonify(response), 200

        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
    
    def normalize_revenue_data(self, data):
        nested_keys = ["room_details", "restaurant", "other_revenue", "room_stats"]
        
        flat_data = data.copy()
        for key in nested_keys:
            if key in data and isinstance(data[key], dict):
                flat_data.update(data[key])
                del flat_data[key]
        
        return flat_data
        
    def hotel_exists(self, hotel_id):
        try:
            return self.db.hotels.find_one({"_id": ObjectId(hotel_id)}) is not None
        except Exception:
            return False

    def create_revenue(self):
        revenue_data = request.json

        if not revenue_data.get("hotel_id"):
            return jsonify({"success": False, "message": "hotel_id is required"}), 400

        hotel_id_raw = revenue_data["hotel_id"]

        if not self.hotel_exists(hotel_id_raw):
            return jsonify({"success": False, "message": "Hotel ID not found"}), 404

        try:
            revenue_data["hotel_id"] = ObjectId(hotel_id_raw) if isinstance(hotel_id_raw, str) else hotel_id_raw

            flat_data = self.normalize_revenue_data(revenue_data)
            processed_data = self.calculate_revenue(flat_data)
            processed_data["hotel_id"] = revenue_data["hotel_id"]

            inserted = self.db.collection.insert_one(processed_data)
            print("Inserted revenue with ID:", inserted.inserted_id)

            processed_data["_id"] = str(inserted.inserted_id)
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
            revenue_oid = ObjectId(revenue_id)

            existing_doc = self.db.collection.find_one({"_id": revenue_oid})
            if not existing_doc:
                return jsonify({"success": False, "message": "Revenue record not found"}), 404

            hotel_id_raw = updated_data.get("hotel_id", existing_doc.get("hotel_id"))
            try:
                hotel_id = ObjectId(hotel_id_raw) if isinstance(hotel_id_raw, str) else hotel_id_raw
            except Exception as e:
                print(f"Invalid hotel_id: {e}")
                return jsonify({"success": False, "message": "Invalid hotel ID"}), 400

            if not self.hotel_exists(hotel_id):
                return jsonify({"success": False, "message": "Hotel not found"}), 400
            
            merged_data = existing_doc.copy()
            merged_data.update(updated_data)
            merged_data["hotel_id"] = hotel_id

            flat_data = self.normalize_revenue_data(merged_data)
            processed_data = self.calculate_revenue(flat_data)
            processed_data["hotel_id"] = hotel_id

            result = self.db.collection.update_one(
                {"_id": revenue_oid},
                {"$set": processed_data}
            )

            print("Matched:", result.matched_count, "Modified:", result.modified_count)

            if result.modified_count == 0:
                return jsonify({"success": False, "message": "No matching fields found for update"}), 400

            updated_revenue = self.db.collection.find_one({"_id": revenue_oid})
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
            revenue_oid = ObjectId(revenue_id)

            # Attempt to delete
            result = self.db.collection.delete_one({"_id": revenue_oid})

            if result.deleted_count:
                return jsonify({"success": True, "message": "Revenue deleted successfully"}), 200
            else:
                return jsonify({"success": False, "message": "Revenue not found"}), 404

        except Exception as e:
            print(f"Error deleting revenue: {e}")
            return jsonify({"success": False, "message": "Invalid revenue ID format"}), 400
    
