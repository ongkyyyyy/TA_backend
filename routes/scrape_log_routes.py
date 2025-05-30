from flask import Blueprint  # type: ignore
from controllers.scrape_log_controller import ScrapeLogController

def create_scrape_log_blueprint(app):
    bp = Blueprint("scrape_logs", __name__)
    controller = ScrapeLogController(app.scrape_log_db)

    bp.add_url_rule("/scrape_logs", "get_scrape_logs", controller.get_scrape_logs, methods=["GET"])
    bp.add_url_rule("/scrape_logs/<log_id>", "get_scrape_log", controller.get_scrape_log, methods=["GET"])
    bp.add_url_rule("/scrape_logs", "create_scrape_log", controller.create_scrape_log, methods=["POST"])
    bp.add_url_rule("/scrape_logs/<log_id>", "update_scrape_log", controller.update_scrape_log, methods=["PUT"])
    bp.add_url_rule("/scrape_logs/<log_id>", "delete_scrape_log", controller.delete_scrape_log, methods=["DELETE"])

    return bp
