import smtplib
import ssl
from email.message import EmailMessage
import os
from dotenv import load_dotenv
import random

load_dotenv()

SENDER_ADDRESS = os.getenv("SENDER_ADDRESS")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

def verify_uchicago(email):
    """Checks if an email address ends with @uchicago.edu."""
    return email.lower().endswith('@uchicago.edu')


def generate_token():
    """Generates a random 6-digit numeric token as a string."""
    return str(random.randint(100000, 999999))


def verify_email(receiver_email, token):
    """Sends a 6-digit verification token to a given receiver email."""
    subject = "Maroon Line: Verify Your Email"
    body = f"""
    Hello!

    Thanks for signing up for the Maroon Line RideShare app.

    Your 6-digit verification code is: {token}

    Please enter this code in the app to complete your verification.

    If you did not request this, you can ignore this email.

    Thanks,
    The Maroon Line Team
    """

    em = EmailMessage()
    em['From'] = SENDER_ADDRESS
    em['To'] = receiver_email
    em['Subject'] = subject
    em.set_content(body)

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context= context) as smtp:
        smtp.login(SENDER_ADDRESS, SENDER_PASSWORD)
        smtp.send_message(em)
