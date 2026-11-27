from flask import Flask, render_template, jsonify, request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
import math
import os
import requests

load_dotenv(Path(__file__).parent / ".env")

app = Flask(__name__)

HUB_TIMEZONE = "America/New_York"
FAMILY = ["Dan", "Liv", "Leo", "Sarah"]
UNDO_SECONDS = 5
CALENDAR_SERVICE_URL = os.environ.get("CALENDAR_SERVICE_URL", "http://localhost:8000")
CALENDAR_ID = os.environ.get("CALENDAR_ID", "persinaj")
EVENTS_URL = f"{CALENDAR_SERVICE_URL}/calendars/{CALENDAR_ID}/events"
FLIGHT_SERVICE_URL = os.environ.get("FLIGHT_SERVICE_URL", "http://127.0.0.1:5002")
HUB_LATITUDE = float(os.environ["HUB_LATITUDE"])
HUB_LONGITUDE = float(os.environ["HUB_LONGITUDE"])
FLIGHT_RADIUS_NM = 25
OVERHEAD_LIMIT = 12
# Ground distance from the hub that counts as overhead, at any altitude.
OVERHEAD_RADIUS_NM = 8
EARTH_RADIUS_NM = 3440
# How far off the straight line between its airports a plane can be before
# its looked-up route is assumed to belong to a different leg of that flight number.
ROUTE_DETOUR_NM = 40
ROUTE_SERVICE_URL = "https://api.adsbdb.com/v0/callsign"

# callsign -> route dict, or None when adsbdb doesn't know the callsign
route_cache = {}

def call_service(name, method, url, **kwargs):
    """
    Send a request to a microservice and return its JSON and status code.
    """
    try:
        response = requests.request(method, url, timeout=10, **kwargs)
    except requests.RequestException:
        return {"error": f"{name} service is unavailable"}, 503
    return response.json(), response.status_code


### Services ###

def calendar_service(method, url, **kwargs):
    """
    Send a request to the calendar service and return its JSON and status code.
    """
    return call_service("Calendar", method, url, **kwargs)

def flight_service(path, **kwargs):
    """
    Send a request to the flight service and return its JSON and status code.
    """
    return call_service("Flight", "GET", f"{FLIGHT_SERVICE_URL}{path}", **kwargs)

def airport(info):
    return {
        "code": info.get("iata_code") or info["icao_code"],
        "city": info.get("municipality"),
        "latitude": info["latitude"],
        "longitude": info["longitude"],
    }

def distance_nm(lat1, lon1, lat2, lon2):
    """
    Great-circle distance between two points, in nautical miles.
    """
    lat1, lon1, lat2, lon2 = map(math.radians, (lat1, lon1, lat2, lon2))
    a = (math.sin((lat2 - lat1) / 2) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2)
    return 2 * EARTH_RADIUS_NM * math.asin(math.sqrt(a))

def ground_distance_nm(aircraft):
    """
    Distance along the ground from the hub to the aircraft, or None without a position.
    """
    if aircraft["latitude"] is None or aircraft["longitude"] is None:
        return None
    return distance_nm(HUB_LATITUDE, HUB_LONGITUDE, aircraft["latitude"], aircraft["longitude"])

def on_route(aircraft, route):
    """
    Whether the aircraft is roughly between the route's airports.
    """
    origin, destination = route["origin"], route["destination"]
    position = (aircraft["latitude"], aircraft["longitude"])
    direct = distance_nm(origin["latitude"], origin["longitude"], destination["latitude"], destination["longitude"])
    via_aircraft = (distance_nm(origin["latitude"], origin["longitude"], *position)
                    + distance_nm(*position, destination["latitude"], destination["longitude"]))
    return via_aircraft - direct <= ROUTE_DETOUR_NM

def public_airport(info):
    return {"code": info["code"], "city": info["city"]}

def flight_route(callsign):
    """
    Look up a flight's origin and destination by callsign
    """
    if callsign in route_cache:
        return route_cache[callsign]
    try:
        response = requests.get(f"{ROUTE_SERVICE_URL}/{callsign}", timeout=5)
    except requests.RequestException:
        return None
    if response.status_code == 404:
        route_cache[callsign] = None
        return None
    if not response.ok:
        return None
    flightroute = response.json()["response"]["flightroute"]
    route = {
        "origin": airport(flightroute["origin"]),
        "destination": airport(flightroute["destination"]),
    }
    route_cache[callsign] = route
    return route

###
### Routes ###
###

@app.get("/")
def index():
    return render_template(
        "index.html",
        hub_timezone=HUB_TIMEZONE,
        family=FAMILY,
        undo_seconds=UNDO_SECONDS,
    )

## Calendar routes ##
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

## Flight routes ##
@app.get("/api/flights/near")
def flights_near():
    params = {
        "lat": request.args.get("lat", HUB_LATITUDE),
        "lon": request.args.get("lon", HUB_LONGITUDE),
        "radius": request.args.get("radius", FLIGHT_RADIUS_NM),
    }
    result, status = flight_service("/aircraft/near", params=params)
    return jsonify(result), status

@app.get("/api/flights/overhead")
def flights_overhead():
    """
    Airborne flights over the hub at any altitude, closest first, for the home screen banner.
    """
    result, status = flight_service("/aircraft/near", params={
        "lat": HUB_LATITUDE,
        "lon": HUB_LONGITUDE,
        "radius": OVERHEAD_RADIUS_NM,
    })
    if status != 200:
        return jsonify(result), status

    overhead = []
    for a in result["aircraft"]:
        ground = ground_distance_nm(a)
        if a["callsign"] and not a["on_ground"] and ground is not None and ground <= OVERHEAD_RADIUS_NM:
            overhead.append((ground, a))
    overhead.sort(key=lambda pair: pair[0])
    aircraft = [a for _, a in overhead[:OVERHEAD_LIMIT]]

    with ThreadPoolExecutor(max_workers=6) as pool:
        routes = list(pool.map(flight_route, [a["callsign"] for a in aircraft]))

    flights = []
    for a, route in zip(aircraft, routes):
        known = route is not None and on_route(a, route)
        flights.append({
            "callsign": a["callsign"],
            "aircraft_type": a["aircraft_type"],
            "origin": public_airport(route["origin"]) if known else None,
            "destination": public_airport(route["destination"]) if known else None,
        })
    return jsonify({"flights": flights})

@app.get("/api/flights/<callsign>")
def flight_by_callsign(callsign):
    aircraft, status = flight_service(f"/aircraft/callsign/{callsign}")
    return jsonify(aircraft), status

if __name__ == "__main__":
    app.run(debug=True, port=5001)
