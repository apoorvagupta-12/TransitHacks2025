import smtplib
import ssl
from email.message import EmailMessage
import random

def verify_uchicago(email: str) -> bool:
    return email.lower().endswith('@uchicago.edu')

def generate_token() -> str:
    return str(random.randint(100000, 999999))

def verify_email(receiver_email: str, token: str, sender_address: str, sender_password: str):
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
    em['From'] = sender_address
    em['To'] = receiver_email
    em['Subject'] = subject
    em.set_content(body)
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(sender_address, sender_password)
        smtp.send_message(em)
