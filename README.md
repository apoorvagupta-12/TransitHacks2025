# CTA Red Line Ride-Match

Match UChicago riders on the Chicago CTA Red Line so they can travel together,
talk about shared interests, and cut wait time.

---

## Features

| Status | Component                | Notes                               |
|--------|------------------------- |-------------------------------------|
| Done     | Email verification       | Streamlit password-less “magic link” |
| Done    | CTA Train Tracker API    | Live departure/arrival data         |
| Done    | Topic-based matching     | Cosine similarity on user interests |
| Done     | Ride-scheduling engine   | Optimizes **time together × lateness** |
| Done     | Profile & trip storage   | MySQL (AWS RDS)                     |
| Done     | Route / match display    | Interactive Streamlit UI            |
|      | CNET single-sign-on      | Nice-to-have                        |
|      | Photo verification      | Nice-to-have                        |
|      | Train schedule change alerts      | Nice-to-have                        |
|      | Tools to identify yourself and confirm the identity of your match      | Nice-to-have                        |
|      | News-feed / updates      | Nice-to-have                        |
|      | Mobile games      | Nice-to-have                        |

---

## Tech Stack

* **Frontend / UI**: Streamlit  
* **Backend logic**: Python 3.10  
* **Database**       : MySQL 8 on Amazon RDS  
* **APIs**           : CTA Train Tracker, SMTP (mail), optional SendGrid  
* **Infra-as-Code**  : Terraform (optional)  

---

## Database Schema

```sql
CREATE TABLE profiles (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    email        VARCHAR(255) UNIQUE,
    origin       VARCHAR(50),
    destination  VARCHAR(50),
    interests    TEXT
);

CREATE TABLE trips (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    profile_id      INT,
    earliest        DATETIME,
    latest          DATETIME,
    matched         BOOLEAN DEFAULT FALSE,
    fastest_seconds INT,
    FOREIGN KEY(profile_id) REFERENCES profiles(id)
);

CREATE TABLE matches (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    trip_a    INT,
    trip_b    INT,
    departure DATETIME,
    arrival   DATETIME,
    score     FLOAT,
    FOREIGN KEY(trip_a) REFERENCES trips(id),
    FOREIGN KEY(trip_b) REFERENCES trips(id)
);
```


## Future Work

In the future, there are several features we would like to implement:

* Work with The University of Chicago IT to leverage CNET Verification for log-in purposes
* Photo Verification of our Users
* Broaden the scope of this project to go beyong the CTA Red Line
* Increase the number of "matching topics" to include real-time news and conversation topics like Newspaper Headlines and Sporting Events
