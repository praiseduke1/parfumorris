# Address Module — Black-Box Test Report

**Date:** 2026-06-26  
**Test file:** `tests_address.py`  
**Total tests:** 94  
**Passed:** 94  
**Failed:** 0  
**Duration:** 64.99s  

---

## Test Groups

| Group | Tests | Description |
|---|---|---|
| `TestRegionApiProvince` | 4 | Province list API, ordering, format, 38 provinces |
| `TestRegionApiCity` | 6 | City API by province, missing/invalid params, FK, uniqueness |
| `TestRegionApiDistrict` | 6 | District API by city, missing/invalid params, FK, uniqueness |
| `TestRegionApiPostalCode` | 7 | Postal code API by district, missing/non-numeric/invalid params, FK |
| `TestAddressAccessControl` | 10 | Login required for list/create/edit/delete/set_default |
| `TestAddressCreate` | 10 | CRUD create — success, null regions, default, validation |
| `TestAddressEdit` | 6 | CRUD edit — success, permissions, prefills, field preservation |
| `TestAddressDelete` | 4 | CRUD delete — success, permissions, isolation |
| `TestAddressDefault` | 5 | Default address — set, unset, model save, ordering, permissions |
| `TestAddressList` | 6 | List — empty, own addresses, default badge, action buttons |
| `TestAddressFormValidation` | 12 | Form validation — cascade, label choices, required fields |
| `TestAddressRtRw` | 3 | RT/RW — max 4 chars, optional fields |
| `TestAddressCascadeIntegrity` | 4 | Cascade — PROTECT on regions with addresses, CASCADE without |
| `TestAddressOrdering` | 2 | Ordering — default first, newest first |
| `TestSeedDataCoverage` | 4 | Seed data — 38 provinces, DKI Jakarta cities, cascade depth |
| `TestAddressEdgeCases` | 5 | Edge cases — long address, phone formatting, label choices, str |

---

## Region API — Cascade Endpoint Verification

All four cascade endpoints return JSON with `id`, `code`, and `name` fields, ordered alphabetically by name.

### Province API (`/api/regions/provinces/`)

| Endpoint | Valid Request | 200 | `id`/`code`/`name` present |
|---|---|---|---|
| `regions:api_provinces` | `GET` | ✅ | ✅ |

### City API (`/api/regions/cities/`)

| Scenario | Expected | Actual |
|---|---|---|
| `?province_id=<valid>` | 200 + JSON array | ✅ |
| No params | 400 + error | ✅ |
| `?province_id=99999` | 200 + `[]` | ✅ |
| City FK references correct province | — | ✅ |
| City code unique | Constraint enforced | ✅ |
| City code starts with province code | — | ✅ |

### District API (`/api/regions/districts/`)

| Scenario | Expected | Actual |
|---|---|---|
| `?city_id=<valid>` | 200 + JSON array | ✅ |
| No params | 400 | ✅ |
| `?city_id=99999` | 200 + `[]` | ✅ |
| District FK references correct city | — | ✅ |
| District code unique | Constraint enforced | ✅ |
| District code starts with city code | — | ✅ |

### Postal Code API (`/api/regions/postal_code/`)

| Scenario | Expected | Actual |
|---|---|---|
| `?district_id=<valid>` | 200 + JSON array | ✅ |
| No params | 400 | ✅ |
| `?district_id=abc` | 400 | ✅ |
| `?district_id=99999` | 200 + `[]` | ✅ |
| Postal code FK references correct district | — | ✅ |
| Multiple codes per district | Allowed | ✅ |
| 5-digit numeric format | — | ✅ |

---

## Cascade Integrity Verification

| Relationship | FK on Child | `on_delete` | Protected by address? | Test |
|---|---|---|---|---|
| Province ← City | `City.province` | `CASCADE` | No (direct test uses City.delete) | ✅ CASCADE deletes districts and postal codes |
| City ← District | `District.city` | `CASCADE` | N/A | ✅ |
| District ← PostalCode | `PostalCode.district` | `CASCADE` | N/A | ✅ |
| Province → CustomerAddress | `CustomerAddress.province` | `PROTECT` | ✅ Cannot delete with addresses | ✅ |
| City → CustomerAddress | `CustomerAddress.city` | `PROTECT` | ✅ Cannot delete with addresses | ✅ |
| Province without addresses | — | — | ✅ Can delete | ✅ |

**Key finding:** Region-to-region FK uses `CASCADE`; region-to-address FK uses `PROTECT`. A province or city with any associated address cannot be deleted.

---

## Form Validation Details

| Validation Rule | Test | Status |
|---|---|---|
| Valid cascade (all 4 levels match) | `test_valid_cascade` | ✅ |
| City must belong to selected province | `test_city_not_in_province` | ✅ |
| District must belong to selected city | `test_district_not_in_city` | ✅ |
| Postal code must belong to selected district | `test_postal_code_not_in_district` | ✅ |
| Missing region fields (all nullable) | `test_missing_all_region_fields` | ✅ |
| Missing required fields (name, phone, address) | `test_missing_required_fields` | ✅ |
| Label must be one of choices | `test_label_choices` | ✅ |
| Address line ≥ 15 chars | `test_address_line_min_15_chars` | ✅ |
| Phone ≥ 10 digits | `test_phone_10_digits_minimum` | ✅ |
| Phone must start with 08 | `test_phone_must_start_with_08` | ✅ |
| City queryset filtered by province | `test_city_queryset_filtered_by_province` | ✅ |
| District queryset filtered by city | `test_district_queryset_filtered_by_city` | ✅ |
| Postal code queryset filtered by district | `test_postal_code_queryset_filtered_by_district` | ✅ |
| RT max 4 chars | `test_rt_max_4_chars` | ✅ |
| RW max 4 chars | `test_rw_max_4_chars` | ✅ |
| RT/RW optional (blank) | `test_rt_rw_optional` | ✅ |

---

## Bugs Found & Fixed

### ADR-01: Label field missing `choices` constraint

- **Severity:** Medium
- **File:** `apps/accounts/models.py:179`
- **Description:** The `label` field defines `LABEL_CHOICES` at the class level but does not pass `choices=LABEL_CHOICES` to the `CharField`. The form widget uses a `<select>` with these choices for UI, but there is no model-level or form-level validation. A POST with label `'INVALID'` would be silently accepted.
- **Fix:** Added `choices=LABEL_CHOICES` to the field definition.
- **Migration:** `apps/accounts/migrations/0010_add_label_choices.py` created.

### ADR-02: RT/RW tests had incorrect assertions (test bug, not code bug)

- **Severity:** Low
- **File:** `tests_address.py:795-821`
- **Description:** `test_rt_max_4_chars` and `test_rw_max_4_chars` sent 5-character values but asserted `resp.status_code == 302` (expecting success). Django's `ModelForm` correctly enforces `max_length=4` at the form level, so the form returns 200 with validation errors.
- **Fix:** Changed assertions to expect `200` and verify the field appears in `resp.context['form'].errors`.

---

## Seed Data Coverage

| Data | Test | Status |
|---|---|---|
| 38 Indonesian provinces with unique codes | `test_all_38_provinces_have_unique_codes` | ✅ |
| DKI Jakarta has 6 cities | `test_dki_jakarta_has_6_cities` | ✅ |
| Each province can have cities | `test_each_province_has_at_least_one_city` | ✅ |
| 4-level cascade (Province → City → District → PostalCode) | `test_cascade_depth` | ✅ |

---

## Access Control Summary

| Action | Unauthenticated | Admin (staff) |
|---|---|---|
| View address list | 302 redirect | 302 redirect |
| Create address | 302 redirect | 302 redirect |
| Edit address | 302 redirect | 302 redirect |
| Delete address | 302 redirect | 302 redirect |
| Set default | 302 redirect | 302 redirect |
| Edit another user's address | 404 | 404 |
| Delete another user's address | 404 | 404 |
| Set default on another user's address | 404 | 404 |

---

## Edge Cases

| Scenario | Status |
|---|---|
| Very long address line (500+ chars) | ✅ Accepted |
| Phone with formatting `(0812) 3456-7890` | ✅ Accepted (digits validated) |
| All valid label choices | ✅ Each accepted |
| Address `__str__` with label | ✅ Contains recipient name and label |
| Address `__str__` without label | ✅ Falls back to 'Alamat' |
| Empty address list | ✅ 200 with content |
| Multiple addresses (5) | ✅ All created |
| Phone too short under 10 digits | ✅ Rejected |
| Phone not starting with 08 | ✅ Rejected |
| Address line shorter than 15 chars | ✅ Rejected |
