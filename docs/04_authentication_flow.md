# Authentication Flow

## Objective

Provide secure authentication for:

- Guest Users
- Google Users
- GitHub Users
- Admin Users

---

# User Types

## Guest User

Capabilities:

- Use tools
- Limited requests/day
- No history
- No bookmarks

Restrictions:

- Cannot save executions
- Cannot access profile

---

## Google User

Capabilities:

- Unlimited access (subject to limits)
- Save history
- Save bookmarks
- Access profile

Authentication:

Google OAuth

---

## GitHub User

Capabilities:

- Save history
- Save bookmarks
- Access profile

Authentication:

GitHub OAuth

---

## Admin User

Capabilities:

- Dashboard Access
- Analytics Access
- User Management
- Tool Monitoring

---

# Authentication Methods

1. Continue as Guest
2. Login with Google
3. Login with GitHub

---

# Authentication Journey

Homepage

↓

Choose Login Method

↓

Authenticate

↓

Create User (if needed)

↓

Create Session

↓

Store Session

↓

Redirect to Homepage

---

# Session Flow

User Login

↓

Session Created

↓

Session Stored

↓

User Uses Platform

↓

Session Expires

OR

Logout

↓

Session Removed

---

# API Routes

POST /auth/guest

GET /auth/google

GET /auth/github

GET /auth/callback/google

GET /auth/callback/github

GET /auth/me

POST /auth/logout

---

# Success Criteria

✓ Guest Login Works

✓ Google Login Works

✓ GitHub Login Works

✓ Session Persists

✓ Logout Works

✓ User Profile Loads

✓ Protected Routes Work
