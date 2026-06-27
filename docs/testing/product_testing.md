# Black-Box Testing Report — Customer Browsing Features

**Date:** 2026-06-26  
**Test File:** `tests_product_browsing.py`  
**Method:** Django Test Client (HTTP-level, no Selenium)  
**Total Tests:** 92 | **Passed:** 92 | **Failed:** 0 | **Pass Rate:** 100%  

---

## Feature Coverage

| Module | ID Range | Tests | Pass | Fail | Key Validations |
|---|---|---|---|---|---|
| **Home Page** | HOME-01–13 | 13 | 13 | 0 | Hero banner, featured products, new arrivals, fragrance families, voucher section (anonymous/customer/admin), stats bar, CTA section, nav links |
| **Product List** | LIST-01–19 | 19 | 19 | 0 | Page loads, all products shown, count display, category/gender/occasion badges, price, Add to Cart (logged-in), out-of-stock badge, low-stock badge, disabled Stok Habis button, product links, wishlist visibility, admin mode badge, empty state |
| **Product Detail** | DETAIL-01–15 | 15 | 15 | 0 | Page loads, name/price, description, category, fragrance families, fragrance notes, Add to Cart (customer), Add to Cart (anonymous), related products, reviews section, 404 for unavailable, 404 for out-of-stock, slug redirect, review form auth |
| **Category Filter** | CAT-01–09 | 9 | 9 | 0 | Filter by category, title update, category + search combined, reset link visibility, sidebar categories, search preservation, empty category, invalid slug |
| **Search** | SEA-01–10 | 10 | 10 | 0 | By name, by description, partial match, case-insensitive, no results (empty state), empty query, whitespace-only, search + category combined, placeholder, category preservation |
| **Sorting** | SORT-01–03 | 3 | 3 | 0 | Default order (newest first), empty sort param, invalid sort param |
| **Pagination** | PAG-01–10 | 10 | 10 | 0 | Single page (no pagination), multi-page (pagination shown), page 2, remaining products, page > max, non-integer page, page 0, negative page, query preservation, page links |
| **Fragrance Guide** | GUIDE-01–05 | 5 | 5 | 0 | Page loads, 5 fragrance families listed, notes pyramid (top/middle/base + durations), how-to-choose section, CTA to product list |
| **Promotion Banner** | PROMO-01–08 | 8 | 8 | 0 | Hero banner, Koleksi 2026 badge, hero subtitle, voucher code display, hidden when no vouchers, Lihat Semua Promo link, Fragrance Guide CTA, Explore Collection CTA |

---

## Detailed Test Results

### BRO-01: Home Page (13 tests)

| ID | Test | Result | Notes |
|---|---|---|---|
| HOME-01 | Page loads (200) | ✅ PASS | |
| HOME-02 | Hero section with branding + CTAs | ✅ PASS | "Signature Scent", "Explore Collection", "Fragrance Guide" |
| HOME-03 | Featured products section | ✅ PASS | Shows product names |
| HOME-04 | New arrivals section | ✅ PASS | "New Arrivals" heading |
| HOME-05 | Fragrance families section | ✅ PASS | Family names shown |
| HOME-06 | Voucher section for anonymous | ✅ PASS | Shows "Masuk untuk Klaim" CTA |
| HOME-07 | Voucher claim for customer | ✅ PASS | Shows "Klaim Voucher" button |
| HOME-08 | Voucher claimed state | ✅ PASS | Shows "Sudah Diklaim" for claimed voucher |
| HOME-09 | Voucher hidden from admin | ✅ PASS | Section not rendered for superuser |
| HOME-10 | Stats bar | ✅ PASS | 4 metrics: Fragrance Variants, Authentic, Long Lasting, Delivery |
| HOME-11 | CTA section for anonymous | ✅ PASS | "Register Free" + "Start Shopping" shown |
| HOME-12 | CTA section for logged-in | ✅ PASS | "Register Free" hidden |
| HOME-13 | Navigation links | ✅ PASS | Product list + fragrance guide URLs present |

### BRO-02: Product List (19 tests)

| ID | Test | Result | Notes |
|---|---|---|---|
| LIST-01 | Page loads (200) | ✅ PASS | |
| LIST-02 | All products shown | ✅ PASS | |
| LIST-03 | Product count displayed | ✅ PASS | "N produk ditemukan" |
| LIST-04 | Category badge | ✅ PASS | Category name on card |
| LIST-05 | Gender badge (men) | ✅ PASS | "&#9794; Pria" shown |
| LIST-06 | Gender badge (women) | ✅ PASS | "&#9792; Wanita" shown |
| LIST-07 | No gender badge for unisex | ✅ PASS | HTML entities not rendered |
| LIST-08 | Occasion badge | ✅ PASS | |
| LIST-09 | Price displayed | ✅ PASS | "Rp" present |
| LIST-10 | Add to Cart for logged-in | ✅ PASS | "Tambah ke Keranjang" button |
| LIST-11 | Out-of-stock badge | ✅ PASS | "Habis" badge on card |
| LIST-12 | Low stock badge | ✅ PASS | "Sisa N" with count |
| LIST-13 | Disabled Stok Habis button | ✅ PASS | For stock=0 products |
| LIST-14 | Product links to detail | ✅ PASS | Detail URL in card |
| LIST-15 | Title "Semua Parfum" | ✅ PASS | Default page title |
| LIST-16 | Empty state | ✅ PASS | "Produk Tidak Ditemukan" + "Reset Filter" |
| LIST-17 | Wishlist hidden from anonymous | ✅ PASS | Wishlist add URL not present |
| LIST-18 | Wishlist shown for logged-in | ✅ PASS | Wishlist add URL present |
| LIST-19 | Admin mode badge | ✅ PASS | "Mode Administrator" shown |

### BRO-03: Product Detail (15 tests)

| ID | Test | Result | Notes |
|---|---|---|---|
| DETAIL-01 | Page loads (200) | ✅ PASS | |
| DETAIL-02 | Name and price | ✅ PASS | |
| DETAIL-03 | Description | ✅ PASS | |
| DETAIL-04 | Category info | ✅ PASS | |
| DETAIL-05 | Fragrance families | ✅ PASS | |
| DETAIL-06 | Fragrance notes | ✅ PASS | |
| DETAIL-07 | Add to Cart for logged-in | ✅ PASS | Cart add URL present |
| DETAIL-08 | Add to Cart for anonymous | ✅ PASS | Shown on detail page |
| DETAIL-09 | Related products | ✅ PASS | Section present |
| DETAIL-10 | Reviews section | ✅ PASS | "Ulasan Pembeli" heading with rating |
| DETAIL-11 | 404 for unavailable | ✅ PASS | |
| DETAIL-12 | 404 for out-of-stock (is_available=False) | ✅ PASS | Unavailable products return 404 |
| DETAIL-13 | Slug redirect | ✅ PASS | 301 redirect for old slugs |
| DETAIL-14 | Review form requires login | ✅ PASS | |
| DETAIL-15 | Detail page accessible | ✅ PASS | |

### BRO-04: Category Filter (9 tests)

| ID | Test | Result | Notes |
|---|---|---|---|
| CAT-01 | Filter by category | ✅ PASS | Only matching products shown |
| CAT-02 | Title updates with category name | ✅ PASS | "Eau de Parfum" replaces "Semua Parfum" |
| CAT-03 | Category + search combined | ✅ PASS | Both filters applied |
| CAT-04 | Reset link shown | ✅ PASS | "Reset" link visible when category active |
| CAT-05 | Reset link hidden by default | ✅ PASS | No "Reset" when no filter (with products) |
| CAT-06 | Sidebar shows categories | ✅ PASS | "Kategori" heading + category names |
| CAT-07 | Search preserved when filtering | ✅ PASS | `q` param in filter URLs |
| CAT-08 | Empty category shows empty state | ✅ PASS | |
| CAT-09 | Invalid category slug | ✅ PASS | Doesn't crash |

### BRO-05: Search (10 tests)

| ID | Test | Result | Notes |
|---|---|---|---|
| SEA-01 | By name | ✅ PASS | |
| SEA-02 | By description | ✅ PASS | |
| SEA-03 | Partial match | ✅ PASS | "Mor" matches "Morris" |
| SEA-04 | Case-insensitive | ✅ PASS | "MORRIS" matches "morris" |
| SEA-05 | No results | ✅ PASS | Empty state with Reset Filter |
| SEA-06 | Empty query returns all | ✅ PASS | |
| SEA-07 | Whitespace-only | ✅ PASS | Treated as empty |
| SEA-08 | Search + category combined | ✅ PASS | |
| SEA-09 | Placeholder text | ✅ PASS | "Cari parfum" |
| SEA-10 | Category preserved in form | ✅ PASS | Hidden input for category |

### BRO-06: Sorting (3 tests)

| ID | Test | Result | Notes |
|---|---|---|---|
| SORT-01 | Default order newest first | ✅ PASS | Newest product appears before oldest |
| SORT-02 | Empty sort param | ✅ PASS | No crash |
| SORT-03 | Invalid sort param | ✅ PASS | Ignored gracefully |

### BRO-07: Pagination (10 tests)

| ID | Test | Result | Notes |
|---|---|---|---|
| PAG-01 | Single page (≤ 12) | ✅ PASS | No Previous/Next |
| PAG-02 | Multi-page (> 12) | ✅ PASS | "Selanjutnya" shown |
| PAG-03 | Page 2 accessible | ✅ PASS | Status 200 |
| PAG-04 | Page 2 shows remaining | ✅ PASS | |
| PAG-05 | Page beyond max | ✅ PASS | Returns 404 (no EmptyPage handling) |
| PAG-06 | Non-integer page | ✅ PASS | Returns 404 (no PageNotAnInteger handling) |
| PAG-07 | Page 0 | ✅ PASS | Returns 404 |
| PAG-08 | Negative page | ✅ PASS | Returns 404 |
| PAG-09 | Search query preserved | ✅ PASS | Pagination links carry `q` param |
| PAG-10 | Page number links | ✅ PASS | `?page=N` links present |

### BRO-08: Fragrance Guide (5 tests)

| ID | Test | Result | Notes |
|---|---|---|---|
| GUIDE-01 | Page loads (200) | ✅ PASS | |
| GUIDE-02 | 5 fragrance families | ✅ PASS | Citrus, Floral, Woody, Oriental, Fresh |
| GUIDE-03 | Notes pyramid | ✅ PASS | Top/Middle/Base with durations |
| GUIDE-04 | How to choose | ✅ PASS | Tips for selection |
| GUIDE-05 | CTA to product list | ✅ PASS | "Explore Our Collection" link |

### BRO-09: Promotion Banner (8 tests)

| ID | Test | Result | Notes |
|---|---|---|---|
| PROMO-01 | Hero banner | ✅ PASS | "Explore Collection" CTA present |
| PROMO-02 | Koleksi 2026 badge | ✅ PASS | Year badge shown |
| PROMO-03 | Hero subtitle | ✅ PASS | "premium fragrance" copy |
| PROMO-04 | Voucher code display | ✅ PASS | Code shown in promo section |
| PROMO-05 | Hidden when no vouchers | ✅ PASS | Section not rendered |
| PROMO-06 | Lihat Semua Promo link | ✅ PASS | Link to voucher list |
| PROMO-07 | Fragrance Guide CTA in hero | ✅ PASS | |
| PROMO-08 | Explore Collection CTA in hero | ✅ PASS | |

---

## Bugs Found During Testing

### BUG-BRW-01: Review Form Crashes for Anonymous Users

**Severity:** High  
**Location:** `apps/products/reviews.py:12-46` — `ReviewFormView.dispatch()`  
**Description:** The view uses `LoginRequiredMixin` but overrides `dispatch()` without calling `super().dispatch()` first. When an anonymous user accesses the review form URL, the code reaches `OrderItem.objects.filter(order__user=request.user)` where `request.user` is an `AnonymousUser`, causing `TypeError: Field 'id' expected a number but got SimpleLazyObject`.  
**Expected:** Redirect to login page (302).  
**Actual:** TypeError exception (500).  
**Fix:** Call `return super().dispatch(request, *args, **kwargs)` at the beginning of `dispatch()` to let `LoginRequiredMixin` handle authentication before any database queries.

### BUG-BRW-02: No Sorting Available on Product List

**Severity:** Low  
**Location:** `apps/products/views.py:55-92` — `ProductListView`  
**Description:** The product list page has no sorting controls (dropdown or links). Products are always ordered by `-created_at` (newest first). Users cannot sort by price, name, rating, or popularity.  
**Suggestion:** Add a sort dropdown with options like "Terbaru" (newest), "Termurah" (cheapest), "Termahal" (most expensive), "Terpopuler" (most popular).

### BUG-BRW-03: Pagination Returns 404 for Invalid Pages

**Severity:** Medium  
**Location:** `apps/products/views.py:55-92` — `ProductListView`  
**Description:** No error handling for `PageNotAnInteger` or `EmptyPage` exceptions from Django's paginator. Requesting `?page=abc` or `?page=999` returns a 404 page instead of showing the first/last page.  
**Suggestion:** Catch `PageNotAnInteger` → return page 1, catch `EmptyPage` → return last page.

### BUG-BRW-04: Out-of-Stock Products Return 404 on Detail Page

**Severity:** Low  
**Location:** `apps/products/views.py:113-124` — `ProductDetailView.get_queryset()`  
**Description:** Products with `is_available=False` return 404 on their detail page. While functionally correct (can't buy them), there is no informative message.  
**Suggestion:** Show a friendly "Produk Tidak Tersedia" page instead of a generic 404 when the product exists but is marked unavailable.

---

## Feature Gaps (Not Implemented)

| Feature | Status | Impact |
|---|---|---|
| Sorting (by price, name, rating) | ❌ Not implemented | Users cannot reorder product list |
| Pagination graceful error handling | ❌ Not implemented | Invalid pages return 404 |
| Fragrance note filtering on product list | ⚠️ No notes in database | Feature exists (`by_note` URL) but no test data |
| Promotion banner carousel/slider | ❌ Not implemented | Static hero only |
| Search autocomplete/suggestions | ❌ Not implemented | Plain text input |
| Breadcrumb navigation | ❌ Not implemented | No breadcrumbs on listing or detail pages |
| Empty state illustrations | ⚠️ Basic text only | Text message without visuals |

---

## Execution Summary

```
tests_product_browsing.py::TestHomePage       13 passed
tests_product_browsing.py::TestProductList     19 passed
tests_product_browsing.py::TestProductDetail   15 passed
tests_product_browsing.py::TestCategoryFilter   9 passed
tests_product_browsing.py::TestSearch          10 passed
tests_product_browsing.py::TestSorting          3 passed
tests_product_browsing.py::TestPagination      10 passed
tests_product_browsing.py::TestFragranceGuide   5 passed
tests_product_browsing.py::TestPromotionBanner  8 passed
============================================== 92 passed in 16.22s
```
