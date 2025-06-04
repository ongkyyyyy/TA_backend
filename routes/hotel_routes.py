from flask import Blueprint  # type: ignore
from controllers.hotel_controller import HotelController
from models.hotels import Hotels
from controllers.middleware.auth_middleware import token_required  # Import token_required

def create_hotel_blueprint(app):
    hotel_bp = Blueprint("hotels", __name__)
    db = Hotels()
    controller = HotelController(db)

    hotel_bp.add_url_rule("/hotels", "get_hotels", token_required(controller.get_hotels), methods=["GET"])
    hotel_bp.add_url_rule("/hotels", "create_hotel", token_required(controller.create_hotel), methods=["POST"])
    hotel_bp.add_url_rule("/hotels/<hotel_id>", "update_hotel", token_required(controller.update_hotel), methods=["PUT"])
    hotel_bp.add_url_rule("/hotels/<hotel_id>", "delete_hotel", token_required(controller.delete_hotel), methods=["DELETE"])
    hotel_bp.add_url_rule("/hotels/dropdown", "get_hotels_dropdown", token_required(controller.get_hotels_dropdown), methods=["GET"])

    return hotel_bp
