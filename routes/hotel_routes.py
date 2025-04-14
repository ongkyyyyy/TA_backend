from flask import Blueprint  # type: ignore
from controllers.hotel_controller import HotelController
from models.hotels import HotelsDB

def create_hotel_blueprint(app):
    hotel_bp = Blueprint("hotels", __name__)
    db = HotelsDB(app)
    controller = HotelController(db)

    hotel_bp.add_url_rule("/hotels", "get_hotels", controller.get_hotels, methods=["GET"])
    hotel_bp.add_url_rule("/hotels/<hotel_id>", "get_hotel", controller.get_hotel, methods=["GET"])
    hotel_bp.add_url_rule("/hotels", "create_hotel", controller.create_hotel, methods=["POST"])
    hotel_bp.add_url_rule("/hotels/<hotel_id>", "update_hotel", controller.update_hotel, methods=["PUT"])
    hotel_bp.add_url_rule("/hotels/<hotel_id>", "delete_hotel", controller.delete_hotel, methods=["DELETE"])

    return hotel_bp
