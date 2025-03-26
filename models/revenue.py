from flask_pymongo import PyMongo

class RevenueDB:
    def __init__(self, app):
        self.mongo = PyMongo(app)

    def get_all_revenues(self):
        return list(self.mongo.db.revenues.find({}, {"_id": 0}))

    def get_revenue_by_id(self, revenue_id):
        return self.mongo.db.revenues.find_one({"revenue_id": revenue_id}, {"_id": 0})

    def calculate_revenue(self, revenue_data):
        rooms_sold = revenue_data.get("rooms_sold", 0)
        total_rooms = revenue_data.get("total_rooms", 0) 
        room_revenue = revenue_data.get("room_revenue", 0)

        occupancy_rate = (rooms_sold / total_rooms) * 100 if total_rooms > 0 else 0
        average_daily_rate = room_revenue / rooms_sold if rooms_sold > 0 else 0
        revPAR = room_revenue / total_rooms if total_rooms > 0 else 0

        restaurant_revenue = revenue_data.get("restaurant_revenue", 0)
        bar_revenue = revenue_data.get("bar_revenue", 0)
        total_fnb_revenue = restaurant_revenue + bar_revenue

        spa_revenue = revenue_data.get("spa_revenue", 0)
        laundry_revenue = revenue_data.get("laundry_revenue", 0)
        event_revenue = revenue_data.get("event_revenue", 0)
        parking_revenue = revenue_data.get("parking_revenue", 0)
        total_other_revenue = spa_revenue + laundry_revenue + event_revenue + parking_revenue

        total_revenue = room_revenue + total_fnb_revenue + total_other_revenue

        return {
            "revenue_id": revenue_data["revenue_id"],
            "date": revenue_data.get("date", ""),
            "room_sales": {
                "rooms_sold": rooms_sold,
                "total_rooms": total_rooms,
                "room_revenue": room_revenue,
                "occupancy_rate": round(occupancy_rate, 2),
                "average_daily_rate": round(average_daily_rate, 2),
                "revPAR": round(revPAR, 2)
            },
            "food_beverage": {
                "restaurant_revenue": restaurant_revenue,
                "bar_revenue": bar_revenue,
                "total_fnb_revenue": total_fnb_revenue
            },
            "additional_services": {
                "spa_revenue": spa_revenue,
                "laundry_revenue": laundry_revenue,
                "event_revenue": event_revenue,
                "parking_revenue": parking_revenue,
                "total_other_revenue": total_other_revenue
            },
            "total_revenue": total_revenue
        }

    def add_revenue(self, revenue_data):
        processed_data = self.calculate_revenue(revenue_data)
        self.mongo.db.revenues.insert_one(processed_data)
        return processed_data
    
    def update_revenue(self, revenue_id, updated_data):
        existing_doc = self.mongo.db.revenues.find_one({"revenue_id": revenue_id})
        if not existing_doc:
            return -1  

        rooms_sold = existing_doc["room_sales"]["rooms_sold"]
        total_rooms = existing_doc["room_sales"]["total_rooms"]
        room_revenue = existing_doc["room_sales"]["room_revenue"]

        restaurant_revenue = existing_doc["food_beverage"]["restaurant_revenue"]
        bar_revenue = existing_doc["food_beverage"]["bar_revenue"]

        spa_revenue = existing_doc["additional_services"]["spa_revenue"]
        laundry_revenue = existing_doc["additional_services"]["laundry_revenue"]
        event_revenue = existing_doc["additional_services"]["event_revenue"]
        parking_revenue = existing_doc["additional_services"]["parking_revenue"]

        rooms_sold = updated_data.get("rooms_sold", rooms_sold)
        total_rooms = updated_data.get("total_rooms", total_rooms)
        room_revenue = updated_data.get("room_revenue", room_revenue)

        restaurant_revenue = updated_data.get("restaurant_revenue", restaurant_revenue)
        bar_revenue = updated_data.get("bar_revenue", bar_revenue)

        spa_revenue = updated_data.get("spa_revenue", spa_revenue)
        laundry_revenue = updated_data.get("laundry_revenue", laundry_revenue)
        event_revenue = updated_data.get("event_revenue", event_revenue)
        parking_revenue = updated_data.get("parking_revenue", parking_revenue)

        occupancy_rate = (rooms_sold / total_rooms) * 100 if total_rooms > 0 else 0
        average_daily_rate = room_revenue / rooms_sold if rooms_sold > 0 else 0
        revPAR = room_revenue / total_rooms if total_rooms > 0 else 0

        total_fnb_revenue = restaurant_revenue + bar_revenue
        total_other_revenue = spa_revenue + laundry_revenue + event_revenue + parking_revenue
        total_revenue = room_revenue + total_fnb_revenue + total_other_revenue

        updated_doc = {
            "room_sales": {
                "rooms_sold": rooms_sold,
                "total_rooms": total_rooms,
                "room_revenue": room_revenue,
                "occupancy_rate": round(occupancy_rate, 2),
                "average_daily_rate": round(average_daily_rate, 2),
                "revPAR": round(revPAR, 2)
            },
            "food_beverage": {
                "restaurant_revenue": restaurant_revenue,
                "bar_revenue": bar_revenue,
                "total_fnb_revenue": total_fnb_revenue
            },
            "additional_services": {
                "spa_revenue": spa_revenue,
                "laundry_revenue": laundry_revenue,
                "event_revenue": event_revenue,
                "parking_revenue": parking_revenue,
                "total_other_revenue": total_other_revenue
            },
            "total_revenue": total_revenue
        }

        result = self.mongo.db.revenues.update_one({"revenue_id": revenue_id}, {"$set": updated_doc})
        return result.modified_count

    def delete_revenue(self, revenue_id):
        result = self.mongo.db.revenues.delete_one({"revenue_id": revenue_id})
        return result.deleted_count
