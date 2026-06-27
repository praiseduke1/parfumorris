# PROJECT_CONTEXT.md

> Single source of truth for project overview, goals, tech stack, and architecture principles.

## Ringkasan Proyek

**Parfum Morris** adalah aplikasi E-Commerce parfum premium berbasis web yang dibangun dengan Django. Aplikasi ini memungkinkan customer untuk menjelajahi katalog parfum, melihat detail aroma (fragrance notes), melakukan pembelian melalui keranjang belanja, dan menyelesaikan pembayaran menggunakan Midtrans Snap API.

## Tujuan Aplikasi

- Menyediakan platform belanja parfum online dengan pengalaman premium.
- Memberikan informasi lengkap tentang komposisi aroma setiap parfum (Top, Middle, Base Notes).
- Memudahkan customer menemukan parfum berdasarkan aroma favorit atau keluarga aroma.
- Menyediakan sistem pembayaran yang aman dan terintegrasi dengan Midtrans.
- Memberikan dashboard customer untuk memantau pesanan.
- Memberikan program loyalitas (poin, level Silver/Gold/Platinum) untuk meningkatkan retensi pelanggan.

## Teknologi yang Digunakan

| Teknologi | Versi | Keterangan |
|---|---|---|
| Python | 3.14 | Runtime |
| Django | 6.0.5 | Web framework |
| SQLite | - | Database development |
| Tailwind CSS | CDN (v3) | Frontend styling |
| Midtrans Snap | API v2 | Payment gateway |
| django-cleanup | 8.0+ | Auto cleanup file gambar |
| Whitenoise | 6.6+ | Static file serving production |
| Pillow | 10.0+ | Image processing |
| pytest | 9.1.0 | Testing framework |
| pytest-django | 4.12.0 | Django test integration |

## Struktur Django Apps

```
parfumoray/
├── parfumoray/          # Project configuration (settings, urls, wsgi, asgi)
├── apps/
│   ├── core/            # Shared utilities, context processors, template tags
│   ├── accounts/        # User authentication, profile management
│   ├── products/        # Product catalog, categories, fragrance notes, reviews
│   ├── carts/           # Shopping cart management
│   ├── orders/          # Order processing, vouchers, status management
│   ├── payments/        # Midtrans Snap payment integration
│   └── promotions/      # Customer voucher promotions (per-user assignment)
├── templates/           # Global templates (base, includes)
├── static/              # Static files (css, js)
├── media/               # Uploaded images (products)
└── docs/                # Project documentation
```

### core
- Tidak memiliki models.
- Menyediakan: `format_rupiah()`, `status_badge_html()` di admin_utils.
- Template tags: `rupiah` filter, `query_transform`.
- Context processors: `cart_count` (jumlah item di navbar), `wishlist_ids` (set of product IDs in wishlist).

### accounts
- Model: `Profile` (OneToOne ke User), `MemberProfile` (loyalty level/poin), `PointTransaction` (riwayat poin), `CustomerAddress` (multi-address per user), `Wishlist`.
- Fitur: register, login, logout, profile update, forgot password, reset password via email, multi-address, wishlist, loyalty program (poin & level Silver/Gold/Platinum), member dashboard, member benefits page.
- Signal: auto-create profile saat user baru dibuat.
- Endpoints auth: `/accounts/login/`, `/accounts/register/`, `/accounts/forgot-password/`, `/accounts/reset/<uidb64>/<token>/`, `/accounts/reset/success/`, `/accounts/member/`, `/accounts/member-benefits/`.
- Email: file-based (development) / SMTP (production) via environment variables.

### products
- Models: `Category`, `FragranceFamily`, `Brand`, `FragranceNote`, `Product`, `ProductVariant`, `ProductImage`, `Review`.
- Fitur: katalog produk, search, filter kategori, filter brand, filter aroma, filter keluarga aroma, pagination, varian ukuran, galeri gambar, review/rating, About Morris page, Fragrance Guide page.
- Relasi: Product ManyToMany ke FragranceNote dan FragranceFamily, FK ke Brand dan Category.
- New Morris fields: `gender_target`, `occasion`, `sillage`, `longevity`, `season` (additive with defaults).

### carts
- Models: `Cart`, `CartItem` (dengan variant FK nullable).
- Fitur: tambah/ubah/hapus item keranjang, validasi stok (variant-aware), unique_together [cart, product, variant].

### orders
- Models: `Order`, `OrderItem` (snapshot varian_name), `OrderStatusHistory` (audit trail dengan field `status`), `Voucher`.
- Fitur: create order dari cart, cancel order (hanya `PENDING_PAYMENT`), history pesanan, tracking pesanan (timeline visual), status audit trail (auto via save()), voucher diskon (product + shipping terpisah via session), checkout dengan 2-step courier→service.
- Flow checkout: Alamat → Penerima → Kurir → Layanan → Voucher Ongkir → Daftar Produk → Voucher Produk → Catatan → Ringkasan → Bayar.
- Status: `PENDING_PAYMENT` → `PAID` → `PROCESSING` → `SHIPPED` → `DELIVERED`.

### payments
- Models: `Payment`, `PaymentStatusHistory` (audit trail).
- Fitur: integrasi Midtrans Snap, callback notification, update status otomatis, status audit trail (auto via save()).
- Keamanan: verifikasi signature HMAC Midtrans.

### promotions
- Models: `Voucher` (template promo dengan category PRODUCT/SHIPPING), `UserVoucher` (per-user assignment with individual expiry).
- Fitur: auto-assign welcome voucher saat registrasi (`services.assign_welcome_voucher()`), daftar voucher customer (`/accounts/vouchers/`), pilih voucher per-kategori di checkout via modal.
- Session keys terpisah: `product_voucher_id`, `shipping_voucher_id` (bukan combined dict).
- Fungsi diskon: `calculate_product_discount()`, `calculate_shipping_discount()`, `calculate_subtotal()`, `calculate_shipping_cost()`, `calculate_total()`.

## Prinsip Pengembangan

1. **Separation of Concerns** — Setiap Django app memiliki tanggung jawab spesifik.
2. **Database Normalization (3NF)** — Brand sebagai entity terpisah, relasi ManyToMany untuk fragrance notes, hindari duplikasi data.
3. **Audit Trail** — Setiap perubahan status Order dan Payment tercatat di tabel history (append-only).
4. **Query Optimization** — Gunakan `select_related` dan `prefetch_related` untuk menghindari N+1.
5. **Security First** — Validasi signature Midtrans, CSRF protection, login required untuk protected views, role separation.
6. **Mobile Responsive** — Semua tampilan menggunakan Tailwind CSS dengan pendekatan mobile-first.

## Arah Desain UI

- **Premium** — Menggunakan font Playfair Display (serif) untuk heading, Inter untuk body.
- **Modern** — Tailwind CSS dengan shadow halus, rounded corners, transisi animasi.
- **Luxury Warm Palette** — Tema hangat mewah dengan warna krem sebagai latar (`#F3ECE4`), _dark brown_ untuk sidebar/navbar/footer (`#1A1411`, `#2A1F1A`), dan aksen amber yang hangat (`amber-400/500/600`) menggantikan emas.
- **Responsive** — Grid fleksibel, mobile menu, touch-friendly.

### Color Palette (Utama)

```css
/* Global body background (warm cream) */
body { background: #F3ECE4; }

/* Dark surfaces: navbar, footer */
dark-1: '#1A1411'

/* Sidebar panels */
dark-2: '#2A1F1A'

/* Accent colors (replaces gold) */
amber: {
  400: '#fbbf24',  /* hover states on dark */
  500: '#f59e0b',  /* brand accent */
  600: '#d97706',  /* buttons, active states */
}

/* Card backgrounds */
card: '#ffffff'  /* solid white with subtle shadow */
```

### Legacy Morris & Gold Palettes
Palet `morris` (50–950) dan `gold` (400/500/600) masih didefinisikan di `tailwind.config` untuk kompatibilitas dengan halaman lain (detail produk, fragrance guide, about, admin). Halaman koleksi (`product_list`) menggunakan palet baru di atas.
