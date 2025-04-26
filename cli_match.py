#!/usr/bin/env python3
"""
CLI tool for testing rider matching logic with verbose output.
Usage:
  python cli_match.py --email alice@uchicago.edu \
       --origin Howard --destination Bryn\ Mawr \
       --interests Food,Music,Tech \
       [--earliest 2025-04-26T08:00] [--latest 2025-04-26T08:15]
"""
import os
import argparse
from datetime import datetime, timedelta
from dotenv import load_dotenv
import mysql.connector
from math import sqrt
from cta_api import compute_fastest

# Load environment variables from .env
load_dotenv()

# DB connection helper
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )

# Fetch existing profiles/trips or insert if new

def ensure_profile(cursor, email, origin, destination, interests):
    cursor.execute("SELECT id, origin, destination, interests FROM profiles WHERE email=%s", (email,))
    row = cursor.fetchone()
    if row:
        pid, orig, dest, saved = row
        print(f"Using existing profile (ID {pid}): origin={orig}, dest={dest}, interests={saved}")
    else:
        cursor.execute(
            "INSERT INTO profiles (email, origin, destination, interests) VALUES (%s,%s,%s,%s)",
            (email, origin, destination, interests)
        )
        pid = cursor.lastrowid
        print(f"Created profile (ID {pid}): origin={origin}, dest={destination}, interests={interests}")
    return pid

# Insert a trip request
def insert_trip(cursor, profile_id, earliest, latest, fastest_seconds):
    cursor.execute(
        "INSERT INTO trips (profile_id, earliest, latest, fastest_seconds) VALUES (%s,%s,%s,%s)",
        (profile_id, earliest, latest, fastest_seconds)
    )
    tid = cursor.lastrowid
    print(f"Inserted trip (ID {tid}): earliest={earliest}, latest={latest}, fastest={fastest_seconds}s")
    return tid

# Fetch candidate trips for matching
def fetch_candidates(cursor, trip_id, origin, destination, earliest, latest):
    cursor.execute(
        """
        SELECT t.id, t.earliest, t.latest, t.fastest_seconds, p.email, p.interests
        FROM trips t JOIN profiles p ON t.profile_id = p.id
        WHERE t.matched = FALSE
          AND t.id != %s
          AND p.origin = %s
          AND p.destination = %s
          AND t.earliest < %s
          AND t.latest > %s
        """,
        (trip_id, origin, destination, latest, earliest)
    )
    return cursor.fetchall()

# Compute similarity metrics and score

def compute_metrics(self, candidate, origin_earliest, origin_latest, origin_fastest, origin_interests):
    b_earliest = candidate['earliest']
    b_latest = candidate['latest']
    overlap = min(origin_latest, b_latest) - max(origin_earliest, b_earliest)
    overlap_sec = overlap.total_seconds()
    if overlap_sec <= 0:
        return None
    closeness = overlap_sec / max(origin_fastest, candidate['fastest_seconds'])
    set_a = set(origin_interests.split(','))
    set_b = set(candidate['interests'].split(','))
    sim = (len(set_a & set_b) / sqrt(len(set_a) * len(set_b))) if set_a and set_b else 0
    score = overlap_sec * closeness * sim
    return {
        'email': candidate['email'],
        'overlap_s': overlap_sec,
        'closeness': closeness,
        'similarity': sim,
        'score': score,
        'departure': max(origin_earliest, b_earliest),
        'arrival': min(origin_latest, b_latest),
    }

# Main CLI
def main():
    parser = argparse.ArgumentParser(description="Test CTA rider matching logic.")
    parser.add_argument('--email', required=True, help='User email')
    parser.add_argument('--origin', required=True, help='Origin station')
    parser.add_argument('--destination', required=True, help='Destination station')
    parser.add_argument('--interests', required=True, help='Comma-separated interests')
    parser.add_argument('--earliest', help='Earliest departure (YYYY-MM-DDTHH:MM)', default=None)
    parser.add_argument('--latest', help='Latest arrival   (YYYY-MM-DDTHH:MM)', default=None)
    args = parser.parse_args()

    # Parse times
    now = datetime.now()
    if args.earliest:
        origin_earliest = datetime.fromisoformat(args.earliest)
    else:
        origin_earliest = now
    if args.latest:
        origin_latest = datetime.fromisoformat(args.latest)
    else:
        origin_latest = origin_earliest + timedelta(minutes=30)

    # Compute fastest travel
    fastest_s, dep_time, arr_time = compute_fastest(
        args.origin, args.destination, os.getenv('CTA_API_KEY')
    )
    print(f"Fastest travel: {fastest_s}s (dep: {dep_time}, arr: {arr_time})")

    # Connect DB and setup
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    pid = ensure_profile(cursor, args.email, args.origin, args.destination, args.interests)
    conn.commit()

    # Insert trip
    tid = insert_trip(cursor, pid, origin_earliest, origin_latest, fastest_s or 0)
    conn.commit()

    # Fetch candidates
    candidates = fetch_candidates(cursor, tid, args.origin, args.destination, origin_earliest, origin_latest)
    print(f"Found {len(candidates)} candidate trips")

    # Score candidates
    results = []
    for cand in candidates:
        m = compute_metrics(cand, origin_earliest, origin_latest, fastest_s or 0, args.interests)
        if m:
            results.append(m)
    results.sort(key=lambda x: x['score'], reverse=True)

    # Display verbose metrics
    print("\n=== Top Matches ===")
    for r in results[:5]:
        print(f"Email: {r['email']}")
        print(f"  Overlap: {r['overlap_s']}s")
        print(f"  Closeness: {r['closeness']:.3f}")
        print(f"  Similarity: {r['similarity']:.3f}")
        print(f"  Score: {r['score']:.3f}")
        print(f"  Depart together at: {r['departure']}")
        print(f"  Arrive together by: {r['arrival']}")
        print("--------------------")

    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
