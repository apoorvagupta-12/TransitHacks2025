import streamlit as st
from datetime import datetime, timedelta, time

from db import init_db, get_db_connection
from verification import verify_uchicago, generate_token, verify_email
from cta_api import compute_fastest, red_line_stations
from matching import find_matches

from PIL import Image

VERBOSE = True

TOPICS=['Food','Sports','Music','Tech','Art','Movies','Books','Travel','Fitness','Gaming','Photography','Science','Politics','History','Comedy']
STATIONS=list(red_line_stations.keys())

db_config=st.secrets['mysql']
cta_key=st.secrets['cta']['api_key']
email_sender=st.secrets['email']['sender_address']
email_pass=st.secrets['email']['sender_password']

init_db(db_config)

# Logout only when logged in
if st.session_state.get('logged_in'):
    if st.sidebar.button('Logout'):
        st.session_state.clear()
        st.stop()

# Login
if not st.session_state.get("logged_in"):
    st.title("Maroon Line RideShare")
    email = st.text_input("UChicago Email:", key="login_email")

    # Admin shortcut: immediate bypass
    if email and email.lower() == "admin@uchicago.edu":
        st.session_state["email"] = email
        st.session_state["logged_in"] = True
        st.success("Welcome, admin—auto-logged in.")
        # NO st.stop() here, so we fall through into the main app

    else:
        # Normal verification flow
        if st.button("Send Code"):
            if not verify_uchicago(email):
                st.error("Use your @uchicago.edu email.")
            else:
                token = generate_token()
                st.session_state["verification_code"] = token
                verify_email(email, token, email_sender, email_pass)
                st.session_state["email"] = email
                st.session_state["code_sent"] = True
                st.success("Code sent!")
        if st.session_state.get("code_sent"):
            code = st.text_input("Enter Code:", key="login_code")
            if st.button("Verify"):
                if code == st.session_state.get("verification_code"):
                    st.session_state["logged_in"] = True
                    st.success("Verified!")
                else:
                    st.error("Incorrect code.")
        # Only stop here for non-admin users
        st.stop()

# Onboarding interests
conn=get_db_connection(db_config)
cursor=conn.cursor(dictionary=True)
cursor.execute('SELECT * FROM profiles WHERE email=%s',(st.session_state.email,))
profile=cursor.fetchone()
if not profile:
    st.header('Select Your Interests')
    cols=st.columns(2)
    sel=[]
    for i,t in enumerate(TOPICS):
        with cols[i%2]:
            if st.checkbox(t,key=f'topic_{t}'):
                sel.append(t)
    if st.button('Save Interests'):
        cursor.execute('INSERT INTO profiles (email,origin,destination,interests) VALUES (%s,%s,%s,%s)',
                       (st.session_state.email,'','',','.join(sel)))
        conn.commit()
        st.success('Interests saved! Reload.')
        st.stop()
    st.stop()

# Ride request
st.sidebar.write(f"Logged in as: {st.session_state.email}")
st.header('Plan Your Ride')
mode=st.radio('Plan to',['Depart by','Arrive by'], horizontal=True)
origin=st.selectbox('Origin',STATIONS)
dest=st.selectbox('Destination',STATIONS)
time_sel=st.time_input(f'{mode}', value=time(8,0))

if st.button('Find Matches'):
    today=datetime.now().date()
    dt=datetime.combine(today, time_sel)

    if mode == 'Depart by':
        earliest, latest = dt, dt+timedelta(minutes=15)
    else:
        latest, earliest = dt, dt-timedelta(minutes=15)
    fastest, dep, arr = compute_fastest(origin, dest, cta_key, earliest)
    if fastest is None:
        st.error("No upcoming Red Line train found at that time – please choose an earlier departure or later arrival.")
        st.stop()

    cursor.execute(
        """
        INSERT INTO trips (profile_id, origin, destination, earliest, latest, fastest_seconds)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (profile['id'], origin, dest, earliest, latest, fastest or 0)
    )
    conn.commit()
    trip_id = cursor.lastrowid


    with st.spinner('Matching riders...'):
        matches = find_matches(
            conn, trip_id,
            origin, dest,
            earliest, latest,
            fastest, profile['interests'],
            verbose=VERBOSE
        )
    if not matches: st.info('No rides found.')
    else:
        m=matches[0]
        st.success('Matched!')
        c=st.columns([1,3])
        img = Image.open("pfp.jpeg")
        c[0].image(img, width=80)
        email = m['email']

        if email == "admin@uchicago.edu" or email == "kyler@uchicago.edu":
            email = "bstoller@uchicago.edu"
        c[1].markdown(f"**{email}**")
        common=set(profile['interests'].split(','))&set(m['interests'].split(','))
        c[1].markdown(f"Shared: {', '.join(list(common)[:3])}")

        if st.button("Contact the person"):
            st.info("Calling email...")
cursor.close()
conn.close()
