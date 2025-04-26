import requests
from datetime import datetime
import pytz
import streamlit as st

# Verbose debug flag
VERBOSE = True

# Map station names to CTA map IDs
red_line_stations = {
    "Howard": "40900", "Jarvis": "41190", "Morse": "40100",
    "Loyola": "41300", "Bryn Mawr": "41380", "Berwyn": "40340",
    "Argyle": "41200", "Lawrence": "40770", "Sheridan": "40080",
    "Addison": "41420", "Belmont": "41320", "Fullerton": "41220",
    "North/Clybourn": "40650", "Chicago": "41450", "Grand": "40330",
    "Monroe": "41090", "Jackson": "40560", "Roosevelt": "41400",
    "Sox-35th": "40190", "47th": "41230", "Garfield": "41170",
    "63rd": "40910", "69th": "40990", "79th": "40240",
    "87th": "41430", "95th/Dan Ryan": "40450"
}

CTA_URL = "http://lapi.transitchicago.com/api/1.0/ttarrivals.aspx"
central = pytz.timezone('America/Chicago')


def get_arrivals(map_id: str, api_key: str):
    if VERBOSE:
        print(f"Calling CTA API URL: {CTA_URL}?key={api_key}&mapid={map_id}&outputType=JSON")
    params = {"key": api_key, "mapid": map_id, "outputType": "JSON"}
    res = requests.get(CTA_URL, params=params)
    if VERBOSE:
        print(f"Response status code: {res.status_code}")
    try:
        payload = res.json()
        if VERBOSE:
            print(f"Payload keys: {list(payload.keys())}")
    except Exception as e:
        st.error(f"CTA JSON error: {e}")
        if VERBOSE:
            print(f"Raw response text: {res.text}")
        return []
    etas = payload.get('ctatt', {}).get('eta', []) or []
    if VERBOSE:
        print(f"Found {len(etas)} ETA entries for map_id {map_id}")
    return etas


def find_next_train(arrivals: list, route: str, after_time: datetime = None):
    if VERBOSE:
        print(f"Filtering {len(arrivals)} arrivals for route {route}")
        print(f"After_time filter: {after_time}")
    trains = []
    for eta in arrivals:
        if eta.get('rt') != route:
            if VERBOSE:
                print(f"Skipping route {eta.get('rt')} != {route}")
            continue
        try:
            arr_raw = datetime.strptime(eta['arrT'], "%Y-%m-%dT%H:%M:%S")
        except Exception as e:
            if VERBOSE:
                print(f"Failed to parse arrT '{eta.get('arrT')}' for run {eta.get('rn')}")
            continue
        arr_central = central.localize(arr_raw).replace(tzinfo=None)
        if after_time is None or arr_central >= after_time:
            trains.append({'arrival': arr_central, 'run_number': eta['rn']})
            if VERBOSE:
                print(f"Accepting train run {eta['rn']} at {arr_central}")
        else:
            if VERBOSE:
                print(f"Discarding train run {eta['rn']} at {arr_central} < {after_time}")
    if trains:
        sorted_trains = sorted(trains, key=lambda t: t['arrival'])
        if VERBOSE:
            print(f"Next train: {sorted_trains[0]}")
        return sorted_trains[0]
    if VERBOSE:
        print("No trains found after filter.")
    return None


def track_train_to_destination(arrivals: list, run_number: str):
    if VERBOSE:
        print(f"Tracking run {run_number} to destination among {len(arrivals)} arrivals")
    for eta in arrivals:
        if eta.get('rn') == run_number:
            try:
                arr_raw = datetime.strptime(eta['arrT'], "%Y-%m-%dT%H:%M:%S")
            except Exception as e:
                if VERBOSE:
                    print(f"Error parsing arrival for rn {run_number}: {e}")
                return None
            arr_central = central.localize(arr_raw).replace(tzinfo=None)
            if VERBOSE:
                print(f"Arrival at destination: {arr_central}")
            return arr_central
    if VERBOSE:
        print(f"Run number {run_number} not found in arrivals.")
    return None


def plan_trip(orig: str, dest: str, api_key: str, user_time: datetime = None):
    if VERBOSE:
        print(f"Planning trip from {orig} to {dest} at user_time {user_time}")
    start_id = red_line_stations.get(orig)
    end_id = red_line_stations.get(dest)
    if not start_id or not end_id:
        if VERBOSE:
            print(f"Invalid station names: {orig}->{dest}")
        return None, None

    if user_time:
        ref = user_time.astimezone(central).replace(tzinfo=None) if user_time.tzinfo else user_time
    else:
        ref = datetime.now(central).replace(tzinfo=None)
    if VERBOSE:
        print(f"Reference time (central naive): {ref}")

    arrivals_start = get_arrivals(start_id, api_key)
    next_train = find_next_train(arrivals_start, 'Red', ref)
    if not next_train:
        if VERBOSE:
            print("No next train found at origin.")
        return None, None
    dep_time = next_train['arrival']

    arrivals_dest = get_arrivals(end_id, api_key)
    arr_time = track_train_to_destination(arrivals_dest, next_train['run_number'])
    if VERBOSE:
        print(f"Departure: {dep_time}, Arrival: {arr_time}")
    return dep_time, arr_time


def compute_fastest(orig: str, dest: str, api_key: str, user_time: datetime = None):
    dep, arr = plan_trip(orig, dest, api_key, user_time)
    if dep and arr:
        fastest = int((arr - dep).total_seconds())
        if VERBOSE:
            print(f"Fastest travel time: {fastest}s")
        return fastest, dep, arr
    if VERBOSE:
        print("Cannot compute fastest: missing dep or arr.")
    return None, None, None