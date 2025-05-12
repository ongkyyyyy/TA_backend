from flask import jsonify, request  # type: ignore
from bson import ObjectId  # type: ignore
from datetime import datetime
from collections import defaultdict
from models.diagram import db
import calendar
from dateutil.parser import parse  # type: ignore


def get_month_key(date):
    if isinstance(date, str):
        date = parse(date)
    return date.strftime('%Y-%m')


def calculate_growth(current, previous):
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return round(((current - previous) / previous) * 100, 2)


def get_revenue_sentiment_diagram():
    hotel_ids_param = request.args.get("hotel_id", "All")
    year = request.args.get("year", type=int)

    today = datetime.today()
    current_year = today.year
    current_month = today.month

    # Handle hotel_id param
    if hotel_ids_param == "All":
        hotel_ids = None
    else:
        try:
            hotel_ids = [ObjectId(hid.strip()) for hid in hotel_ids_param.split(",")]
        except Exception:
            return jsonify({"error": "One or more hotel_id values are not valid ObjectIds."}), 400

    # Query revenues
    revenue_query = {}
    if hotel_ids:
        revenue_query["hotel_id"] = {"$in": hotel_ids}
    revenues = db.revenues.find(revenue_query)

    monthly_revenue = defaultdict(lambda: defaultdict(list))
    for rev in revenues:
        rev_date = datetime.strptime(rev["date"], "%d-%m-%Y")
        if year and rev_date.year != year:
            continue
        if year == current_year and rev_date.month > current_month:
            continue

        month_key = get_month_key(rev["date"])
        month = month_key if year else month_key[-2:]

        monthly_revenue[month]["room_revenue"].append(rev["room_details"]["total_room_revenue"])
        monthly_revenue[month]["restaurant_revenue"].append(rev["restaurant"]["total_restaurant_revenue"])
        monthly_revenue[month]["other_revenue"].append(rev["other_revenue"]["total_other_revenue"])
        monthly_revenue[month]["nett_revenue"].append(rev["nett_revenue"])
        monthly_revenue[month]["gross_revenue"].append(rev["gross_revenue"])
        monthly_revenue[month]["grand_total_revenue"].append(rev["grand_total_revenue"])

    # Query reviews
    review_query = {}
    if hotel_ids:
        review_query["hotel_id"] = {"$in": hotel_ids}
    reviews = list(db.reviews.find(review_query))

    monthly_sentiment = defaultdict(lambda: {
        "total": 0,
        "score_sum": 0,
        "positive": 0,
        "negative": 0,
        "neutral": 0,
    })

    sentiments = list(db.sentiments.find({
        "review_id": {"$in": [r["_id"] for r in reviews]}
    }))
    sentiment_map = {s["review_id"]: s for s in sentiments}

    for review in reviews:
        review_date = datetime.strptime(review["timestamp"], "%d-%m-%Y")
        if year and review_date.year != year:
            continue
        if year == current_year and review_date.month > current_month:
            continue

        month_key = get_month_key(review["timestamp"])
        month = month_key if year else month_key[-2:]

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

    # Setup month labels
    if year:
        month_limit = current_month if year == current_year else 12
        months_range = [f"{year}-{m:02d}" for m in range(1, month_limit + 1)]
        month_labels = [datetime.strptime(m, "%Y-%m").strftime("%b") for m in months_range]
        key_fn = lambda m: m
    else:
        months_range = [f"{m:02d}" for m in range(1, 13)]
        month_labels = [calendar.month_abbr[int(m)] for m in months_range]
        key_fn = lambda m: m[-2:]

    # Assemble result
    diagram_data = {
        "months": month_labels,
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
        key = key_fn(month_key)
        rev_data = monthly_revenue.get(key, {})
        sent = monthly_sentiment.get(key, {})

        for key_name in ["room_revenue", "restaurant_revenue", "other_revenue",
                         "nett_revenue", "gross_revenue", "grand_total_revenue"]:
            values = rev_data.get(key_name, [])
            total = round(sum(values), 2) if values else 0
            diagram_data[key_name].append(total)

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

    # Summary
    grand_totals = diagram_data["grand_total_revenue"]
    total_revenue = round(sum(grand_totals), 2)
    avg_monthly_revenue = round(total_revenue / len(grand_totals), 2) if grand_totals else 0
    total_reviews = sum(diagram_data["review_volume"])
    latest_sentiment_score = diagram_data["sentiment_score"][-1] if diagram_data["sentiment_score"] else 0

    best_month_index = grand_totals.index(max(grand_totals)) if grand_totals else 0
    best_month = diagram_data["months"][best_month_index] if diagram_data["months"] else ""

    if len(grand_totals) >= 2:
        revenue_growth_pct = calculate_growth(grand_totals[-1], grand_totals[-2])
        review_growth_pct = calculate_growth(diagram_data["review_volume"][-1], diagram_data["review_volume"][-2])
        sentiment_growth_pct = calculate_growth(diagram_data["sentiment_score"][-1], diagram_data["sentiment_score"][-2])
    else:
        revenue_growth_pct = review_growth_pct = sentiment_growth_pct = 0.0

    diagram_data["summary"] = {
        "total_revenue": total_revenue,
        "avg_monthly_revenue": avg_monthly_revenue,
        "total_reviews": total_reviews,
        "latest_sentiment_score": latest_sentiment_score,
        "best_month": {
            "month": best_month,
            "revenue": grand_totals[best_month_index] if grand_totals else 0
        }
    }

    diagram_data["growth"] = {
        "revenue_growth_pct": revenue_growth_pct,
        "reviews_growth_pct": review_growth_pct,
        "sentiment_growth_pct": sentiment_growth_pct
    }

    return jsonify(diagram_data)