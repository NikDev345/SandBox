# Authentication Database Contract

## Purpose

Define the database requirements needed by the authentication system.

---

# User Table

Purpose:

Store platform users.

Fields:

id
email
provider
is_admin
created_at
updated_at

---

# Provider Values

guest

google

github

---

# Session Table

Purpose:

Store active user sessions.

Fields:

id
user_id
session_token
expires_at
created_at

---

# Relationships

User

↓

Many Sessions

---

# Authentication Requirements

Guest User:

Create temporary user

Create session

---

Google User:

Create user if not exists

Create session

---

GitHub User:

Create user if not exists

Create session

---

# Future Fields

name

avatar_url

last_login

is_active

---

# Indexes

email

session_token

provider

---

# Success Criteria

User lookup fast

Session lookup fast

Session creation fast

Session deletion fast
