import os
import smtplib

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from dotenv import load_dotenv

load_dotenv()


EMAIL = os.getenv("EMAIL_FROM")
PASSWORD = os.getenv("EMAIL_PASSWORD")


def send_otp_email(receiver_email: str, otp: str):

    try:

        subject = "Sandbox Email Verification"

        body = f"""
Hello,

Your Sandbox verification code is:

{otp}

This OTP will expire in 5 minutes.

If you didn't request this, please ignore this email.

Regards,
Sandbox Team
"""

        message = MIMEMultipart()

        message["From"] = EMAIL
        message["To"] = receiver_email
        message["Subject"] = subject

        message.attach(
            MIMEText(body, "plain")
        )

        with smtplib.SMTP(
            "smtp.gmail.com",
            587
        ) as server:

            server.starttls()

            server.login(
                EMAIL,
                PASSWORD
            )

            server.send_message(message)

        return True

    except Exception as e:

        print("EMAIL ERROR:", e)

        return False
    
def send_reset_password_email(
    email: str,
    token: str
):

    try:

        reset_link = (
            f"http://127.0.0.1:8000/reset-password"
            f"?token={token}"
        )

        message = MIMEMultipart()

        message["From"] = EMAIL
        message["To"] = email
        message["Subject"] = "Reset your Sandbox password"

        body = f"""
Hello,

We received a request to reset your Sandbox password.

Click the link below to reset your password:

{reset_link}

This link will expire in 15 minutes.

If you didn't request this, simply ignore this email.

Regards,
Sandbox Team
"""

        message.attach(
            MIMEText(body, "plain")
        )

        with smtplib.SMTP(
            "smtp.gmail.com",
            587
        ) as smtp:

            smtp.starttls()

            smtp.login(
                EMAIL,
                PASSWORD
            )

            smtp.send_message(message)

        return True

    except Exception as e:

        print("EMAIL ERROR:", e)

        return False