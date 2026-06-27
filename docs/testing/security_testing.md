# Security Testing Report — ParfumoRay (Morris Parfum)

**Generated:** 2026-06-27
**Scope:** Full codebase — Django 6.0 e-commerce application (8 apps)

---

## Summary

| Severity | Count |
|----------|-------|
| Critical | 1 |
| High     | 2 |
| Medium   | 6 |
| Low      | 6 |

---

## Critical

### C-01: Sensitive Credentials in `.env` File on Disk

**Category:** Sensitive Data Exposure
**File:** `.env`
**Lines:** 10–12

Active Midtrans payment gateway credentials and Django `SECRET_KEY` stored in plaintext:

```
MIDTRANS_MERCHANT_ID=M760617262
MIDTRANS_CLIENT_KEY=Mid-client-Qp5ISr2xqVTJQpLR
MIDTRANS_SERVER_KEY=YOUR_MIDTRANS_SERVER_KEY
SECRET_KEY=django-insecure-*v-1(p=ip!b1-yj5ag-qoa8(#0pg%y3lg_*s8(fc7y73%$_8ru
```

**Risk:** Server key allows direct Midtrans API calls — charge transactions, refunds, status queries. `SECRET_KEY` compromise enables session forging, CSRF bypass, and signed-data tampering.

**Test:**
1. Verify `.env` is in `.gitignore`.
2. Confirm production uses environment variables (not `.env` file).
3. Rotate all exposed credentials immediately.

**Remediation:** Remove `.env` from production, use environment variables or vault, rotate secrets.

---

## High

### H-01: Open Redirect in Login Redirect

**Category:** Broken Access Control
**File:** `apps/accounts/views.py:140–144`
**Severity:** High

```python
def get_success_url(self):
    next_url = self.request.POST.get('next') or self.request.GET.get('next')
    if next_url:
        return next_url
    return reverse_lazy('products:list')
```

The `get_success_url()` override bypasses Django's built-in `url_has_allowed_host_and_scheme()` safety check. An attacker can craft a login link with `?next=https://evil.com/` and after successful authentication the user will be redirected to an external site (phishing).

**Test:**
```
GET /accounts/login/?next=https://evil.com/phish
→ login → 302 redirect to https://evil.com/phish
```

**Remediation:** Use `url_has_allowed_host_and_scheme()` or let `AuthViewsMixin.get_success_url()` handle validation.

```python
def get_success_url(self):
    redirect_to = self.request.POST.get('next') or self.request.GET.get('next')
    if redirect_to and url_has_allowed_host_and_scheme(redirect_to, allowed_hosts={self.request.get_host()}):
        return redirect_to
    return reverse_lazy('products:list')
```

---

### H-02: No Rate Limiting on Any Endpoint

**Category:** Rate Limiting
**Files:** All views across all 8 apps

No rate limiting is implemented anywhere:

| Endpoint | Risk |
|----------|------|
| `POST /accounts/login/` | Brute-force password guessing |
| `POST /accounts/register/` | Account creation spam |
| `/accounts/reset/<uidb64>/<token>/` | Password reset brute-force |
| `POST /payment/notification/` | Webhook replay attacks |
| `POST /cart/apply-voucher/` | Voucher code brute-force |
| `GET /api/locations/*` | Data scraping |
| `POST /promotions/claim/<id>/` | Voucher claim abuse |

**Test:** Attempt 1000 rapid requests to login endpoint — observe no throttle/block.

**Remediation:** Implement `django-ratelimit` or use Redis-based throttling middleware. At minimum, add rate limiting to login, registration, password reset, and voucher claim endpoints.

---

## Medium

### M-01: Admin Session Cookie Has Broad Path

**Category:** Session Hijacking
**File:** `apps/core/middleware.py:38–39`

```python
response.cookies[self.ADMIN_COOKIE] = admin_cookie_val
response.cookies[self.ADMIN_COOKIE]['path'] = '/'
```

The `admin_sessionid` cookie is set with `path='/'`, meaning it is sent with **every request** to the site, not just `/admin/*` paths. This increases exposure to XSS-based session theft and CSRF on non-admin pages.

**Test:**
```
GET / (any page)
Cookie: admin_sessionid=<valid admin session>
→ Confirm admin session is sent on non-admin requests
```

**Remediation:** Set `path='/admin/'` on the admin session cookie.

---

### M-02: State-Changing Operations via GET Requests

**Category:** CSRF
**File:** `apps/payments/views.py:113–145`

`payment_finish`, `payment_unfinish`, and `payment_error` are GET-only views (`@login_required`) that trigger payment status updates, stock deductions, and loyalty point awards.

While ownership checks (`_ensure_order_owner`) mitigate direct exploitation, GET-based state changes violate HTTP semantics and can be triggered by:
- Image prefetching
- CSRF via `<img>` tags
- Browser preconnect/prerender

**Test:**
```
GET /payment/finish/<order_id>/
→ Payment status updated, stock deducted via GET
```

**Remediation:** Use POST for state changes. Accept GET only as a redirect target from Midtrans, then have the frontend POST to confirm.

---

### M-03: No Session Timeout or Rotation on Sensitive Actions

**Category:** Session Fixation / Session Hijacking
**Files:** `parfumoray/settings.py:238`, `apps/accounts/views.py:153–160`

- `SESSION_COOKIE_AGE = 86400` (24 hours) — no idle timeout
- `SESSION_ENGINE = 'db'` — sessions stored in SQLite, no encryption
- Session key logged at login: `logger.warning(f"...session_key={request.session.session_key}")` — session key leak

**Test:**
1. Login, capture session cookie.
2. Wait 24 hours — session still valid.
3. Check logs for exposed session keys.

**Remediation:** Configure `SESSION_COOKIE_AGE` lower (e.g., 2 hours), add idle timeout middleware, avoid logging session keys.

---

### M-04: Debug Mode Enabled in `.env`

**Category:** Sensitive Data Exposure
**File:** `.env:2`

```
DEBUG=True
```

If this configuration reaches a production environment, Django's debug mode will leak:
- Full stack traces with local variables
- Database queries and credentials
- Settings (including `SECRET_KEY`)

**Test:**
```
GET /nonexistent-page
→ Django debug traceback with settings dump
```

**Remediation:** Set `DEBUG=False` in production via environment variable override. Add a check in `settings.py` to warn if `DEBUG=True` when not in local dev.

---

### M-05: Staff Users (Non-Superuser) Bypass `customer_required`

**Category:** Authorization
**Files:** `apps/core/decorators.py:7–17`, `apps/core/mixins.py:5–13`

```python
def customer_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_superuser:
            messages.warning(...)
            return redirect('products:home')
        return view_func(request, *args, **kwargs)
```

Only `is_superuser` is checked. Users with `is_staff=True` but `is_superuser=False` can access customer-only endpoints (checkout, orders, cart, profile, reviews, vouchers).

**Test:** Create a staff (non-superuser) account and access `/orders/create/` — should be blocked but is not.

**Remediation:** Use `is_staff` instead of or in addition to `is_superuser`:
```python
if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
```

---

### M-06: JSONField Stores Raw Midtrans Response Unbounded

**Category:** Sensitive Data Exposure
**File:** `apps/payments/models.py:47`

```python
raw_response = models.JSONField('Response Midtrans', default=dict, blank=True)
```

The full Midtrans payment notification response is stored as-is. If Midtrans ever returns sensitive data (PAN truncations, etc.) in the notification body, it will be persisted in the database with no access control at the model level.

**Test:** Check a Payment record's `raw_response` field for any card or account identifiers.

**Remediation:** Whitelist specific fields to store or ensure Midtrans sandbox/production notifications are reviewed for sensitive data.

---

## Low

### L-01: Safe Filter with System-Generated Help Text

**Category:** XSS
**File:** `templates/accounts/create_new_password.html:48`

```django
{% for tip in form.new_password1.help_text|safe %}
```

Uses the `safe` filter on password help text. While Django's password help text is system-generated and not user-controllable, this bypasses auto-escaping. If a custom password validator with user-supplied help_text were added, it would be rendered unsanitized.

**Test:** Manual review only — confirm no custom password validators return user-supplied data.

**Remediation:** Remove `|safe` filter unless required; if needed, ensure help_text is never user-controllable.

---

### L-02: No File Upload Validation

**Category:** File Upload
**File:** `apps/products/models.py` (Product.image, ProductImage.image)

Product/category images use Django's `ImageField` which validates that uploaded content is a valid image. However, there is no:
- File size limit
- File type whitelist enforcement (beyond PIL validation)
- Virus/malware scanning
- Upload quota per user

**Test:**
```
POST /admin/products/product/1/change/
→ Upload a 100MB file or a polyglot (valid image + embedded script)
```

**Remediation:** Add `MAX_UPLOAD_SIZE` validator, explicit `Content-Type` checks, and consider using secure file storage with upload scanning.

---

### L-03: Production Media Serving Not Configured

**Category:** File Upload
**File:** `parfumoray/urls.py:24–25`

```python
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

Media files are only served in DEBUG mode. In production, there is no route or configuration for serving user-uploaded images. Whitenoise (configured for static files) does not serve media files by default.

**Test:** Access `/media/products/image.jpg` in production — returns 404.

**Remediation:** Configure a production media serving strategy: nginx/Apache direct, S3/CDN, or django-storages.

---

### L-04: Logging of Session Keys and User Details

**Category:** Sensitive Data Exposure
**Files:** `apps/accounts/views.py:122–128`, `apps/accounts/views.py:133–137`, `apps/products/views.py:19–22, 62–65, 114–117`

```python
logger.warning(
    f"LOGIN PAGE — user={request.user.id} "
    f"username={request.user.username} "
    f"superuser={request.user.is_superuser} "
    f"session_key={request.session.session_key}"
)
```

Session keys and user details are logged at `WARNING` level in multiple views across accounts and products apps. Log files may be accessible to system administrators or stored in centralized logging systems, increasing the attack surface for session hijacking.

**Test:** Check `django_server.log` for session keys in plaintext.

**Remediation:** Remove session key from logs. Reduce log level to DEBUG for user activity details. Never log session keys.

---

### L-05: Password Reset Email Exposes Username

**Category:** Authentication
**File:** `templates/registration/password_reset_email.html:8`

```django
{% translate "Your username, in case you have forgotten:" %} {{ user.get_username }}
```

The password reset email includes the username in plaintext. If the email is intercepted, the attacker knows both the email address and username, reducing the search space for credential attacks.

**Test:** Trigger password reset and inspect email content.

**Remediation:** Remove the username disclosure or use a generic greeting.

---

### L-06: No Content Security Policy (CSP) Headers

**Category:** XSS (Defense in Depth)
**Files:** `parfumoray/settings.py` (no CSP configuration)

Inline scripts are used extensively (Tailwind config `<script>` blocks, CDN-loaded scripts, Tom Select, Chart.js). No CSP headers are configured to restrict script sources.

The inline `<script>` tags contain Tailwind configuration, alert auto-dismiss logic, and mobile menu toggle. CDN scripts load from `cdn.tailwindcss.com`, `cdn.jsdelivr.net`, `fonts.googleapis.com`, `fonts.gstatic.com`.

**Test:**
```
curl -I https://parfumoray.com
→ No Content-Security-Policy header
```

**Remediation:** Implement CSP headers. At minimum:
```
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' cdn.tailwindcss.com cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' fonts.googleapis.com cdn.jsdelivr.net; font-src fonts.gstatic.com; img-src 'self' data:;
```

---

## Detailed Test Procedures

### SQL Injection
```
# Test search endpoints
GET /products/?q=' OR '1'='1
GET /products/?q='; DROP TABLE products;--

# Test region API parameters
GET /api/locations/cities/?province_id=1' OR '1'='1

# Expected: Django ORM parameterizes all queries. No raw SQL with user input.
```

### XSS
```
# Test search input reflection
GET /products/?q=<script>alert(1)</script>
# Expected: <script> is HTML-escaped by Django template engine

# Test address form fields
POST /accounts/dashboard/addresses/create/
  recipient_name=<img src=x onerror=alert(1)>
# Expected: Auto-escaped by template {{ }}

# Test review comment
POST /products/review/<slug>/
  comment=<script>alert(1)</script>
# Expected: Auto-escaped in template
```

### CSRF
```
# Verify CSRF token on forms
GET /accounts/login/
→ Response includes csrf_token in form

# Verify CSRF rejection
POST /accounts/login/ (without csrf_token)
→ 403 Forbidden

# Verify csrf_exempt webhook
POST /payment/notification/ (without csrf_token)
→ 200 OK (intentional, HMAC-signed)
```

### Authentication
```
# Account lockout
for i in {1..100}; do
  curl -X POST /accounts/login/ -d "username=admin&password=wrong$i"
done
# Expected: No lockout (missing rate limiting)

# Password reset token enumeration
# Django uses signed tokens (uidb64 + timestamp + hash) — not enumerable
```

### Authorization
```
# Horizontal privilege escalation
As user A: GET /orders/order/<user_B_order_id>/
Expected: 404 (filtered by user=request.user)

# Vertical privilege escalation (staff → customer)
As staff user (not superuser): GET /orders/create/
Expected: Should be blocked but isn't (M-05)

# Admin access
As regular user: GET /admin/dashboard/
Expected: Redirect to login (staff_member_required)
```

### Open Redirect
```
GET /accounts/login/?next=https://evil.com
→ Login with valid credentials
→ 302 redirect to https://evil.com (H-01)
```

### Rate Limiting
```
# Brute force test
for i in {1..1000}; do
  curl -s -o /dev/null -X POST /accounts/login/ \
    -d "username=admin&password=guess$i"
done
# Expected: All 1000 requests accepted (H-02)
```

### Session Testing
```
# Session fixation
1. Get a session cookie from /products/
2. Set that session cookie before login
3. Login — verify session_key changes (Django rotates on login)
```

### Sensitive Data Exposure
```
# Check .env file in version control
git log --all --full-history -- .env
# Check for committed secrets

# Check debug mode
GET /nonexistent
Expected in dev: Debug traceback
Expected in prod: 404 page (but currently DEBUG=True in .env)
```

---

## Remediation Priority Matrix

| ID | Finding | Severity | Effort | Priority |
|----|---------|----------|--------|----------|
| C-01 | Exposed credentials in `.env` | Critical | Low | **Immediate** |
| H-01 | Open redirect on login | High | Low | **Immediate** |
| H-02 | No rate limiting | High | Medium | **High** |
| M-04 | DEBUG=True in `.env` | Medium | Low | **High** |
| M-01 | Admin session cookie path=/ | Medium | Low | **High** |
| M-02 | GET-based state changes | Medium | Medium | **Medium** |
| M-05 | Staff bypass customer_required | Medium | Low | **Medium** |
| M-03 | No session timeout | Medium | Medium | **Medium** |
| M-06 | Raw Midtrans response stored | Medium | Low | **Medium** |
| L-04 | Session keys in logs | Low | Low | **Low** |
| L-06 | No CSP headers | Low | Medium | **Low** |
| L-01 | Safe filter on help text | Low | Low | **Low** |
| L-02 | No file upload validation | Low | Medium | **Low** |
| L-03 | Production media serving | Low | Medium | **Low** |
| L-05 | Username in password reset email | Low | Low | **Low** |
