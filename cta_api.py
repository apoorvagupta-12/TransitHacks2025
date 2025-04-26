import requests
from datetime import datetime

def get_cta_schedule(cta_key: str, origin: str, destination: str):
    url = (
        f"https://www.transitchicago.com/api/1.0/ttarrivals.aspx"
        f"?key={cta_key}&mapid={origin}&mapid_dest={destination}"
    )
    res = requests.get(url)
    data = res.json().get('ctatt', {}).get('eta', [])
    schedules = []
    for e in data:
        dep = datetime.fromisoformat(e['prdt'])
        arr = datetime.fromisoformat(e['arrT'])
        schedules.append((dep, arr))
    return schedules

def compute_fastest(schedules: list) -> int:
    durations = [(arr - dep).total_seconds() for dep, arr in schedules]
    return int(min(durations)) if durations else None
