import requests
from datetime import datetime
import pytz
import streamlit as st

# Map station names to CTA map IDs
red_line_stations = {
    "Howard":                   "40900",
    "Jarvis":                   "41190",
    "Morse":                    "40100",
    "Loyola":                   "41300",
    "Bryn Mawr":                "41380",
    "Berwyn":                   "40340",
    "Argyle":                   "41200",
    "Lawrence":                 "40770",
    "Sheridan":                 "40080",
    "Addison":                  "41420",
    "Belmont":                  "41320",
    "Fullerton":                "41220",
    "North/Clybourn":           "40650",
    "Chicago":                  "41450",
    "Grand":                    "40330",
    "Monroe":                   "41090",
    "Jackson":                  "40560",
    "Roosevelt":                "41400",
    "Sox-35th":                 "40190",
    "47th":                     "41230",
    "Garfield":                 "41170",
    "63rd":                     "40910",
    "69th":                     "40990",
    "79th":                     "40240",
    "87th":                     "41430",
    "95th/Dan Ryan":            "40450",
}

CTA_URL = "http://lapi.transitchicago.com/api/1.0/ttarrivals.aspx"
central = pytz.timezone('America/Chicago')


def get_arrivals(map_id: str, api_key: str):
    params = {"key": api_key, "mapid": map_id, "outputType": "JSON"}
    res = requests.get(CTA_URL, params=params)
    try:
        payload = res.json()
    except Exception as e:
        st.error(f"CTA JSON error: {e}")
        return []
    return payload.get('ctatt', {}).get('eta', [])


def find_next_train(arrivals: list, route: str, after_time: datetime = None):
    trains = []
    for eta in arrivals:
        if eta.get('rt') != route:
            continue
        try:
            arr = datetime.strptime(eta['arrT'], "%Y-%m-%dT%H:%M:%S")
            arr = central.localize(arr)
            if after_time is None or arr >= after_time:
                trains.append({'arrival': arr.replace(tzinfo=None), 'run_number': eta['rn']})
        except Exception:
            continue
    if trains:
        return sorted(trains, key=lambda t: t['arrival'])[0]
    return None


def track_train_to_destination(arrivals: list, run_number: str):
    for eta in arrivals:
        if eta.get('rn') == run_number:
            try:
                return datetime.strptime(eta['arrT'], "%Y-%m-%dT%H:%M:%S")
            except:
                return None
    return None


def plan_trip(start: str, end: str, api_key: str, user_time: datetime = None):
    start_id = red_line_stations.get(start)
    end_id = red_line_stations.get(end)
    if not start_id or not end_id:
        return None, None
    arrivals = get_arrivals(start_id, api_key)
    now = central.localize(user_time) if user_time and user_time.tzinfo else central.localize(user_time or datetime.now(central))
    next_train = find_next_train(arrivals, route="Red", after_time=now)
    if not next_train:
        return None, None
    dep_time = next_train['arrival']
    dest_arrivals = get_arrivals(end_id, api_key)
    arr_time = track_train_to_destination(dest_arrivals, next_train['run_number'])
    return dep_time, arr_time


def compute_fastest(orig: str, dest: str, api_key: str):
    dep, arr = plan_trip(orig, dest, api_key)
    if dep and arr:
        return int((arr - dep).total_seconds()), dep, arr
    return None, None, None