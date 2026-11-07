from flask import Flask, render_template, jsonify
from pathlib import Path
from storage import EventStore

app = Flask(__name__)

HUB_TIMEZONE = "America/New_York"
EVENTS_FILE = Path(__file__).parent / "data" / "events.json"

store = EventStore(EVENTS_FILE)

@app.get("/")
def index():
    return render_template("index.html", hub_timezone=HUB_TIMEZONE)

@app.get("/api/events")
def list_events():
    visible = [e for e in store.load() if e.get("deletedAt") is None]
    visible.sort(key=lambda e: e["start"])
    return jsonify(visible)

if __name__ == "__main__":
    app.run(debug=True, port=5001)
