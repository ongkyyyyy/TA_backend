from flask_pymongo import PyMongo # type: ignore
from bson import ObjectId # type: ignore
from flask import jsonify # type: ignore

class RevenueDB:
    def __init__(self, app):
        self.mongo = PyMongo(app)

    def get_all_revenues(self):
        return list(self.mongo.db.revenues.find({}))

    def get_revenue_by_id(self, object_id):
        return self.mongo.db.revenues.find_one({"_id": object_id})

    def calculate_revenue(self, data):
        room_lodging = data.get("room_lodging", 0)
        rebate_discount = data.get("rebate_discount", 0)
        total_room_revenue = room_lodging - rebate_discount
        
        breakfast = data.get("breakfast", 0)
        restaurant_food = data.get("restaurant_food", 0)
        restaurant_beverage = data.get("restaurant_beverage", 0)
        total_restaurant_revenue = breakfast + restaurant_food + restaurant_beverage

        other_room_revenue = data.get("other_room_revenue", 0)
        telephone = data.get("telephone", 0)
        business_center = data.get("business_center", 0)
        other_income = data.get("other_income", 0)
        spa_therapy = data.get("spa_therapy", 0)
        misc = data.get("misc", 0)
        allowance_other = data.get("allowance_other", 0)
        total_other_revenue = (
            other_room_revenue + telephone + business_center +
            other_income + spa_therapy + misc - allowance_other
        )

        nett_revenue = total_room_revenue + total_restaurant_revenue + total_other_revenue
        service_charge = nett_revenue * 0.10 
        government_tax = nett_revenue * 0.11 
        gross_revenue = nett_revenue + service_charge + government_tax
        ap_restaurant = data.get("ap_restaurant", 0)
        tips = data.get("tips", 0)
        grand_total_revenue = gross_revenue + ap_restaurant + tips

        active_rooms = data.get("active_rooms", 0)
        room_available = data.get("room_available", 0)
        house_use = data.get("house_use", 0)
        complimentary = data.get("complimentary", 0)
        rooms_occupied = data.get("rooms_occupied", 0)
        rooms_sold = data.get("rooms_sold", 0)
        guests_in_house = data.get("guests_in_house", 0)
        vacant_rooms = room_available - rooms_occupied if room_available > 0 else 0
        occupancy = (rooms_occupied / room_available) * 100 if room_available > 0 else 0
        average_room_rate = total_room_revenue / rooms_sold if rooms_sold > 0 else 0

        return {
            "hotel_id": data.get("hotel_id"),
            "date": data.get("date", ""),
            "room_details": {
                "room_lodging": room_lodging,
                "rebate_discount": rebate_discount,
                "total_room_revenue": total_room_revenue
            },
            "restaurant": {
                "breakfast": breakfast,
                "restaurant_food": restaurant_food,
                "restaurant_beverage": restaurant_beverage,
                "total_restaurant_revenue": total_restaurant_revenue
            },
            "other_revenue": {
                "other_room_revenue": other_room_revenue,
                "telephone": telephone,
                "business_center": business_center,
                "other_income": other_income,
                "spa_therapy": spa_therapy,
                "misc": misc,
                "allowance_other": allowance_other,
                "total_other_revenue": total_other_revenue
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
                "vacant_rooms": vacant_rooms,
                "occupancy": round(occupancy, 2),
                "guests_in_house": guests_in_house,
                "average_room_rate": round(average_room_rate, 2)
            }
        }

    def add_revenue(self, revenue_data):
        if "hotel_id" not in revenue_data:
            raise ValueError("Missing hotel_id in revenue_data")

        revenue_data["hotel_id"] = ObjectId(revenue_data["hotel_id"])

        processed_data = self.calculate_revenue(revenue_data)
        processed_data["hotel_id"] = revenue_data["hotel_id"]
        inserted = self.mongo.db.revenues.insert_one(processed_data)
        processed_data["_id"] = inserted.inserted_id
        return processed_data

    def update_revenue(self, revenue_oid, updated_data):
        existing_doc = self.mongo.db.revenues.find_one({"_id": revenue_oid})
        if not existing_doc:
            return -1

        hotel_id_raw = updated_data.get("hotel_id", existing_doc.get("hotel_id"))

        try:
            hotel_id = ObjectId(hotel_id_raw) if isinstance(hotel_id_raw, str) else hotel_id_raw
        except Exception:
            return 0 
        if not self.hotel_exists(hotel_id):
            return 0

        merged_data = existing_doc.copy()
        merged_data.update(updated_data)
        merged_data["hotel_id"] = hotel_id

        processed_data = self.calculate_revenue(merged_data)
        processed_data["hotel_id"] = hotel_id  
        result = self.mongo.db.revenues.update_one(
            {"_id": revenue_oid},
            {"$set": processed_data}
        )

        return result.modified_count

    def delete_revenue(self, revenue_oid):
        result = self.mongo.db.revenues.delete_one({"_id": revenue_oid})
        return result.deleted_count

    def hotel_exists(self, hotel_id):
        try:
            return self.mongo.db.hotels.find_one({"_id": ObjectId(hotel_id)}) is not None
        except Exception:
            return False

    def get_revenues_by_hotel(self, hotel_id):
        return list(self.mongo.db.revenues.find({"hotel_id": ObjectId(hotel_id)}))
    
    def get_all_hotels_with_revenues(self):
        pipeline = [
            {
                "$lookup": {
                    "from": "revenues",
                    "localField": "_id",
                    "foreignField": "hotel_id",
                    "as": "revenues"
                }
            }
        ]
        hotels_with_revenues = list(self.mongo.db.hotels.aggregate(pipeline))
        return hotels_with_revenues

