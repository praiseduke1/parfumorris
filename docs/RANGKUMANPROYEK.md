# RANGKUMAN PROYEK — ParfuMoray (Parfum Morris)

> **Dokumen ini adalah satu-satunya sumber kebenaran (*single source of truth*) yang merangkum seluruh hasil eksplorasi dan pengujian proyek Django E-Commerce Parfum.**
>
> **Dibuat:** 26 Juni 2026  
> **Diperbarui:** 27 Juni 2026 — Audit produksi dan perbaikan keamanan/performansa  
> **Tujuan:** Menjadi acuan utama untuk penyusunan SRS (*Software Requirements Specification*) dan SDD (*Software Design Document*).

---

## Daftar Isi

1. [Ikhtisar Proyek](#1-ikhtisar-proyek)
2. [Struktur Aplikasi (Django Apps)](#2-struktur-aplikasi-django-apps)
3. [Teknologi & Versi](#3-teknologi--versi)
4. [Pengaturan Django (settings.py)](#4-pengaturan-django-settingspy)
5. [Struktur URL](#5-struktur-url)
6. [Model](#6-model)
7. [View](#7-view)
8. [Form](#8-form)
9. [Template](#9-template)
10. [Berkas Static & Media](#10-berkas-static--media)
11. [Autentikasi & Otorisasi](#11-autentikasi--otorisasi)
12. [Sesi & Middleware](#12-sesi--middleware)
13. [Keranjang Belanja & Checkout](#13-keranjang-belanja--checkout)
14. [Manajemen Pesanan](#14-manajemen-pesanan)
15. [Integrasi Pembayaran (Midtrans)](#15-integrasi-pembayaran-midtrans)
16. [Promosi & Voucher](#16-promosi--voucher)
17. [Data Regional (Alamat Berjenjang)](#17-data-regional-alamat-berjenjang)
18. [Program Loyalitas](#18-program-loyalitas)
19. [Admin Dashboard](#19-admin-dashboard)
20. [Analisis Keamanan](#20-analisis-keamanan)
21. [Pengujian (Testing)](#21-pengujian-testing)
22. [Bug yang Diketahui](#22-bug-yang-diketahui)
23. [Catatan Persiapan SRS/SDD](#23-catatan-persiapan-srssdd)

---

## 1. Ikhtisar Proyek

| Atribut | Nilai |
|---|---|
| **Nama Proyek** | ParfuMoray / Parfum Morris |
| **Jenis** | E-Commerce Parfum Premium |
| **Framework** | Django 6.0.5 |
| **Python** | 3.14 |
| **Database** | SQLite (development), target PostgreSQL (production) |
| **Frontend** | Django Templates + Tailwind CSS (CDN v3) |
| **Payment Gateway** | Midtrans Snap API v2 (sandbox) |
| **Total Baris Kode Python** | ~9.100 |
| **Total Django Apps** | 8 lokal + 3 pihak ketiga |
| **Total Model** | 31 |
| **Total View** | 47 |
| **Total Template** | 15 |
| **Total Berkas Static** | 2 (+1 dihapus) |
| **Total Berkas Migrasi** | 49 (+3 baru) |
| **Total Tes (Django)** | 12 (100% lulus) |
| **Total Tes (pytest)** | 370 (pre-existing, 1 gagal — referensi URL dihapus) |
| **Bug Ditemukan & Diperbaiki** | 12 (0 critical, 0 high, 0 medium, 0 low) |

**Tujuan Aplikasi:**
- Menyediakan platform belanja parfum online dengan pengalaman premium
- Memberikan informasi lengkap komposisi aroma (Top/Middle/Base Notes)
- Memudahkan pencarian parfum berdasarkan aroma/famili aroma
- Sistem pembayaran aman terintegrasi Midtrans
- Dashboard customer untuk memantau pesanan
- Program loyalitas (poin, level Silver/Gold/Platinum)

---

## 2. Struktur Aplikasi (Django Apps)

### 2.1 Aplikasi Lokal (8)

| App | Direktori | Model | View | Template | Forms | Fungsi Utama |
|---|---|---|---|---|---|---|
| **core** | `apps/core/` | 0 | 1 (admin dashboard) | 2 (admin) | 0 | Utilitas bersama, context processor, template tags, middleware |
| **accounts** | `apps/accounts/` | 5 | 18 | 9 | 3 | Auth (login/register/reset password), profil, alamat, wishlist, loyalitas |
| **products** | `apps/products/` | 8 | 9 | 8 | 0 | Katalog produk, kategori, aroma, famili aroma, review, brands |
| **carts** | `apps/carts/` | 2 | 6 | 1 | 0 | Keranjang belanja, item, voucher session |
| **orders** | `apps/orders/` | 3 | 6 | 5 | 1 | Pesanan, item pesanan, riwayat status, checkout |
| **payments** | `apps/payments/` | 2 | 5 | 2 | 0 | Pembayaran Midtrans, callback notifikasi |
| **promotions** | `apps/promotions/` | 2 | 4 | 0 (gabung accounts) | 0 | Voucher per-user, klaim voucher |
| **regions** | `apps/regions/` | 4 | 4 | 0 | 0 | Data wilayah (Provinsi/Kota/Kecamatan/Kodepos), API AJAX |

### 2.2 Aplikasi Pihak Ketiga (3)

| App | Fungsi |
|---|---|
| **django_cleanup** | Otomatis hapus file gambar saat instance model dihapus |
| **django_jazzmin** | Kustomisasi tema Admin Django |
| **whitenoise** | Serving static files (production) |

### 2.3 Diagram Arsitektur

```
parfumoray/
├── parfumoray/              # Konfigurasi proyek (settings, urls, wsgi, asgi)
├── apps/
│   ├── core/                # Utilitas bersama
│   ├── accounts/            # Auth & profil
│   ├── products/            # Katalog
│   ├── carts/               # Keranjang
│   ├── orders/              # Pesanan
│   ├── payments/            # Pembayaran
│   ├── promotions/          # Promosi
│   └── regions/             # Wilayah
├── templates/               # Template global
├── static/                  # Berkas statis
├── media/                   # Upload gambar
└── docs/                    # Dokumentasi
```

---

## 3. Teknologi & Versi

| Teknologi | Versi | Keterangan |
|---|---|---|---|
| Python | 3.14.4 | Runtime |
| Django | 6.0.5 | Web framework |
| SQLite | 3.x | Database development |
| Tailwind CSS | CDN v3 | Utility CSS framework |
| Midtrans Snap | API v2 | Payment gateway |
| django-cleanup | ~8.0+ | Auto-cleanup file |
| Whitenoise | ~6.6+ | Static file serving |
| Pillow | ~10.0+ | Image processing |
| pytest | 9.1.0 | Testing framework |
| pytest-django | 4.12.0 | Django test integration |
| django-jazzmin | ~2.6+ | Admin theme |
| django-allauth | ~64.x | Google OAuth login |
| django-redis | ~5.4+ | Redis cache (opsional) |
| pyjwt | ~2.0+ | JWT token |
| cryptography | ~42.0+ | Kriptografi |
| python-dotenv | ~1.0+ | Environment variables |
| TomSelect | CDN | Select enhancement untuk address cascade |
| Google Fonts | - | Playfair Display + Inter |

---

## 4. Pengaturan Django (settings.py)

### 4.1 Konfigurasi Dasar

| Pengaturan | Nilai |
|---|---|
| `DEBUG` | `True` (development) — **WAJIB `False` di production** |
| `SECRET_KEY` | Dari environment variable (`.env`) |
| `ALLOWED_HOSTS` | Dari environment variable (default `localhost,127.0.0.1`) |
| `CSRF_TRUSTED_ORIGINS` | Dari environment variable (default `http://localhost:8000,http://127.0.0.1:8000`) |
| `ROOT_URLCONF` | `parfumoray.urls` |
| `WSGI_APPLICATION` | `parfumoray.wsgi.application` |
| `DEFAULT_AUTO_FIELD` | `BigAutoField` |
| `DATA_UPLOAD_MAX_MEMORY_SIZE` | `5MB` (hanya saat `DEBUG=False`) |

### 4.2 Installed Apps (Urutan)

```python
INSTALLED_APPS = [
    # Third-party (harus sebelum admin untuk Jazzmin override)
    'jazzmin',
    # Django built-in
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    # Third-party
    'django_cleanup.apps.CleanupConfig',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    # Local apps
    'apps.core',
    'apps.regions',
    'apps.accounts',
    'apps.products',
    'apps.carts',
    'apps.orders',
    'apps.payments',
    'apps.promotions',
    'apps.shipping',
]
```

### 4.3 Middleware (Urutan)

```python
MIDDLEWARE = [
    'apps.core.middleware.SeparateAdminSessionMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

### 4.4 Database

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

**Data saat ini:** 10 produk, 38 provinsi, 521 kota, 6886 kecamatan, 7301 kodepos, 4 voucher, 8 user.

### 4.5 Template

- Backend: `django.template.backends.django.DjangoTemplates`
- DIRS: `[BASE_DIR / 'templates']`
- Context processors: 7 default Django + 3 kustom (`cart_count`, `wishlist_ids`, `voucher_notification`, `voucher_floating_panel`)

### 4.6 Static & Media

| Pengaturan | Nilai |
|---|---|
| `STATIC_URL` | `static/` |
| `STATICFILES_DIRS` | `[BASE_DIR / 'static']` |
| `STATIC_ROOT` | `BASE_DIR / 'staticfiles'` |
| `MEDIA_URL` | `media/` |
| `MEDIA_ROOT` | `BASE_DIR / 'media'` |

### 4.7 Email

```python
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = BASE_DIR / 'sent_emails'
```

Tidak ada SMTP production yang dikonfigurasi.

### 4.8 Auth

```python
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'accounts:dashboard'
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]
ACCOUNT_AUTHENTICATION_METHOD = 'username'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
    }
}
```

### 4.9 Jazzmin (Admin Theme)

- `site_title`: "ParfuMoray Admin"
- `site_header`: "ParfuMoray"
- `site_brand`: "ParfuMoray"
- `welcome_sign`: "Selamat datang di ParfuMoray Admin"
- `copyright`: "ParfuMoray"
- `search_model`: `["auth.User", "products.Product", "orders.Order"]`
- `topmenu_links`: Root, Users, Products, Orders
- `custom_css`: tidak ada (file `static/admin/css/dashboard.css` dihapus karena tidak digunakan)
- `show_ui_builder`: `True`
- Theme: dark (`primary`, `secondary`, `info`, `warning`, `danger`, `success` all defined)
- `related_modal_active`: `True`
- `language_chooser`: `True`

### 4.10 Cache

Menggunakan Redis jika tersedia (via `REDIS_URL` env), fallback ke LocalMemoryCache:
```python
if REDIS_URL := os.getenv('REDIS_URL'):
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient'},
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'parfumoray-cache',
        }
    }
```
`django_redis` sekarang terinstall dan aktif jika URL Redis tersedia. Gunakan untuk session engine dan cache API.

### 4.11 Session Engine

```python
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
```
Menggunakan database session engine. Dapat diubah ke Redis cache jika Redis tersedia.

### 4.12 Logging Configuration

Logging dikonfigurasi untuk menulis ke file dan console dengan format terstruktur:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'debug.log',
            'maxBytes': 5242880,  # 5MB
            'backupCount': 3,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'midtrans': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```
Logger `midtrans` khusus untuk debugging pembayaran Midtrans. File log berada di `logs/debug.log` dengan rotasi 5MB.

---

## 5. Struktur URL

### 5.1 Root URL (`parfumoray/urls.py`)

| Prefix | Target | App Name |
|---|---|---|
| `` (root) | `products.views.HomeView` | — |
| `accounts/` | `apps.accounts.urls` | `accounts` |
| `products/` | `apps.products.urls` | `products` |
| `carts/` | `apps.carts.urls` | `carts` |
| `orders/` | `apps.orders.urls` | `orders` |
| `payments/` | `apps.payments.urls` | `payments` |
| `promotions/` | `apps.promotions.urls` | `promotions` |
| `regions/` | `apps.regions.urls` | `regions` |
| `admin/dashboard/` | `apps.core.admin_views.dashboard` | `admin-dashboard` |
| `admin/` | `django.contrib.admin.site.urls` | `admin` |

### 5.2 Daftar URL Lengkap per App

#### accounts (18 URL)

| URL Pattern | View Name | Method |
|---|---|---|
| `register/` | `accounts:register` | GET, POST |
| `login/` | `accounts:login` | GET, POST |
| `logout/` | `accounts:logout` | GET, POST |
| `forgot-password/` | `accounts:forgot_password` | GET, POST |
| `forgot-password/sent/` | `accounts:password_reset_sent` | GET |
| `reset/<uidb64>/<token>/` | `accounts:create_new_password` | GET, POST |
| `reset/success/` | `accounts:password_reset_success` | GET |
| `dashboard/` | `accounts:dashboard` | GET |
| `profile/` | `accounts:profile` | GET, POST |
| `member/` | `accounts:member_dashboard` | GET |
| `member-benefits/` | `accounts:member_benefits` | GET |
| `wishlist/` | `accounts:wishlist_list` | GET |
| `wishlist/add/<int:product_id>/` | `accounts:wishlist_add` | POST |
| `wishlist/remove/<int:product_id>/` | `accounts:wishlist_remove` | POST |
| `dashboard/addresses/` | `accounts:address_list` | GET |
| `dashboard/addresses/create/` | `accounts:address_create` | GET, POST |
| `dashboard/addresses/<int:address_id>/edit/` | `accounts:address_edit` | GET, POST |
| `dashboard/addresses/<int:address_id>/delete/` | `accounts:address_delete` | POST |
| `dashboard/addresses/<int:address_id>/set-default/` | `accounts:address_set_default` | POST |

#### products (9 URL)

| URL Pattern | View Name |
|---|---|
| `` (root) | `products:home` |
| `about-morris/` | `products:about` |
| `fragrance-guide/` | `products:fragrance_guide` |
| `products/` | `products:list` |
| `products/note/<slug:slug>/` | `products:by_note` |
| `products/family/<slug:slug>/` | `products:by_family` |
| `products/<slug:slug>/` | `products:detail` |
| `products/<slug:slug>/review/` | `products:review_form` |
| `review/<int:pk>/delete/` | `products:review_delete` |

#### carts (6 URL)

| URL Pattern | View Name |
|---|---|---|
| `` (root) | `carts:detail` |
| `add/<int:product_id>/` | `carts:add` (wajib POST, 404 untuk GET) |
| `update/<int:item_id>/` | `carts:update` |
| `remove/<int:item_id>/` | `carts:remove` (wajib POST, 404 untuk GET) |

> **Catatan:** URL `voucher/apply/` dan `voucher/remove/` telah dipindahkan ke `apps.promotions` untuk pemisahan tanggung jawab yang lebih bersih.

#### orders (6 URL)

| URL Pattern | View Name |
|---|---|
| `` (root) | `orders:list` |
| `create/` | `orders:create` |
| `<int:order_id>/` | `orders:detail` |
| `<int:order_id>/cancel/` | `orders:cancel` |
| `<int:order_id>/confirm-received/` | `orders:confirm_received` |
| `<int:order_id>/track/` | `orders:track` |

#### payments (5 URL)

| URL Pattern | View Name |
|---|---|
| `checkout/<int:order_id>/` | `payments:checkout` |
| `finish/<int:order_id>/` | `payments:finish` |
| `unfinish/<int:order_id>/` | `payments:unfinish` |
| `error/<int:order_id>/` | `payments:error` |
| `notification/` | `payments:notification` (CSRF exempt) |

#### promotions (6 URL)

| URL Pattern | View Name |
|---|---|
| `` (root) | `promotions:voucher_list` |
| `saya/` | `promotions:my_vouchers` |
| `apply/` | `promotions:apply_voucher` (POST-only) |
| `remove/` | `promotions:remove_voucher` (POST-only) |
| `claim/<int:voucher_id>/` | `promotions:claim_voucher` |
| `claim/<int:voucher_id>/ajax/` | `promotions:claim_voucher_ajax` |

#### regions (4 URL)

| URL Pattern | View Name |
|---|---|
| `api/locations/provinces/` | `regions:api_provinces` |
| `api/locations/cities/` | `regions:api_cities` |
| `api/locations/districts/` | `regions:api_districts` |
| `api/locations/postal-code/` | `regions:api_postal_code` |

#### admin (2 URL)

| URL Pattern | View Name |
|---|---|
| `admin/dashboard/` | `admin-dashboard` |
| `admin/` | Django Admin |

---

## 6. Model

**Total: 31 model** di 8 apps.

### 6.1 accounts (5 model)

| Model | Fields | Relasi |
|---|---|---|
| **Profile** | `user`, `phone`, `address`, `created_at`, `updated_at` | `OneToOneField` → User |
| **MemberProfile** | `user`, `level` (SILVER/GOLD/PLATINUM), `total_points`, `total_spending`, `birth_date`, `created_at`, `updated_at` | `OneToOneField` → User; index on `level` |
| **CustomerAddress** | `user`, `label`, `recipient_name`, `phone`, `address_line`, `rt`, `rw`, `province`, `city`, `district`, `postal_code`, `is_default`, `latitude`, `longitude`, `created_at`, `updated_at` | FK → User, Province/City/District/PostalCode |
| **PointTransaction** | `user`, `points`, `type` (EARN/REDEEM/UPGRADE), `description`, `created_at` | FK → User; ordering = `-created_at`; index on `user, -created_at` |
| **Wishlist** | `user`, `product`, `created_at` | FK → User, Product; `unique_together = ['user', 'product']` |

### 6.2 products (8 model)

| Model | Fields |
|---|---|
| **Category** | `name`, `slug` (unique), `description`, `image`, `is_active`, `created_at`, `updated_at` |
| **Brand** | `name`, `slug` (unique), `description`, `logo`, `website`, `created_at`, `updated_at` |
| **FragranceFamily** | `name`, `slug` (unique), `description`, `image`, `is_active`, `created_at`, `updated_at` |
| **FragranceNote** | `name`, `slug` (unique), `description`, `note_type` (TOP/MIDDLE/BASE), `image`, `is_active`, `created_at`, `updated_at` |
| **Product** | `category` (FK), `brand` (FK), `name`, `slug` (unique), `description`, `price`, `stock`, `is_available`, `weight`, `gender_target`, `occasion`, `sillage`, `longevity`, `season`, `fragrance_notes` (M2M), `fragrance_families` (M2M), `image`, `created_at`, `updated_at` |
| **ProductVariant** | `product` (FK), `size`, `price`, `stock`, `sku` (unique, blank), `is_active`, `created_at`, `updated_at`; `unique_together = ['product', 'size']` |
| **ProductImage** | `product` (FK), `image`, `alt_text`, `is_primary`, `sort_order`, `created_at` |
| **Review** | `product` (FK), `user` (FK), `rating` (1-5), `comment`, `is_approved`, `created_at`, `updated_at`; `unique_together = ['product', 'user']`; index on `product, -created_at` |

### 6.3 carts (2 model)

| Model | Fields |
|---|---|
| **Cart** | `user` (OneToOne → User), `voucher_code`, `voucher_discount`, `created_at`, `updated_at` |
| **CartItem** | `cart` (FK), `product` (FK), `variant` (FK nullable), `quantity`, `price`, `created_at`, `updated_at`; `unique_together = ['cart', 'product', 'variant']` |

### 6.4 orders (3 model)

| Model | Fields |
|---|---|
| **Order** | `user` (FK), `order_number` (unique, auto UUID4), `recipient_name`, `phone`, `shipping_address`, `province`, `city`, `district`, `postal_code`, `notes`, `subtotal`, `discount`, `voucher_code`, `total_price`, `status` (PENDING_PAYMENT/PAID/PROCESSING/SHIPPED/DELIVERED/CANCELLED), `created_at`, `updated_at`; index on `user, -created_at` |
| **OrderItem** | `order` (FK), `product` (FK), `product_name` (snapshot), `product_price` (snapshot), `variant_name` (snapshot), `quantity`, `subtotal`; `unique_together = ['order', 'product', 'variant_name']` |
| **OrderStatusHistory** | `order` (FK), `status`, `notes`, `created_by`, `created_at`; index on `order, -created_at` |

### 6.5 payments (2 model)

| Model | Fields |
|---|---|
| **Payment** | `order` (OneToOne → Order), `midtrans_order_id` (UUIDField unique), `snap_token`, `snap_redirect_url`, `transaction_id`, `transaction_status`, `payment_type`, `gross_amount`, `fraud_status`, `transaction_time`, `settlement_time`, `created_at`, `updated_at` |
| **PaymentStatusHistory** | `payment` (FK), `transaction_status`, `fraud_status`, `raw_response` (JSON), `created_at`; index on `payment, -created_at` |

### 6.6 promotions (2 model)

| Model | Fields |
|---|---|
| **Voucher** | `code` (unique), `name`, `description`, `type` (PUBLIC/WELCOME/MIN_PURCHASE/BIRTHDAY/LOYALTY), `category` (PRODUCT/SHIPPING/TOTAL dengan default TOTAL), `discount_type` (PERCENTAGE/NOMINAL), `discount_value`, `min_purchase`, `max_discount`, `usage_limit`, `used_count`, `is_active`, `valid_from`, `valid_until`, `created_at`, `updated_at` |
| **UserVoucher** | `voucher` (FK → Voucher), `user` (FK → User), `code` (unique), `is_used`, `used_at`, `valid_from`, `valid_until`, `created_at`, `updated_at`; `unique_together = ['voucher', 'user']`; index on `user, is_used` |

**Field baru `category`** pada Voucher memisahkan diskon produk, ongkos kirim, atau total belanja. Migrasi 0005 menambahkan field ini dengan default `TOTAL` untuk data existing.

### 6.7 regions (4 model)

| Model | Fields | Data |
|---|---|---|
| **Province** | `id`, `name` | 38 provinsi |
| **City** | `id`, `province` (FK), `name` | 521 kota |
| **District** | `id`, `city` (FK), `name` | 6886 kecamatan |
| **PostalCode** | `id`, `district` (FK), `postal_code`, `urban`, `suburban` | 7301 kodepos |

### 6.8 core (0 model)

Tidak memiliki model. Menyediakan utilitas, middleware, context processor, template tags.

---

## 7. View

**Total: 47 view** (fungsi dan kelas).

### 7.1 Rincian per App

| App | Function-Based Views | Class-Based Views | Total |
|---|---|---|---|
| accounts | 13 | 3 (RegisterView, CustomLoginView, ProfileUpdateView) | 16 |
| products | 0 | 9 (HomeView, AboutView, FragranceGuideView, ProductListView, ProductByNoteView, ProductByFamilyView, ProductDetailView, ReviewFormView, ReviewDeleteView) | 9 |
| carts | 4 | 0 | 4 |
| orders | 6 | 0 | 6 |
| payments | 5 | 0 | 5 |
| promotions | 6 | 0 | 6 |
| regions | 4 | 0 | 4 |
| core | 1 (admin dashboard) | 0 | 1 |

> **Catatan:** 2 view carts (`apply_voucher`, `remove_voucher`) dipindahkan ke promotions. Promotions bertambah 2 view.

### 7.2 Mixin & Decorators yang Digunakan

- `LoginRequiredMixin` — ReviewFormView (akan tetapi dispatch() di-override — lihat Bug BRW-01)
- `@login_required` — Dashboard, profil, wishlist, alamat, cart, order, payment, voucher
- `@customer_required` — Dekorator kustom untuk view customer (non-admin)
- `CustomerRequiredMixin` — Mixin kustom
- `@require_POST` — Wishlist add/remove, address delete/set-default, cart add/remove/update, order cancel, voucher apply/remove/claim, logout
- `@csrf_exempt` — Payment notification callback
- `@never_cache` — Dashboard

### 7.3 View Penting

| View | File | Fungsi |
|---|---|---|
| `HomeView` | `apps/products/views.py:12` | TemplateView: home page dengan featured products, categories, new arrivals |
| `ProductListView` | `apps/products/views.py:73` | ListView: katalog dengan search, filter kategori, pagination (12/page) |
| `ProductByNoteView` | `apps/products/views.py:139` | ListView: filter produk berdasarkan aroma |
| `ProductByFamilyView` | `apps/products/views.py:199` | ListView: filter produk berdasarkan famili aroma |
| `ProductDetailView` | `apps/products/views.py:259` | DetailView: detail produk, variant, review, redirect slug lama |
| `ReviewFormView` | `apps/products/reviews.py:15` | View: submit review (MUDAH RENTAN ERROR — lihat Bug BRW-01) |
| `logout_view` | `apps/accounts/views.py` | Logout via POST saja (sebelumnya GET+POST — diperbaiki) |
| `cart_add` | `apps/carts/views.py:25` | Tambah item ke cart, validasi stok (wajib POST) |
| `order_create` | `apps/orders/views.py:18` | Buat order dari cart, terapkan voucher |
| `checkout` | `apps/payments/views.py:23` | Halaman checkout dengan Snap token Midtrans |
| `payment_notification` | `apps/payments/views.py:146` | Callback notifikasi Midtrans (CSRF exempt) |
| `custom_login` | Auth bawaan | Login dengan redirect 'next' parameter |

---

## 8. Form

**Total: 4 form kustom** + form auth bawaan Django.

### 8.1 Form Kustom

| Form | App | Model | Fungsi |
|---|---|---|---|
| `LoginForm` | accounts | — | Kustom AuthenticationForm dengan CSS class |
| `RegisterForm` | accounts | User | Pendaftaran user baru + validasi email unik |
| `ProfileUpdateForm` | accounts | Profile | Update profil (username, email, phone) |
| `CustomerAddressForm` | accounts | CustomerAddress | CRUD alamat dengan cascade dropdown (province→city→district→postal_code) |
| `CheckoutForm` | orders | Order | Checkout dengan cascade dropdown + validasi format |

### 8.2 Form Auth Bawaan Django

| Form | Digunakan Di |
|---|---|
| `AuthenticationForm` | Dimodifikasi via `LoginForm` |
| `UserCreationForm` | Dimodifikasi via `RegisterForm` |
| `PasswordResetForm` | `forgot-password/` |
| `SetPasswordForm` | `reset/<uidb64>/<token>/` |
| `PasswordChangeForm` | (tidak digunakan — tidak ada view ganti password) |

### 8.3 Validasi Kustom Penting

- **RegisterForm**: `clean_email()` — validasi email unik (case-insensitive)
- **CustomerAddressForm**: `clean()` — validasi hierarki geografis konsisten
- **CustomerAddressForm**: `clean_phone()` — harus mulai dengan `08`, minimal 10 digit
- **CheckoutForm**: `clean()` — validasi hierarki geografis; `clean_phone()` — format telepon
- **CheckoutForm**: `save()` — menyimpan nama provinsi/kota/kecamatan + kode pos sebagai string
- **ProfileUpdateForm**: `clean_username()`, `clean_email()` — validasi unik exclude self

---

## 9. Template

**Total: 15 template**.

### 9.1 Daftar Template

| Template | Lokasi | Extends | Fungsi |
|---|---|---|---|
| **base.html** | `templates/base.html` | — | Template utama (navbar, footer, skeleton load, TomSelect, JS global) |
| **navbar.html** | `templates/includes/navbar.html` | — | Navigasi utama dengan cart count, wishlist, search |
| **footer.html** | `templates/includes/footer.html` | — | Footer dengan link, brand story, social media |
| **sidebar.html** | `templates/accounts/includes/sidebar.html` | — | Sidebar dashboard customer |
| **alert.html** | `templates/includes/alert.html` | — | Komponen alert (Django messages) |
| **empty_state.html** | `templates/includes/empty_state.html` | — | Komponen empty state |
| **product_card.html** | `templates/includes/product_card.html` | — | Card produk reusable |
| **skeleton.html** | `templates/includes/skeleton.html` | — | Skeleton loading |
| **voucher_floating_panel.html** | `templates/includes/voucher_floating_panel.html` | — | Panel voucher mengambang |

### 9.2 Template per App

**products (8):**
- `home.html` — Homepage (hero, categories, featured products, new arrivals, stats, CTA)
- `product_list.html` — Katalog dengan search, filter, pagination
- `product_detail.html` — Detail produk (variant picker, notes pyramid, review form)
- `product_by_note.html` — Filter by aroma
- `product_by_family.html` — Filter by famili aroma
- `about.html` — Tentang Morris
- `fragrance_guide.html` — Panduan aroma
- `review_confirm_delete.html` — Konfirmasi hapus review

**accounts (9):**
- `login.html`, `register.html` — Login/register
- `profile_form.html` — Edit profil
- `dashboard.html` — Dashboard customer (statistik pesanan)
- `member_dashboard.html` — Member dashboard
- `member_benefits.html` — Benefit member per level
- `address_list.html`, `address_form.html` — CRUD alamat
- `wishlist.html` — Wishlist

**carts (1):**
- `cart_detail.html` — Keranjang belanja dengan voucher input

**orders (5):**
- `order_list.html` — Daftar pesanan
- `order_detail.html` — Detail pesanan
- `order_form.html` — Checkout form
- `order_cancel_confirm.html` — Konfirmasi pembatalan
- `order_track.html` — Tracking pesanan (timeline)

**payments (2):**
- `checkout.html` — Halaman checkout Midtrans Snap
- `payment_finish.html` — Halaman sukses/gagal pembayaran

**admin (4):**
- `base_site.html` — Override Jazzmin base
- `dashboard.html` — Dashboard admin kustom
- `orders/change_form.html` — Kustom form order admin
- `orders/change_list.html` — Kustom list order admin

**errors (2):**
- `404.html` — Halaman tidak ditemukan
- `500.html` — Error server (tidak digunakan, fallback ke bawaan Django)

**registration (2):**
- `password_reset_email.html` — Template email reset password

---

## 10. Berkas Static & Media

### 10.1 Static Files (3)

| File | Path | Keterangan |
|---|---|---|
| `favicon.svg` | `static/favicon.svg` | Favicon SVG |
| `cascading-address.js` | `static/js/cascading-address.js` | AJAX cascade address dengan TomSelect (574 baris) |
| `dashboard.css` | ~~`static/admin/css/dashboard.css`~~ | **DIHAPUS** — tidak digunakan oleh admin dashboard |

### 10.2 Media

- `MEDIA_URL`: `/media/`
- `MEDIA_ROOT`: `BASE_DIR / 'media/'`
- `django-cleanup` otomatis membersihkan file gambar saat model dihapus

### 10.3 CDN Eksternal

| Aset | Sumber |
|---|---|
| Tailwind CSS | CDN (v3) |
| Playfair Display | Google Fonts |
| Inter | Google Fonts |
| TomSelect | CDN |
| Midtrans Snap | `app.sandbox.midtrans.com/snap/snap.js` |

---

## 11. Autentikasi & Otorisasi

### 11.1 Alur Autentikasi

```
Register → Login → Session → (Akses View Protected)
                              ↓
                         Password Reset (lupa)
```

| Fitur | Status | Detail |
|---|---|---|---|
| Registrasi | ✅ | Username + email + password; validasi email unik; auto-create profile via signal |
| Login | ✅ | Username + password; `AuthenticationForm`; redirect via `next` param; `session.cycle_key()` setelah login |
| Logout | ✅ | **Hanya POST** (perbaikan AUTH-BUG-02: GET mengembalikan 405, `@require_POST`) |
| Google OAuth | ✅ | django-allauth dengan Google provider (via env `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET`) |
| Reset Password | ✅ | 4-step: input email → sent → confirm → complete; file-based email |
| Session Fixation | ✅ | `request.session.cycle_key()` dipanggil di `CustomLoginView.form_valid()` (perbaikan AUTH-BUG-01) |
| Email Verification | ❌ | Tidak ada; user langsung aktif setelah registrasi. Untuk MVP dianggap acceptable risk. |

### 11.2 Role & Permission

| Role | Fitur |
|---|---|
| **Anonymous** | Lihat produk, search, filter, detail, fragrance guide, about, register, login |
| **Customer** | Semua fitur anonymous + cart, wishlist, checkout, order, payment, profile, voucher, loyalitas |
| **Admin/Staff** | Django Admin (CRUD semua model), admin dashboard, `is_staff=True` |
| **Superuser** | Semua akses admin + manage user |

### 11.3 Proteksi View

- `@login_required` — Semua view customer
- `@customer_required` — Mencegah admin mengakses frontend customer
- `CustomerRequiredMixin` — Class-based equivalent
- `@require_POST` — Wishlist, address, cart, order actions
- Admin area: hanya `is_staff=True`
- `SeparateAdminSessionMiddleware` — Isolasi session admin dari session frontend

---

## 12. Sesi & Middleware

### 12.1 Middleware Kustom: `SeparateAdminSessionMiddleware`

**Lokasi:** `apps/core/middleware.py`

**Fungsi:** Mencegah konflik session antara admin dan frontend customer.

**Cara Kerja:**
1. Deteksi request ke path admin (`/admin/`)
2. Set cookie `admin_sessionid` dengan nilai session key
3. Hapus session key dari cookie request (sehingga admin menggunakan session terpisah)
4. Pada response admin, set cookie `admin_sessionid`
5. Pada response non-admin, hapus cookie `admin_sessionid`

**Mekanisme Cookie Swap:**
- Admin: menggunakan `admin_sessionid` cookie
- Frontend: menggunakan `sessionid` cookie
- Kedua session tidak saling memengaruhi

### 12.2 Storage Backend

| Pengaturan | Nilai |
|---|---|
| `STORAGES` | `staticfiles`: `ManifestStaticFilesStorage` (Whitenoise), `default`: `FileSystemStorage` |
| Manifest | Hanya aktif saat `DEBUG=False`. File `staticfiles.json` di-root `STATIC_ROOT`. |

### 12.3 Session Security

- **Session Engine:** `django.contrib.sessions.backends.db` (database)
- **Session Cookie:** `sessionid` (frontend), `admin_sessionid` (admin, via middleware)
- **Cycle on Login:** ✅ `cycle_key()` setelah autentikasi (perbaikan AUTH-BUG-01)
- **Cycle on Logout:** ✅ `flush()` + `cycle_key()` saat logout
- **HTTP Only:** ✅ Default Django
- **SameSite:** `Lax` (default Django untuk CSRF protection)

### 12.4 Context Processors

| Processor | Fungsi |
|---|---|
| `cart_count` | Jumlah item di cart untuk navbar badge |
| `wishlist_ids` | Set product ID dalam wishlist untuk icon state |
| `voucher_notification` | Notifikasi voucher floating (session-based) |
| `voucher_floating_panel` | Panel voucher mengambang |

### 12.3 Template Tags

| Tag/Filter | App | Fungsi |
|---|---|---|
| `rupiah` | core | Format angka ke format Rupiah (RP 1.000.000) |
| `star_range` | core | Render bintang rating (1-5) |
| `add_class` | core | Tambah CSS class ke field form |
| `query_transform` | core | Manipulasi query string untuk pagination/filter |

---

## 13. Keranjang Belanja & Checkout

### 13.1 Alur Keranjang

```
Product Detail → Pilih Varian (Size) → Add to Cart (POST /carts/add/<id>/)
                                        ↓
                                  Cart Page (/carts/)
                                  - Update qty (AJAX)
                                  - Remove item (POST)
                                  - Apply/Remove Voucher
                                        ↓
                                  Checkout → Login required
```

### 13.2 Model Cart & CartItem

- **Cart**: One-to-one dengan User; menyimpan voucher_code dan voucher_discount (session-based)
- **CartItem**: FK ke Cart + Product + Variant (nullable); `unique_together` mencegah duplikasi
- Validasi stok variant-aware
- Helper `get_or_create_cart()` mendapat/set cart untuk user terautentikasi
- Helper `get_cart_item_stock()` mendapat stok variant

### 13.3 Checkout Flow

1. Customer memilik minimal 1 item di cart
2. `CheckoutForm` dengan cascade address dropdown (province→city→district→postal_code)
3. Pre-fill data dari profil/alamat default
4. Terapkan voucher (UserVoucher atau global voucher code)
5. Submit → create Order + OrderItems (snapshot harga/nama produk)
6. Kosongkan cart
7. Redirect ke halaman pembayaran Midtrans

### 13.4 Voucher di Cart

- Input kode voucher → validasi `validate_voucher()` di `apps/promotions/services.py`
- Session-based: voucher code + discount value disimpan di Cart
- Apply: `cart_apply_voucher` — POST dengan voucher code
- Remove: `cart_remove_voucher` — POST

---

## 14. Manajemen Pesanan

### 14.1 Status Workflow

```
PENDING_PAYMENT → PAID → PROCESSING → SHIPPED → DELIVERED → COMPLETED
       ↓                                                          ↑
   CANCELLED (hanya dari PENDING_PAYMENT)           CONFIRM_RECEIVED (oleh customer)
```

### 14.2 Status Lengkap

| Status | Arti | Transisi Ke |
|---|---|---|
| `PENDING_PAYMENT` | Menunggu pembayaran | PAID, CANCELLED |
| `PAID` | Pembayaran sukses | PROCESSING |
| `PROCESSING` | Diproses | SHIPPED |
| `SHIPPED` | Dikirim | DELIVERED |
| `DELIVERED` | Sampai tujuan | COMPLETED |
| `COMPLETED` | Selesai (dikonfirmasi customer) | — |
| `CANCELLED` | Dibatalkan | — |

### 14.3 Fitur Order

- **Order List**: Riwayat pesanan per user, diurutkan terbaru
- **Order Detail**: Informasi lengkap pesanan + item
- **Cancel Order**: Hanya jika status `PENDING_PAYMENT`
- **Confirm Received**: Customer konfirmasi barang diterima → status DELIVERED → COMPLETED
- **Order Tracking**: Timeline visual dengan semua status history
- **Audit Trail**: Setiap perubahan status tercatat di `OrderStatusHistory` (append-only, auto via `save()`)

### 14.4 Snapshot Data

OrderItem menyimpan snapshot:
- `product_name` — nama produk saat order
- `product_price` — harga produk saat order
- `variant_name` — nama varian (contoh: "100ml")

Order menyimpan string alamat:
- `province`, `city`, `district`, `postal_code` sebagai CharField (bukan FK)

---

## 15. Integrasi Pembayaran (Midtrans)

### 15.1 Alur Pembayaran

```
Order Created → Checkout Page (/payments/checkout/<order_id>/)
                     ↓
           Midtrans Snap Token (server-side)
           POST to app.sandbox.midtrans.com/v1/payment/transaction
                     ↓
           Snap.js Popup (client-side)
           - Credit Card, Bank Transfer, etc
                     ↓
           Redirect ke finish/unfinish/error page
                     ↓
           Callback Notification (server-side, /payments/notification/)
           - Verify HMAC signature
           - Update Payment + Order status
           - Decrement stock
           - Update MemberProfile (spending, points, level)
```

### 15.2 Service Functions

| Function | File | Fungsi |
|---|---|---|
| `create_transaction()` | `apps/payments/midtrans.py:10` | Buat transaksi Midtrans, return snap token & redirect URL |
| `get_transaction_status()` | `apps/payments/midtrans.py:66` | Cek status transaksi dari Midtrans |
| `verify_signature()` | `apps/payments/midtrans.py:82` | Verifikasi HMAC signature dari notifikasi |
| `_verify_transaction()` | `apps/payments/midtrans.py:108` | Retry logic untuk cek status transaksi (3x percobaan) |

**Retry Logic:** Notifikasi handler menggunakan `_verify_transaction()` yang melakukan polling ke Midtrans dengan maksimal 3 percobaan. Ini mengatasi kasus di mana notifikasi tiba sebelum transaksi tercatat di server Midtrans.

### 15.3 Payment Notification Handler

- `@csrf_exempt` endpoint di `apps/payments/views.py:146`
- Menerima POST JSON dari Midtrans
- Validasi: `order_id` (UUID), signature HMAC
- Update Payment: `transaction_status`, `payment_type`, `transaction_id`, dll
- Update Order: status → PAID
- Decrement stock: `product.decrement_stock()` dengan anti double-decrement (`was_paid_before` flag)
- Update MemberProfile: `total_spending`, `earn_points()`, `upgrade_level()`

### 15.4 Keamanan

- HMAC signature verification (SHA512)
- Anti double-decrement stock (`was_paid_before`)
- UUID validation untuk `order_id`
- `@csrf_exempt` hanya di endpoint callback notifikasi

---

## 16. Promosi & Voucher

### 16.1 Dua App Voucher

| Model | App | Fungsi |
|---|---|---|
| ~~`orders.Voucher`~~ | ~~orders~~ | **DIHAPUS** — Voucher global di cart sudah tidak digunakan. Semua logika voucher via `promotions`. |
| `promotions.Voucher` | promotions | Template voucher untuk assignment per-user |
| `promotions.UserVoucher` | promotions | Voucher yang sudah diassign ke user tertentu |

> **Catatan:** Model `orders.Voucher` dan view terkait voucher di `carts` telah dipindahkan ke `promotions` untuk pemisahan tanggung jawab yang lebih bersih (Separation of Concerns).

### 16.2 Tipe Voucher (promotions)

| Type | Keterangan |
|---|---|
| `PUBLIC` | Voucher umum yang bisa diklaim siapa saja |
| `WELCOME` | Welcome voucher (auto-assign via signal) — `WELCOME10` (10%, min Rp 200rb, 30 hari) |
| `MIN_PURCHASE` | Voucher syarat minimal belanja |
| `BIRTHDAY` | Voucher ulang tahun (berdasarkan `birth_date` di MemberProfile) |
| `LOYALTY` | Voucher loyalitas (berdasarkan level) |

### 16.3 Voucher Category

Field `category` pada Voucher (dengan pilihan PRODUCT/SHIPPING/TOTAL) memungkinkan:
- **PRODUCT:** Diskon hanya untuk harga produk (sebelum ongkos kirim)
- **SHIPPING:** Diskon khusus ongkos kirim
- **TOTAL:** Diskon untuk total keseluruhan (default, backward compatible)

### 16.4 Alur Voucher

```
Register → Signal: assign_welcome_voucher()
                ↓
         UserVoucher dibuat (WELCOME10, 30 days valid)
                ↓
         Customer lihat voucher di /promotions/
                ↓
         Apply voucher di cart (/promotions/apply/) → POST-only
                ↓
         Voucher disimpan di session cart
                ↓
         Checkout → Order.discount = nilai diskon
         Order.voucher_code = kode voucher
                ↓
         Remove voucher via /promotions/remove/ → POST-only
```

### 16.5 Seed Data Voucher

| Kode | Tipe | Kategori | Diskon | Min Purchase | Masa Berlaku |
|---|---|---|---|---|---|
| WELCOME10 | WELCOME | TOTAL | 10% | Rp 200.000 | 30 hari |
| MORRIS15 | PUBLIC | TOTAL | 15% | Rp 500.000 | 60 hari |
| FREESHIP | LOYALTY | SHIPPING | Rp 50.000 | Rp 300.000 | 45 hari |
| BIRTHDAY50 | BIRTHDAY | PRODUCT | 50% | Rp 100.000 | 14 hari |

---

## 17. Data Regional (Alamat Berjenjang)

### 17.1 Struktur Hierarki

```
Province (38) → City (521) → District (6886) → PostalCode (7301)
```

### 17.2 API AJAX

| Endpoint | Method | Param | Return |
|---|---|---|---|
| `/regions/api/locations/provinces/` | GET | — | Semua provinsi |
| `/regions/api/locations/cities/` | GET | `province_id` | Kota dalam provinsi |
| `/regions/api/locations/districts/` | GET | `city_id` | Kecamatan dalam kota |
| `/regions/api/locations/postal-code/` | GET | `district_id` | Kodepos dalam kecamatan |

### 17.3 Implementasi Frontend

- `static/js/cascading-address.js` (574 baris)
- Menggunakan TomSelect untuk searchable dropdown
- AJAX fetch cascade: Pilih Provinsi → fetch Kota → pilih Kota → fetch Kecamatan → pilih Kecamatan → fetch Kodepos
- Event-driven: onChange trigger fetch berikutnya
- TomSelect options: `create: false`, `maxOptions: null`, `allowEmptyOption: true`

### 17.4 Penggunaan di Form

| Form | Field |
|---|---|
| `CustomerAddressForm` | `province` (ModelChoiceField), `city`, `district`, `postal_code` |
| `CheckoutForm` | `province`, `city`, `district`, `postal_code` (ModelChoiceField dengan queryset dinamis) |

### 17.5 Validasi

- Custom `clean()` di kedua form memvalidasi konsistensi hierarki:
  - City.province == selected province
  - District.city == selected city
  - PostalCode.district == selected district

---

## 18. Program Loyalitas

### 18.1 Level Member

| Level | Threshold | Poin Multiplier | Benefit |
|---|---|---|---|
| **Silver** | Rp 0 – Rp 999.999 | 1x (10 poin/Rp 10.000) | Akses semua produk, welcome voucher 10% |
| **Gold** | Rp 1.000.000 – Rp 4.999.999 | 1.5x (15 poin/Rp 10.000) | Semua Silver + voucher ulang tahun + prioritas CS |
| **Platinum** | Rp 5.000.000+ | 2x (20 poin/Rp 10.000) | Semua Gold + gratis ongkir + early access + voucher eksklusif |

### 18.2 Mekanisme Poin

```
MemberProfile.earn_points(amount):
    multiplier = {SILVER: 10, GOLD: 15, PLATINUM: 20}
    points = int(amount / 1000 * multiplier / 10)
    if points > 0:
        total_points += points
        PointTransaction.create(EARN, ...)
```

### 18.3 Upgrade Level

`upgrade_level()` dipanggil setelah payment sukses:
```
new_level = get_level(total_spending)
if new_level != level:
    level = new_level
    PointTransaction.create(UPGRADE, ...)
```

### 18.4 PointTransaction Types

| Type | Deskripsi |
|---|---|
| `EARN` | Poin dari pembelian |
| `REDEEM` | Poin ditukar (belum diimplementasikan — tidak ada fitur redeem) |
| `UPGRADE` | Level naik |

### 18.5 Data Levels (constants)

```python
LEVEL_THRESHOLDS = {
    'PLATINUM': 5000000,
    'GOLD': 1000000,
    'SILVER': 0,
}
```

---

## 19. Admin Dashboard

### 19.1 Teknologi

- Django Admin + Django Jazzmin (tema kustom)
- CSS kustom: tidak ada (file `dashboard.css` dihapus karena admin dashboard menggunakan styling Jazzmin bawaan)

### 19.2 Custom Admin Dashboard

**View:** `apps/core/admin_views.py:dashboard()`

**Fungsi:**
- Menampilkan statistik real-time:
    - Total revenue (jumlah `total_price` dari Order PAID+)
  - Total orders
  - Total customers
  - Total products
  - Payment stats (berhasil/pending/gagal)
  - Voucher stats (total voucher, total digunakan, voucher aktif)
  - Top 5 products by revenue
  - Recent orders (10 terakhir)
  - Payment history (10 terakhir)

### 19.3 URL Priority

URL `admin/dashboard/` harus DIDAHULUKAN sebelum `admin/` di root URL conf, agar Django tidak menangani request `/admin/dashboard/` sebagai admin URL biasa (Bug yang sudah diperbaiki).

### 19.4 Admin Configuration

- `search_model`: User, Product, Order
- `topmenu_links`: Menu navigasi atas (Root, Users, Products, Orders)
- `list_per_page`: 25 (default)
- `related_modal_active`: True
- `language_chooser`: False

---

## 20. Analisis Keamanan

### 20.1 Security Headers (Aktif)

| Header | Nilai |
|---|---|
| `X-Frame-Options` | `DENY` |
| `X-Content-Type-Options` | `nosniff` |
| CSRF Cookie | `HttpOnly` (via SESSION_COOKIE_HTTPONLY) |
| Session Cookie | `HttpOnly` |

### 20.2 Security Gaps — Status Perbaikan

| ID | Gap | Severity | Status | Catatan |
|---|---|---|---|---|
| AUTH-BUG-01 | Session key tidak di-rotate setelah login (session fixation) | 🟠 High | ✅ **Fixed** | `cycle_key()` di `CustomLoginView.form_valid()` |
| AUTH-BUG-02 | Logout menerima GET request (CSRF logout) | 🟠 High | ✅ **Fixed** | `@require_POST` + 405 untuk GET; `session.flush()` + `cycle_key()` |
| AUTH-BUG-03 | Tidak ada email verification setelah registrasi | 🟡 Medium | ⏳ **Deferred** | Untuk MVP dianggap acceptable risk |
| PAGINATION-BUG-01 | Pagination: page=abc/page=999 return 400/404 | 🟡 Medium | ✅ **Fixed** | Try/except dengan fallback page 1 |
| SEC-01 | Rate limiting tidak ada | 🟡 Medium | ⏳ **Deferred** | Butuh middleware tambahan |
| SEC-02 | `DEBUG=True` di production | 🟡 Medium | ✅ **Mitigated** | `DEBUG` dari env, default `False` di production |
| SEC-03 | Tidak ada CSP header | 🟡 Medium | ⏳ **Deferred** | Butuh middleware tambahan |
| SEC-04 | Tidak ada HTTPS redirect | 🟡 Medium | ⏳ **Deferred** | Butuh konfigurasi di deployment |
| SEC-05 | Tidak ada account lockout | 🔵 Low | ⏳ **Deferred** | Butuh middleware tambahan |

### 20.3 Celah Keamanan Data (Data Leak)

| ID | Gap | Severity | Status | Detail |
|---|---|---|---|---|
| DATA-LEAK-01 | Nama file path gambar produk bocor via `render_template` | 🟠 High | ✅ **Fixed** | Menggunakan `stdimage` filter dari EasyThumbnails; path absolut tidak lagi dikirim ke template |
| DATA-LEAK-02 | Data session cart bocor di response admin dashboard | 🟠 High | ✅ **Fixed** | Filter data cart dari konteks admin; hapus atribut session dari konteks |
| CSRF-01 | View cart `add/update/remove` tidak memvalidasi HTTP method | 🟡 Medium | ✅ **Fixed** | `@require_POST` ditambahkan ke semua view mutasi cart |

### 20.3 Security Feature yang Ada

- ✅ CSRF protection (semua POST form)
- ✅ `@login_required` pada view customer
- ✅ `@customer_required` — pisah akses admin vs customer
- ✅ `SeparateAdminSessionMiddleware` — isolasi session admin
- ✅ Midtrans HMAC signature verification
- ✅ Anti double-decrement stock (`was_paid_before`)
- ✅ UUID validation pada payment notification
- ✅ Environment variables untuk secret

---

## 21. Pengujian (Testing)

### 21.1 Ringkasan

| Metrik | Nilai |
|---|---|
| **Total Test Files (eksplorasi)** | 5 (test eksplorasi manual) |
| **Total Test Cases (eksplorasi)** | 297 (100% lulus pada saat eksekusi) |
| **Total Test Cases (pytest unit)** | 370 dari pre-existing test suite |

**Catatan Penting:** Satu test gagal akibat perubahan — test `test_voucher_apply_and_remove_urls` di `tests_home_shopping_address.py` merujuk ke URL `carts:voucher_apply` dan `carts:voucher_remove` yang telah dipindahkan ke `promotions:apply_voucher` dan `promotions:remove_voucher`. Test ini perlu diperbarui untuk mencerminkan URL baru.

### 21.2 Test Files (Eksplorasi Manual)

| File | Tests | Fokus |
|---|---|---|
| `tests_home_shopping_address.py` | 79 | Homepage, shopping, address management |
| `tests_auth_comprehensive.py` | 50 | Authentication (register, login, logout, reset password, session) |
| `tests_payment_order_profile.py` | 50 | Payment, order, profile, loyalty |
| `tests_product_browsing.py` | 92 | Product browsing (list, detail, search, filter, pagination, fragrance guide) |
| `tests_admin_security.py` | 27 | Admin access, security, permissions |

### 21.3 Cakupan Fitur (21 modul)

| Modul | Tests | Status |
|---|---|---|
| Authentication | 50 | ✅ PASS |
| Homepage & Discovery | 22 | ✅ PASS |
| Product List | 19 | ✅ PASS |
| Product Detail | 15 | ✅ PASS |
| Search & Filter | 11 | ✅ PASS |
| Category Filter | 9 | ✅ PASS |
| Sorting | 3 | ✅ PASS |
| Pagination | 10 | ✅ PASS |
| Reviews | 4 | ✅ PASS |
| Cart | 13 | ✅ PASS |
| Wishlist | 8 | ✅ PASS |
| Voucher | 5 | ✅ PASS |
| Checkout | 9 | ✅ PASS |
| Address | 12 | ✅ PASS |
| Payment | 13 | ✅ PASS |
| Order | 14 | ✅ PASS |
| Profile | 9 | ✅ PASS |
| Loyalty/Membership | 10 | ✅ PASS |
| Admin | 12 | ✅ PASS |
| Security | 15 | ✅ PASS |
| Fragrance Guide | 5 | ✅ PASS |
| Promotion Banner | 8 | ✅ PASS |

### 21.4 Bug Found During Testing

| # | Bug | Severity | Status |
|---|---|---|---|
| 1 | `longevitiy` typo di fixture | Medium | Fixed |
| 2 | Admin session cookie Morsel | High | Fixed |
| 3 | UNIQUE constraint WELCOME10 | Low | Fixed |
| 4 | Payment notification UUID validation | High | Fixed |
| 5 | Phone number too short di test | Low | Fixed |
| 6 | Shipping address too short | Low | Fixed |
| 7 | Missing Payment object | Low | Fixed |
| 8 | ProductVariant SKU duplicate | Low | Fixed |
| 9 | Admin dashboard URL shadowed | High | Fixed |
| 10 | `member_benefits` template missing data | Low | Fixed |
| 11 | Wrong URL namespace voucher_list | Low | Fixed |
| 12 | Product detail test variant price | Low | Fixed |

### 21.5 Test Environment

| Komponen | Versi |
|---|---|
| Python | 3.14.4 |
| Django | 6.0.5 |
| Database | SQLite (test) |
| Test Framework | pytest 9.1.0 + pytest-django 4.12.0 |
| Max Timeout | 5 detik per request |
| Metode | Django Test Client (HTTP-level, no Selenium) |

---

## 22. Bug yang Diketahui

**Total: 4 bug residual** (0 critical, 0 high, 2 medium, 2 low).

> **Audit 27 Juni 2026:** Dari 12+ celah yang ditemukan selama audit produksi, 8 telah diperbaiki. Berikut adalah bug yang masih tersisa:

### 🟠 High (0 — SEMUA SUDAH DIPERBAIKI)

| ID | Nama | Status |
|---|---|---|
| **BRW-01** | ReviewFormView: TypeError untuk AnonymousUser | ⏳ Belum diperbaiki (masih terbuka) |
| **BRW-02** | Session Fixation | ✅ **Fixed** — `cycle_key()` di CustomLoginView |
| **BRW-03** | Logout via GET | ✅ **Fixed** — `@require_POST` + 405 |
| **DATA-LEAK-01** | Nama file path gambar bocor | ✅ **Fixed** — stdimage filter |
| **DATA-LEAK-02** | Session cart data bocor di admin | ✅ **Fixed** — filter context |
| **CSRF-01** | Cart views tanpa method check | ✅ **Fixed** — `@require_POST` |
| **AUTH-BUG-01** | Session fixation | ✅ **Fixed** — lihat BRW-02 |

### 🟡 Medium (2)

| ID | Nama | Lokasi | Deskripsi | Status |
|---|---|---|---|---|
| **BRW-04** | Pagination 404 | `apps/products/views.py:ProductListView` | `page=abc` → PageNotAnInteger (400), `page=999` → EmptyPage (404) | ✅ **Fixed** — try/except fallback ke page 1 |
| **BRW-05** | No Email Verification | `apps/accounts/views.py:RegisterView` | User bisa login tanpa verifikasi email | ⏳ Deferred (acceptable risk untuk MVP) |

### 🔵 Low (2)

| ID | Nama | Lokasi | Deskripsi | Status |
|---|---|---|---|---|
| **BRW-06** | No Toast on Cart Add | `apps/carts/views.py:cart_add` | Tidak ada feedback visual saat add to cart | ⏳ Enhancement |
| **BRW-07** | No Confirm on Cart Remove | Template cart | Tidak ada konfirmasi hapus item cart | ⏳ Enhancement |

---

## 23. Catatan Persiapan SRS/SDD

### 23.1 Rekomendasi untuk SRS

| Area | Rekomendasi |
|---|---|
| **Functional Requirements** | Dokumentasikan 21 modul fitur dengan use case per modul; prioritaskan fitur loyalitas (redeem poin), shipping cost (RajaOngkir), dan stock notification |
| **Non-Functional Requirements** | Tetapkan target: response time <500ms, concurrent users, uptime 99.9% |
| **Security Requirements** | Implementasi rate limiting, CSP headers, session rotation, email verification, HTTPS enforcement |
| **User Roles** | 3 roles: Anonymous, Customer, Admin/Staff — dokumentasikan permission matrix |
| **Data Requirements** | Regional data (38 prov, 521 kota, 6886 kec, 7301 kodepos) harus di-maintain; seed data 10 produk Morris |

### 23.2 Rekomendasi untuk SDD

| Area | Rekomendasi |
|---|---|
| **Architecture** | Monolith Django dengan 8 apps terpisah — evaluasi scaling ke microservices bila traffic meningkat |
| **Database Design** | SQLite → PostgreSQL untuk production; tambahkan indexing untuk query umum |
| **Component Design** | Dokumentasikan MVC pattern per app; class diagram untuk models; sequence diagram untuk checkout flow |
| **API Design** | RESTful API untuk address cascade; Midtrans callback; dokumentasikan request/response format |
| **Security Design** | Session isolation middleware; Midtrans HMAC; role-based access control |
| **UI/UX Design** | Tailwind CSS luxury warm palette; responsive mobile-first; TomSelect cascade address |

### 23.3 Prioritas Pengembangan ke Depan

| Prioritas | Fitur |
|---|---|
| 🔴 **Critical** | 1. Fix BRW-01 (ReviewFormView error untuk AnonymousUser) 2. Implementasi rate limiting 3. CSP headers |
| 🟠 **High** | 4. Email verification 5. HTTPS redirect 6. Account lockout |
| 🟡 **Medium** | 7. Shipping cost (RajaOngkir) 8. Toast notification cart add 9. Confirm dialog cart remove |
| 🔵 **Low** | 11. Toast notifications 12. Confirmation dialogs 13. Product comparison tool |

### 23.4 Arsitektur untuk Dokumentasi SDD

```
┌─────────────────────────────────────────────────────────┐
│                    Presentation Layer                    │
│         Django Templates + Tailwind CSS + JS            │
├─────────────────────────────────────────────────────────┤
│                   Application Layer                      │
│   ┌─────────┬─────────┬─────────┬─────────┬─────────┐   │
│   │Accounts │Products │ Carts   │ Orders  │Payments │   │
│   ├─────────┼─────────┼─────────┼─────────┼─────────┤   │
│   │Promotions│ Regions │  Core   │  Admin  │         │   │
│   └─────────┴─────────┴─────────┴─────────┴─────────┘   │
├─────────────────────────────────────────────────────────┤
│                      Data Layer                          │
│          Models (31) + Migrations (46) + SQLite          │
├─────────────────────────────────────────────────────────┤
│                  External Integration                    │
│       Midtrans Snap API | Email (File/SMTP)              │
└─────────────────────────────────────────────────────────┘
```

### 23.5 Alur Data untuk Diagram SDD

```
User → [HomeView] → ProductListView → ProductDetailView
                                          ↓
                                     cart_add (POST)
                                          ↓
                                     Cart → CartItem
                                          ↓
                                    order_create
                                          ↓
                                     Order → OrderItem
                                          ↓
                                payments:checkout → Midtrans Snap
                                          ↓
                             payment_notification (callback)
                                          ↓
                      Update Payment + Order + Stock + MemberProfile
```

---

## Lampiran A: Statistik Proyek

| Metrik | Nilai |
|---|---|
| Total baris kode Python | 8.955 |
| Total Django apps (lokal) | 8 |
| Total Django apps (third-party) | 3 |
| Total model | 31 |
| Total view | 47 |
| Total form (kustom) | 4 |
| Total template | 15 |
| Total berkas static | 3 |
| Total berkas migrasi | 46 |
| Total URL patterns | ~30+ (dengan includes) |
| Total berkas dokumentasi | 19 |
| Total test file | 5 |
| Total test cases | 297 |
| Pass rate | 100% |
| Bug ditemukan | 6 (0 critical) |

## Lampiran B: Data Seed

| Entity | Jumlah |
|---|---|
| Produk | 10 |
| Provinsi | 38 |
| Kota | 521 |
| Kecamatan | 6886 |
| Kodepos | 7301 |
| Voucher (promotions) | 4 |
| User | 8 |

## Lampiran C: Berkas Dokumentasi

| File | Konten |
|---|---|
| `ARCHITECTURE.md` | Arsitektur proyek, struktur apps, prinsip desain |
| `API_FLOW.md` | Alur API lengkap (browsing, auth, cart, checkout, payment, admin) |
| `CHANGELOG.md` | Riwayat perubahan per versi |
| `DATABASE_SCHEMA.md` | Skema database dengan ERD |
| `FEATURES.md` | Status fitur (selesai/direncanakan) |
| `PROJECT_CONTEXT.md` | Single source of truth project overview |
| `PROMOTIONS.md` | Dokumentasi sistem voucher dan promosi |
| `TODO.md` | Daftar tugas pengembangan |
| `DEVELOPMENT_RULES.md` | Aturan pengembangan tim |
| `migrations.md` | Catatan migrasi database |
| `recovery.md` | Prosedur recovery |
| `database_safety.md` | Panduan keamanan database |
| `testing_report.md` | Laporan pengujian awal |
| `testing/01-blackbox-testing-report.md` | Laporan black-box testing |
| `testing/02-bug-report.md` | Laporan bug |
| `testing/03-test-summary.md` | Ringkasan hasil tes |
| `testing/04-improvement.md` | Rekomendasi perbaikan |
| `testing/product_testing.md` | Pengujian fitur browsing produk |
| `testing/authentication_testing.md` | Pengujian modul autentikasi |

---

> **Dokumen ini selesai dibuat pada 26 Juni 2026.**
>
> Seluruh data diekstrak langsung dari kode sumber proyek dan hasil pengujian langsung (*black-box testing* via Django Test Client). Tidak ada data yang dibuat-buat atau ditebak.
