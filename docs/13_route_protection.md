# Route Protection

## Purpose

Define public and protected routes.

---

# Public Routes

/

/login

/tools/*

/faq

/about

/contact

---

# Protected Routes

/profile

/history

/bookmarks

/settings

---

# Admin Routes

/admin

/admin/users

/admin/tools

/admin/analytics

---

# Access Rules

## Anonymous User

Allowed:

Public Routes

Denied:

Protected Routes

Admin Routes

---

## Guest User

Allowed:

Public Routes

Denied:

Protected Routes

Admin Routes

---

## Google User

Allowed:

Public Routes

Protected Routes

Denied:

Admin Routes

---

## GitHub User

Allowed:

Public Routes

Protected Routes

Denied:

Admin Routes

---

## Admin User

Allowed:

All Routes

---

# Redirection Rules

Anonymous User

↓

Protected Route

↓

Redirect:

/login

---

Guest User

↓

Protected Route

↓

Redirect:

/login

---

Authenticated User

↓

Protected Route

↓

Allow Access
