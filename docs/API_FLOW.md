# API_FLOW.md

## 1. Alur Browsing Produk

```
User                      Browser                    Server (Django)
│                           │                            │
│  Buka halaman utama       │                            │
│──────────────────────────►│                            │
│                           │  GET /                     │
│                           │───────────────────────────►│
│                           │                            │  SELECT * FROM product
│                           │                            │  WHERE is_available=True
│                           │                            │  LIMIT 8 (featured)
│                           │                            │  + categories + new arrivals
│                           │                            │  + fragrance_families
│                           │                            │
│                           │◄────────── home.html ──────│
│◄──────────────────────────│                            │
│                           │                            │
│  Klik kategori            │                            │
│──────────────────────────►│                            │
│                           │  GET /products/?category=  │
│                           │      <slug>                │
│                           │───────────────────────────►│
│                           │                            │  SELECT * FROM product
│                           │                            │  WHERE category__slug=X
│                           │                            │  AND is_available=True
│                           │                            │  Pagination (12/page)
│                           │                            │
│                           │◄──── product_list.html ────│
│◄──────────────────────────│                            │
│                           │                            │
│  Cari parfum              │                            │
│──────────────────────────►│                            │
│                           │  GET /products/?q=vanilla  │
│                           │───────────────────────────►│
│                           │                            │  SELECT * FROM product
│                           │                            │  WHERE name ILIKE '%vanilla%'
│                           │                            │  OR desc ILIKE '%vanilla%'
│                           │                            │  AND is_available=True
│                           │◄──── product_list.html ────│
│◄──────────────────────────│                            │
│                           │                            │
│  Kunjungi halaman         │                            │
│  filter by aroma          │                            │
│──────────────────────────►│                            │
│                           │  GET /products/note/       │
│                           │      vanilla/              │
│                           │───────────────────────────►│
│                           │                            │  SELECT * FROM product
│                           │                            │  WHERE fragrance_notes__slug='vanilla'
│                           │                            │
│                           │◄──── product_list.html ────│
│◄──────────────────────────│                            │
│                           │                            │
│  Kunjungi halaman         │                            │
│  filter by keluarga aroma │                            │
│──────────────────────────►│                            │
│                           │  GET /products/family/     │
│                           │      woody/                │
│                           │───────────────────────────►│
│                           │                            │  SELECT * FROM product
│                           │                            │  WHERE fragrance_families__slug='woody'
│                           │                            │
│                           │◄──── product_list.html ────│
│◄──────────────────────────│                            │
│                           │                            │
│  Klik produk              │                            │
│──────────────────────────►│                            │
│                           │  GET /products/<slug>/     │
│                           │───────────────────────────►│
│                           │                            │  SELECT product + category
│                           │                            │  + prefetch fragrance_notes
│                           │                            │  + prefetch fragrance_families
│                           │                            │  + prefetch variants
│                           │                            │  + prefetch reviews__user
│                           │                            │  + related products (same category)
│                           │                            │
│                           │◄── product_detail.html ────│
│◄──────────────────────────│                            │
│                           │                            │
│  Buka About Morris        │                            │
│──────────────────────────►│                            │
│                           │  GET /about-morris/        │
│                           │───────────────────────────►│
│                           │◄────── about.html ────────│
│◄──────────────────────────│                            │
│                           │                            │
│  Buka Fragrance Guide     │                            │
│──────────────────────────►│                            │
│                           │  GET /fragrance-guide/     │
│                           │───────────────────────────►│
│                           │◄── fragrance_guide.html ──│
│◄──────────────────────────│                            │
```

## 2. Alur Cart

```
User                      Browser                    Server (Django)
│                           │                            │
│  Tambah ke keranjang      │                            │
│──────────────────────────►│                            │
│                           │  POST /cart/add/<id>/      │
│                           │  (quantity=2, variant=X)   │
│                           │───────────────────────────►│
│                           │                            │  Cek user login
│                           │                            │  Cek stok cukup (variant-aware)
│                           │                            │  Jika item sudah ada: update qty
│                           │                            │  Jika belum: create baru
│                           │                            │
│                           │◄── redirect /cart/ ────────│
│◄──────────────────────────│                            │
│                           │                            │
│  Lihat keranjang          │                            │
│──────────────────────────►│                            │
│                           │  GET /cart/                │
│───────────────────────────►│                            │
│                           │                            │  SELECT cart + items
│                           │                            │  + product details
│                           │                            │  + variant info
│                           │                            │  + voucher from session (if any)
│                           │                            │
│                           │◄── cart_detail.html ───────│
│                           │    (voucher input +        │
│                           │     discount line)         │
│◄──────────────────────────│                            │
│                           │                            │
│  Update jumlah            │                            │
│──────────────────────────►│                            │
│                           │  POST /cart/update/<id>/   │
│                           │  (quantity=3)              │
│                           │───────────────────────────►│
│                           │                            │  Update qty (capped by stock)
│                           │                            │  Jika qty=0: delete item
│                           │◄── redirect /cart/ ────────│
│◄──────────────────────────│                            │
│                           │                            │
│  Hapus item               │                            │
│──────────────────────────►│                            │
│                           │  POST /cart/remove/<id>/   │
│                           │───────────────────────────►│
│                           │                            │  Delete CartItem
│                           │◄── redirect /cart/ ────────│
│◄──────────────────────────│                            │
```

## 3. Alur Checkout

```
User                      Browser                    Server (Django)
│                           │                            │
│  Checkout dari cart       │                            │
│──────────────────────────►│                            │
│                           │  GET /orders/create/       │
│                           │───────────────────────────►│
│                           │                            │  Read product_voucher_id /
│                           │                            │    shipping_voucher_id dari session
│                           │                            │  Hitung: calculate_product_discount()
│                           │                            │    + calculate_shipping_discount()
│                           │                            │  Pre-fill form dari Profile
│                           │◄── order_create.html ──────│
│                           │    (subtotal + product_diskon+
│                           │     shipping_diskon +      │
│                           │     ringkasan)             │
│◄──────────────────────────│                            │
│                           │                            │
│  Pilih alamat (district)  │                            │
│  → auto hitung ongkir     │                            │
│──────────────────────────►│                            │
│                           │  POST /shipping/api/cost/  │
│                           │  (district_id)             │
│                           │───────────────────────────►│
│                           │                            │  lookup_komerce_id()
│                           │                            │  get_cached_cost()
│                           │                            │  format_courier_services()
│                           │◄── {services: [...]} ──────│
│◄──────────────────────────│                            │
│                           │                            │
│  Pilih kurir →            │                            │
│  tampil layanan           │                            │
│──────────────────────────►│                            │
│                           │  (client-side: filter      │
│                           │   services by courier_code)│
│◄──────────────────────────│                            │
│                           │                            │
│  Pilih layanan            │                            │
│──────────────────────────►│                            │
│                           │  POST /shipping/api/select/│
│                           │  (courier, service, cost)  │
│                           │───────────────────────────►│
│                           │                            │  Store di session['shipping']
│                           │◄── {ok: true} ────────────│
│◄──────────────────────────│                            │
│                           │                            │
│  Pilih voucher            │                            │
│  (product/shipping)       │                            │
│──────────────────────────►│                            │
│                           │  GET /promotions/api/my_vouchers/?category=product
│                           │───────────────────────────►│
│                           │◄── {vouchers: [...]} ──────│
│◄──────────────────────────│                            │
│                           │                            │
│  Select voucher           │                            │
│──────────────────────────►│                            │
│                           │  POST /promotions/api/voucher/select/
│                           │  (voucher_id, category)    │
│                           │───────────────────────────►│
│                           │                            │  Validate + calculate discount
│                           │                            │  Store product_voucher_id/
│                           │                            │    shipping_voucher_id di session
│                           │◄── {discounts + voucher_id}│
│◄──────────────────────────│                            │
│                           │                            │
│  Submit form              │                            │
│──────────────────────────►│                            │
│                           │  POST /orders/create/      │
│                           │───────────────────────────►│
│                           │                            │  Validasi form + stok
│                           │                            │  Recalculate discounts
│                           │                            │  Create Order dari form
│                           │                            │  Mark UserVoucher as USED
│                           │                            │  Clear session keys
│                           │                            │  Create OrderItems (snapshot)
│                           │                            │  Hapus CartItems
│                           │                            │
│                           │◄─ redirect /payment/       │
│                           │    checkout/<order_id>/    │
│◄──────────────────────────│                            │
```

## 4. Alur Pembayaran Midtrans Snap

```
User                      Browser              Midtrans Snap           Server (Django)
│                           │                      │                       │
│  Klik "Bayar Sekarang"    │                      │                       │
│──────────────────────────►│                      │                       │
│                           │  GET /payment/checkout/<order_id>/           │
│                           │─────────────────────────────────────────────►│
│                           │                      │                       │  Cek order milik user
│                           │                      │                       │  Cek status PENDING_PAYMENT
│                           │                      │                       │  Create/get Payment
│                           │                      │                       │
│                           │                      │                       │  If no snap_token:
│                           │                      │                       │  POST /charges (Midtrans API)
│                           │                      │◄──────────────────────│
│                           │                      │──{"token","redirect"}─►│
│                           │                      │                       │
│                           │◄── checkout.html ────│                       │
│                           │  (snap_token)        │                       │
│◄──────────────────────────│                      │                       │
│                           │                      │                       │
│  Snap popup muncul        │                      │                       │
│──────────────────────────►│                      │                       │
│                           │  Snap.js modal       │                       │
│                           │─────────────────────►│                       │
│                           │                      │                       │
│  User pilih metode        │                      │                       │
│  bayar + konfirmasi       │                      │                       │
│──────────────────────────►│                      │                       │
│                           │─────────────────────►│                       │
│                           │                      │                       │
│                           │◄── onSuccess ────────│                       │
│                           │  redirect ke         │                       │
│                           │  /payment/finish/     │                       │
│──────────────────────────►│                      │                       │
│                           │  GET /payment/finish/<order_id>/             │
│                           │─────────────────────────────────────────────►│
│                           │                      │                       │  GET status transaksi
│                           │                      │◄──────────────────────│
│                           │                      │──{status:settlement}──►│
│                           │                      │                       │
│                           │◄─── success.html ────│                       │
│◄──────────────────────────│                      │                       │
```

## 5. Alur Callback Midtrans (Notification Handler)

```
Midtrans Server                          Server (Django)
│                                           │
│  POST /payment/notification/              │
│  (JSON body)                              │
│──────────────────────────────────────────►│
│                                           │  Parse JSON body
│                                           │
│                                           │  Validasi field wajib:
│                                           │  - order_id, transaction_status
│                                           │
│                                           │  Verifikasi signature HMAC:
│                                           │  SHA512(order_id + status_code
│                                           │    + gross_amount + server_key)
│                                           │
│                                           │  Parse order_id (remove "ORDER-" prefix)
│                                           │
│                                           │  Validasi gross_amount match
│                                           │
│                                           │  Update Payment record:
│                                           │  - transaction_id
│                                           │  - payment_method
│                                           │  - fraud_status
│                                           │  - raw_response (JSON)
│                                           │  - payment_time
│                                           │
│                                           │  Determine status:
│                                           │  capture + fraud accept → SUCCESS
│                                           │  settlement → SUCCESS
│                                           │  deny/cancel/expire → FAILED
│                                           │  pending → PENDING
│                                           │
│                                           │  Update Order status:
│                                           │  SUCCESS → PAID
│                                           │  FAILED → CANCELLED
│                                           │
│                                           │  If first time SUCCESS:
│                                           │    Decrement stock untuk
│                                           │    setiap OrderItem
│                                           │    Update MemberProfile:
│                                           │      total_spending += amount
│                                           │      earn_points(amount)
│                                           │      upgrade_level()
│                                           │
│  ◄───────────── HTTP 200 ─────────────────│
│                                           │
```

## 6. Alur Perubahan Status Order

```
                ┌─────────────────┐
                │ PENDING_PAYMENT │
                └───────┬─────────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
         Payment     User         Admin
         Success     Cancel       Action
              │          │          │
              ▼          ▼          │
         ┌────────┐ ┌──────────┐    │
         │  PAID  │ │CANCELLED │    │
         └───┬────┘ └──────────┘    │
             │                      │
         Admin Action               │
             │                      │
             ▼                      │
         ┌──────────┐               │
         │PROCESSING│               │
         └───┬──────┘               │
             │                      │
         Admin Action               │
             │                      │
             ▼                      │
         ┌─────────┐               │
         │ SHIPPED │               │
         └────┬────┘               │
              │                    │
         Admin Action              │
              │                    │
              ▼                    │
         ┌───────────┐             │
         │ DELIVERED │             │
         └───────────┘             │
                                   │
              ┌────────────────────┘
              ▼
         ┌──────────┐
         │CANCELLED │
         └──────────┘
```

## Ringkasan Endpoint

| Metode | URL | Deskripsi | Auth |
|---|---|---|---|
| GET | `/` | Home page | - |
| GET | `/about-morris/` | About Morris brand story | - |
| GET | `/fragrance-guide/` | Fragrance guide | - |
| GET | `/products/` | Product list (with search/filter) | - |
| GET | `/products/note/<slug>/` | Product by fragrance note | - |
| GET | `/products/<slug>/` | Product detail | - |
| POST | `/products/<slug>/review/` | Submit review | Login+Customer |
| POST | `/review/<pk>/delete/` | Delete review | Login+Owner |
| POST | `/cart/add/<id>/` | Add to cart (variant-aware) | Login+Customer |
| POST | `/cart/update/<id>/` | Update cart item | Login+Customer |
| POST | `/cart/remove/<id>/` | Remove cart item | Login+Customer |
| GET | `/cart/` | Cart detail (ringkasan produk saja) | Login+Customer |
| GET | `/orders/create/` | Checkout form (multi-section) | Login+Customer |
| POST | `/orders/create/` | Submit order | Login+Customer |
| GET | `/orders/` | Order list | Login+Customer |
| GET | `/orders/<id>/` | Order detail | Login+Customer |
| POST | `/orders/<id>/cancel/` | Cancel order | Login+Customer |
| GET | `/orders/<id>/track/` | Track order | Login+Customer |
| GET | `/payment/checkout/<id>/` | Payment checkout | Login+Customer |
| POST | `/payment/notification/` | Midtrans callback | CSRF Exempt |
| GET | `/accounts/register/` | Register | - |
| GET | `/accounts/login/` | Login | - |
| GET | `/accounts/logout/` | Logout | - |
| GET | `/accounts/dashboard/` | Customer dashboard | Login+Customer |
| GET | `/accounts/member/` | Member dashboard | Login+Customer |
| GET | `/accounts/member-benefits/` | Member benefits | - |
| GET | `/accounts/profile/` | Edit profile | Login+Customer |
| GET/POST | `/accounts/forgot-password/` | Forgot password | - |
| GET/POST | `/accounts/forgot-password/sent/` | Reset email sent | - |
| GET/POST | `/accounts/reset/<uidb64>/<token>/` | Create new password | - |
| GET | `/accounts/reset/success/` | Password reset success | - |
| GET | `/accounts/wishlist/` | Wishlist list | Login+Customer |
| POST | `/accounts/wishlist/add/<id>/` | Add to wishlist | Login+Customer |
| POST | `/accounts/wishlist/remove/<id>/` | Remove from wishlist | Login+Customer |
| GET | `/accounts/vouchers/` | User voucher list | Login+Customer |
| POST | `/shipping/api/cost/` | Get shipping costs (RajaOngkir) | Login+Customer |
| POST | `/shipping/api/select/` | Select shipping service | Login+Customer |
| POST | `/shipping/api/clear/` | Clear shipping selection | Login+Customer |
| GET | `/promotions/api/my_vouchers/?category=` | User vouchers by category | Login+Customer |
| POST | `/promotions/api/voucher/select/` | Select voucher (product/shipping) | Login+Customer |
| POST | `/promotions/api/voucher/remove/` | Remove selected voucher | Login+Customer |
| POST | `/promotions/api/calculate/totals/` | Recalculate totals | Login+Customer |
