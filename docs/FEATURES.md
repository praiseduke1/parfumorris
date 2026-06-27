# FEATURES.md

> Status fitur aplikasi Parfum Morris.

## Fitur yang Sudah Selesai (✅)

### Backend
- [x] Django project setup dengan struktur apps terpisah (7 apps: core, accounts, products, carts, orders, payments, promotions)
- [x] Model Category, FragranceFamily, Product, FragranceNote, ProductVariant, Brand, ProductImage, Review dengan relasi lengkap
- [x] Product Morris fields: `gender_target`, `occasion`, `sillage`, `longevity`, `season` (TextChoices, additive migration)
- [x] Model Cart, CartItem dengan unique_together constraint (termasuk variant)
- [x] Model Order, OrderItem dengan snapshot data produk + variant_name
- [x] Model Voucher (orders) — global promo codes (diskon persen/nominal, min purchase, usage limit, periode)
- [x] Model Voucher, UserVoucher (promotions) — per-user voucher assignment
- [x] Model Payment dengan integrasi Midtrans Snap
- [x] Model CustomerAddress (multi-address per user), Wishlist
- [x] Model MemberProfile, PointTransaction (loyalty level/poin)
- [x] Model OrderStatusHistory, PaymentStatusHistory (audit trail append-only)
- [x] Django Admin untuk semua model (custom display, bulk actions, filter horizontal, read-only history)
- [x] Migrations untuk semua perubahan database (termasuk 0007_add_product_morris_fields)
- [x] Loyalty program: MemberProfile (level Silver/Gold/Platinum), PointTransaction, poin multiplier per level
- [x] Auto-update level & poin saat pembayaran sukses (via payment callback)
- [x] Seed data: 12 produk Morris, fragrance notes, variants, 4 voucher promo

### Frontend
- [x] Home page dengan hero Morris branding, categories, featured products, new arrivals, stats, CTA
- [x] Product list dengan search, filter category, pagination, luxury warm theme (sidebar note/family filter dihapus, akses via `/products/note/<slug>/` dan `/products/family/<slug>/`)
- [x] Product detail dengan fragrance notes grouping (Top/Middle/Base), fragrance families, Morris fields grid
- [x] Size picker varian produk (30ml/50ml/100ml) di halaman detail
- [x] Product card dengan gender/occasion badges, note badges, amber-600 CTA (white card, luxury warm palette)
- [x] Link aroma ke halaman filter by note
- [x] Halaman khusus filter by aroma (`/products/note/<slug>/`) dan keluarga aroma (`/products/family/<slug>/`)
- [x] Responsive design dengan Tailwind CSS
- [x] Premium UI dengan font Playfair Display + Inter, luxury warm palette (cream bg, dark brown, amber accents)
- [x] Mobile navigation
- [x] About Morris page (`/about-morris/`) — brand story
- [x] Fragrance Guide page (`/fragrance-guide/`) — fragrance families, notes pyramid, choosing guide
- [x] WCAG AA color contrast compliance di semua template (verified audit)

### Authentication
- [x] User registration dengan validasi email unik
- [x] User login dengan redirect (next parameter)
- [x] User logout
- [x] Forgot Password (input email → kirim tautan reset)
- [x] Password Reset via Email (tautan aman dengan token Django)
- [x] Password Reset Confirm (buat password baru dengan validasi)
- [x] Password Reset Complete (konfirmasi sukses + redirect login)
- [x] Auto-create profile via signal
- [x] Dashboard customer (statistik pesanan, riwayat)
- [x] Profile update (username, email, phone, address)
- [x] Member dashboard (`/accounts/member/`) with member benefits page

### Cart
- [x] Add to cart dengan validasi stok (variant-aware)
- [x] Update quantity (increase, decrease, set)
- [x] Remove item dari cart
- [x] Cart summary di navbar
- [x] Voucher code input di cart dihapus — pindah ke checkout modal

### Orders
- [x] Checkout form dengan pre-fill dari profile + discount breakdown
- [x] Checkout section reorder: Alamat → Penerima → Kurir → Layanan → Voucher Ongkir → Daftar Produk → Voucher Produk → Catatan → Ringkasan → Bayar
- [x] Order creation dengan snapshot produk + variant
- [x] Order list per user
- [x] Order detail
- [x] Cancel order (hanya status PENDING_PAYMENT)
- [x] Status management (PENDING_PAYMENT → PAID → PROCESSING → SHIPPED → DELIVERED)
- [x] Order tracking page dengan timeline visual
- [x] Voucher integration: product & shipping voucher terpisah, modal selection, realtime recalculation

### Payment
- [x] Integrasi Midtrans Snap API dengan 15s timeout
- [x] Generate Snap token (termasuk SHIPPING item agar gross_amount match)
- [x] Snap.js popup payment
- [x] Payment success/pending/error pages
- [x] Notification callback handler (CSRF Exempt)
- [x] HMAC signature verification
- [x] Auto-update Order status dari callback
- [x] Decrement stock on successful payment
- [x] Anti double-decrement (check was_paid_before)
- [x] Auto-update MemberProfile (spending, poin, level) on payment success

### Testing
- [x] 85+ pytest tests (models, forms, views)
- [x] pytest-django configuration
- [x] All tests pass

### Security
- [x] Environment variables via .env
- [x] CSRF protection
- [x] Login required decorators
- [x] Midtrans signature verification
- [x] Production security settings (HSTS, SSL, secure cookies)
- [x] Role separation (Admin/Superuser vs Customer)
- [x] `@customer_required` decorator & `CustomerRequiredMixin`
- [x] Frontend protection (hidden cart/checkout for admin)
- [x] Server-side validation di semua view customer

### Promotions
- [x] Voucher model (promotions) — kode, tipe diskon, min purchase, expiry, category (PRODUCT / SHIPPING)
- [x] UserVoucher — per-user assignment with individual expiry
- [x] WELCOME10 auto-assignment (10%, min Rp 200k, 30 days validity)
- [x] Customer voucher list at `/accounts/vouchers/`
- [x] Checkout integration: modal per-category, API select/remove, realtime recalculation
- [x] Separate discount functions: `calculate_product_discount()`, `calculate_shipping_discount()`, `calculate_total()`
- [x] Session keys terpisah: `product_voucher_id`, `shipping_voucher_id`

---

## Fitur yang Direncanakan (📋)

### Customer Experience
- [ ] Similar perfume recommendation based on fragrance notes
- [ ] Perfume comparison tool
- [ ] Scent quiz / fragrance finder (rekomendasi berdasarkan preferensi)
- [ ] Product reviews dengan foto
- [ ] Recently viewed products
- [ ] Stock notification (notifikasi saat produk tersedia kembali)

### Order & Shipping
- [x] Shipping cost calculation (RajaOngkir Komerce API, fallback dummy di dev mode)
- [x] 2-step courier selection: Pilih Kurir → Pilih Layanan
- [ ] Invoice PDF generation
- [ ] Order cancellation request (dengan alasan)
- [ ] Export orders ke CSV/Excel

### Payment
- [ ] Midtrans subscription for recurring payment
- [ ] Payment retry (untuk expired/failed payment)
- [ ] Payment method preference
- [ ] Refund handling

### Promo & Discount
- [x] Discount codes / voucher system (global + per-user)
- [x] Loyalty points / reward system (poin, level Silver/Gold/Platinum, otomatis dari pembayaran)
- [ ] Flash sale management
- [ ] Buy one get one (BOGO)
- [ ] Free shipping threshold

### Admin
- [x] Inventory management dashboard
- [x] Sales analytics (total revenue, order stats, payment stats)
- [ ] Customer management
- [ ] Stock alert (notifikasi saat stok menipis)
- [ ] Bulk import/export produk (CSV/Excel)
- [ ] Order status automation

### Performance & Optimization
- [x] Database query optimization (indexing)
- [x] Redis caching untuk product list (falls back to locmem)
- [x] Image optimization (WebP filter, lazy loading)
- [ ] CDN untuk static files
- [ ] Database migration ke PostgreSQL
- [ ] Search indexing (Elasticsearch/SearchVector)

### Infrastructure & Deployment
- [ ] Docker containerization
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Production deployment (VPS, Railway, or similar)
- [ ] SSL certificate (Let's Encrypt)
- [ ] Monitoring (Sentry, error tracking)
- [ ] Automated backup database

### Fitur Tambahan
- [x] Multi-language support (i18n framework, ID/EN)
- [ ] Scent intensity / longevity info (done)
- [ ] Gift wrapping option
- [ ] WhatsApp notification integration
- [ ] SEO optimization (meta tags, sitemap, canonical, JSON-LD)
- [x] Favicon (production-ready)
