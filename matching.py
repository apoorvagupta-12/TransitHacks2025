from math import sqrt

def find_matches(db_conn, trip_id, origin, destination, earliest, latest, fastest, interests):
    cursor = db_conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT t.id, t.earliest, t.latest, t.fastest_seconds, p.email, p.interests
        FROM trips t
        JOIN profiles p ON t.profile_id = p.id
        WHERE t.matched = FALSE
          AND t.id != %s
          AND p.origin = %s
          AND p.destination = %s
          AND t.earliest < %s
          AND t.latest > %s
        """,
        (trip_id, origin, destination, latest, earliest)
    )
    candidates = cursor.fetchall()
    topics_a = set(i.strip() for i in interests.split(','))
    scored = []
    for b in candidates:
        overlap = min(latest, b['latest']) - max(earliest, b['earliest'])
        if overlap.total_seconds() <= 0:
            continue
        closeness = overlap.total_seconds() / max(fastest, b['fastest_seconds'])
        topics_b = set(i.strip() for i in b['interests'].split(','))
        sim = (len(topics_a & topics_b) / sqrt(len(topics_a) * len(topics_b))) if topics_a and topics_b else 0
        score = overlap.total_seconds() * closeness * sim
        departure = max(earliest, b['earliest'])
        arrival = min(latest, b['latest'])
        scored.append({
            'email': b['email'],
            'score': score,
            'departure': departure,
            'arrival': arrival,
            'interests': b['interests']
        })
    cursor.close()
    scored.sort(key=lambda x: x['score'], reverse=True)
    return scored[:3]
