from flask import Flask, render_template, jsonify, request, abort
from pathlib import Path
from datetime import datetime, timedelta, timezone
import uuid
from storage import EventStore

app = Flask(__name__)

HUB_TIMEZONE = "America/New_York"
FAMILY = ["Dan", "Liv", "Leo", "Mia"]
UNDO_SECONDS = 5
PURGE_AFTER_SECONDS = UNDO_SECONDS + 5
EVENTS_FILE = Path(__file__).parent / "data" / "events.json"

store = EventStore(EVENTS_FILE)

def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def purge_deleted(events):
    #Soft-deleted events stay in the file for the undo window, then get dropped the next time anything is saved
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=PURGE_AFTER_SECONDS)
    events[:] = [
        e for e in events
        if e.get("deletedAt") is None or datetime.fromisoformat(e["deletedAt"]) > cutoff
    ]

def find_event(events, uid):
    for e in events:
        if e["uid"] == uid:
            return e
    abort(404)

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
    visible = [e for e in store.load() if e.get("deletedAt") is None]
    visible.sort(key=lambda e: e["start"])
    return jsonify(visible)

@app.post("/api/events")
def add_event():
    form = request.get_json()
    start = datetime.fromisoformat(f"{form['date']}T{form['startTime']}")
    end = datetime.fromisoformat(f"{form['date']}T{form['endTime']}")
    event = {
        "@type": "calendarEvent",
        "uid": str(uuid.uuid4()),
        "updated": utc_now(),
        "title": form["title"].strip(),
        "participants": form["participants"],
        "description": form.get("description", "").strip(),
        "start": start.strftime("%Y-%m-%dT%H:%M:%S"),
        "timeZone": HUB_TIMEZONE,
        "durationMinutes": int((end - start).total_seconds() // 60),
        "location": form.get("location", "").strip(),
        "status": "confirmed",
        "deletedAt": None,
    }

    def add(events):
        purge_deleted(events)
        events.append(event)

    store.update(add)
    return jsonify(event), 201

@app.delete("/api/events/<uid>")
def delete_event(uid):
    def soft_delete(events):
        purge_deleted(events)
        event = find_event(events, uid)
        event["deletedAt"] = event["updated"] = utc_now()

    store.update(soft_delete)
    return "", 204

@app.post("/api/events/<uid>/restore")
def restore_event(uid):
    def restore(events):
        purge_deleted(events)
        event = find_event(events, uid)
        event["deletedAt"] = None
        event["updated"] = utc_now()
        return event

    return jsonify(store.update(restore))

if __name__ == "__main__":
    app.run(debug=True, port=5001)
