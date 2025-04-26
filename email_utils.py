import random
import smtplib
from email.mime.text import MIMEText

def send_verification_email(email_config, to_email, session_state):
    code = str(random.randint(100000, 999999))
    session_state['verification_code'] = code
    msg = MIMEText(f"Your verification code is: {code}")
    msg['Subject'] = 'CTA Match Verification'
    msg['From'] = email_config['from_email']
    msg['To'] = to_email

    with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
        server.starttls()
        server.login(email_config['username'], email_config['password'])
        server.send_message(msg)