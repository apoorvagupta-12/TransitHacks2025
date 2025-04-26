#!/usr/bin/env python3
"""
test_matching.py

This script clears the test database tables, inserts 20 test riders with overlapping trips,
then inserts a 21st rider and prints the top matches for the 21st rider.

Usage:
    python test_matching.py

Ensure the following environment variables are set (e.g. in a .env file):
    DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
"""
import os
from dotenv import load_dotenv
import mysql.connector
from datetime import datetime, timedelta
from matching import find_matches

# Load .env variables
load_dotenv()

# Database connection helper
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )

# Initialize and clear tables
def init_db(conn):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM matches")
    cursor.execute("DELETE FROM trips")
    cursor.execute("DELETE FROM profiles")
    conn.commit()
    cursor.close()

# Populate 20 test riders
def populate_riders(conn):
    cursor = conn.cursor()
    now = datetime.now().replace(second=0, microsecond=0)
    earliest = now
    latest = now + timedelta(minutes=15)
    topics = ['Food', 'Music', 'Tech', 'Art', 'Movies', 'Books']
    for i in range(20):
        email = f"user{i}@uchicago.edu"
        interests = ",".join(topics[i % len(topics):(i % len(topics)) + 3])
        # Insert profile with route
        cursor.execute(
            "INSERT INTO profiles (email, origin, destination, interests) VALUES (%s, %s, %s, %s)",
            (email, 'Howard', 'Bryn Mawr', interests)
        )
        pid = cursor.lastrowid
        # Compute a distinct fastest time per user
        fastest = 600 + i * 10  # seconds
        # Insert trip tied to that profile
        cursor.execute(
            "INSERT INTO trips (profile_id, origin, destination, earliest, latest, fastest_seconds) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (pid, 'Howard', 'Bryn Mawr', earliest, latest, fastest)
        )
    conn.commit()
    cursor.close()

# Test matching for the 21st rider
def test_match(conn):
    cursor = conn.cursor()
    now = datetime.now().replace(second=0, microsecond=0)
    earliest = now
    latest = now + timedelta(minutes=15)
    email = 'test21@uchicago.edu'
    origin = 'Howard'
    destination = 'Bryn Mawr'
    interests = 'Food,Books,Tech'
    fastest = 700
    # Insert 21st profile
    cursor.execute(
        "INSERT INTO profiles (email, origin, destination, interests) VALUES (%s, %s, %s, %s)",
        (email, origin, destination, interests)
    )
    pid = cursor.lastrowid
    # Insert 21st trip
    cursor.execute(
        "INSERT INTO trips (profile_id, origin, destination, earliest, latest, fastest_seconds) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (pid, origin, destination, earliest, latest, fastest)
    )
    tid = cursor.lastrowid
    conn.commit()
    cursor.close()

    # Run matching
    matches = find_matches(
        conn, tid, origin, destination,
        earliest, latest, fastest, interests,
        verbose=True
    )
    print(f"Found {len(matches)} matches for {email}:")
    for m in matches:
        print(f" - {m['email']}, score={m['score']:.2f}")
    assert matches, "No matches found for the 21st rider!"


def main():
    conn = get_db_connection()
    init_db(conn)
    populate_riders(conn)
    test_match(conn)
    conn.close()

if __name__ == '__main__':
    main()
