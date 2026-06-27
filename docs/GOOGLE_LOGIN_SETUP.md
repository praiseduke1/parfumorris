# Google OAuth 2.0 Login — Setup Guide

Guide for configuring Google Login (OAuth 2.0) using `django-allauth`.

---

## Prerequisites

- Google Cloud Platform account (free tier)
- Access to project root (`.env` + Django migrations)

---

## Step 1: Credentials

Credentials are loaded from `.env` (never hardcoded):

```env
GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET=YOUR_GOOGLE_CLIENT_SECRET
```

### Authorized URIs (Google Cloud Console)

| Type | URI |
|------|-----|
| JavaScript origins | `http://localhost:8000` |
| Redirect URIs | `http://localhost:8000/accounts/google/login/callback/` |

---

## Step 2: Apply Migrations

```bash
python manage.py migrate
```

Creates:
- `SocialApp(provider='google')` — auto-created from env vars by migration 0012
- `Site(id=1, domain='localhost:8000')` — migration 0011
- allauth tables

---

## Step 3: Verify

```bash
python manage.py check_google_login
```

Should show all PASS.

---

## How It Works

```
Clicks "Lanjutkan dengan Google"
  ↓  /accounts/google/login/
  ↓  Redirects to accounts.google.com
  ↓  Chooses account, grants permission
  ↓  /accounts/google/login/callback/
  ↓  allauth processes response
  ↓
  Email exists? → Link & login
  No email?     → Create User + Profile + MemberProfile
  ↓
  Redirect to Dashboard (accounts:dashboard)
```

### Auto-creation

When a first-time Google user logs in:

1. `django-allauth` creates `User(username=email_prefix, email=..., first_name=..., last_name=...)`
2. `post_save` signal creates `Profile` + `MemberProfile`
3. `SocialAccount` record links Google account to User

### Existing user

If Google email matches an existing user:
- allauth links the social account
- No duplicate accounts

---

## Configuration

| Setting | Value | Purpose |
|---------|-------|---------|
| `SOCIALACCOUNT_AUTO_SIGNUP` | `True` | Auto-create user without signup form |
| `SOCIALACCOUNT_EMAIL_REQUIRED` | `True` | Require email from Google |
| `SOCIALACCOUNT_LOGIN_ON_GET` | `True` | Skip intermediate page |
| `SOCIALACCOUNT_EMAIL_AUTHENTICATION` | `True` | Auto-link existing email |
| `SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT` | `True` | Auto-connect social to existing user |
| `SOCIALACCOUNT_ADAPTER` | `apps.accounts.adapter.CustomSocialAccountAdapter` | Custom error handling |
| `ACCOUNT_DEFAULT_HTTP_PROTOCOL` | `http` | Use HTTP for local dev |
| `LOGIN_REDIRECT_URL` | `accounts:dashboard` | Post-login redirect |
| `CSRF_TRUSTED_ORIGINS` | `localhost:8000, 127.0.0.1:8000` | CSRF for dev |
| `ACCOUNT_EMAIL_VERIFICATION` | `none` | Google handles verification |

---

## Error Handling

| Error | Handler |
|-------|---------|
| Cancelled login | Adapter: `access_denied` → message + redirect to login |
| Missing email | allauth raises `ImmediateHttpResponse` |
| Invalid callback | Google returns 400 (check redirect URI config) |
| Expired token | Google returns 401 (user re-authenticates) |
| API failure | Adapter: generic error message + redirect to login |

---

## Production

1. **Google Cloud Console**:
   - JS origins: `https://yourdomain.com`
   - Redirect URIs: `https://yourdomain.com/accounts/google/login/callback/`

2. **Django Site**: domain = `yourdomain.com`

3. **`.env`**: production credentials

4. **`settings.py`**: `ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'`

---

## Troubleshooting

### 400 redirect_uri_mismatch
URI in Google Cloud Console doesn't match callback. Verify:
`http://localhost:8000/accounts/google/login/callback/`

### SocialApp not found
Run `python manage.py migrate` or create at `/admin/socialaccount/socialapp/`

### Site not found
Run `python manage.py migrate` to create Site(id=1)

### Wrong redirect after login
Check `LOGIN_REDIRECT_URL` = `accounts:dashboard`

---

## Modified Files

| File | Change |
|------|--------|
| `.env` | Real Google credentials |
| `parfumoray/settings.py` | allauth config, CSRF_TRUSTED_ORIGINS, adapter, redirect |
| `parfumoray/urls.py` | allauth URLs |
| `apps/accounts/adapter.py` | Custom SocialAccountAdapter |
| `apps/accounts/management/commands/check_google_login.py` | Diagnostic command |
| `apps/accounts/migrations/0012_create_socialapp.py` | Auto-create SocialApp from env vars |
| `apps/accounts/migrations/0011_configure_default_site.py` | Auto-create Site(id=1) |
| `apps/accounts/templates/accounts/login.html` | Google button + messages |
| `apps/accounts/templates/accounts/register.html` | Google button + messages |
| `docs/GOOGLE_LOGIN_SETUP.md` | This file |
