# Google OAuth Diagnostic Report

**Generated**: 2026-06-27

## Root Cause

The Google OAuth request was missing `client_id` because **`SOCIALACCOUNT_PROVIDERS['google']['APP']` in `settings.py` was unconditionally injected with empty values**, which blocked allauth from falling back to the database `SocialApp` record.

### The exact failure chain

```
.env
  └─ GOOGLE_CLIENT_ID=                 ← empty (user hasn't configured)
  └─ GOOGLE_CLIENT_SECRET=             ← empty

settings.py
  └─ os.getenv('GOOGLE_CLIENT_ID', '') → ''
  └─ os.getenv('GOOGLE_CLIENT_SECRET', '') → ''
  └─ SOCIALACCOUNT_PROVIDERS['google']['APP'] = {
         'client_id': '',              ← always injected, even when empty
         'secret': '',
     }

allauth credential resolution (GoogleOAuth2Adapter)
  └─ get_app() checks SOCIALACCOUNT_PROVIDERS['google']['APP']
  └─ APP is present → uses it (even with empty client_id)
  └─ NEVER falls back to SocialApp database record
  └─ builds URL: https://accounts.google.com/o/oauth2/v2/auth?client_id=&...
  └─ Google responds: 400 invalid_request "Missing required parameter: client_id"
```

## What Was Fixed

### 1. `parfumoray/settings.py` — Conditional APP injection

**Before** (broken): APP always present, even with empty credentials — blocked DB fallback.

```python
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': os.getenv('GOOGLE_CLIENT_ID', ''),   # ''
            'secret': os.getenv('GOOGLE_CLIENT_SECRET', ''),  # ''
        },
    }
}
```

**After** (fixed): APP only injected when env vars are non-empty.

```python
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '').strip()
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', '').strip()

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'VERIFIED_EMAIL': True,
    }
}

if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    SOCIALACCOUNT_PROVIDERS['google']['APP'] = {
        'client_id': GOOGLE_CLIENT_ID,
        'secret': GOOGLE_CLIENT_SECRET,
        'key': '',
    }
```

### 2. `apps/accounts/management/commands/check_google_login.py` — Diagnostic command

Run `python manage.py check_google_login` to verify the configuration.

## Configuration Status

| Component | Status | Detail |
|-----------|--------|--------|
| `.env` file | OK | Found at project root |
| `GOOGLE_CLIENT_ID` | MISSING | Empty in `.env` — configure via Google Cloud Console |
| `GOOGLE_CLIENT_SECRET` | MISSING | Empty in `.env` — configure via Google Cloud Console |
| `allauth` in INSTALLED_APPS | OK | `allauth`, `account`, `socialaccount`, `providers.google` |
| `django.contrib.sites` in INSTALLED_APPS | OK | Present |
| `AccountMiddleware` | OK | In MIDDLEWARE |
| `AuthenticationBackend` | OK | In AUTHENTICATION_BACKENDS |
| `SITE_ID` | OK | `1` |
| Site record | OK | `localhost:8000` — `ParfuMoray` |
| `SOCIALACCOUNT_PROVIDERS['google']` | OK | Configured with scopes |
| APP config injection | OK | Conditional — absent when env vars empty |
| `SocialApp` (database) | MISSING | No record in DB — create via admin |
| Credential resolution | BLOCKED | Will work once credentials are configured |

**21 checks total — 17 pass, 4 expected informational (missing credentials)**

## How to Fix the Remaining Issue

**Option A — Set environment variables (recommended)**

1. Create a Google Cloud Project → OAuth consent screen → OAuth client ID
2. Copy **Client ID** and **Client Secret**
3. Add to `.env`:

```env
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
```

4. Restart the server
5. `settings.py` will automatically inject `APP` with your credentials
6. Verify: `python manage.py check_google_oauth` should show all PASS

**Option B — Create SocialApp in Django Admin**

1. Fill in the env vars (above) OR leave them empty
2. Go to `/admin/socialaccount/socialapp/`
3. Click **Add Social Application**
4. Provider: `Google`
5. Name: `Google`
6. Client ID: (paste from Google Cloud Console)
7. Secret Key: (paste from Google Cloud Console)
8. Sites: Select `ParfuMoray`
9. Save

## Modified Files

| File | Change |
|------|--------|
| `parfumoray/settings.py` | `SOCIALACCOUNT_PROVIDERS` — APP injection is now conditional on non-empty env vars |
| `apps/accounts/management/commands/check_google_oauth.py` | **NEW** — diagnostic command (`python manage.py check_google_oauth`) |
| `docs/GOOGLE_OAUTH_DIAGNOSTIC.md` | **NEW** — this report |

## Remaining Manual Steps

1. [ ] Create Google Cloud OAuth credentials (see `docs/GOOGLE_LOGIN_SETUP.md`)
2. [ ] Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env`
3. [ ] OR create `SocialApp` at `/admin/socialaccount/socialapp/`
4. [ ] Run `python manage.py check_google_login` to verify readiness
5. [ ] Click "Lanjutkan dengan Google" — should redirect to Google's account chooser
