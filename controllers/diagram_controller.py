from flask import jsonify, request # type: ignore
from bson import ObjectId # type: ignore
from datetime import datetime
from collections import defaultdict
from models.diagram import db
import calendar
from dateutil.parser import parse # type: ignore

def get_month_key(date):
    if isinstance(date, str):
        date = parse(date)
    return date.strftime('%Y-%m')

def month_label(date_str):
    dt = datetime.strptime(date_str, "%Y-%m")
    return f"{calendar.month_abbr[dt.month]} {dt.year}"

def get_filter_year():
    year = request.args.get('year')
    return int(year) if year and year.isdigit() else None

def get_revenue_sentiment_diagram():
    hotel_id = request.args.get("hotel_id", "All")
    year = request.args.get("year", type=int)
    today = datetime.today()
    current_year = today.year
    current_month = today.month

    revenue_query = {}
    if hotel_id != "All":
        revenue_query["hotel_id"] = ObjectId(hotel_id)

    revenues = [
        rev for rev in db.revenues.find(revenue_query)
        if datetime.strptime(rev["date"], "%d-%m-%Y").year == year and
           (year != current_year or datetime.strptime(rev["date"], "%d-%m-%Y").month <= current_month)
    ]

    monthly_revenue = defaultdict(lambda: defaultdict(list))
    for rev in revenues:
        month = get_month_key(rev["date"])
        monthly_revenue[month]["room_revenue"].append(rev["room_details"]["total_room_revenue"])
        monthly_revenue[month]["restaurant_revenue"].append(rev["restaurant"]["total_restaurant_revenue"])
        monthly_revenue[month]["other_revenue"].append(rev["other_revenue"]["total_other_revenue"])
        monthly_revenue[month]["nett_revenue"].append(rev["nett_revenue"])
        monthly_revenue[month]["gross_revenue"].append(rev["gross_revenue"])
        monthly_revenue[month]["grand_total_revenue"].append(rev["grand_total_revenue"])

    review_query = {} if hotel_id == "All" else {"hotel_id": ObjectId(hotel_id)}
    reviews = [
        r for r in db.reviews.find(review_query)
        if datetime.strptime(r["timestamp"], "%d-%m-%Y").year == year and
           (year != current_year or datetime.strptime(r["timestamp"], "%d-%m-%Y").month <= current_month)
    ]

    sentiment_map = {
        s["review_id"]: s for s in db.sentiments.find({
            "review_id": {"$in": [r["_id"] for r in reviews]}
        })
    }

    monthly_sentiment = defaultdict(lambda: {
        "total": 0,
        "score_sum": 0,
        "positive": 0,
        "negative": 0,
        "neutral": 0,
    })

    for review in reviews:
        month = get_month_key(review["timestamp"])
        sentiment = sentiment_map.get(review["_id"])
        if not sentiment:
            continue

        label = sentiment["sentiment"]
        if label == "positive":
            monthly_sentiment[month]["positive"] += 1
            monthly_sentiment[month]["score_sum"] += 1
        elif label == "negative":
            monthly_sentiment[month]["negative"] += 1
            monthly_sentiment[month]["score_sum"] -= 1
        elif label == "neutral":
            monthly_sentiment[month]["neutral"] += 1

        monthly_sentiment[month]["total"] += 1

    month_limit = current_month if year == current_year else 12
    months_range = [f"{year}-{m:02d}" for m in range(1, month_limit + 1)]

    diagram_data = {
        "months": [],
        "room_revenue": [],
        "restaurant_revenue": [],
        "other_revenue": [],
        "nett_revenue": [],
        "gross_revenue": [],
        "grand_total_revenue": [],
        "sentiment_score": [],
        "composite_sentiment_index": [],
        "positive_sentiment": [],
        "negative_sentiment": [],
        "neutral_sentiment": [],
        "review_volume": [],
        "positive_ratio": [],
        "negative_ratio": [],
        "neutral_ratio": [],
    }

    for month_key in months_range:
        label = datetime.strptime(month_key, "%Y-%m").strftime("%b")
        diagram_data["months"].append(label)

        for key in ["room_revenue", "restaurant_revenue", "other_revenue",
                    "nett_revenue", "gross_revenue", "grand_total_revenue"]:
            values = monthly_revenue[month_key].get(key, [])
            total = round(sum(values), 2) if values else 0
            diagram_data[key].append(total)

        sent = monthly_sentiment.get(month_key, {})
        total_reviews = sent.get("total", 0)
        pos = sent.get("positive", 0)
        neg = sent.get("negative", 0)
        neu = sent.get("neutral", 0)
        
        wsi = ((pos * 1) + (neu * 0.5)) / total_reviews if total_reviews else 0
        sentiment_score = round(wsi * 100, 2)

        pos_ratio = pos / total_reviews if total_reviews else 0
        neg_ratio = neg / total_reviews if total_reviews else 0
        neu_ratio = neu / total_reviews if total_reviews else 0

        csi_raw = (pos_ratio * 1.0) + (neu_ratio * 0.5) + (neg_ratio * -1.0)
        csi_normalized = round(((csi_raw + 1) / 2) * 100, 2) if total_reviews else 50

        diagram_data["sentiment_score"].append(sentiment_score)
        diagram_data["composite_sentiment_index"].append(csi_normalized)
        diagram_data["positive_sentiment"].append(pos)
        diagram_data["negative_sentiment"].append(neg)
        diagram_data["neutral_sentiment"].append(neu)
        diagram_data["review_volume"].append(total_reviews)
        diagram_data["positive_ratio"].append(round(pos_ratio, 2))
        diagram_data["negative_ratio"].append(round(neg_ratio, 2))
        diagram_data["neutral_ratio"].append(round(neu_ratio, 2))

    return jsonify(diagram_data)