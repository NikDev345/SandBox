"""
Sandbox Email Service
---------------------

Handles transactional emails for Sandbox.

Supported emails:
- Email verification OTP
- Password reset

Features:
- Responsive HTML emails
- Plain-text fallback
- Sandbox logo
- Sandbox premium banner
- No image MIME attachments
- Gmail SMTP
- Production-safe reset URLs
"""

from __future__ import annotations

import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import *


# ============================================================
# Public Asset URLs
# ============================================================

# IMPORTANT:
# These images are loaded directly by the email client.
# They are NOT attached to the email as MIME files.
#
# This prevents Gmail from displaying them as downloadable
# attachments.

SANDBOX_LOGO_URL = (
    "https://www.sandboxhome.online"
    "/email-assets/logo.png"
)

SANDBOX_BANNER_URL = (
    "https://www.sandboxhome.online"
    "/email-assets/sandbox_banner.png"
)


# ============================================================
# Shared Email Sender
# ============================================================

def _send_email(
    receiver_email: str,
    subject: str,
    plain_body: str,
    html_body: str,
) -> bool:

    try:

        # ----------------------------------------------------
        # Root message
        # ----------------------------------------------------

        message = MIMEMultipart("alternative")

        message["From"] = email_from
        message["To"] = receiver_email
        message["Subject"] = subject

        # ----------------------------------------------------
        # Plain-text fallback
        # ----------------------------------------------------

        message.attach(
            MIMEText(
                plain_body,
                "plain",
                "utf-8",
            )
        )

        # ----------------------------------------------------
        # HTML version
        # ----------------------------------------------------

        message.attach(
            MIMEText(
                html_body,
                "html",
                "utf-8",
            )
        )

        # ----------------------------------------------------
        # Gmail SMTP
        # ----------------------------------------------------

        with smtplib.SMTP(
            "smtp.gmail.com",
            587,
        ) as server:

            server.starttls()

            server.login(
                email_from,
                email_api_key,
            )

            server.send_message(message)

        return True

    except Exception as exc:

        print(
            "[EMAIL ERROR]",
            repr(exc),
        )

        return False


# ============================================================
# OTP Verification Email
# ============================================================

def send_otp_email(
    receiver_email: str,
    otp: str,
) -> bool:

    subject = "Your Sandbox verification code"

    # ========================================================
    # Plain-text fallback
    # ========================================================

    plain_body = f"""
Hello,

We received a request to verify your email address for Sandbox.

Your verification code is:

{otp}

This code will expire in 5 minutes.

For your security, never share this verification code with anyone.

If you did not request this verification code,
you can safely ignore this email.

Regards,
Sandbox Team

https://sandboxhome.online
"""

    # ========================================================
    # HTML Email
    # ========================================================

    html_body = f"""
<!DOCTYPE html>

<html lang="en">

<head>

    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>Sandbox Email Verification</title>

</head>


<body
    style="
        margin:0;
        padding:0;
        width:100%;
        background:#ffffff;
        font-family:Arial, Helvetica, sans-serif;
        color:#111111;
    "
>

<!-- ========================================================
     OUTER WRAPPER
========================================================= -->

<table
    width="100%"
    cellpadding="0"
    cellspacing="0"
    border="0"
    style="
        width:100%;
        margin:0;
        padding:0;
        background:#ffffff;
    "
>

<tr>

<td
    style="
        width:100%;
        padding:0;
    "
>


<!-- ========================================================
     EMAIL CONTAINER
========================================================= -->

<table
    width="100%"
    cellpadding="0"
    cellspacing="0"
    border="0"
    style="
        width:100%;
        margin:0;
        padding:0;
        background:#ffffff;
    "
>


<!-- ========================================================
     BRAND HEADER
========================================================= -->

<tr>

<td
    style="
        width:100%;
        background:#080808;
        padding:22px 5%;
    "
>

<table
    width="100%"
    cellpadding="0"
    cellspacing="0"
    border="0"
>

<tr>

<td
    valign="middle"
>

<img
    src="{SANDBOX_LOGO_URL}"
    width="42"
    height="42"
    alt="Sandbox"
    style="
        display:block;
        width:42px;
        height:42px;
        border:0;
        border-radius:10px;
    "
>

</td>


<td
    align="right"
    valign="middle"
    style="
        color:#ffffff;
        font-size:22px;
        line-height:28px;
        font-weight:700;
        letter-spacing:-0.5px;
    "
>

Sandbox

</td>

</tr>

</table>

</td>

</tr>


<!-- ========================================================
     PREMIUM SANDBOX BANNER
========================================================= -->

<tr>

<td
    style="
        width:100%;
        background:#080808;
        padding:0;
    "
>

<img
    src="{SANDBOX_BANNER_URL}"
    width="100%"
    alt="Sandbox"
    style="
        display:block;
        width:100%;
        height:auto;
        border:0;
        margin:0;
        padding:0;
    "
>

</td>

</tr>


<!-- ========================================================
     MAIN CONTENT
========================================================= -->

<tr>

<td
    style="
        width:100%;
        padding:48px 7%;
        background:#ffffff;
    "
>


<!-- Heading -->

<div
    style="
        font-size:30px;
        line-height:38px;
        font-weight:700;
        color:#111111;
        margin:0 0 14px 0;
    "
>

Verify your email

</div>


<!-- Description -->

<div
    style="
        font-size:16px;
        line-height:26px;
        color:#6b7280;
        margin:0 0 32px 0;
    "
>

We received a request to verify this email
address for your Sandbox account.

<br>

Enter the verification code below to continue.

</div>


<!-- ========================================================
     OTP BOX
========================================================= -->

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
        padding:30px 20px;
    "
>


<div
    style="
        font-size:11px;
        line-height:16px;
        color:#a1a1aa;
        text-transform:uppercase;
        letter-spacing:3px;
        margin:0 0 14px 0;
    "
>

Verification Code

</div>


<div
    style="
        font-size:40px;
        line-height:50px;
        font-weight:700;
        color:#d9a441;
        letter-spacing:10px;
        font-family:Arial, Helvetica, sans-serif;
    "
>

{otp}

</div>


</td>

</tr>

</table>


<!-- ========================================================
     EXPIRY NOTICE
========================================================= -->

<table
    width="100%"
    cellpadding="0"
    cellspacing="0"
    border="0"
    style="
        margin-top:24px;
    "
>

<tr>

<td
    style="
        background:#fafafa;
        border:1px solid #e5e7eb;
        border-radius:10px;
        padding:17px 20px;
    "
>

<div
    style="
        font-size:14px;
        line-height:22px;
        color:#374151;
    "
>

<strong style="color:#111111;">
This code expires in 5 minutes.
</strong>

<br>

For your security, never share this verification
code with anyone.

</div>

</td>

</tr>

</table>


<!-- ========================================================
     SECURITY MESSAGE
========================================================= -->

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


<!-- ========================================================
     FOOTER
========================================================= -->

<tr>

<td
    align="center"
    style="
        width:100%;
        background:#fafafa;
        border-top:1px solid #eeeeee;
        padding:28px 7%;
    "
>

<div
    style="
        font-size:15px;
        line-height:20px;
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
        line-height:18px;
        color:#9ca3af;
    "
>

AI tools. One workspace.

</div>


<div
    style="
        margin-top:12px;
        font-size:11px;
        line-height:17px;
        color:#b0b0b0;
    "
>

© Sandbox Team

</div>

</td>

</tr>


</table>

</td>

</tr>

</table>


</body>

</html>
"""

    return _send_email(
        receiver_email=receiver_email,
        subject=subject,
        plain_body=plain_body,
        html_body=html_body,
    )


# ============================================================
# Password Reset Email
# ============================================================

def send_reset_password_email(
    email: str,
    token: str,
) -> bool:

    # ========================================================
    # Production Reset URL
    # ========================================================

    reset_link = (
        f"{APP_BASE_URL}/reset-password"
        f"?token={token}"
    )

    subject = "Reset your Sandbox password"

    # ========================================================
    # Plain-text fallback
    # ========================================================

    plain_body = f"""
Hello,

We received a request to reset the password
for your Sandbox account.

Use the link below to reset your password:

{reset_link}

This link will expire in 15 minutes.

For your security, never share this link with anyone.

If you did not request a password reset,
you can safely ignore this email.

Regards,
Sandbox Team

https://sandboxhome.online
"""

    # ========================================================
    # HTML Email
    # ========================================================

    html_body = f"""
<!DOCTYPE html>

<html lang="en">

<head>

    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>Reset your Sandbox password</title>

</head>


<body
    style="
        margin:0;
        padding:0;
        width:100%;
        background:#ffffff;
        font-family:Arial, Helvetica, sans-serif;
        color:#111111;
    "
>


<!-- ========================================================
     OUTER WRAPPER
========================================================= -->

<table
    width="100%"
    cellpadding="0"
    cellspacing="0"
    border="0"
    style="
        width:100%;
        margin:0;
        padding:0;
        background:#ffffff;
    "
>

<tr>

<td
    style="
        width:100%;
        padding:0;
    "
>


<!-- ========================================================
     EMAIL CONTAINER
========================================================= -->

<table
    width="100%"
    cellpadding="0"
    cellspacing="0"
    border="0"
    style="
        width:100%;
        margin:0;
        padding:0;
        background:#ffffff;
    "
>


<!-- ========================================================
     BRAND HEADER
========================================================= -->

<tr>

<td
    style="
        width:100%;
        background:#080808;
        padding:22px 5%;
    "
>

<table
    width="100%"
    cellpadding="0"
    cellspacing="0"
    border="0"
>

<tr>

<td
    valign="middle"
>

<img
    src="{SANDBOX_LOGO_URL}"
    width="42"
    height="42"
    alt="Sandbox"
    style="
        display:block;
        width:42px;
        height:42px;
        border:0;
        border-radius:10px;
    "
>

</td>


<td
    align="right"
    valign="middle"
    style="
        color:#ffffff;
        font-size:22px;
        line-height:28px;
        font-weight:700;
        letter-spacing:-0.5px;
    "
>

Sandbox

</td>

</tr>

</table>

</td>

</tr>


<!-- ========================================================
     PREMIUM SANDBOX BANNER
========================================================= -->

<tr>

<td
    style="
        width:100%;
        background:#080808;
        padding:0;
    "
>

<img
    src="{SANDBOX_BANNER_URL}"
    width="100%"
    alt="Sandbox"
    style="
        display:block;
        width:100%;
        height:auto;
        border:0;
        margin:0;
        padding:0;
    "
>

</td>

</tr>


<!-- ========================================================
     MAIN CONTENT
========================================================= -->

<tr>

<td
    style="
        width:100%;
        padding:48px 7%;
        background:#ffffff;
    "
>


<!-- Heading -->

<div
    style="
        font-size:30px;
        line-height:38px;
        font-weight:700;
        color:#111111;
        margin:0 0 14px 0;
    "
>

Reset your password

</div>


<!-- Description -->

<div
    style="
        font-size:16px;
        line-height:26px;
        color:#6b7280;
        margin:0 0 32px 0;
    "
>

We received a request to reset the password
for your Sandbox account.

</div>


<!-- ========================================================
     RESET BUTTON
========================================================= -->

<table
    cellpadding="0"
    cellspacing="0"
    border="0"
>

<tr>

<td
    align="center"
    style="
        border-radius:10px;
        background:#080808;
    "
>

<a
    href="{reset_link}"
    style="
        display:inline-block;
        padding:15px 30px;
        color:#ffffff;
        text-decoration:none;
        font-size:14px;
        line-height:20px;
        font-weight:600;
        border-radius:10px;
    "
>

Reset Password

</a>

</td>

</tr>

</table>


<!-- ========================================================
     EXPIRY NOTICE
========================================================= -->

<div
    style="
        margin-top:28px;
        padding:17px 20px;
        background:#fafafa;
        border:1px solid #e5e7eb;
        border-radius:10px;
        font-size:13px;
        line-height:21px;
        color:#6b7280;
    "
>

<strong style="color:#111111;">
This link expires in 15 minutes.
</strong>

<br>

For your security, never share this link with anyone.

</div>


<!-- ========================================================
     SECURITY MESSAGE
========================================================= -->

<div
    style="
        margin-top:25px;
        font-size:13px;
        line-height:21px;
        color:#9ca3af;
    "
>

If you did not request a password reset,
you can safely ignore this email.

</div>


<!-- ========================================================
     FALLBACK LINK
========================================================= -->

<div
    style="
        margin-top:25px;
        font-size:12px;
        line-height:19px;
        color:#9ca3af;
        word-break:break-all;
    "
>

If the button doesn't work, copy and paste this link
into your browser:

<br><br>

<a
    href="{reset_link}"
    style="
        color:#6b7280;
        text-decoration:underline;
        word-break:break-all;
    "
>

{reset_link}

</a>

</div>


</td>

</tr>


<!-- ========================================================
     FOOTER
========================================================= -->

<tr>

<td
    align="center"
    style="
        width:100%;
        background:#fafafa;
        border-top:1px solid #eeeeee;
        padding:28px 7%;
    "
>

<div
    style="
        font-size:15px;
        line-height:20px;
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
        line-height:18px;
        color:#9ca3af;
    "
>

AI tools. One workspace.

</div>


<div
    style="
        margin-top:12px;
        font-size:11px;
        line-height:17px;
        color:#b0b0b0;
    "
>

© Sandbox Team

</div>

</td>

</tr>


</table>

</td>

</tr>

</table>


</body>

</html>
"""

    return _send_email(
        receiver_email=email,
        subject=subject,
        plain_body=plain_body,
        html_body=html_body,
    )