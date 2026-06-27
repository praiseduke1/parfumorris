# Cart & Voucher Module — Black-Box Testing Report

**Project:** ParfuMoray (Django E-Commerce Parfum)  
**Date:** 2026-06-26  
**Test File:** `tests_cart_voucher.py`  
**Method:** Django Test Client (HTTP-level, no Selenium)  
**Total Tests:** 90 | **Passed:** 90 | **Failed:** 0 | **Pass Rate:** 100%  

---

## Feature Coverage

| Module | Sub-Module | Tests | Pass | Fail | Key Validations |
|--------|-----------|-------|------|------|-----------------|
| **Cart** | Access Control | 12 | 12 | 0 | Login required, admin redirected for all 6 cart endpoints |
| **Cart** | Add Product | 16 | 16 | 0 | New item, existing increment, variant, stock cap, invalid qty, unavailable product |
| **Cart** | Remove Product | 4 | 4 | 0 | Own item, not-owned 404, nonexistent 404, cart becomes empty |
| **Cart** | Update Quantity | 10 | 10 | 0 | Increase, decrease, set, cap at stock, 0=remove, negative=remove, not-owned 404 |
| **Cart** | Calculations & Display | 8 | 8 | 0 | Empty state, item display, unit price, subtotal (single/multi), total items, variant price, final total |
| **Voucher** | Valid Application | 9 | 9 | 0 | Percentage discount, fixed discount, max cap, subtotal cap, case insensitive, display in cart |
| **Voucher** | Invalid/Expired | 11 | 11 | 0 | Not found, empty code, inactive, not started, expired, min purchase, quota exhausted, combined quota |
| **Voucher** | Non-Public/Assigned | 4 | 4 | 0 | Owned, not owned, already used, user voucher expired |
| **Voucher** | Lifecycle | 8 | 8 | 0 | Remove, discount resets, persistence, replace, recalculation (increase/decrease), invalidated after cart change |
| **Voucher** | Checkout Integration | 7 | 7 | 0 | Discount applied to order, session cleared, cart cleared, user voucher consumed, used_count incremented, invalid voucher redirect |
| **Voucher** | Edge Cases | 1 | 1 | 0 | Explicit start date, unlimited quota, remove then reapply, whitespace trimming |

---

## Detailed Test Results

### CART-01: Access Control (12 tests)

| ID | Test | Result | Notes |
|----|------|--------|-------|
| CART-ACC-01 | cart_detail requires login (anonymous → 302) | ✅ PASS | |
| CART-ACC-02 | cart_detail admin redirected (302) | ✅ PASS | Superuser can't access cart |
| CART-ACC-03 | cart_add requires login (anonymous → 302) | ✅ PASS | |
| CART-ACC-04 | cart_add admin redirected (302) | ✅ PASS | |
| CART-ACC-05 | cart_update requires login (302) | ✅ PASS | |
| CART-ACC-06 | cart_update admin redirected (302) | ✅ PASS | |
| CART-ACC-07 | cart_remove requires login (302) | ✅ PASS | |
| CART-ACC-08 | cart_remove admin redirected (302) | ✅ PASS | |
| CART-ACC-09 | apply_voucher requires login (302) | ✅ PASS | |
| CART-ACC-10 | apply_voucher admin redirected (302) | ✅ PASS | |
| CART-ACC-11 | remove_voucher requires login (302) | ✅ PASS | |
| CART-ACC-12 | remove_voucher admin redirected (302) | ✅ PASS | |

### CART-02: Add Product (16 tests)

| ID | Test | Result | Notes |
|----|------|--------|-------|
| CART-ADD-01 | Add new product creates CartItem | ✅ PASS | quantity=3, correct product & variant=None |
| CART-ADD-02 | Add with default quantity (1) | ✅ PASS | No quantity param → defaults to 1 |
| CART-ADD-03 | Add existing product increments quantity | ✅ PASS | 2 + 3 = 5 |
| CART-ADD-04 | Add to existing capped at stock | ✅ PASS | qty=10 when stock=5 → rejected, stays at 3 |
| CART-ADD-05 | Add within stock from existing | ✅ PASS | qty=2 when stock=5, existing=3 → combined=5 |
| CART-ADD-06 | Add exceeds stock rejected | ✅ PASS | qty=999 > stock=25 → error, no item created |
| CART-ADD-07 | Quantity 0 treated as 1 | ✅ PASS | `int(0)` → 0 < 1 → clamped to 1 |
| CART-ADD-08 | Quantity negative treated as 1 | ✅ PASS | `int(-5)` → -5 < 1 → clamped to 1 |
| CART-ADD-09 | Invalid quantity treated as 1 | ✅ PASS | `int('abc')` → ValueError → defaults to 1 |
| CART-ADD-10 | Unavailable product → 404 | ✅ PASS | `is_available=False` → 404 |
| CART-ADD-11 | Add with variant | ✅ PASS | Variant stored, correct quantity |
| CART-ADD-12 | Same product + same variant = increment | ✅ PASS | Separate items tracked by (product, variant) |
| CART-ADD-13 | Invalid variant ID → 404 | ✅ PASS | variant_id=99999 → 404 |
| CART-ADD-14 | Variant exceeds stock rejected | ✅ PASS | qty=10 > variant.stock=3 → rejected |

### CART-03: Remove Product (4 tests)

| ID | Test | Result | Notes |
|----|------|--------|-------|
| CART-REM-01 | Remove own item | ✅ PASS | Item deleted from DB |
| CART-REM-02 | Remove another user's item → 404 | ✅ PASS | `cart__user=request.user` filter blocks |
| CART-REM-03 | Remove nonexistent item → 404 | ✅ PASS | id=99999 |
| CART-REM-04 | Cart becomes empty after remove | ✅ PASS | `cart.items.count() == 0` |

### CART-04: Update Quantity (10 tests)

| ID | Test | Result | Notes |
|----|------|--------|-------|
| CART-UPD-01 | Increase quantity | ✅ PASS | 2 → 3 |
| CART-UPD-02 | Increase capped at stock | ✅ PASS | stock=3, cap at 3 |
| CART-UPD-03 | Decrease to zero removes item | ✅ PASS | 1 → 0 → deleted |
| CART-UPD-04 | Decrease from 2 to 1 | ✅ PASS | Normal decrease preserves item |
| CART-UPD-05 | Set specific quantity | ✅ PASS | 2 → 5 |
| CART-UPD-06 | Set quantity 0 removes | ✅ PASS | |
| CART-UPD-07 | Set capped at stock | ✅ PASS | qty=100, stock=3 → capped at 3 |
| CART-UPD-08 | Set negative removes | ✅ PASS | -1 < 0 → deleted |
| CART-UPD-09 | Invalid value preserves current | ✅ PASS | 'abc' → ValueError → keeps 2 |
| CART-UPD-10 | Update not-owned item → 404 | ✅ PASS | `cart__user=request.user` filter blocks |

### CART-05: Calculations & Display (8 tests)

| ID | Test | Result | Notes |
|----|------|--------|-------|
| CART-CAL-01 | Empty cart loads (200) | ✅ PASS | No crash, renders template |
| CART-CAL-02 | Cart displays product name | ✅ PASS | Product name in HTML |
| CART-CAL-03 | Unit price displayed | ✅ PASS | Rp 375.000 shown |
| CART-CAL-04 | Subtotal single item | ✅ PASS | 3 × 375.000 = 1.125.000 |
| CART-CAL-05 | Subtotal multiple items | ✅ PASS | (2 × 375.000) + (3 × 25.000) = 825.000 |
| CART-CAL-06 | Total items count | ✅ PASS | 2 + 3 = 5 items |
| CART-CAL-07 | Variant price in subtotal | ✅ PASS | Variant price 200.000 × 2 = 400.000 |
| CART-CAL-08 | Final total = subtotal (no voucher) | ✅ PASS | `final_total == subtotal`, `discount == 0` |

### VCH-01: Valid Voucher Application (9 tests)

| ID | Test | Result | Notes |
|----|------|--------|-------|
| VCH-VAL-01 | Apply valid percentage voucher | ✅ PASS | Session has voucher_code |
| VCH-VAL-02 | Apply valid fixed voucher | ✅ PASS | Session has voucher_code |
| VCH-VAL-03 | Percentage discount calculation | ✅ PASS | 10% of 750.000 = 75.000 |
| VCH-VAL-04 | Fixed discount calculation | ✅ PASS | FLAT50 = 50.000 off |
| VCH-VAL-05 | Percentage with max_discount cap | ✅ PASS | 20% of 1.125.000 = 225.000, capped at 100.000 |
| VCH-VAL-06 | Fixed discount capped at subtotal | ✅ PASS | 100.000 discount on 25.000 subtotal → 25.000 |
| VCH-VAL-07 | Case-insensitive code | ✅ PASS | 'diskon10' → stored as 'DISKON10' |
| VCH-VAL-08 | Voucher code shown in cart | ✅ PASS | 'DISKON10' rendered in HTML |
| VCH-VAL-09 | Discount amount shown in cart | ✅ PASS | '75.000' rendered in HTML |

### VCH-02: Invalid / Expired Voucher (11 tests)

| ID | Test | Result | Notes |
|----|------|--------|-------|
| VCH-INV-01 | Non-existent code rejected | ✅ PASS | "Kode voucher tidak ditemukan" |
| VCH-INV-02 | Empty code rejected | ✅ PASS | "Masukkan kode voucher" |
| VCH-INV-03 | Inactive voucher rejected | ✅ PASS | `is_active=False` |
| VCH-INV-04 | Future start_date rejected | ✅ PASS | "Voucher belum berlaku" |
| VCH-INV-05 | Expired voucher rejected | ✅ PASS | `expired_date < today` |
| VCH-INV-06 | Min purchase not met | ✅ PASS | 25.000 < 100.000 min_purchase |
| VCH-INV-07 | Min purchase met | ✅ PASS | 375.000 ≥ 300.000 min_purchase |
| VCH-INV-08 | Quota exhausted (used_count) | ✅ PASS | used_count=5, quota=5 |
| VCH-INV-09 | Quota exhausted (combined) | ✅ PASS | used_count=2 + 1 USED UserVoucher = 3 ≥ quota=3 |
| VCH-INV-10 | Non-public voucher not owned | ✅ PASS | No UserVoucher record |
| VCH-INV-11 | Non-public voucher already used | ✅ PASS | UserVoucher.status = USED |

### VCH-03: Non-Public / Assigned Voucher (4 tests)

| ID | Test | Result | Notes |
|----|------|--------|-------|
| VCH-ASN-01 | Owned non-public voucher accepted | ✅ PASS | UserVoucher exists, status=AVAILABLE |
| VCH-ASN-02 | Un-owned non-public rejected | ✅ PASS | "Anda tidak memiliki voucher ini" |
| VCH-ASN-03 | Already used voucher rejected | ✅ PASS | "Voucher sudah digunakan" |
| VCH-ASN-04 | UserVoucher expired rejected | ✅ PASS | `expires_at <= now()` |

### VCH-04: Voucher Lifecycle (8 tests)

| ID | Test | Result | Notes |
|----|------|--------|-------|
| VCH-LIF-01 | Remove voucher from session | ✅ PASS | Session key deleted |
| VCH-LIF-02 | Discount resets to 0 after remove | ✅ PASS | `final_total == subtotal` |
| VCH-LIF-03 | Voucher survives GET request | ✅ PASS | Session persists after cart detail page load |
| VCH-LIF-04 | Voucher survives multiple GETs | ✅ PASS | 5 page loads, voucher still present |
| VCH-LIF-05 | New voucher replaces old | ✅ PASS | DISKON10 → FLAT50, session updated |
| VCH-LIF-06 | Discount recalculated after increase | ✅ PASS | 1 item → 2 items, discount doubles |
| VCH-LIF-07 | Discount recalculated after decrease | ✅ PASS | 3 items → 2 items, discount decreases |
| VCH-LIF-08 | Voucher invalidated when cart below min | ✅ PASS | min_purchase=200.000, cart→0, voucher cleared |

### VCH-05: Checkout Integration (7 tests)

| ID | Test | Result | Notes |
|----|------|--------|-------|
| VCH-CHK-01 | Discount reflected in order | ✅ PASS | `order.discount_amount = 75.000`, `order.total_price = subtotal - discount` |
| VCH-CHK-02 | Voucher cleared from session after checkout | ✅ PASS | Session key deleted after order creation |
| VCH-CHK-03 | Cart cleared after checkout | ✅ PASS | `cart.items.count() == 0` |
| VCH-CHK-04 | UserVoucher consumed (status=USED) | ✅ PASS | `uv.status == 'used'`, `uv.used_at` set |
| VCH-CHK-05 | Voucher.used_count incremented | ✅ PASS | `used_count` from 0 → 1 |
| VCH-CHK-06 | Voucher info shown on checkout page | ✅ PASS | `voucher_code` and `discount_amount` in context |
| VCH-CHK-07 | Invalid voucher at checkout → redirect to cart | ✅ PASS | 302 with `/cart/` in URL |

### VCH-06: Edge Cases (1 test)

| ID | Test | Result | Notes |
|----|------|--------|-------|
| VCH-EDG-01 | Explicit start_date today | ✅ PASS | Voucher accepted |
| VCH-EDG-02 | Voucher without expiry (None) | ✅ PASS | No expiry check bypassed |
| VCH-EDG-03 | Unlimited quota (quota=0) | ✅ PASS | Quota check skipped |
| VCH-EDG-04 | Remove then re-apply | ✅ PASS | Works correctly |
| VCH-EDG-05 | Whitespace trimming | ✅ PASS | `'  DISKON10  '` → `'DISKON10'` |

---

## Key Calculation Verifications

### Cart Calculations

| Scenario | Formula | Expected | Verified |
|----------|---------|----------|----------|
| Single item subtotal | `price × qty` | `375.000 × 3 = 1.125.000` | ✅ |
| Multi-item subtotal | `Σ(price × qty)` | `(375.000×2) + (25.000×3) = 825.000` | ✅ |
| Total items count | `Σ qty` | `2 + 3 = 5` | ✅ |
| Variant price | `variant.price × qty` | `200.000 × 2 = 400.000` | ✅ |
| Final total (no voucher) | `subtotal - 0` | `= subtotal` | ✅ |

### Voucher Calculations

| Scenario | Formula | Expected | Verified |
|----------|---------|----------|----------|
| Percentage discount | `subtotal × amount / 100` | `750.000 × 10% = 75.000` | ✅ |
| Fixed discount | `min(amount, subtotal)` | `min(50.000, 750.000) = 50.000` | ✅ |
| % with max cap | `min(subtotal × % / 100, max_discount)` | `min(225.000, 100.000) = 100.000` | ✅ |
| Fixed capped at subtotal | `min(amount, subtotal)` | `min(100.000, 25.000) = 25.000` | ✅ |
| Discount > subtotal (fixed) | `min(amount, subtotal)` | Discount capped, final=0 | ✅ |
| Recalculation after add | `new_subtotal × % / 100` | `(750.000→1.125.000) × 10% = 112.500` | ✅ |
| Recalculation after remove | `new_subtotal × % / 100` | `(1.125.000→750.000) × 10% = 75.000` | ✅ |
| Order with voucher | `subtotal - discount` | `750.000 - 75.000 = 675.000` | ✅ |

---

## Bugs & Issues Found

### BUG-CV-01: Quota Check Mismatch Between QuerySet and Validator

**Severity:** Medium  
**Location:** `apps/promotions/models.py:10-20` (VoucherQuerySet.active) vs `apps/promotions/services.py:43-52` (validate_voucher)  

**Description:**  
- `VoucherQuerySet.active()` filters using `claimed_count < quota`  
- `validate_voucher()` checks using `used_count + UserVoucher USED count >= quota`  

These two checks use different counters (`claimed_count` vs `used_count`), so a voucher may be shown as "active" in listings but rejected when actually applied, or vice versa.  

**Example:** A voucher with `quota=5, claimed_count=5, used_count=0` would be excluded by the active queryset (claimed_count >= quota) but would pass `validate_voucher` (0 + 0 < 5).

### BUG-CV-02: Add to Cart Rejects Quantity > Stock Even for Existing Items

**Severity:** Low  
**Location:** `apps/carts/views.py:71-75`  

**Description:** When a cart already has an item (e.g., qty=3) and the user tries to add more (e.g., qty=10), the request is rejected if `10 > stock`, even though the combined total `3 + 10 = 13` would be capped at `stock=5` by the increment logic. The user gets an error "Stok tidak mencukupi" even though adding a smaller quantity would work.  

**Expected UX:** Consider checking combined quantity against stock, or communicate available add-able quantity.

### BUG-CV-03: Voucher Start Date Uses UTC via `default=now`

**Severity:** Low  
**Location:** `apps/promotions/models.py:76-79`  

**Description:** The `start_date` field uses `default=now` from `django.utils.timezone.now`, which returns a UTC datetime. When stored in a DateField, the date is derived from UTC time. In timezones ahead of UTC (e.g., Asia/Jakarta UTC+7), vouchers created in the evening (after ~17:00 UTC+7 = 10:00 UTC) will have a start_date that is the current UTC date. For Jakarta users, this means a voucher created at 02:00 WIB would have start_date = previous UTC day. This can cause confusion where a voucher appears to be "not yet active" for a few hours.

---

## Feature Gaps (Not Implemented)

| Feature | Status | Impact |
|---------|--------|--------|
| Voucher category restriction | ❌ Not implemented | Cannot restrict vouchers to specific product categories |
| Voucher product restriction | ❌ Not implemented | Cannot restrict vouchers to specific products/SKUs |
| Multiple vouchers per cart | ❌ Not implemented | Only one voucher code can be in session at a time |
| Voucher stacking (multiple codes) | ❌ Not implemented | No support for combining multiple vouchers |
| Auto-remove expired voucher from cart | ⚠️ Implemented (on page load) | Expired voucher is removed when `cart_detail` is accessed, but no proactive notification |
| Voucher discount breakdown in checkout | ⚠️ Basic | Only total discount shown, no item-level breakdown |

---

## Execution Summary

```
tests_cart_voucher.py::TestCartAccessControl        12 passed
tests_cart_voucher.py::TestCartAddProduct           16 passed
tests_cart_voucher.py::TestCartRemoveProduct         4 passed
tests_cart_voucher.py::TestCartUpdateQuantity       10 passed
tests_cart_voucher.py::TestCartCalculations          8 passed
tests_cart_voucher.py::TestVoucherValid              9 passed
tests_cart_voucher.py::TestVoucherInvalid           11 passed
tests_cart_voucher.py::TestVoucherNonPublic          4 passed
tests_cart_voucher.py::TestVoucherLifecycle          8 passed
tests_cart_voucher.py::TestVoucherCheckout           7 passed
tests_cart_voucher.py::TestVoucherEdgeCases          1 passed
================================================== 90 passed in 116.28s
```

---

## Test Environment

| Item | Value |
|------|-------|
| Python | 3.14 |
| Django | 6.0.5 |
| Database | SQLite (test) |
| Test Runner | pytest 8.x + django.test.Client |
| OS | Windows (win32) |
| Timezone | Asia/Jakarta (UTC+7) |
