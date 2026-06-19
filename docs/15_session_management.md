# Session Management

## Purpose

Manage authenticated users.

---

# Session Lifecycle

Login

↓

Create Session

↓

Store Session

↓

Access Platform

↓

Logout

OR

Expiration

↓

Delete Session

---

# Session Storage

Redis

---

# Session Key

session:{session_id}

---

# Session Data

user_id

provider

expires_at

---

# Session Duration

Guest:

24 Hours

Google:

30 Days

GitHub:

30 Days

Admin:

30 Days

---

# Logout

Delete Session

Invalidate Cookie

Redirect Home