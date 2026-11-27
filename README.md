# The Persina Home

A family hub web app with a Flask backend. The backend acts as an API gateway: the browser only talks to
this app, and this app forwards requests to the microservices.

| Service | Folder | URL |
|---|---|---|
| Hub (this app) | `Main Program` | `http://localhost:5001` |
| Calendar Microservice | `Calendar Microservice` | `http://localhost:8000` |
| Flight Tracker Microservice | `FlightMicroservice/Flight-Tracker-Microservice` | `http://127.0.0.1:5002` |

Requires Python 3.10+. Each service runs in its own terminal.

## Hub setup

```bash
cd "Main Program"
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then set your home's coordinates in .env
python app.py
```

Open `http://localhost:5001`.

## Calendar Microservice setup

```bash
cd "Calendar Microservice"
pip install -r requirements.txt
python app.py
```

The hub uses the `persinaj` calendar (`data/events/persinaj.json`).

## Flight Tracker setup

The Flight Tracker looks up live aircraft from [adsb.lol](https://api.adsb.lol), so it needs an internet
connection. No API key is required.

```bash
cd FlightMicroservice/Flight-Tracker-Microservice
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

The service starts on `http://127.0.0.1:5002`. To check that it's running:

```bash
curl http://127.0.0.1:5002/health
# {"status": "ok"}
```

With the Flight Tracker and the hub both running, the hub exposes:

| Hub route | What it returns |
|---|---|
| `GET /api/flights/near` | Aircraft within 25 nautical miles of the hub, as `{"count": N, "aircraft": [...]}`. Optional `?lat=`, `?lon=`, and `?radius=` (1–100 nm) override the defaults. |
| `GET /api/flights/overhead` | Airborne flights within 8 nm of the hub along the ground, at any altitude, closest first, with origin and destination. Shown in the home screen banner. |
| `GET /api/flights/<callsign>` | One aircraft by callsign, e.g. `/api/flights/ual123`. Returns 404 if no aircraft matches. |

To try it: `curl http://localhost:5001/api/flights/near`

Routes come from the free [adsbdb.com](https://www.adsbdb.com) database, since ADS-B position data
doesn't include them. Airlines reuse flight numbers across legs, so a route is only shown when the
aircraft is actually between its two airports; otherwise the banner shows "Route unknown".

If the Flight Tracker isn't running, these routes return `503` with
`{"error": "Flight service is unavailable"}`.

## Configuration

Settings are read from environment variables. The hub loads them from `Main Program/.env`, which
is ignored by git so your home's location stays private. `.env.example` is the template.

| Variable | Default | Purpose |
|---|---|---|
| `HUB_LATITUDE` | required | Center of the flight search |
| `HUB_LONGITUDE` | required | Center of the flight search |
| `CALENDAR_SERVICE_URL` | `http://localhost:8000` | Calendar Microservice address |
| `CALENDAR_ID` | `persinaj` | Which calendar the hub reads and writes |
| `FLIGHT_SERVICE_URL` | `http://127.0.0.1:5002` | Flight Tracker address |

The hub's time zone is Eastern (`HUB_TIMEZONE = "America/New_York"` in `app.py`), which handles the
switch between EST and EDT automatically.
