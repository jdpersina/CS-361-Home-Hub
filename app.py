from flask import Flask, render_template, jsonify, request
from datetime import datetime
import os
import requests

app = Flask(__name__)

HUB_TIMEZONE = "America/New_York"
FAMILY = ["Dan", "Liv", "Leo", "Sarah"]
UNDO_SECONDS = 5
CALENDAR_SERVICE_URL = os.environ.get("CALENDAR_SERVICE_URL", "http://localhost:8000")
CALENDAR_ID = os.environ.get("CALENDAR_ID", "persinaj")
EVENTS_URL = f"{CALENDAR_SERVICE_URL}/calendars/{CALENDAR_ID}/events"

def calendar_service(method, url, **kwargs):
    """
    Send a request to the Calendar Microservice and return its JSON and status code.
    """
    try:
        response = requests.request(method, url, timeout=5, **kwargs)
    except requests.RequestException:
        return {"error": "Calendar service is unavailable"}, 503
    return response.json(), response.status_code

@app.get("/")
def index():
    return render_template(
        "index.html",
        hub_timezone=HUB_TIMEZONE,
        family=FAMILY,
        undo_seconds=UNDO_SECONDS,
    )

@app.get("/api/events")
def list_events():
    events, status = calendar_service("GET", EVENTS_URL)
    if status == 200:
        events.sort(key=lambda e: e["start"])
    return jsonify(events), status

@app.post("/api/events")
def add_event():
    form = request.get_json()
    start = datetime.fromisoformat(f"{form['date']}T{form['startTime']}")
    end = datetime.fromisoformat(f"{form['date']}T{form['endTime']}")
    event, status = calendar_service("POST", EVENTS_URL, json={
        "title": form["title"].strip(),
        "participants": form["participants"],
        "description": form.get("description", "").strip(),
        "start": start.strftime("%Y-%m-%dT%H:%M:%S"),
        "timeZone": HUB_TIMEZONE,
        "durationMinutes": int((end - start).total_seconds() // 60),
        "location": form.get("location", "").strip(),
    })
    return jsonify(event), status

@app.delete("/api/events/<uid>")
def delete_event(uid):
    event, status = calendar_service("DELETE", f"{EVENTS_URL}/{uid}")
    return jsonify(event), status

@app.post("/api/events/<uid>/restore")
def restore_event(uid):
    event, status = calendar_service("POST", f"{EVENTS_URL}/{uid}/restore")
    return jsonify(event), status

if __name__ == "__main__":
    app.run(debug=True, port=5001)
