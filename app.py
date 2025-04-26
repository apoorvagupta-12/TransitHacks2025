import streamlit as st
from datetime import datetime, timedelta, time

from db import init_db, get_db_connection
from verification import verify_uchicago, generate_token, verify_email
from cta_api import get_cta_schedule, compute_fastest
from matching import find_matches

# Available topics for onboarding
TOPICS = [
    'Food','Sports','Music','Tech','Art','Movies','Books','Travel','Fitness',
    'Gaming','Photography','Science','Politics','History','Comedy'
]

# Red Line stations
STATIONS = [
    'Howard','Jarvis','Morse','Loyola','Granville','Thorndale','Bryn Mawr','Berwyn',
    'Argyle','Lawrence','Wilson','Sheridan','Addison','Belmont','Fullerton','North/Clybourn',
    'Chicago','Grand','Lake','Monroe','Jackson','Harrison','Roosevelt','Cermak-Chinatown',
    'Sox-35th','47th','Garfield','63rd','69th','79th','87th','95th/Dan Ryan'
]

# Load secrets
db_config = st.secrets['mysql']
cta_key = st.secrets['cta']['api_key']
email_sender = st.secrets['email']['sender_address']
email_pass = st.secrets['email']['sender_password']

# Initialize DB
init_db(db_config)

# --- Login ---
def login_flow():
    st.title("Maroon Line RideShare")
    if not st.session_state.get("logged_in"):
        email = st.text_input("UChicago Email:", key="login_email")
        if st.button("Send Code"):
            if not verify_uchicago(email):
                st.error("Use your @uchicago.edu email.")
            else:
                token = generate_token()
                st.session_state['verification_code'] = token
                verify_email(email, token, email_sender, email_pass)
                st.session_state['email'] = email
                st.session_state['code_sent'] = True
                st.success("Code sent! Check your inbox.")
        if st.session_state.get('code_sent'):
            code = st.text_input("Enter Code:", key="login_code")
            if st.button("Verify"):
                if code == st.session_state.get('verification_code'):
                    st.session_state['logged_in'] = True
                    st.success("Verified!")
                else:
                    st.error("Incorrect code.")
        st.stop()

# --- Onboarding/profile ---
def profile_flow(conn):
    email = st.session_state['email']
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM profiles WHERE email=%s", (email,))
    profile = cursor.fetchone()
    if profile:
        return profile

    st.header("Tell us what you like")
    interests = st.multiselect("Select your interests:", TOPICS, key="onboard_interests")
    st.header("Set your route")
    origin = st.selectbox("Origin Station", STATIONS, key="onboard_origin")
    destination = st.selectbox("Destination Station", STATIONS, key="onboard_destination")
    if st.button("Save Profile"):
        cursor.execute(
            "INSERT INTO profiles (email, origin, destination, interests) VALUES (%s,%s,%s,%s)",
            (email, origin, destination, ','.join(interests))
        )
        conn.commit()
        st.success("Profile created! Reload to continue.")
        st.stop()

# --- Request & Match UI ---
def request_flow(conn, profile):
    st.sidebar.write(f"Welcome, {profile['email']}")
    st.header("Plan Your Ride")
    mode = st.radio("Plan to", ["Depart by", "Arrive by"], horizontal=True)
    station_origin = st.selectbox("Origin", STATIONS, index=STATIONS.index(profile['origin']))
    station_dest = st.selectbox("Destination", STATIONS, index=STATIONS.index(profile['destination']))
    ride_time = st.time_input(f"{mode} at", value=time(hour=8, minute=0), key="ride_time")

    if st.button("Find Matches"):
        today = datetime.now().date()
        dt = datetime.combine(today, ride_time)
        if mode == "Depart by":
            earliest = dt
            latest = dt + timedelta(minutes=15)
        else:
            latest = dt
            earliest = dt - timedelta(minutes=15)

        schedules = get_cta_schedule(cta_key, station_origin, station_dest)
        fastest = compute_fastest(schedules)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO trips (profile_id, earliest, latest, fastest_seconds) VALUES (%s,%s,%s,%s)",
            (profile['id'], earliest, latest, fastest)
        )
        conn.commit()
        trip_id = cursor.lastrowid

        with st.spinner('Matching riders...'):
            matches = find_matches(
                conn, trip_id, station_origin, station_dest,
                earliest, latest, fastest, profile['interests']
            )
        if not matches:
            st.info("No rides found.")
        else:
            best = matches[0]
            st.success("You're matched!")
            cols = st.columns([1,3])
            cols[0].image("https://via.placeholder.com/80", width=80)
            cols[1].markdown(f"**Name:** {best['email']}  \n"
                             f"**Score:** {best['score']:.2f}")
            common = set(profile['interests'].split(',')) & set(best['interests'].split(','))
            cols[1].markdown(f"**Shared Interests:** {', '.join(list(common)[:3])}")
        cursor.close()

# --- Main ---
def main():
    login_flow()
    conn = get_db_connection(db_config)
    profile = profile_flow(conn)
    if profile:
        request_flow(conn, profile)
    conn.close()

if __name__ == "__main__":
    main()
