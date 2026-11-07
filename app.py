from flask import Flask, render_template, jsonify

from datetime import datetime
from zoneinfo import ZoneInfo

app = Flask(__name__)

HUB_TIMEZONE = "America/New_York"
now = datetime.now(ZoneInfo(HUB_TIMEZONE))

EVENTS = [
    {
        "uid": "4",
        "title": "Dinner",
        "start": now.replace(hour=18, minute=30, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%S"),
        "durationMinutes": 60,
        "timeZone": HUB_TIMEZONE,
        "users": ["Leo"],
        "location": "Riverside Park · Field 2",
        "description": "",
        "status": "confirmed",
        "deletedAt": None,
    },
    {
        "uid": "1",
        "title": "Soccer practice",
        "start": now.replace(hour=15, minute=30, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%S"),
        "durationMinutes": 60,
        "timeZone": HUB_TIMEZONE,
        "users": ["Leo"],
        "location": "Riverside Park · Field 2",
        "description": "",
        "status": "confirmed",
        "deletedAt": None,
    },
    {
        "uid": "2",
        "title": "Soccer practice",
        "start": "2026-11-06T15:30:00",
        "durationMinutes": 60,
        "timeZone": HUB_TIMEZONE,
        "users": ["Leo"],
        "location": "Riverside Park · Field 2",
        "description": "",
        "status": "confirmed",
        "deletedAt": None,
    },
    {
        "uid": "2",
        "title": "Soccer practice",
        "start": "2026-11-10T15:30:00",
        "durationMinutes": 60,
        "timeZone": HUB_TIMEZONE,
        "users": ["Leo"],
        "location": "Riverside Park · Field 2",
        "description": "",
        "status": "confirmed",
        "deletedAt": None,
    }
]

@app.get("/")
def index():
    return render_template("index.html")

@app.get("/api/events")
def list_events():
    visible = [e for e in EVENTS if e["deletedAt"] is None]
    visible = sorted(visible, key=lambda e: e["start"])
    return jsonify(visible)

if __name__ == "__main__":
    app.run(debug=True)
