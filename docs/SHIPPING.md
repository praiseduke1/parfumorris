# Shipping Module — Layanan Pengiriman (RajaOngkir via Komerce)

Fitur pemilihan layanan pengiriman menggunakan RajaOngkir API (Komerce).

---

## Alur Checkout

```
User                     Browser/JS                 Django Server              Komerce API
 │                          │                           │                        │
 │  1. Pilih Alamat         │                           │                        │
 │ ───────────────────────► │                           │                        │
 │                          │  selectAddress()          │                        │
 │                          │  → cascading address       │                        │
 │                          │  → district terisi        │                        │
 │                          │                           │                        │
 │  2. Pilih Kurir          │                           │                        │
 │ ───────────────────────► │                           │                        │
 │                          │  selectCourier(code)      │                        │
 │                          │  POST /shipping/api/cost/ │                        │
 │                          │  {district_id,            │                        │
 │                          │   courier_code}           │                        │
 │                          │ ────────────────────────► │                        │
 │                          │                           │  lookup_komerce_origin  │
 │                          │                           │  lookup_komerce_id      │
 │                          │                           │  POST calculate/domestic-cost
 │                          │                           │ ─────────────────────► │
 │                          │                           │ ◄──── {services} ────── │
 │                          │ ◄── {services: [...]} ────│                        │
 │                          │                           │                        │
 │  3. Pilih Layanan        │                           │                        │
 │ ───────────────────────► │                           │                        │
 │                          │  selectShipping(radio)    │                        │
 │                          │  POST /shipping/api/select/│                        │
 │                          │  → simpan ke session      │                        │
 │                          │  → update total realtime  │                        │
 │                          │                           │                        │
 │  4. Submit Order          │                           │                        │
 │ ───────────────────────► │                           │                        │
 │                          │  POST form                │                        │
 │                          │ ────────────────────────► │                        │
 │                          │                           │  Order.shipping_courier │
 │                          │                           │  Order.shipping_service │
 │                          │                           │  Order.shipping_cost    │
 │                          │                           │  Order.shipping_etd     │
 │                          │                           │  Order.shipping_weight  │
 │                          │                           │                        │
 │                          │  → Redirect ke payment    │                        │
```

## Flow Ongkir

1. **User pilih alamat** → cascading address JS mengisi province→city→district→postal code.
2. **District terpilih** → section "Layanan Pengiriman" muncul.
3. **Grid kurir** ditampilkan berdasarkan `ShippingConfig.enabled_couriers`.
4. **User klik kurir** (misal JNE) → AJAX `POST /shipping/api/cost/` dengan `{district_id, courier_code: 'jne'}`.
5. **Backend**:
   - Cari Komerce origin ID (dari `ShippingConfig.komerce_origin_id` atau lookup).
   - Cari Komerce destination ID (dari `District.komerce_id` atau lookup).
   - Hitung ongkir via `POST /calculate/domestic-cost` ke RajaOngkir.
   - Format response via `format_courier_services()`.
   - Cache per `origin:destination:weight:courier` selama 10 menit.
6. **Service radio buttons** ditampilkan (contoh: JNE REG Rp18.000, JNE OKE Rp14.000).
7. **User pilih service** → `POST /shipping/api/select/` simpan ke session + update total realtime.
8. **Submit form** → session `shipping` dibaca, disimpan ke Order.

## Cara Mengganti Origin (Lokasi Toko)

1. Buka Django Admin → Shipping → Shipping Config.
2. Ubah field:
   - `origin_province` — Provinsi asal (default: "Jawa Tengah")
   - `origin_city` — Kota/Kabupaten asal (default: "Kabupaten Banyumas")
   - `origin_district` — Kecamatan asal (default: "Purwokerto")
3. Kosongkan `komerce_origin_id` agar di-lookup ulang otomatis.
4. Simpan.

Atau via code:
```python
from apps.shipping.models import ShippingConfig
config = ShippingConfig.load()
config.origin_province = 'Jawa Timur'
config.origin_city = 'Kota Surabaya'
config.origin_district = 'Tegalsari'
config.komerce_origin_id = None  # force re-lookup
config.save()
ShippingConfig.clear_cache()
```

## Cara Menambah/Mengurangi Kurir

1. Buka Django Admin → Shipping → Shipping Config.
2. Ubah field `enabled_couriers` (comma-separated courier codes).
3. Kode kurir yang tersedia:
   - `jne` — JNE
   - `jnt` — J&T
   - `sicepat` — SiCepat
   - `pos` — POS Indonesia
   - `anteraja` — AnterAja
   - `ninja` — Ninja Xpress
   - `tiki` — TIKI
   - `lion` — Lion Parcel
   - `sap` — SAP Express
   - `idexpress` — ID Express
4. Contoh: `jne,jnt,sicepat` hanya mengaktifkan 3 kurir.

## API Endpoints

### `POST /shipping/api/cost/`

Menghitung ongkos kirim untuk satu kurir.

**Request:**
```json
{
    "district_id": 123,
    "courier_code": "jne"
}
```

**Response (200):**
```json
{
    "services": [
        {
            "courier_code": "jne",
            "courier_name": "JNE",
            "courier_logo": "https://...",
            "service": "REG",
            "description": "Reguler",
            "cost": 18000,
            "etd": "2-3 hari",
            "note": ""
        }
    ],
    "weight": 500,
    "origin": "Purwokerto, Kabupaten Banyumas",
    "destination": "Sukajadi, Kota Bandung",
    "errors": []
}
```

**Error (502):**
```json
{
    "error": "Gagal menghitung ongkos kirim",
    "detail": "Kecamatan 'XYZ' tidak ditemukan di RajaOngkir",
    "errors": [{"courier": "jne", "message": "..."}]
}
```

### `POST /shipping/api/select/`

Menyimpan pilihan layanan ke session.

**Request:**
```json
{
    "courier_code": "jne",
    "service": "REG",
    "cost": 18000,
    "etd": "2-3 hari"
}
```

**Response:** `{"ok": true}`

### `GET /shipping/api/clear/`

Menghapus shipping session.

**Response:** `{"ok": true}`

## Struktur Response API RajaOngkir (Komerce V2)

Endpoint: `POST /calculate/domestic-cost`

**Request body** (form-urlencoded):
```
origin=72918
destination=12345
weight=500
courier=jne
```

**Response** (JSON):
```json
{
    "meta": {"message": "Success", "code": 200, "status": "success"},
    "data": [
        {
            "name": "JNE",
            "code": "jne",
            "service": "CTC",
            "description": "City Courier",
            "cost": 8000,
            "etd": "3 day"
        },
        {
            "name": "JNE",
            "code": "jne",
            "service": "REG",
            "description": "Reguler",
            "cost": 18000,
            "etd": "2-3"
        }
    ]
}
```

Backend memformat response ini via `format_courier_services()`:
- `name` → `courier_name`
- `code` → `courier_code`
- `service` → `service`
- `cost` → `cost`
- `etd` → di-normalize (contoh: `"3 day"` → `"3 hari"`, `"2-3"` → `"2-3 hari"`)

## Models

### ShippingConfig (`apps/shipping/models.py`)
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `origin_province` | CharField | "Jawa Tengah" | Provinsi asal |
| `origin_city` | CharField | "Kabupaten Banyumas" | Kota/Kabupaten asal |
| `origin_district` | CharField | "Purwokerto" | Kecamatan asal |
| `komerce_origin_id` | PositiveIntegerField | null | ID origin di Komerce (cache) |
| `default_weight` | PositiveIntegerField | 500 | Berat default (gram) jika produk tanpa weight |
| `cache_ttl` | PositiveIntegerField | 10 | Cache TTL dalam menit |
| `enabled_couriers` | TextField | "jne,jnt,sicepat,pos,..." | Daftar kurir aktif |

### Order (`apps/orders/models.py`)
| Field | Type | Description |
|-------|------|-------------|
| `shipping_cost` | DecimalField | Ongkos kirim |
| `shipping_courier` | CharField(20) | Kode kurir (jne, jnt, dll) |
| `shipping_service` | CharField(50) | Nama layanan (REG, OKE, dll) |
| `shipping_estimation` | CharField(50) | Estimasi (2-3 hari) |
| `shipping_weight` | PositiveIntegerField | Total berat (gram) |
| `shipping_origin` | CharField(200) | Asal pengiriman |
| `shipping_destination` | CharField(200) | Tujuan pengiriman |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `KOMERCE_API_KEY` | ✅ | API Key dari Komerce |
| `KOMERCE_BASE_URL` | ❌ | Default: `https://rajaongkir.komerce.id/api/v1` |

API key **tidak boleh hardcode**. Dibaca dari `.env` via `settings.py`.

## Caching

Hasil ongkir di-cache selama **10 menit** (konfigurabel via `ShippingConfig.cache_ttl`).

Cache key: `shipping:cost:{origin_id}:{destination_id}:{weight}:{courier_code}`

Cache menggunakan Django cache framework (memory/file/Redis).

## Testing

```bash
# Semua shipping tests
python -m pytest apps/shipping/tests.py -v

# Full suite
python -m pytest
```

## Troubleshooting

| Gejala | Penyebab | Solusi |
|--------|----------|--------|
| Shipping section tidak muncul | District belum dipilih | Pilih kecamatan di form alamat |
| "Gagal menghitung ongkos kirim" | API key invalid / koneksi | Periksa `.env` `KOMERCE_API_KEY`, log server |
| "Tidak ada layanan tersedia" | Kurir tidak melayani rute | Coba kurir lain, periksa `enabled_couriers` |
| 502 Bad Gateway | Lookup subdistrict gagal | Cek log: `lookup_komerce_id` / `lookup_komerce_origin_id` |
| Total tidak berubah | Service belum dipilih | Klik salah satu layanan |
| Berat 0 di order | Produk/variant tanpa weight | Set weight via Admin atau default 500g |
