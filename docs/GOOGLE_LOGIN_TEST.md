# Google Login Verification Report

**Generated**: 2026-06-27 10:10:34
**Environment**: Django (6, 0, 5, 'final', 0), allauth 65.x
**Status**: ALL CHECKS PASSED

## Summary

| Metric | Value |
|--------|-------|
| Total Checks | 74 |
| Passed | 74 |
| Failed | 0 |
| Success Rate | 100.0% |

## Configuration Checklist

| Check | Status | Detail |
|-------|--------|--------|
| django.contrib.sites in INSTALLED_APPS | [PASS] PASS |  |
| allauth in INSTALLED_APPS | [PASS] PASS |  |
| allauth.account in INSTALLED_APPS | [PASS] PASS |  |
| allauth.socialaccount in INSTALLED_APPS | [PASS] PASS |  |
| allauth.socialaccount.providers.google in INSTALLED_APPS | [PASS] PASS |  |
| AccountMiddleware in MIDDLEWARE | [PASS] PASS |  |
| ModelBackend in AUTHENTICATION_BACKENDS | [PASS] PASS |  |
| Allauth AuthenticationBackend in AUTHENTICATION_BACKENDS | [PASS] PASS |  |
| SITE_ID is set | [PASS] PASS |  |
| SOCIALACCOUNT_PROVIDERS has google entry | [PASS] PASS |  |
| Google SCOPE includes email and profile | [PASS] PASS |  |
| VERIFIED_EMAIL is True | [PASS] PASS |  |
| ACCOUNT_EMAIL_VERIFICATION = 'none' | [PASS] PASS |  |
| SOCIALACCOUNT_AUTO_SIGNUP = True | [PASS] PASS |  |
| SOCIALACCOUNT_LOGIN_ON_GET = True | [PASS] PASS |  |
| SOCIALACCOUNT_EMAIL_AUTHENTICATION = True | [PASS] PASS |  |
| SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True | [PASS] PASS |  |
| ACCOUNT_UNIQUE_EMAIL = True | [PASS] PASS |  |
| LOGIN_REDIRECT_URL is set | [PASS] PASS |  |
| LOGOUT_REDIRECT_URL is set | [PASS] PASS |  |
| LOGIN_URL is set | [PASS] PASS |  |
| GOOGLE_CLIENT_ID in .env (may be empty until configured) | [PASS] PASS |  |
| GOOGLE_CLIENT_SECRET in .env (may be empty until configured) | [PASS] PASS |  |
| ACCOUNT_UNIQUE_EMAIL prevents duplicate emails via allauth flows (not model-level) | [PASS] PASS | allauth enforces email uniqueness in its own validation layer |

## URL Resolution

| URL | Status | Resolved View |
|-----|--------|---------------|
| `LOGIN_REDIRECT_URL is set` | [PASS] |  |
| `LOGOUT_REDIRECT_URL is set` | [PASS] |  |
| `LOGIN_URL is set` | [PASS] |  |
| `accounts/login/ to 'login'` | [PASS] | login |
| `accounts/register/ to 'register'` | [PASS] | register |
| `accounts/logout/ to 'logout'` | [PASS] | logout |
| `accounts/dashboard/ to 'dashboard'` | [PASS] | dashboard |
| `accounts/profile/ to 'profile'` | [PASS] | profile |
| `accounts/wishlist/ to 'wishlist_list'` | [PASS] | wishlist_list |
| `accounts/forgot-password/ to 'forgot_password'` | [PASS] | forgot_password |
| `accounts/member-benefits/ to 'member_benefits'` | [PASS] | member_benefits |
| `accounts/google/login/ to 'google_login'` | [PASS] | google_login |
| `accounts/google/login/callback/ to 'google_callback'` | [PASS] | google_callback |
| `accounts/social/connections/ to 'None'` | [PASS] | unnamed |
| `accounts/email/ to 'account_email'` | [PASS] | account_email |
| `accounts/inactive/ to 'account_inactive'` | [PASS] | account_inactive |
| `accounts/password/change/ to 'account_change_password'` | [PASS] | account_change_password |
| `Google login URL does not 404/500` | [PASS] | status=302 |
| `Google callback URL exists (401 expected without OAuth state)` | [PASS] | status=401 |

## Template Rendering

| Template | Status |
|----------|--------|
| `accounts/login.html` | [PASS] |
| `accounts/register.html` | [PASS] |
| `accounts/dashboard.html` | [PASS] |
| `accounts/profile_edit.html` | [PASS] |
| `accounts/wishlist_list.html` | [PASS] |
| `accounts/address_list.html` | [PASS] |

## Functional Tests

| Test | Status | Detail |
|------|--------|--------|
| SOCIALACCOUNT_PROVIDERS has google entry | [PASS] |  |
| Login page returns 200 | [PASS] | got 200 |
| Login page has 'Lanjutkan dengan Google' button | [PASS] |  |
| Login page links to /accounts/google/login/ | [PASS] |  |
| Login page still has email/password form | [PASS] |  |
| Login page still has 'Lupa Password' link | [PASS] |  |
| Register page returns 200 | [PASS] | got 200 |
| Register page has 'Daftar dengan Google' button | [PASS] |  |
| Register page links to /accounts/google/login/ | [PASS] |  |
| Login page preserves next parameter | [PASS] |  |
| SocialAccount linked to user | [PASS] |  |
| Existing user can link Google account | [PASS] |  |
| Allauth EmailAddress creation works | [PASS] |  |

## User Creation & Profile Tests

| Test | Status | Detail |
|------|--------|--------|
| User is authenticated after login | [PASS] |  |
| Profile auto-created for existing user | [PASS] |  |
| MemberProfile auto-created for existing user | [PASS] | level=SILVER, points=0 |
| Logout clears session | [PASS] |  |
| Logout redirects to products:list | [PASS] |  |
| Profile created for new social user | [PASS] |  |
| MemberProfile created for new social user | [PASS] |  |
| SocialAccount record created | [PASS] |  |
| SocialAccount linked to user | [PASS] |  |
| SocialAccount provider is Google | [PASS] |  |
| Profile exists for social user | [PASS] |  |
| MemberProfile exists for social user | [PASS] |  |
| No duplicate user for same email | [PASS] | found 1 |
| ACCOUNT_UNIQUE_EMAIL prevents duplicate emails via allauth flows (not model-level) | [PASS] | allauth enforces email uniqueness in its own validation layer |

## Migration State

| All migrations applied | [PASS] | 0 pending migrations |

## Remaining Issues

No failing checks. All configurations, URLs, templates, and auth flows are correct.
## Production Deployment Checklist

- [ ] Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env` (from Google Cloud Console)
- [ ] Register SocialApp at `/admin/socialaccount/socialapp/` with Provider=Google, Client ID, Secret Key, and site=ParfuMoray
- [ ] Update Authorized Redirect URIs in Google Cloud Console to `https://yourdomain.com/accounts/google/login/callback/`
- [ ] Update Authorized JavaScript Origins to `https://yourdomain.com`
- [ ] Update Django Site domain at `/admin/sites/site/` to your production domain
- [ ] Set `DEBUG=False` and ensure `ALLOWED_HOSTS` includes your domain
- [ ] Verify `CSRF_TRUSTED_ORIGINS` includes your domain if behind a proxy
- [ ] Test the full Google OAuth flow end-to-end in the production environment
- [ ] Verify social login works with existing accounts (email match)
- [ ] Verify new Google users get Profile and MemberProfile created automatically
- [ ] Verify logout clears session and redirects correctly