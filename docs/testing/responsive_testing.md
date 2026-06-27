# Responsive UI Testing — ParfuMoray

**Date:** 2026-06-27  
**Methodology:** Code review of responsive CSS/Tailwind breakpoints across all 47+ templates  
**Viewports Tested:** Desktop (≥1280px), Laptop (1024–1279px), Tablet (640–1023px), Mobile (<640px)  
**Framework:** Tailwind CSS (CDN via `base.html:15`) — no custom `@media` queries

---

## Breakpoint Mapping

| Device | Tailwind Prefix | Range | Notes |
|--------|----------------|-------|-------|
| Desktop | `xl:` | ≥1280px | `max-w-7xl` container = 1280px |
| Laptop | `lg:` | ≥1024px | Some layouts switch at this breakpoint |
| Tablet | `md:` | ≥768px | Primary mobile→tablet breakpoint |
| Small Tablet | `sm:` | ≥640px | Minor adjustments |
| Mobile | default | <640px | No prefix = base |

---

## 1. Navbar (`templates/includes/navbar.html`)

### Structure
- Desktop nav links (`hidden md:flex`, line 26) — visible ≥768px
- Mobile hamburger button (`md:hidden`, lines 106–142) — visible <768px
- Mobile dropdown menu (`#mobile-menu`, line 146) — toggled via JS, hidden by default

### Desktop (≥1280px)
- Layout correct: horizontal nav links, CTA buttons, user avatar dropdown
- `h-16 lg:h-20` (line 20): nav height increases at ≥1024px
- `text-2xl lg:text-3xl` brand (line 22): logo scales up at ≥1024px
- Admin alert bar uses `max-w-7xl mx-auto px-4 sm:px-6 lg:px-8` (line 5): padding scales correctly

### Laptop (1024–1279px)
- No issues — all desktop features present
- Brand text at `lg:text-3xl` renders at its full size

### Tablet (768–1023px)
- Desktop links (`hidden md:flex`) still visible — no collapse point for tablet
- `md:` breakpoint = 768px, so at 768px the nav is still in desktop mode
- At ~767px the hamburger appears and desktop links hide
- **Issue:** No intermediate tablet-friendly nav — the transition from full desktop to hamburger is abrupt

### Mobile (<768px)
- Hamburger menu (lines 106–142) rendered for all auth states
- Cart and voucher icons shown in mobile toolbar row alongside hamburger (lines 106–128)
- Mobile menu items (lines 147–172): full-width links, proper tap targets (~44px)
- **Issue:** Cart badge (`w-4.5 h-4.5` with `text-[10px]`, line 71, 121) has `min-w-[18px] min-h-[18px]` — just meets 44px? No, the badge is on an icon that's `w-5 h-5` (20px), well below 44px touch target
- **Issue:** User avatar (`w-7 h-7` = 28px, line 77) on desktop is below 44px touch target
- **Issue:** Close button in voucher panel (`w-8 h-8` = 32px, line 1070) below 44px touch target

### Remediation
- Consider a `lg:hdden md:flex` → `flex` for a condensed tablet nav layout
- Increase icon touch targets to ≥44px using `p-2` padding on small icons (adds ~16px around 28px icon)

---

## 2. Cards / Product Grid

### Product Card (`templates/includes/product_card.html`)
- **Fixed:**  `aspect-[4/5]` (line 3) — image container ratio, flex-grows
- Wishlist heart button: `w-9 h-9` (36px, line 35, 43) — **below 44px touch target**
- Badge text: `text-[11px]` (lines 19, 21) — small but acceptable for informational badges
- Price: `text-xl` (line 95) — readable
- CTA button: responsive width `w-full` (lines 111, 120, 128) — good, full-width on mobile
- Category label: `text-[11px]` (line 54) — very small, may fail WCAG AA (needs 4.5:1 contrast + min 12px for body text equivalents)
- Fragrance notes: `text-[10px]` (lines 60, 66, 74, 87) — **below minimum readable size**, fails WCAG AA

### Product Grid (assumed from `product_list.html`)
- Common pattern: `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4`
- Single column on mobile → 2 cols at small tablet → 3 cols on laptop → 4 cols on desktop

### Remediation
- Increase `text-[10px]` to `text-xs` (12px) for WCAG compliance
- Increase wishlist button from `w-9 h-9` to `w-11 h-11` (44px)
- Use `srcset` / `sizes` on product images to serve smaller files on mobile

---

## 3. Forms

### Login/Register (`apps/accounts/templates/accounts/login.html`)
- `w-full max-w-md` (line 753): centered card, max 448px — **perfect on mobile**
- `px-4 py-12` (line 752): safe horizontal padding on mobile
- Inputs: `w-full` (lines 779, 784) — full-width, good
- No responsive issues identified

### Checkout Form (`apps/orders/templates/orders/order_create.html`)
- Layout: `grid grid-cols-1 lg:grid-cols-3` (line 25) — stacks on mobile, 3-col on ≥1024px
- Form sections: `p-6 lg:p-8` (lines 39, 84, 111, 162) — padding scales up on laptop+
- Address cards grid: `grid grid-cols-1 md:grid-cols-2 gap-4` (line 49) — splits at ≥768px
- Region cascade selects: `grid grid-cols-1 md:grid-cols-4 gap-5` (line 129) — **4-column on md+ is too narrow for select dropdowns on tablet** (each column ~25% width with `gap-5`). Better to use 2-col on tablet, 4-col on lg+
- Submit button: `lg:hidden` mobile version (line 177) + `hidden lg:flex` sticky sidebar version (line 257) — **good**, avoids ghost tap on mobile

### Remediation
- Change address cascade grid: `grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5`

---

## 4. Checkout / Payment

### Checkout Page (`apps/orders/templates/orders/order_create.html`)
- Order summary sidebar (line 185): `sticky top-24` — works on desktop
- On mobile, summary is not visible without scrolling past long form
- **Issue:** No way to see order total while filling form on mobile without scrolling
- Mobile CTA (lines 177–182): fixed to bottom of the form section, not sticky to viewport

### Payment Page (`apps/payments/templates/payments/checkout.html`)
- Layout: `grid grid-cols-1 lg:grid-cols-5` (line 829) — 5-col spec: 3 for order/address + 2 for payment summary
- **Issue:** `lg:grid-cols-5` at 1024px means each column is ~205px — very narrow for the order items list
- Payment summary (line 889): `lg:col-span-2` — takes 40% width
- On mobile: single column stack, correct

### Remediation
- Change to `lg:grid-cols-3` or `lg:grid-cols-12` with `lg:col-span-7 lg:col-span-5`
- Add a sticky mobile order summary bar at the bottom

---

## 5. Cart (`apps/carts/templates/carts/cart_detail.html`)

### Desktop/Laptop (≥1024px)
- Layout: `grid grid-cols-1 lg:grid-cols-3` (line 326) — 2:1 ratio (items:summary)
- Cart items: `flex-col sm:flex-row` (line 330) — image stacked on mobile, side-by-side on ≥640px
- Quantity controls: `w-10 h-10` buttons (lines 372, 375) — 40px, **below 44px touch target**
- Item total price: `min-w-[7rem] text-right` (line 380) — 112px minimum width, necessary for IDR formatting

### Tablet (768–1023px)
- Still uses 2-column layout, but summary column is narrow (~256px) with 3 items + voucher form + CTA
- **Issue:** Voucher code input + button `flex gap-2` (line 463) may overflow on narrow sidebar

### Mobile (<768px)
- Single column stack — correct
- Item cards: `p-4` (line 329) — tight padding
- Quantity -/+ buttons at 40px touch target

### Remediation
- Increase quantity buttons to `w-11 h-11` (44px)
- On tablet, switch to single column at `md:` breakpoint instead of `lg:`

---

## 6. Customer Dashboard (`apps/accounts/templates/accounts/dashboard.html`)

### Desktop (≥1024px)
- KPI cards: `grid grid-cols-2 lg:grid-cols-4` (line 557) — 4 per row
- Voucher stats: `grid grid-cols-3` (line 612) — 3 per row, static
- Main layout: `grid grid-cols-1 lg:grid-cols-4` (line 655) — sidebar 1fr + content 3fr
- Order history: full-width in content area

### Tablet (768–1023px)
- KPI cards: `grid-cols-2` — 2 per row, correct
- Main layout: still single column (no `md:` grid-cols variant)
- Sidebar (`lg:col-span-1`, line 656) becomes part of the single column at <1024px
- **Issue:** Voucher stats grid stays at 3 columns on mobile (line 612) — very cramped on small screens

### Mobile (<768px)
- KPI cards: 2 per row — acceptable
- Voucher stats: `grid-cols-3` (line 612) — three cards at ~33% each with `gap-4` on a <640px screen means each card is very narrow (~160px on 360px screen)
- **Issue:** Text in KPI card stats `text-2xl` (lines 566, 579, 592, 605) may overflow in `p-5` card on narrow screens

### Remediation
- Add `sm:grid-cols-3` to voucher stats for mobile layout improvement, or use `xs:grid-cols-3`
- Ensure KPI cards use `truncate` or `text-balance` for long number values

---

## 7. Footer (`templates/includes/footer.html`)

### Desktop (≥1024px)
- Layout: `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12` (line 3) — 4 columns, correct
- Brand column: `lg:col-span-1` (line 4) — single column width

### Tablet (768–1023px)
- `md:grid-cols-2` — 2 columns, correct
- `gap-12` (48px) — generous spacing

### Mobile (<768px)
- Single column, correct
- Contact section with SVG icons + text (lines 44–56) — `flex items-center gap-3` — good layout
- Copyright bar: `flex-col sm:flex-row` (line 59) — stacks on mobile, correct

### No responsive issues identified

---

## 8. Images

### Pattern Across Templates
- **No `srcset` or `sizes` attributes** on any `<img>` tag — same resolution image served to all devices
- Examples: `product_card.html:6`, `cart_detail.html:334`, `order_create.html:194`, `checkout.html:849`, `admin/dashboard.html:240`
- Admin dashboard `rank-thumb` (line 240): `<img>` with no width/height attributes — CLS risk
- All product images use `class="w-full h-full object-cover"` with aspect ratio containers — OK for layout
- Cart item thumbnails: `w-full sm:w-24 h-24` (cart_detail.html:332) — full-width on mobile, 96px on desktop

### Remediation
- Add `srcset` and `sizes` attributes: `srcset="... 480w, ... 768w, ... 1200w" sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 25vw"`
- Add `width` and `height` attributes to admin dashboard product thumbnails
- Consider using `<picture>` element with WebP fallback

---

## 9. Overflow / Scroll

### Issues Found
- **Cart sidebar** (`cart_detail.html:407`): `truncate max-w-[180px]` on item name in summary — 180px may be too narrow on mobile sidebar
- **Admin dashboard comparison table** (admin/dashboard.html:358): `max-height:400px` with `overflow-y:auto` — correct
- **Admin dashboard timeline** (admin/dashboard.html:399): `max-height:480px` with `scroll-thin` — correct
- **Voucher floating panel** (`voucher_floating_panel.html:1077`): `overflow-y-auto` with `scrollbar-thin` on `max-w-md` panel — correct
- **Product card category/gender/family tags** (`product_card.html:58-92`): `flex flex-wrap gap-1.5` — correct wrapping behavior
- **No horizontal overflow** detected in any template on viewports ≥320px

### Remediation
- Change `max-w-[180px]` to `max-w-[50%]` or `max-w-[160px]` to be relative to parent width

---

## 10. Admin Dashboard (`templates/admin/dashboard.html`)

### Bootstrap-Class Hybrid Layout
- Admin dashboard uses **Jazzmin** (Bootstrap-based), not Tailwind, for its grid
- KPI cards: `col-xl-2 col-md-4 col-12` (lines 53, 63, 73, 83, 96, 106) — 6 per row on ≥1200px, 3 per row ≥768px, 1 per row on mobile
- Main chart + insights: `col-lg-8` + `col-lg-4` (lines 122, 143)
- Product performance + customer growth: `col-lg-6` + `col-lg-6` (lines 226, 263)
- Order status + summary: `col-lg-6` + `col-lg-6` (lines 282, 312)
- Order summary mini-grid: `col-3 col-md-3` (lines 320, 324, 328, 332)

### Responsive Assessment
- **Desktop (≥1200px):** All 6 KPI cards in 1 row — may be too cramped for longer currency values
- **Tablet (768–1199px):** 3 KPI cards per row — correct
- **Mobile (<768px):** Single column — correct
- **Issue:** KPI value `font-size:22px` (line 326, etc.) in order summary section may be large but acceptable
- **Issue:** No `max-width` constraint on the dashboard wrapper — content spans full browser width

### Remediation
- KPI cards on large screens: consider `col-xl-3 col-lg-4 col-md-6 col-12` instead of `col-xl-2`
- Add `mx-auto` with a max-width container to prevent over-stretching on ultra-wide screens

---

## Summary of Issues

| # | Severity | Component | Viewport | Issue | File:Line |
|---|----------|-----------|----------|-------|-----------|
| 1 | Medium | Product Card | All | `text-[10px]` on badges/notes fails WCAG AA | `product_card.html:60,66,74,87` |
| 2 | Low | Product Card | All | Wishlist button `w-9 h-9` (36px) below 44px touch target | `product_card.html:35,43` |
| 3 | Low | Navbar | Desktop | User avatar `w-7 h-7` (28px) below 44px touch target | `navbar.html:77` |
| 4 | Low | Navbar | All | Cart/voucher badge wrapper `w-5 h-5` (20px) below 44px | `navbar.html:67,107,116` |
| 5 | Medium | Checkout | Mobile | Order total not visible when filling long form | `order_create.html:177` |
| 6 | Low | Checkout | Tablet | Address cascade 4-col grid too narrow for select widgets | `order_create.html:129` |
| 7 | Low | Payment | Laptop | `lg:grid-cols-5` creates 205px columns at 1024px | `checkout.html:829` |
| 8 | Low | Cart | All | Quantity -/+ buttons `w-10 h-10` (40px) below 44px | `cart_detail.html:372,375` |
| 9 | Low | Customer Dashboard | Mobile | Voucher stats 3-column grid cramped on <640px | `dashboard.html:612` |
| 10 | Medium | All Images | All | No `srcset`/`sizes` — same image on all devices | All `<img>` tags |
| 11 | Low | Admin Dashboard | Desktop | 6 KPI cards in `col-xl-2` may overflow on 1280px | `admin/dashboard.html:53-115` |
| 12 | Low | Navbar | Tablet | No tablet-optimized nav — abrupt desktop→hamburger switch | `navbar.html:26,106` |

---

## Key Fix Priorities

1. **WCAG compliance:** Replace `text-[10px]` and `text-[11px]` with `text-xs` (12px) throughout product cards
2. **Touch targets:** Increase icon wrappers to ≥44px (use `p-3` or `w-11 h-11`)
3. **Image optimization:** Add `srcset`/`sizes` for responsive images
4. **Checkout UX:** Add sticky order total bar on mobile checkout
5. **Payment grid:** Replace `lg:grid-cols-5` with `lg:grid-cols-12` for more flexible column distribution
6. **Dashboard KPI:** Add `col-xl-3` fallback for 6-card row on narrower desktops
