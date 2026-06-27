# Customer Dashboard — Black-Box Test Report

**Date:** 2026-06-27  
**Test file:** `tests_customer_dashboard.py`  
**Total tests:** 115  
**Passed:** 115  
**Failed:** 0  
**Duration:** 147.59s  

---

## Test Groups

| Group | Tests | Module | Description |
|---|---|---|---|
| `TestDashboard` | 9 | Dashboard | Main dashboard rendering, order counts, voucher counts, profile in context, other-user isolation |
| `TestProfileEdit` | 11 | Profile / Edit Profile | Form rendering, update success, duplicate username/email, empty field validation, auto-create, sidebar info |
| `TestWishlist` | 12 | Wishlist | List empty/with items, add/remove, duplicate add, unavailable product, AJAX add/remove, context processor |
| `TestMyVouchers` | 12 | Voucher (My Vouchers) | Filter by available/used/expired/all, counts accuracy, other-user isolation, accounts URL prefix |
| `TestVoucherClaim` | 9 | Voucher (Claim) | Success, already claimed, quota exhausted, inactive/expired voucher, AJAX claim |
| `TestOrderHistory` | 12 | Order History | List empty/with orders, own orders only, newest-first, payment status, detail rendering, other-user 404, cancel button |
| `TestOrderCancel` | 5 | Order Cancel | Pending→cancelled, paid stays, already cancelled stays, other-user 404 |
| `TestOrderConfirmReceived` | 4 | Order Confirm | Delivered→completed, pending→stays, other-user 404 |
| `TestOrderTrack` | 6 | Order Tracking | Timeline rendering, pending/cancelled states, other-user 404 |
| `TestMemberDashboard` | 12 | Loyalty | Level display, points, total_spending, points history empty/with data, levels_data context, upgrade to Gold/Platinum, earn/upgrade transactions |
| `TestContextProcessors` | 8 | Notifications | cart_count, wishlist_ids, voucher_notification, floating_vouchers — authenticated and anonymous |
| `TestSuperuserBlocked` | 8 | Auth | Verify all 8 customer dashboard views redirect superusers (302) |

---

## Dashboard (Main)

| Scenario | Expected | Actual |
|---|---|---|
| GET without login | 302 redirect | ✅ |
| GET as superuser | 302 redirect | ✅ |
| GET as customer | 200 + welcome message | ✅ |
| Order counts 0 (no orders) | all zero | ✅ |
| Order counts with mixed statuses | pending=1, cancelled=1, total=3 | ✅ |
| Recent orders shown in context | order in context | ✅ |
| Voucher availability counts | available=1, used=0, expired=0 | ✅ |
| Profile in context | profile.user == request.user | ✅ |
| Other user's orders excluded | order_count=0 | ✅ |

---

## Profile / Edit Profile

| Scenario | Expected | Actual |
|---|---|---|
| GET without login | 302 | ✅ |
| GET as superuser | 302 | ✅ |
| GET as customer | 200 + "Edit Profil" or "Profil Saya" | ✅ |
| Form has username, email, phone fields | all 3 present | ✅ |
| Submit valid update → username/email/phone saved | fields persist | ✅ |
| Duplicate username → form error | "Username sudah digunakan" | ✅ |
| Duplicate email → form error | "Email sudah terdaftar" | ✅ |
| Empty username → form error | form.errors has 'username' key | ✅ |
| Success message after update | "Profil berhasil diperbarui." | ✅ |
| Profile auto-created if missing | Profile.exists() after GET | ✅ |
| Sidebar shows user info | username + email in HTML | ✅ |

---

## Wishlist

| Scenario | Expected | Actual |
|---|---|---|
| GET without login | 302 | ✅ |
| GET as superuser | 302 | ✅ |
| Empty wishlist | 200 + "Wishlist Masih Kosong" | ✅ |
| Wishlist with items shows product name | product.name in HTML | ✅ |
| Add product → Wishlist record created | exists in DB | ✅ |
| Add duplicate → no duplicate created | count=1 | ✅ |
| Add unavailable product | 404 | ✅ |
| Remove product → Wishlist record deleted | not in DB | ✅ |
| Remove nonexistent → redirect (no error) | 302 | ✅ |
| AJAX add → JSON `{saved: true, in_wishlist: true}` | ✅ |
| AJAX remove → JSON `{removed: true, in_wishlist: false}` | ✅ |
| Context processor: wishlist_product_ids includes product | ✅ |

---

## Voucher — My Vouchers

| Scenario | Expected | Actual |
|---|---|---|
| GET without login | 302 | ✅ |
| GET as superuser | 302 | ✅ |
| Empty list (status=all) | counts.available == 0 | ✅ |
| Available filter shows voucher code | code in HTML | ✅ |
| Filter available | UserVoucher in context | ✅ |
| Filter used | used UserVoucher in context | ✅ |
| Filter expired by status | expired UserVoucher in context | ✅ |
| Filter expired by date (available but past expiry) | in context + counts.expired == 1 | ✅ |
| Counts accuracy (1 available + 1 used) | available=1, used=1, expired=0 | ✅ |
| filter_status in context | matches query param | ✅ |
| Other user's vouchers not visible | available=0 | ✅ |
| Accessible via /accounts/vouchers/saya/ | 200 | ✅ |

### Filter Logic Verified

| Filter | Query |
|---|---|
| `available` | `status=AVAILABLE AND expires_at > now` |
| `used` | `status=USED` |
| `expired` | `status=EXPIRED OR (status=AVAILABLE AND expires_at <= now)` |
| `all` (default) | No filter (all UserVouchers for user) |

---

## Voucher — Claim

| Scenario | Expected | Actual |
|---|---|---|
| GET without login | 302 | ✅ |
| GET as superuser | 302 | ✅ |
| Claim valid voucher → UserVoucher created | exists in DB | ✅ |
| Claim already-claimed → no duplicate | count stays 1 | ✅ |
| Claim quota exhausted → error | is_claimable() returns False | ✅ |
| Claim inactive voucher → error | is_claimable() returns False | ✅ |
| Claim expired voucher → error | is_claimable() returns False | ✅ |
| AJAX claim success → `{success: true, voucher_code: "..."}` | ✅ |
| AJAX claim already claimed → `{success: false, error: "..."}` | ✅ |

---

## Order History

| Scenario | Expected | Actual |
|---|---|---|
| GET without login | 302 | ✅ |
| GET as superuser | 302 | ✅ |
| Empty order list | 200 + "Belum Ada Pesanan" | ✅ |
| List shows order numbers | order.order_number in HTML | ✅ |
| List only shows own orders | other user's order not in context | ✅ |
| Orders newest first | newer order first in list | ✅ |
| Payment status shown | "pending" in HTML | ✅ |
| Detail requires login | 302 | ✅ |
| Detail blocks superusers | 302 | ✅ |
| Detail renders order info | order_number in HTML | ✅ |
| Detail other user returns 404 | 404 | ✅ |
| Detail shows order items | product name in HTML | ✅ |
| Cancel button shown for PENDING_PAYMENT | "Batalkan" in HTML | ✅ |
| Cancel button hidden for PAID | not shown | ✅ |

---

## Order Cancel

| Scenario | Expected | Actual |
|---|---|---|
| GET without login | 302 | ✅ |
| GET as superuser | 302 | ✅ |
| Cancel PENDING_PAYMENT → CANCELLED | status changed + success message | ✅ |
| Cancel PAID → stays PAID | status unchanged + error message | ✅ |
| Cancel already CANCELLED → stays CANCELLED | status unchanged | ✅ |
| Cancel other user's order | 404 | ✅ |

---

## Order Confirm Received

| Scenario | Expected | Actual |
|---|---|---|
| GET without login | 302 | ✅ |
| GET as superuser | 302 | ✅ |
| Confirm DELIVERED → COMPLETED | status changed + success message | ✅ |
| Confirm PENDING_PAYMENT → stays | status unchanged + error message | ✅ |
| Confirm other user's order | 404 | ✅ |

---

## Order Tracking

| Scenario | Expected | Actual |
|---|---|---|
| GET without login | 302 | ✅ |
| GET as superuser | 302 | ✅ |
| Timeline rendered for pending order | 200 + "Menunggu" | ✅ |
| Cancelled order shows cancelled state | 200 | ✅ |
| Detail renders for other user | 404 | ✅ |

---

## Loyalty — Member Dashboard

| Scenario | Expected | Actual |
|---|---|---|
| GET without login | 302 | ✅ |
| GET as superuser | 302 | ✅ |
| Page renders | 200 + "Loyalty" or "Member" | ✅ |
| Shows current level | level in (SILVER, GOLD, PLATINUM) | ✅ |
| Shows total points | 500 displayed | ✅ |
| Shows total spending | Rp 2.000.000 | ✅ |
| Points history empty | 0 items + "Belum Ada Riwayat Poin" | ✅ |
| Points history with data | 1 record + description shown | ✅ |
| levels_data in context | contains SILVER, GOLD, PLATINUM | ✅ |
| Default level is SILVER | member.level == 'SILVER' | ✅ |
| Upgrade to Gold at 1,000,000 spending | member.level == 'GOLD' | ✅ |
| Upgrade to Platinum at 5,000,000 spending | member.level == 'PLATINUM' | ✅ |
| earn_points creates PointTransaction record | EARN type exists | ✅ |
| upgrade_level creates UPGRADE transaction | UPGRADE type exists | ✅ |

### Level Thresholds (verified)

| Level | Spending Threshold | Points Multiplier |
|---|---|---|
| Silver | ≥ 0 | 1x (10 pts per Rp 10k) |
| Gold | ≥ 1,000,000 | 1.5x (15 pts per Rp 10k) |
| Platinum | ≥ 5,000,000 | 2x (20 pts per Rp 10k) |

---

## Notifications (Context Processors)

| Scenario | Expected | Actual |
|---|---|---|
| cart_count for logged-in user (no cart) | 0 | ✅ |
| wishlist_ids for logged-in user (empty) | empty set | ✅ |
| wishlist_ids with item | contains product.id | ✅ |
| unclaimed_vouchers_count (none) | 0 | ✅ |
| unclaimed_vouchers_count with UserVoucher | 1 | ✅ |
| floating_vouchers in context | list present | ✅ |
| cart_count for anonymous | 0 | ✅ |
| wishlist_ids for anonymous | empty set | ✅ |
| voucher_notification for anonymous | 0 | ✅ |

---

## Superuser Blocking

All 8 customer-facing views redirect superusers (status 302) with the message "Administrator tidak diperbolehkan melakukan transaksi.":

| View | URL Name | Status |
|---|---|---|
| Dashboard | `accounts:dashboard` | ✅ 302 |
| Edit Profile | `accounts:profile` | ✅ 302 |
| Wishlist | `accounts:wishlist_list` | ✅ 302 |
| Loyalty | `accounts:member_dashboard` | ✅ 302 |
| My Vouchers | `promotions:my_vouchers` | ✅ 302 |
| Address List | `accounts:address_list` | ✅ 302 |
| Order List | `orders:list` | ✅ 302 |
| Order Create | `orders:create` | ✅ 302 |

---

## Module Coverage Summary

| Module | Tests | Coverage |
|---|---|---|
| **Dashboard** | 9 | Order counts, voucher counts, profile, auth guards, other-user isolation |
| **Profile / Edit Profile** | 11 | Form rendering, CRUD, duplicate validation, auto-creation, success message, sidebar |
| **Address** | — | Already covered by `tests_address.py` (94 tests, 1009 lines) |
| **Wishlist** | 12 | CRUD, AJAX, unavailable product guard, context processor |
| **Voucher (My Vouchers)** | 12 | All 4 filters, counts accuracy, auth, URL prefix |
| **Voucher (Claim)** | 9 | Success, already-claimed, quota, inactive, expired, AJAX |
| **Order History** | 12 | List/detail rendering, access control, ordering, cancel buttons |
| **Order Cancel** | 5 | All status transitions, other-user guard |
| **Order Confirm** | 4 | Delivered→completed, wrong status guard |
| **Order Track** | 6 | Timeline, cancelled state, auth |
| **Loyalty** | 12 | Level display, points, spending, history, upgrade thresholds, transactions |
| **Notifications** | 8 | All 4 context processors, authenticated + anonymous |
| **Superuser Blocking** | 8 | All 8 customer views |

---

## Bugs Found

### CV-03 (revisited): `Voucher.is_claimable()` timezone-bound date comparison

**File:** `apps/promotions/models.py:98-108`  
**Severity:** Medium  
**Description:** `Voucher.start_date` uses `default=now` (`django.utils.timezone.now`). When saved to a `DateField`, Django converts the UTC datetime to the server timezone (`Asia/Jakarta`, UTC+7) and extracts the date. However, `is_claimable()` computes `today = now().date()` which extracts the UTC date. If UTC date < Jakarta date (e.g., Jakarta at 00:30 = previous day UTC 17:30), the voucher appears to have a future `start_date` and is rejected as "not yet started".  
**Impact:** This affects both `is_claimable()` and `validate_voucher()` — voucher claiming, validation at checkout, and the `active()` queryset.  
**Note:** Same root cause as CV-02 documented in `cart_voucher_testing.md`. Fix requires using `localtime()` or `localdate()` for date comparisons.
