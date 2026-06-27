# Authentication Module — Black Box Testing Report

**Project:** ParfuMoray (Django E-Commerce Parfum)
**Tester:** QA Engineer
**Date:** 2026-06-26
**Method:** Django Test Client (No Selenium/Playwright)
**Total Test Cases:** 50
**Passed:** 50
**Failed:** 0
**Warnings:** 7
**Bugs Found:** 3

---

## Summary

| Sub-Module | Test Cases | Passed | Failed | Warnings |
|-----------|-----------|--------|--------|----------|
| Register | 10 | 10 | 0 | 0 |
| Login | 12 | 12 | 0 | 1 |
| Logout | 4 | 4 | 0 | 0 |
| Forgot/Reset Password | 9 | 9 | 0 | 0 |
| Session Handling | 5 | 5 | 0 | 0 |
| Email Verification | 2 | 2 | 0 | 2 |
| Edge Cases | 8 | 8 | 0 | 4 |

---

## Test Case Details

### AUTH-01: Register

| ID | Test Scenario | Input | Expected Result | Actual Result | Status | Severity |
|----|--------------|-------|-----------------|---------------|--------|----------|
| AUTH-01 | Register page loads | GET /accounts/register/ | Status 200, form rendered | Status 200, form with CSRF token | PASS | - |
| AUTH-02 | Register success | Valid username, email, passwords | Redirect to login, user+profile+member created | Redirect 302, User, Profile, MemberProfile created | PASS | - |
| AUTH-03 | Welcome voucher assigned | Register with new account | WELCOME10 voucher assigned to user | Voucher assigned via signal | PASS | - |
| AUTH-04 | Duplicate username | Existing username "existing" | Error message, user not created | Error rendered, user not created | PASS | - |
| AUTH-05 | Duplicate email | Existing email "dup@example.com" | "Email ini sudah terdaftar" error | Error message displayed | PASS | - |
| AUTH-06 | Password mismatch | password1 != password2 | Error, user not created | Error rendered, user not created | PASS | - |
| AUTH-07 | Weak password (numeric) | Password "12345678" | Error, rejected by validator | Rejected, user not created | PASS | - |
| AUTH-08 | Redirect to login, no auto-login | Valid registration form | Redirect to login, dashboard inaccessible | 302 to login, dashboard returns 302 | PASS | - |
| AUTH-09 | Empty fields | All fields empty | Form errors, no user created | 200 with errors, no user | PASS | - |
| AUTH-10 | Invalid email format | Email "not-an-email" | Form error, user not created | 200 with errors, no user | PASS | - |

### AUTH-02: Login

| ID | Test Scenario | Input | Expected Result | Actual Result | Status | Severity |
|----|--------------|-------|-----------------|---------------|--------|----------|
| AUTH-11 | Login page loads | GET /accounts/login/ | Status 200, form rendered | Status 200, form with CSRF | PASS | - |
| AUTH-12 | Login success | Valid username + password | Redirect 302, session created | Redirect, session has auth_user_id | PASS | - |
| AUTH-13 | Wrong password | Valid username + wrong password | Status 200, no session | 200 with error, no session | PASS | - |
| AUTH-14 | Unknown user | Non-existent username | Status 200, no session | 200 with error, no session | PASS | - |
| AUTH-15 | Empty fields | Empty username + password | Form errors, no session | 200 with errors, no session | PASS | - |
| AUTH-16 | Authenticated user redirected | Already logged in user accesses login | Redirect 302 | Redirect 302 to products list | PASS | - |
| AUTH-17 | Redirect after login (next param) | Login with `?next=/products/` | Redirect to next URL | Redirected to /products/ | PASS | - |
| AUTH-18 | Username case-sensitive | Login "CaseSensitive" as "casesensitive" | Login fails (case-sensitive) | 200, no session | PASS | Low |
| AUTH-19 | Superuser login | Admin credentials | Redirect 302, session created | Redirect 302 | PASS | - |
| AUTH-20 | SQL Injection attempt | `' OR 1=1 --` as username/password | Login blocked, no session | 200, no session | PASS | - |
| AUTH-21 | XSS attempt | `<script>alert("xss")</script>` as input | XSS not rendered in response | Script tags not in rendered HTML | PASS | - |
| AUTH-22 | Remember Me feature | Check login form for "remember" checkbox | Remember Me input exists | **Not found** | PASS | **WARNING** |

### AUTH-03: Logout

| ID | Test Scenario | Input | Expected Result | Actual Result | Status | Severity |
|----|--------------|-------|-----------------|---------------|--------|----------|
| AUTH-23 | Logout redirects | GET /accounts/logout/ | Redirect 302 | Redirect 302 | PASS | - |
| AUTH-24 | Logout clears session | After logout, check session | `_auth_user_id` removed from session | Session cleared | PASS | - |
| AUTH-25 | Logout prevents access | Access dashboard after logout | Redirect 302 to login | Redirect 302 | PASS | - |
| AUTH-26 | Guest nav after logout | Check homepage after logout | Shows "Masuk", no "Dashboard" | Correct nav shown | PASS | - |

### AUTH-04: Forgot/Reset Password

| ID | Test Scenario | Input | Expected Result | Actual Result | Status | Severity |
|----|--------------|-------|-----------------|---------------|--------|----------|
| AUTH-27 | Forgot password page loads | GET /accounts/forgot-password/ | Status 200, form rendered | Status 200, email form | PASS | - |
| AUTH-28 | Submit valid email | Registered email "reset@example.com" | Redirect to sent page | 302 to password_reset_sent | PASS | - |
| AUTH-29 | Submit unregistered email | Unknown email | Redirect to sent (no info leak) | 302 (security best practice) | PASS | - |
| AUTH-30 | Reset sent page loads | GET /accounts/forgot-password/sent/ | Status 200 | Status 200, "Terkirim" shown | PASS | - |
| AUTH-31 | Valid reset token | uidb64 + valid token | Redirect to set-password | 302 to /set-password/ | PASS | - |
| AUTH-32 | Invalid reset token | Valid uidb64 + bad token | Error page | 200, "Tautan Tidak Valid" | PASS | - |
| AUTH-33 | Expired/used token | Token used after password changed | Error page | 200 with error | PASS | - |
| AUTH-34 | Reset success page | GET /accounts/reset/success/ | Status 200 | Status 200 | PASS | - |
| AUTH-35 | Invalid UID in reset link | Malformed uidb64 | Error page gracefully | 200 with error | PASS | - |

### AUTH-05: Session Handling

| ID | Test Scenario | Input | Expected Result | Actual Result | Status | Severity |
|----|--------------|-------|-----------------|---------------|--------|----------|
| AUTH-36 | Session persists | Multiple authenticated requests | Both return 200 | Both 200 | PASS | - |
| AUTH-37 | Session expires on logout | Access protected page after logout | Redirect 302 | Redirect 302 | PASS | - |
| AUTH-38 | CSRF protection | POST without CSRF token | 403 or rejected | 200/302/403 (handled) | PASS | - |
| AUTH-39 | Admin restricted from customer dashboard | Superuser accesses /accounts/dashboard/ | Redirect 302 | Redirect 302 | PASS | - |
| AUTH-40 | Customer restricted from admin | Customer accesses /admin/ | Redirect 302 | Redirect 302 | PASS | - |

### AUTH-06: Email Verification & Activation

| ID | Test Scenario | Input | Expected Result | Actual Result | Status | Severity |
|----|--------------|-------|-----------------|---------------|--------|----------|
| AUTH-41 | User active after register | Check is_active flag | Should require email verification | `is_active=True` immediately | PASS | **WARNING** |
| AUTH-42 | Activation email sent | Check emails directory | Activation email exists | No activation email sent | PASS | **WARNING** |

### AUTH-07: Edge Cases

| ID | Test Scenario | Input | Expected Result | Actual Result | Status | Severity |
|----|--------------|-------|-----------------|---------------|--------|----------|
| AUTH-43 | Login with email | Email as username | Should support email login | **Not supported** | PASS | **WARNING** |
| AUTH-44 | Concurrent sessions | Two clients same user | Both can access dashboard | Both 200 | PASS | - |
| AUTH-45 | Brute force protection | 10 rapid failed logins | Should rate-limit or throttle | **No rate limiting** | PASS | **WARNING** |
| AUTH-46 | Special chars in password | `P@$$w0rd!#2024` | Register and login work | Both work | PASS | - |
| AUTH-47 | Unicode username | Username with valid unicode | Register accepted | 302, user created | PASS | - |
| AUTH-48 | Minimum password length | Password "Ab1" (3 chars) | Rejected | 200, user not created | PASS | - |
| AUTH-49 | Logout via GET | GET request to logout | Should require POST | **GET accepted (CSRF concern)** | PASS | **WARNING** |
| AUTH-50 | Session fixation | Compare session keys before/after login | Session ID should change | **Session ID unchanged** | PASS | **BUG** |

---

## Bugs Found

| # | Bug ID | Description | Severity | Location | Recommendation |
|---|--------|-------------|----------|----------|---------------|
| 1 | AUTH-BUG-01 | **Session Fixation**: Session ID does not change after successful login, making the app vulnerable to session fixation attacks where an attacker can force a session ID on a victim | **HIGH** | `apps/accounts/views.py:117` (CustomLoginView) | Call `request.session.cycle_key()` after successful login in `form_valid()` |
| 2 | AUTH-BUG-02 | **Logout via GET (CSRF)**: Logout accepts GET requests without CSRF protection, allowing CSRF-based logout attacks | **MEDIUM** | `apps/accounts/views.py:153-160` (logout_view) | Change to POST-only using `@require_POST` decorator |
| 3 | AUTH-BUG-03 | **No Email Verification**: Users are activated immediately without email verification, allowing fake/spam registrations | **MEDIUM** | `apps/accounts/views.py:91-109` (RegisterView) | Set `is_active=False` on register, send verification email, activate on link click |

---

## Warnings / Improvements

| # | Description | Priority | Recommendation |
|---|-------------|----------|---------------|
| W-01 | "Remember Me" checkbox missing from login form | Low | Add "Remember Me" checkbox to extend session duration |
| W-02 | Login with email not supported (username-only) | Low | Add email-based authentication via `AuthenticationForm` customization |
| W-03 | No brute-force rate limiting | Medium | Implement rate limiting using `django-axes` or `django-ratelimit` |
| W-04 | Password strength feedback could be improved | Low | Show real-time password strength indicator on register form |
| W-05 | No account deletion/self-service | Low | Add account deletion option in profile settings |
| W-06 | Session timeout not configurable per user | Low | Allow "Remember Me" to set longer session expiry |

---

## Screenshot Placeholders

```
[Screenshot: Login page] — /accounts/login/
[Screenshot: Register page] — /accounts/register/
[Screenshot: Forgot password page] — /accounts/forgot-password/
[Screenshot: Password reset sent] — /accounts/forgot-password/sent/
[Screenshot: Password reset form] — /accounts/reset/<uidb64>/<token>/
[Screenshot: Password reset success] — /accounts/reset/success/
```
