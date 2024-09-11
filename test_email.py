import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')

def send_test_email():
    try:
        msg = MIMEText('This is a test email.')
        msg['Subject'] = 'Test Email'
        msg['From'] = DEFAULT_FROM_EMAIL
        msg['To'] = 'edwinkivuva01"gmail.com'

        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
            server.sendmail(DEFAULT_FROM_EMAIL, ['recipient@example.com'], msg.as_string())

        print("Test email sent successfully.")
    except Exception as e:
        print(f"Error sending email: {e}")

send_test_email()
