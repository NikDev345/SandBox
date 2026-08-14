import os
import smtplib

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

from config import *


# ============================================================
# Sandbox OTP Email
# ============================================================

def send_otp_email(receiver_email: str, otp: str):

    try:

        subject = "Your Sandbox verification code"

        # ----------------------------------------------------
        # Asset paths
        # ----------------------------------------------------

        logo_path = os.path.join(
            "app",
            "ui",
            "assets",
            "logo.png"
        )

        banner_path = os.path.join(
            "app",
            "ui",
            "assets",
            "sandbox_banner.png"
        )

        # ----------------------------------------------------
        # Check assets
        # ----------------------------------------------------

        if not os.path.exists(logo_path):
            print(f"EMAIL ERROR: Logo not found: {logo_path}")
            return False

        if not os.path.exists(banner_path):
            print(f"EMAIL ERROR: Banner not found: {banner_path}")
            return False

        # ====================================================
        # Plain text fallback
        # ====================================================

        plain_body = f"""
Hello,

We received a request to verify your email address for Sandbox.

Your verification code is:

{otp}

This code will expire in 5 minutes.

For your security, never share this code with anyone.

If you did not request this verification code,
you can safely ignore this email.

Regards,
Sandbox Team

https://sandboxhome.online
"""

        # ====================================================
        # HTML Email
        # ====================================================

        html_body = f"""
<!DOCTYPE html>

<html lang="en">

<head>

    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width,
                 initial-scale=1.0"
    >

    <title>Sandbox Verification</title>

</head>


<body
    style="
        margin:0;
        padding:0;
        background:#f4f4f5;
        font-family:
            Arial,
            Helvetica,
            sans-serif;
    "
>


<!-- ======================================================
     OUTER CONTAINER
====================================================== -->

<table
    width="100%"
    cellpadding="0"
    cellspacing="0"
    border="0"
    style="
        background:#f4f4f5;
        padding:35px 15px;
    "
>

<tr>

<td align="center">


<!-- ======================================================
     EMAIL CARD
====================================================== -->

<table
    width="100%"
    cellpadding="0"
    cellspacing="0"
    border="0"
    style="
        max-width:620px;
        background:#ffffff;
        border-radius:16px;
        overflow:hidden;
        border:1px solid #e5e7eb;
    "
>


<!-- ======================================================
     BRAND HEADER
====================================================== -->

<tr>

<td
    style="
        background:#080808;
        padding:24px 30px;
    "
>

<table
    width="100%"
    cellpadding="0"
    cellspacing="0"
    border="0"
>

<tr>

<td>

    <img
        src="cid:sandbox-logo"
        width="42"
        height="42"
        alt="Sandbox"
        style="
            display:block;
            border:0;
            border-radius:10px;
        "
    >

</td>


<td
    align="right"
    style="
        color:#ffffff;
        font-size:20px;
        font-weight:700;
        letter-spacing:-0.4px;
    "
>

    Sandbox

</td>

</tr>

</table>

</td>

</tr>


<!-- ======================================================
     PREMIUM BANNER
====================================================== -->

<tr>

<td
    style="
        background:#080808;
        padding:0;
    "
>

    <img
        src="cid:sandbox-banner"
        width="620"
        alt="Sandbox"
        style="
            width:100%;
            max-width:620px;
            height:auto;
            display:block;
            border:0;
        "
    >

</td>

</tr>


<!-- ======================================================
     CONTENT
====================================================== -->

<tr>

<td
    style="
        padding:42px 42px 38px 42px;
    "
>


<!-- Heading -->

<div
    style="
        font-size:28px;
        line-height:36px;
        font-weight:700;
        color:#111111;
        margin-bottom:12px;
    "
>

    Verify your email

</div>


<!-- Description -->

<div
    style="
        font-size:15px;
        line-height:24px;
        color:#6b7280;
        margin-bottom:30px;
    "
>

    We received a request to verify this email
    address for your Sandbox account.

    <br>

    Enter the verification code below to continue.

</div>


<!-- ======================================================
     OTP BOX
====================================================== -->

<table
    width="100%"
    cellpadding="0"
    cellspacing="0"
    border="0"
>

<tr>

<td
    align="center"
    style="
        background:#0b0b0b;
        border-radius:14px;
        padding:28px 20px;
    "
>


<div
    style="
        font-size:11px;
        line-height:16px;
        color:#a1a1aa;
        text-transform:uppercase;
        letter-spacing:2px;
        margin-bottom:12px;
    "
>

    Verification Code

</div>


<div
    style="
        font-size:38px;
        line-height:48px;
        font-weight:700;
        color:#d9a441;
        letter-spacing:9px;
        font-family:
            Arial,
            Helvetica,
            sans-serif;
    "
>

    {otp}

</div>


</td>

</tr>

</table>


<!-- ======================================================
     EXPIRY NOTICE
====================================================== -->

<table
    width="100%"
    cellpadding="0"
    cellspacing="0"
    border="0"
    style="
        margin-top:22px;
    "
>

<tr>

<td
    style="
        background:#fafafa;
        border:1px solid #e5e7eb;
        border-radius:10px;
        padding:16px 18px;
    "
>

<div
    style="
        font-size:14px;
        line-height:21px;
        color:#374151;
    "
>

    <strong>
        This code expires in 5 minutes.
    </strong>

    <br>

    For your security, never share this
    verification code with anyone.

</div>

</td>

</tr>

</table>


<!-- ======================================================
     SECURITY MESSAGE
====================================================== -->

<div
    style="
        margin-top:28px;
        font-size:13px;
        line-height:21px;
        color:#9ca3af;
    "
>

    If you did not request this verification code,
    you can safely ignore this email.

</div>


</td>

</tr>


<!-- ======================================================
     FOOTER
====================================================== -->

<tr>

<td
    align="center"
    style="
        background:#fafafa;
        border-top:1px solid #eeeeee;
        padding:25px 30px;
    "
>


<div
    style="
        font-size:14px;
        font-weight:700;
        color:#111111;
    "
>

    Sandbox

</div>


<div
    style="
        margin-top:7px;
        font-size:12px;
        color:#9ca3af;
    "
>

    AI tools. One workspace.

</div>


<div
    style="
        margin-top:12px;
        font-size:11px;
        color:#b0b0b0;
    "
>

    © Sandbox Team

</div>


</td>

</tr>


</table>


<!-- ======================================================
     END
====================================================== -->

</td>

</tr>

</table>


</body>

</html>
"""

        # ====================================================
        # Create email
        # ====================================================

        message = MIMEMultipart("related")

        message["From"] = email_from
        message["To"] = receiver_email
        message["Subject"] = subject


        # ----------------------------------------------------
        # Alternative container
        # ----------------------------------------------------

        alternative = MIMEMultipart("alternative")

        message.attach(alternative)


        # Plain text
        alternative.attach(
            MIMEText(
                plain_body,
                "plain",
                "utf-8"
            )
        )


        # HTML
        alternative.attach(
            MIMEText(
                html_body,
                "html",
                "utf-8"
            )
        )


        # ====================================================
        # Attach Sandbox Logo
        # ====================================================

        with open(logo_path, "rb") as image_file:

            logo = MIMEImage(
                image_file.read(),
                _subtype="png"
            )

        logo.add_header(
            "Content-ID",
            "<sandbox-logo>"
        )

        logo.add_header(
            "Content-Disposition",
            "inline",
            filename="sandbox-logo.png"
        )

        message.attach(logo)


        # ====================================================
        # Attach Sandbox Banner
        # ====================================================

        with open(banner_path, "rb") as image_file:

            banner = MIMEImage(
                image_file.read(),
                _subtype="png"
            )

        banner.add_header(
            "Content-ID",
            "<sandbox-banner>"
        )

        banner.add_header(
            "Content-Disposition",
            "inline",
            filename="sandbox-banner.png"
        )

        message.attach(banner)


        # ====================================================
        # Send Email
        # ====================================================

        with smtplib.SMTP(
            "smtp.gmail.com",
            587
        ) as server:

            server.starttls()

            server.login(
                email_from,
                email_api_key
            )

            server.send_message(message)


        print(
            f"[EMAIL] Verification email sent to {receiver_email}"
        )

        return True


    except Exception as e:

        print(
            "EMAIL ERROR:",
            repr(e)
        )

        return False