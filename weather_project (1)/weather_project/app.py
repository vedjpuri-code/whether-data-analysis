from flask import Flask, render_template, jsonify
import json
from collections import defaultdict
from datetime import datetime

app = Flask(__name__)

# ── Load & parse JSON ──────────────────────────────────────────────────────────
def load_data():
    with open("data/weather_data.json", "r") as f:
        raw = json.load(f)
    for row in raw:
        row["dt"] = datetime.strptime(row["date"], "%Y-%m-%d")
        row["month"] = row["dt"].strftime("%B")
        row["month_num"] = row["dt"].month
    return raw

# ── Region analysis ────────────────────────────────────────────────────────────
def region_stats(data):
    city_data = defaultdict(list)
    for row in data:
        city_data[row["city"]].append(row)

    stats = []
    for city, rows in city_data.items():
        temps = [r["temperature"] for r in rows]
        rainfall = [r["rainfall"] for r in rows]
        humidity = [r["humidity"] for r in rows]
        stats.append({
            "city": city,
            "mean_temp": round(sum(temps) / len(temps), 1),
            "max_temp": max(temps),
            "min_temp": min(temps),
            "total_rainfall": round(sum(rainfall), 1),
            "mean_humidity": round(sum(humidity) / len(humidity), 1),
        })
    return sorted(stats, key=lambda x: x["mean_temp"], reverse=True)

# ── Monthly analysis ───────────────────────────────────────────────────────────
MONTH_ORDER = ["January","February","March","April","May","June",
               "July","August","September","October","November","December"]

def monthly_stats(data):
    month_data = defaultdict(list)
    for row in data:
        month_data[row["month"]].append(row)

    stats = []
    for month in MONTH_ORDER:
        if month not in month_data:
            continue
        rows = month_data[month]
        temps = [r["temperature"] for r in rows]
        rainfall = [r["rainfall"] for r in rows]
        humidity = [r["humidity"] for r in rows]
        stats.append({
            "month": month,
            "mean_temp": round(sum(temps) / len(temps), 1),
            "max_temp": max(temps),
            "min_temp": min(temps),
            "total_rainfall": round(sum(rainfall), 1),
            "mean_humidity": round(sum(humidity) / len(humidity), 1),
        })
    return stats

# ── Insights ───────────────────────────────────────────────────────────────────
def compute_insights(data):
    hottest  = max(data, key=lambda r: r["temperature"])
    coldest  = min(data, key=lambda r: r["temperature"])
    rainiest = max(data, key=lambda r: r["rainfall"])

    monthly = monthly_stats(data)
    hottest_month  = max(monthly, key=lambda m: m["mean_temp"])
    rainiest_month = max(monthly, key=lambda m: m["total_rainfall"])
    coldest_month  = min(monthly, key=lambda m: m["mean_temp"])

    region = region_stats(data)
    hottest_city  = max(region, key=lambda c: c["mean_temp"])
    rainiest_city = max(region, key=lambda c: c["total_rainfall"])
    coldest_city  = min(region, key=lambda c: c["mean_temp"])

    # Moving-average trend (all cities combined, sorted by date)
    sorted_data = sorted(data, key=lambda r: r["dt"])
    temps_all = [r["temperature"] for r in sorted_data]
    dates_all = [r["date"] for r in sorted_data]
    window = 5
    moving_avg = []
    for i in range(len(temps_all)):
        start = max(0, i - window + 1)
        moving_avg.append(round(sum(temps_all[start:i+1]) / (i - start + 1), 2))

    # Simple linear prediction (next 3 points)
    n = len(temps_all)
    x_mean = (n - 1) / 2
    y_mean = sum(temps_all) / n
    num = sum((i - x_mean) * (temps_all[i] - y_mean) for i in range(n))
    den = sum((i - x_mean) ** 2 for i in range(n))
    slope = num / den if den else 0
    intercept = y_mean - slope * x_mean
    predicted = [round(intercept + slope * (n + i), 2) for i in range(3)]

    return {
        "hottest_day":  {"date": hottest["date"],  "city": hottest["city"],  "temp": hottest["temperature"]},
        "coldest_day":  {"date": coldest["date"],  "city": coldest["city"],  "temp": coldest["temperature"]},
        "rainiest_day": {"date": rainiest["date"], "city": rainiest["city"], "rain": rainiest["rainfall"]},
        "hottest_month":  hottest_month["month"],
        "rainiest_month": rainiest_month["month"],
        "coldest_month":  coldest_month["month"],
        "hottest_city":   hottest_city["city"],
        "rainiest_city":  rainiest_city["city"],
        "coldest_city":   coldest_city["city"],
        "trend_dates": dates_all,
        "trend_temps": temps_all,
        "moving_avg": moving_avg,
        "predicted": predicted,
    }

# ── Routes ─────────────────────────────────────────────────────────────────────
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/region")
def region_page():
    return render_template("region.html")

@app.route("/monthly")
def monthly_page():
    return render_template("monthly.html")

@app.route("/insights")
def insights_page():
    return render_template("insights.html")

# ── API endpoints ──────────────────────────────────────────────────────────────
@app.route("/api/region")
def api_region():
    data = load_data()
    return jsonify(region_stats(data))

@app.route("/api/monthly")
def api_monthly():
    data = load_data()
    return jsonify(monthly_stats(data))

@app.route("/api/insights")
def api_insights():
    data = load_data()
    return jsonify(compute_insights(data))

if __name__ == "__main__":
    app.run(debug=True)
