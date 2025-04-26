import mysql.connector
from streamlit import cache_resource

def get_db_connection(config):
    return mysql.connector.connect(
        host=config['host'],
        user=config['user'],
        password=config['password'],
        database=config['database']
    )

@cache_resource
def init_db(_config):
    conn = get_db_connection(_config)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS profiles (
        id INT AUTO_INCREMENT PRIMARY KEY,
        email VARCHAR(255) UNIQUE,
        origin VARCHAR(50),
        destination VARCHAR(50),
        interests TEXT
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trips (
        id INT AUTO_INCREMENT PRIMARY KEY,
        profile_id INT,
        earliest DATETIME,
        latest DATETIME,
        matched BOOLEAN DEFAULT FALSE,
        fastest_seconds INT,
        FOREIGN KEY(profile_id) REFERENCES profiles(id)
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS matches (
        id INT AUTO_INCREMENT PRIMARY KEY,
        trip_a INT,
        trip_b INT,
        departure DATETIME,
        arrival DATETIME,
        score FLOAT,
        FOREIGN KEY(trip_a) REFERENCES trips(id),
        FOREIGN KEY(trip_b) REFERENCES trips(id)
    )""")
    conn.commit()
    cursor.close()
    conn.close()
