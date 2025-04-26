import requests
from datetime import datetime
import streamlit as st

def get_cta_schedule(cta_key: str, origin: str, destination: str):
    url = (
        f"https://www.transitchicago.com/api/1.0/ttarrivals.aspx"
        f"?key={cta_key}&mapid={origin}&mapid_dest={destination}&outputType=JSON"
    )
    try:
        res = requests.get(url)
        payload = res.json()
    except Exception as e:
        st.error(f"Error fetching CTA schedule: {e}")
        return []
    data = payload.get('ctatt', {}).get('eta', [])
    if isinstance(data, dict):
        data = [data]
    schedules = []
    for e in data:
        try:
            dep = datetime.fromisoformat(e['prdt'])
            arr = datetime.fromisoformat(e['arrT'])
        except Exception:
            continue
        schedules.append((dep, arr))
    return schedules


def compute_fastest(schedules: list) -> int:
    durations = [(arr - dep).total_seconds() for dep, arr in schedules]
    return int(min(durations)) if durations else None
