# Performance Testing — ParfuMoray

**Date:** 2026-06-27  
**Method:** `pytest-benchmark` (averaged rounds) + manual query counting via `connection.queries`  
**Environment:** Windows, Python 3.14, SQLite (default), Django 6.0, DEBUG=False  
**DB State:** 9 users, 11 products, 5 categories, 10 orders, 3 cart items in session

---

## Summary

| Page | Avg Time | Queries | Status |
|------|----------|---------|--------|
| Home | 52.0ms | 105 | [ ] Optimize |
| Product List | 46.6ms | 102 | [ ] Optimize |
| Product List (filtered) | 4.9ms | 3 | [x] Good |
| Product Detail | 25.2ms | 50 | [ ] Optimize |
| Cart (empty) | 7.6ms | 12 | [x] Good |
| Cart (3 items) | 10.8ms | 15 | [x] Good |
| Checkout | 14.8ms | 19 | [x] Good |
| Dashboard | 10.7ms | 18 | [x] Good |
| Admin Index | 13.6ms | 6 | [x] Good |
| Admin Dashboard | 83.8ms | 203 | [ ] Optimize |
| Login | 3.0ms | 1 | [x] Good |
| Register | 2.9ms | 1 | [x] Good |
| Fragrance Guide | 2.5ms | 1 | [x] Good |
| About | 2.5ms | 1 | [x] Good |

**Static Assets (all served via Whitenoise, no CDN):**

| Asset | Size | Avg Time | Cache |
|------|------|----------|-------|
| `favicon.svg` | 462 B | 0.2ms | Not cached |
| `admin/css/dashboard.css` | 9.1 KB | 2.6ms | Not cached |
| `js/cascading-address.js` | 23.3 KB | 2.6ms | Not cached |

---

## Detailed Results

### 1. Home Page (`apps/products/views.py:HomeView`)
- **Benchmark mean:** 52.0ms (stddev 9.6ms)
- **DB queries:** 105
- **Status code:** 200
- **Recommendation:** High query count — likely fetching all products, categories, brands, fragrance families, and reviews in separate queries. Use `select_related()` / `prefetch_related()` to reduce to ~5-10 queries.

### 2. Product List (`apps/products/views.py:ProductListView`)
- **Benchmark mean:** 46.6ms (stddev 3.1ms)
- **DB queries:** 102
- **Status code:** 200
- **Filtered variant (gender=men):** 4.9ms, 3 queries
- **Recommendation:** When no filter is applied, the paginator loads products without `select_related`. Apply `select_related('brand', 'category')` and `prefetch_related('variants', 'images', 'fragrance_notes')` to the unfiltered queryset.

### 3. Product Detail (`apps/products/views.py:ProductDetailView`)
- **Benchmark mean:** 25.2ms (stddev 1.3ms)
- **DB queries:** 50
- **Status code:** 200
- **Recommendation:** 50 queries for a single product page is high. Likely fetching reviews, variants, related products, and images in separate queries. Consolidate with prefetching.

### 4. Cart (empty vs 3 items)
- **Empty:** 7.6ms, 12 queries
- **3 items:** 10.8ms, 15 queries (+3 for cart items)
- **Status code:** 200
- **Recommendation:** Acceptable. Cart page uses `CartItem.objects.filter(cart=cart).select_related('product')` already.

### 5. Checkout
- **Benchmark mean:** 14.8ms (stddev 3.1ms)
- **DB queries:** 19
- **Status code:** 200
- **Recommendation:** Acceptable for now. Could be further reduced by prefetching address and payment methods.

### 6. Dashboard
- **Benchmark mean:** 10.7ms (stddev 1.1ms)
- **DB queries:** 18
- **Status code:** 200
- **Recommendation:** Acceptable. Already efficient.

### 7. Admin Pages

#### Admin Index
- **Benchmark mean:** 13.6ms
- **DB queries:** 6
- **Status code:** 200
- **Recommendation:** Good. Jazzmin default index page.

#### Admin Dashboard (Analytics)
- **Benchmark mean:** 83.8ms (stddev 2.1ms)
- **DB queries:** 203
- **Status code:** 200
- **Recommendation:** **Critical.** 203 queries for a dashboard is excessive. The analytics view likely computes totals, counts, charts, and trend data in individual queries. Consolidate into aggregation queries (e.g., `User.objects.aggregate()`, `Order.objects.annotate()`) to reduce to ~10 queries.

### 8. Auth Pages (Login, Register, Fragrance Guide, About)
- **All < 3ms with 1 query each**
- **Recommendation:** Already optimal.

### 9. Static Assets
- Favicon: 0.2ms (in-memory response)
- CSS: 2.6ms (read from disk via Whitenoise)
- JS: 2.6ms (read from disk via Whitenoise)
- **Recommendation:** Negligible overhead. No CDN needed at current scale.

---

## Priority Fixes

| Priority | Page | Issue | Suggested Fix |
|----------|------|-------|---------------|
| P0 | Admin Dashboard | 203 queries | Replace per-metric queries with Django aggregation |
| P1 | Home | 105 queries | Add `select_related`/`prefetch_related` to HomeView |
| P1 | Product List | 102 queries | Add `select_related`/`prefetch_related` to ProductListView |
| P2 | Product Detail | 50 queries | Prefetch reviews, variants, and related products |
| P3 | Cart / Checkout / Dashboard | 12-19 queries | Minor optimization, currently acceptable |

---

## Recommendations

1. **Add `{% with %}` and template-level caching** to avoid re-querying footer categories in every page load.
2. **Use Django's `cached_property`** for dashboard analytics metrics that are computed on every request.
3. **Enable Django template fragment caching** (`{% cache %}`) for the product sidebar and homepage hero section.
4. **Add Redis caching** (already in `requirements.txt` as `django-redis`) for product list and home page.
5. **Set Cache-Control headers** on Whitenoise static files (currently no caching headers).
6. **Consider database indexing** on `Product.is_available`, `CartItem.cart_id`, and `Order.user_id` if not already indexed.

---

## Test Files

- `tests_performance.py`: 18 pytest-benchmark tests (15 page + 3 static)
- `perf_queries.py`: Query-counting script using Django test runner + `connection.queries`
