from math import sqrt
from cta_api import red_line_stations

# Pre-compute station indices for segment overlap
STATION_LIST = list(red_line_stations.keys())
INDEX_MAP = {station: idx for idx, station in enumerate(STATION_LIST)}


def find_matches(db_conn, trip_id, origin, destination, earliest, latest, fastest, interests, verbose=False):
    """
    Finds matching riders whose travel windows and route segments overlap, using each trip's stored origin/destination.

    Parameters:
      db_conn: MySQL connection
      trip_id: ID of the new trip
      origin, destination: station names for the new trip
      earliest, latest: datetime bounds
      fastest: fastest travel time in seconds for new trip
      interests: comma-separated string of interests for new trip
      verbose: if True, prints debug info to console

    Returns:
      List of up to 3 best match dicts with keys: email, interests, departure, arrival, score
    """
    # Map indices for the new trip
    o_idx = INDEX_MAP.get(origin)
    d_idx = INDEX_MAP.get(destination)
    if o_idx is None or d_idx is None:
        raise ValueError(f"Unknown station: {origin} or {destination}")
    start1, end1 = sorted([o_idx, d_idx])

    # Fetch candidates
    cursor = db_conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT t.id,
               t.origin AS cand_origin, t.destination AS cand_dest,
               t.earliest, t.latest, t.fastest_seconds,
               p.email, p.interests
        FROM trips t
        JOIN profiles p ON t.profile_id = p.id
        WHERE t.matched = FALSE
          AND t.id != %s
          AND t.earliest < %s
          AND t.latest > %s
        """,
        (trip_id, latest, earliest)
    )
    candidates = cursor.fetchall()
    cursor.close()

    topics_a = set(i.strip() for i in interests.split(','))
    scored = []

    for cand in candidates:
        bo = cand['cand_origin']; bd = cand['cand_dest']
        b_o = INDEX_MAP.get(bo); b_d = INDEX_MAP.get(bd)
        if b_o is None or b_d is None:
            if verbose:
                print(f"Skipping {cand['email']}: unknown station {bo} or {bd}")
            continue
        start2, end2 = sorted([b_o, b_d])

        # Segment overlap check
        if end1 <= start2 or end2 <= start1:
            if verbose:
                print(f"No segment overlap: {origin}->{destination} vs {bo}->{bd}")
            continue
        if verbose:
            print(f"Segment overlap ok for {cand['email']}")

        # Time overlap
        overlap = min(latest, cand['latest']) - max(earliest, cand['earliest'])
        ov_sec = overlap.total_seconds()
        if ov_sec <= 0:
            if verbose:
                print(f"No time overlap with {cand['email']}")
            continue
        if verbose:
            print(f"Time overlap {ov_sec}s with {cand['email']}")

        # Fastest check
        bf = cand['fastest_seconds']
        if not fastest or not bf:
            if verbose:
                print(f"Skipping {cand['email']}: missing fastest_seconds")
            continue

        # Compute metrics
        closeness = ov_sec / max(fastest, bf)
        topics_b = set(i.strip() for i in cand['interests'].split(','))
        sim = (len(topics_a & topics_b) / sqrt(len(topics_a) * len(topics_b))) if topics_a and topics_b else 0
        score = ov_sec * closeness * sim
        depart = max(earliest, cand['earliest'])
        arr = min(latest, cand['latest'])

        if verbose:
            print(f"Candidate {cand['email']}: closeness={closeness:.3f}, sim={sim:.3f}, score={score:.3f}")

        scored.append({
            'email': cand['email'],
            'interests': cand['interests'],
            'departure': depart,
            'arrival': arr,
            'score': score
        })

    scored.sort(key=lambda x: x['score'], reverse=True)
    return scored[:3]
