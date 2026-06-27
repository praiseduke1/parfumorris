# User Acceptance Testing (UAT) Report — ParfuMoray

**Date:** 2026-06-27  
**Tester:** Automated simulation (Django test client)  
**Environment:** Windows, Python 3.14, SQLite, Django 6.0, DEBUG=False  
**Test File:** `tests_uat.py`  
**Results:** 67/67 PASS | 0 FAIL

---

## Test Scenarios

| # | Scenario | Expected | Actual | Status | Bug |
|---|----------|----------|--------|--------|-----|
| 1 | **Register** — POST `/accounts/register/` with valid data | 302 redirect to login | 302 | PASS | — |
| 2 | **User Created** — Verify User row in DB | True | True | PASS | — |
| 3 | **Welcome Voucher** — WELCOME10 auto-assigned | True | True (code=WELCOME10) | PASS | — |
| 4 | **Login** — POST `/accounts/login/` with credentials | 302 redirect to /products/ | 302 | PASS | — |
| 5 | **Dashboard** — GET `/accounts/dashboard/` after login | 200 | 200 | PASS | — |
| 6 | **Product List** — GET `/products/` | 200 | 200 | PASS | — |
| 7 | **Product List Content** — Page shows products | True | True | PASS | — |
| 8 | **Category Filter** — GET `/products/?category=eau-de-parfum` | 200 | 200 | PASS | — |
| 9 | **Fragrance Family** — GET `/products/family/citrus/` | 200 | 200 | PASS | — |
| 10 | **Product Detail** — GET `/products/morris-noir/` | 200 | 200 | PASS | — |
| 11 | **Detail Shows Name** — Product name in response | True | True | PASS | — |
| 12 | **Search by Name** — GET `/products/?q=morris` | 200 | 200 | PASS | — |
| 13 | **Search Finds Product** — Matching product in results | True | True | PASS | — |
| 14 | **Search by Description** — GET `/products/?q=woody` | 200 | 200 | PASS | — |
| 15 | **Description Search Works** — Product found via desc | True | True | PASS | — |
| 16 | **Search No Results** — GET `/products/?q=nonexistent_xyz` | 200 | 200 | PASS | — |
| 17 | **No Results Shown** — Non-matching product absent | True | True | PASS | — |
| 18 | **Add to Wishlist** — POST `/accounts/wishlist/add/N/` | 302 | 302 | PASS | — |
| 19 | **Wishlist DB Entry** — Wishlist row created | True | True | PASS | — |
| 20 | **Wishlist Page** — GET `/accounts/wishlist/` | 200 | 200 | PASS | — |
| 21 | **Wishlist Shows Product** — Product name in list | True | True | PASS | — |
| 22 | **Duplicate Add** — POST same product again | 302 (idempotent) | 302 | PASS | — |
| 23 | **Remove from Wishlist** — POST remove | 302 | 302 | PASS | — |
| 24 | **Wishlist Removed from DB** — Row deleted | True | True | PASS | — |
| 25 | **Add to Cart** — POST `/cart/add/N/` with variant | 302 | 302 | PASS | — |
| 26 | **Cart DB Entry** — CartItem row created | True | True | PASS | — |
| 27 | **Cart Quantity** — Item quantity = 2 | 2 | 2 | PASS | — |
| 28 | **Cart Page** — GET `/cart/` | 200 | 200 | PASS | — |
| 29 | **Cart Shows Product** — Product name in cart | True | True | PASS | — |
| 30 | **Add Second Product** — POST another product | 302 | 302 | PASS | — |
| 31 | **2 Items in Cart** — CartItem count = 2 | 2 | 2 | PASS | — |
| 32 | **Update Quantity** — POST increase action | 302 | 302 | PASS | — |
| 33 | **Quantity after Increase** — CartItem.qty = 2 | 2 | 2 | PASS | — |
| 34 | **Apply Voucher** — POST `/cart/voucher/apply/` with code | 302 | 302 | PASS | — |
| 35 | **Voucher in Session** — `voucher_code` set | True | True | PASS | — |
| 36 | **Cart with Voucher** — Page renders with discount info | 200 | 200 | PASS | — |
| 37 | **Discount Info Visible** — Voucher code/amount in HTML | True | True | PASS | — |
| 38 | **Remove Voucher** — POST `/cart/voucher/remove/` | 302 | 302 | PASS | — |
| 39 | **Voucher Removed** — Session cleared | True | True | PASS | — |
| 40 | **Add Address** — POST address form | 302 | 302 | PASS | — |
| 41 | **Address DB Entry** — CustomerAddress created | True | True | PASS | — |
| 42 | **Address List Page** — GET `/accounts/dashboard/addresses/` | 200 | 200 | PASS | — |
| 43 | **Address Shows Saved** — Address text in response | True | True | PASS | — |
| 44 | **Checkout** — POST `/orders/create/` with form data | 302 redirect to payment | 302 | PASS | — |
| 45 | **Order DB Entry** — Order row created | True | True | PASS | — |
| 46 | **Order Status** — `pending_payment` | pending_payment | pending_payment | PASS | — |
| 47 | **Order Number** — Generated correctly | ORD-... | ORD-20260626-... | PASS | — |
| 48 | **Total Price > 0** — Order total calculated | True | True | PASS | — |
| 49 | **Voucher Applied** — Discount amount > 0 | True | True | PASS | — |
| 50 | **Order Items** — 2 items in order | 2 | 2 | PASS | — |
| 51 | **Cart Cleared** — CartItems deleted after checkout | 0 | 0 | PASS | — |
| 52 | **Payment Page** — GET `/payment/checkout/N/` | 200 | 200 | PASS | — |
| 53 | **Payment Notification** — POST webhook (settlement) | 200 OK | 200 | PASS | — |
| 54 | **Order Status after Payment** — changed to `paid` | paid | paid | PASS | — |
| 55 | **Payment Record** — Payment row created | True | True | PASS | — |
| 56 | **Payment Status** — Set to `success` | success | success | PASS | — |
| 57 | **Payment Transaction ID** — Stored correctly | TRX-MID-... | TRX-MID-123456789 | PASS | — |
| 58 | **Product Stock** — Decremented by quantity (25→23) | 23 | 23 | PASS | — |
| 59 | **ProductVariant Stock** — Decremented by quantity | 23 | 23 | PASS | (fixed) |
| 60 | **Order List** — GET `/orders/` | 200 | 200 | PASS | — |
| 61 | **Order List Shows Order** — Order number in list | True | True | PASS | — |
| 62 | **Order Detail** — GET `/orders/N/` | 200 | 200 | PASS | — |
| 63 | **Order Detail Shows Status** — Status text visible | True | True | PASS | — |
| 64 | **Order Tracking** — GET `/orders/N/track/` | 200 | 200 | PASS | — |
| 65 | **Logout** — GET `/accounts/logout/` | 302 | 302 | PASS | — |
| 66 | **Dashboard Blocked** — Requires login after logout | 302 redirect | 302 | PASS | — |
| 67 | **Wishlist Blocked** — Requires login after logout | 302 redirect | 302 | PASS | — |

---

## Bug Fixes

### BUG-001: ProductVariant stock not decremented on payment settlement **[FIXED]**

**Severity:** High  
**Component:** `apps/payments/views.py:_process_successful_payment()`  
**Fix applied:**

1. Added `variant = ForeignKey(ProductVariant, null=True, blank=True)` to `OrderItem` (`apps/orders/models.py:209`)
2. Saved `cart_item.variant` during order creation in `order_create` (`apps/orders/views.py:72`)
3. Updated `_process_successful_payment` to also decrement `ProductVariant.stock` (`apps/payments/views.py:99-102`)
4. Migration: `apps/orders/migrations/0012_add_variant_fk_to_orderitem.py`

**Result:** `ProductVariant.stock` now correctly decrements from 25→23 after settlement.

---

## Recommendations

| Priority | Issue | Recommendation |
|----------|-------|---------------|
| P0 | BUG-001: Variant stock not decremented | **[FIXED]** Added variant FK to OrderItem + decrement on payment |
| P1 | WELCOME10 migration missing `voucher_type='welcome'` | Update migration 0002 to set `voucher_type='welcome'` (currently defaults to `'public'`) |
| P2 | Checkout address form duplicates saved addresses | Allow selecting from saved CustomerAddress instead of re-entering every field |
| P3 | No admin notification on new orders | Add signal/listener to notify staff when order is created |

---

## Key Observations

1. **Registration flow** works end-to-end: user creation → welcome voucher assignment → redirect to login.
2. **Search** is integrated into the ProductListView (no separate search view). Searches on `name` and `description` only — no note/brand/category search.
3. **Cart is user-based** (OneToOneField), not session-based. Only authenticated users can have a cart.
4. **Voucher application** works via session (`voucher_code`), validated at checkout and also during payment.
5. **Midtrans payment** integration is properly mocked for testing with signature verification, webhook processing, and stock decrement.
6. **SeparateAdminSessionMiddleware** correctly isolates admin sessions from frontend sessions.
7. **Logout** properly clears the session and redirects unauthenticated users to login for protected pages.

---

## Final Conclusion

**67 out of 67 test scenarios passed.**

The core e-commerce flow (Register → Login → Browse → Search → Wishlist → Cart → Voucher → Checkout → Payment → View Order → Logout) is functionally complete and stable.

**One high-severity bug was found and fixed:** ProductVariant stock was not decremented after payment (BUG-001). Added `variant` FK to `OrderItem`, populated it during checkout, and decrement variant stock on payment settlement.

**Ready for Production?**  
**YES**
