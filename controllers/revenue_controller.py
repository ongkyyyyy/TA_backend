from flask import jsonify, request # type: ignore

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
        revenue = self.db.get_revenue_by_id(revenue_id)
        if revenue:
            return jsonify({"success": True, "data": revenue}), 200
        return jsonify({"success": False, "message": "Revenue not found"}), 404

    def create_revenue(self):
        revenue_data = request.json

        if not revenue_data.get("revenue_id"):
            return jsonify({"success": False, "message": "revenue_id is required"}), 400
        
        processed_data = self.db.add_revenue(revenue_data)

        return jsonify({"success": True, "message": "Revenue added successfully", "data": processed_data}), 201

    def edit_revenue(self, revenue_id):
        updated_data = request.json
        update_status = self.db.update_revenue(revenue_id, updated_data)

        if update_status == -1:
            return jsonify({"success": False, "message": "Revenue record not found"}), 404
        elif update_status == 0:
            return jsonify({"success": False, "message": "No matching fields found for update"}), 400
        else:
            return jsonify({"success": True, "message": "Revenue updated successfully"}), 200

    def remove_revenue(self, revenue_id):
        deleted_count = self.db.delete_revenue(revenue_id)
        if deleted_count:
            return jsonify({"success": True, "message": "Revenue deleted successfully"}), 200
        return jsonify({"success": False, "message": "Revenue not found"}), 404
