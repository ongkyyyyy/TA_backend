from flask import jsonify, request  # type: ignore
from bson import ObjectId  # type: ignore
from datetime import datetime
from collections import defaultdict
from models.diagram import Diagram
import calendar
from dateutil.parser import parse  # type: ignore

db = Diagram()

def parse_date_safe(date_str, fmt="%d-%m-%Y"):
    try:
        return datetime.strptime(date_str, fmt)
    except Exception:
        return None

def get_month_key(date_str):
    dt = parse_date_safe(date_str)
    return dt.strftime("%Y-%m") if dt else None

def aggregate_revenue(revenues, year, current_year, current_month):
    result = defaultdict(lambda: defaultdict(list))
    for rev in revenues:
        rev_date = parse_date_safe(rev.get("date"))
        if not rev_date:
            continue
        if year and rev_date.year != year:
            continue
        if year == current_year and rev_date.month > current_month:
            continue

        month_key = get_month_key(rev["date"])
        if not month_key:
            continue

        month = month_key if year else month_key[-2:]
        fields = ["room_revenue", "restaurant_revenue", "other_revenue", 
                  "nett_revenue", "gross_revenue", "grand_total_revenue"]
        rev_map = {
            "room_revenue": rev.get("room_details", {}).get("total_room_revenue", 0),
            "restaurant_revenue": rev.get("restaurant", {}).get("total_restaurant_revenue", 0),
            "other_revenue": rev.get("other_revenue", {}).get("total_other_revenue", 0),
            "nett_revenue": rev.get("nett_revenue", 0),
            "gross_revenue": rev.get("gross_revenue", 0),
            "grand_total_revenue": rev.get("grand_total_revenue", 0)
        }

        for key in fields:
            result[month][key].append(rev_map[key])
    return result

def aggregate_sentiment(reviews, sentiments, year, current_year, current_month):
    result = defaultdict(lambda: {
        "total": 0, "score_sum": 0,
        "positive": 0, "negative": 0, "neutral": 0
    })

    sentiment_map = {s["review_id"]: s for s in sentiments}

    for review in reviews:
        review_date = parse_date_safe(review.get("timestamp"))
        if not review_date:
            continue
        if year and review_date.year != year:
            continue
        if year == current_year and review_date.month > current_month:
            continue

        month_key = get_month_key(review["timestamp"])
        if not month_key:
            continue
        month = month_key if year else month_key[-2:]

        sentiment = sentiment_map.get(review["_id"])
        if not sentiment:
            continue

        label = sentiment.get("sentiment")
        result[month]["total"] += 1
        if label == "positive":
            result[month]["positive"] += 1
            result[month]["score_sum"] += 1
        elif label == "negative":
            result[month]["negative"] += 1
            result[month]["score_sum"] -= 1
        elif label == "neutral":
            result[month]["neutral"] += 1
    return result

def calculate_growth(current, previous):
    if previous == 0:
        return 0.0
    return round(((current - previous) / previous) * 100, 2)

def get_revenue_sentiment_diagram():
    hotel_ids_param = request.args.get("hotel_id", "All")
    year = request.args.get("year", type=int)

    today = datetime.today()
    current_year, current_month = today.year, today.month

    if hotel_ids_param == "All":
        hotel_ids = None
    else:
        try:
            hotel_ids = [ObjectId(hid.strip()) for hid in hotel_ids_param.split(",")]
        except Exception:
            return jsonify({"error": "Invalid hotel_id format."}), 400

    revenue_query = {"hotel_id": {"$in": hotel_ids}} if hotel_ids else {}
    revenues = db.revenues.find(revenue_query)
    monthly_revenue = aggregate_revenue(revenues, year, current_year, current_month)

    review_query = {"hotel_id": {"$in": hotel_ids}} if hotel_ids else {}
    reviews = list(db.reviews.find(review_query))
    sentiments = list(db.sentiments.find({"review_id": {"$in": [r["_id"] for r in reviews]}}))
    monthly_sentiment = aggregate_sentiment(reviews, sentiments, year, current_year, current_month)

    if year:
        month_limit = current_month if year == current_year else 12
        months_range = [f"{year}-{m:02d}" for m in range(1, month_limit + 1)]
        month_labels = [datetime.strptime(m, "%Y-%m").strftime("%b") for m in months_range]
        key_fn = lambda m: m
    else:
        months_range = [f"{m:02d}" for m in range(1, 13)]
        month_labels = [calendar.month_abbr[int(m)] for m in months_range]
        key_fn = lambda m: m[-2:]

    diagram_data = {
        "months": month_labels,
        "room_revenue": [], "restaurant_revenue": [], "other_revenue": [],
        "nett_revenue": [], "gross_revenue": [], "grand_total_revenue": [],
        "sentiment_score": [], "composite_sentiment_index": [],
        "positive_sentiment": [], "negative_sentiment": [], "neutral_sentiment": [],
        "review_volume": [], "positive_ratio": [], "negative_ratio": [], "neutral_ratio": [],
        "room_revenue_ratio": [], "restaurant_revenue_ratio": [], "other_revenue_ratio": []
    }

    for month_key in months_range:
        key = key_fn(month_key)
        rev_data = monthly_revenue.get(key, {})
        sent = monthly_sentiment.get(key, {})

        room_total = sum(rev_data.get("room_revenue", [])) if rev_data.get("room_revenue") else 0
        restaurant_total = sum(rev_data.get("restaurant_revenue", [])) if rev_data.get("restaurant_revenue") else 0
        other_total = sum(rev_data.get("other_revenue", [])) if rev_data.get("other_revenue") else 0
        nett_total = sum(rev_data.get("nett_revenue", [])) if rev_data.get("nett_revenue") else 0
        gross_total = sum(rev_data.get("gross_revenue", [])) if rev_data.get("gross_revenue") else 0
        grand_total = sum(rev_data.get("grand_total_revenue", [])) if rev_data.get("grand_total_revenue") else 0

        diagram_data["room_revenue"].append(round(room_total, 2))
        diagram_data["restaurant_revenue"].append(round(restaurant_total, 2))
        diagram_data["other_revenue"].append(round(other_total, 2))
        diagram_data["nett_revenue"].append(round(nett_total, 2))
        diagram_data["gross_revenue"].append(round(gross_total, 2))
        diagram_data["grand_total_revenue"].append(round(grand_total, 2))

        diagram_data["room_revenue_ratio"].append(round((room_total / gross_total) * 100, 2) if gross_total else 0)
        diagram_data["restaurant_revenue_ratio"].append(round((restaurant_total / gross_total) * 100, 2) if gross_total else 0)
        diagram_data["other_revenue_ratio"].append(round((other_total / gross_total) * 100, 2) if gross_total else 0)

        total = sent.get("total", 0)
        pos, neg, neu = sent.get("positive", 0), sent.get("negative", 0), sent.get("neutral", 0)
        wsi = ((pos * 1) + (neu * 0.5)) / total if total else 0
        csi = ((pos / total) * 1.0 + (neu / total) * 0.5 - (neg / total) * 1.0) if total else 0

        diagram_data["sentiment_score"].append(round(wsi * 100, 2))
        diagram_data["composite_sentiment_index"].append(round(((csi + 1) / 2) * 100, 2) if total else 50)
        diagram_data["positive_sentiment"].append(pos)
        diagram_data["negative_sentiment"].append(neg)
        diagram_data["neutral_sentiment"].append(neu)
        diagram_data["review_volume"].append(total)
        diagram_data["positive_ratio"].append(round(pos / total, 2) if total else 0)
        diagram_data["negative_ratio"].append(round(neg / total, 2) if total else 0)
        diagram_data["neutral_ratio"].append(round(neu / total, 2) if total else 0)

    grand_totals = diagram_data["grand_total_revenue"]
    sentiment_scores = diagram_data["sentiment_score"]
    review_volumes = diagram_data["review_volume"]

    total_revenue = round(sum(grand_totals), 2)
    active_months = sum(1 for r in grand_totals if r > 0)
    avg_monthly_revenue = round(total_revenue / active_months, 2) if active_months else 0

    total_reviews = sum(review_volumes)
    avg_review_volume = round(total_reviews / len(review_volumes), 2) if review_volumes else 0

    total_pos = sum(diagram_data["positive_sentiment"])
    total_neg = sum(diagram_data["negative_sentiment"])
    total_neu = sum(diagram_data["neutral_sentiment"])
    pos_neg_ratio = round(total_pos / total_neg, 2) if total_neg else total_pos

    avg_sent_score = round(sum(sentiment_scores) / len(sentiment_scores), 2) if sentiment_scores else 0
    latest_sent_score = sentiment_scores[-1] if sentiment_scores else 0

    best_idx = grand_totals.index(max(grand_totals)) if grand_totals else 0
    worst_vals = [v for v in grand_totals if v > 0]
    worst_idx = grand_totals.index(min(worst_vals)) if worst_vals else 0

    best_sent_idx = sentiment_scores.index(max(sentiment_scores)) if sentiment_scores else 0
    worst_sent_idx = sentiment_scores.index(min(sentiment_scores)) if sentiment_scores else 0
    peak_review_idx = review_volumes.index(max(review_volumes)) if review_volumes else 0

    diagram_data["summary"] = {
        "total_revenue": total_revenue,
        "avg_monthly_revenue": avg_monthly_revenue,
        "active_revenue_months": active_months,
        "total_reviews": total_reviews,
        "avg_review_volume": avg_review_volume,
        "latest_sentiment_score": latest_sent_score,
        "avg_sentiment_score": avg_sent_score,
        "positive_negative_ratio": pos_neg_ratio,
        "total_positive_sentiment": total_pos,
        "total_negative_sentiment": total_neg,
        "total_neutral_sentiment": total_neu,
        "best_month": {"month": diagram_data["months"][best_idx], "revenue": grand_totals[best_idx]},
        "worst_month": {"month": diagram_data["months"][worst_idx], "revenue": grand_totals[worst_idx]},
        "best_sentiment_month": {"month": diagram_data["months"][best_sent_idx], "score": sentiment_scores[best_sent_idx]},
        "worst_sentiment_month": {"month": diagram_data["months"][worst_sent_idx], "score": sentiment_scores[worst_sent_idx]},
        "peak_review_month": {"month": diagram_data["months"][peak_review_idx], "reviews": review_volumes[peak_review_idx]},
    }

    if len(grand_totals) >= 2:
        diagram_data["growth"] = {
            "revenue_growth_pct": calculate_growth(grand_totals[-1], grand_totals[-2]),
            "reviews_growth_pct": calculate_growth(review_volumes[-1], review_volumes[-2]),
            "sentiment_growth_pct": calculate_growth(sentiment_scores[-1], sentiment_scores[-2])
        }
    else:
        diagram_data["growth"] = {
            "revenue_growth_pct": 0.0,
            "reviews_growth_pct": 0.0,
            "sentiment_growth_pct": 0.0
        }

    return jsonify(diagram_data)