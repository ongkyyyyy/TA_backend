import os
import subprocess
from models.hotels import Hotels

hotels_db = Hotels()
hotels_collection = hotels_db.collection

SOURCE_MAP = {
    "traveloka": ("scrape_reviews.js", "traveloka_link"),
    "ticketcom": ("ticketcom_scrape_reviews.js", "ticketcom_link"),
    "agoda": ("agoda_scrape_reviews.js", "agoda_link"),
    "tripcom": ("tripcom_scrape_reviews.js", "tripcom_link"),
}

def run_scraping_for_all_hotels():
    print("[Scheduler] Starting scraping job for all hotels...")

    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    script_dir = os.path.join(backend_dir, "scraper")

    for hotel in hotels_collection.find():
        hotel_id = str(hotel["_id"])

        for source, (script_name, link_field) in SOURCE_MAP.items():
            hotel_url = hotel.get(link_field)
            if not hotel_url:
                print(f"[{hotel.get('name', hotel_id)}] No link for {source}, skipping.")
                continue

            script_path = os.path.join(script_dir, script_name)
            if not os.path.exists(script_path):
                print(f"[Error] Script not found: {script_path}")
                continue

            try:
                print(f"[{hotel.get('name', hotel_id)}] Scraping from {source}...")
                result = subprocess.run(
                    ["node", script_path, hotel_url, hotel_id],
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace"
                )

                if result.returncode != 0:
                    print(f"[Error] {source} scraping failed for {hotel.get('name', hotel_id)}: {result.stderr}")
                else:
                    print(f"[Success] {source} scraping completed for {hotel.get('name', hotel_id)}")

            except Exception as e:
                print(f"[Exception] While scraping {source} for {hotel.get('name', hotel_id)}: {e}")

    print("[Scheduler] Scraping job completed.")
