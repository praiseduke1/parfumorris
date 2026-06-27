"""
Re-import complete Indonesian postal code data from open-source dataset.

Data source: https://github.com/detanaputra/KodePosIndonesia
This provides kelurahan-level postal codes which are grouped by kecamatan
and imported into our PostalCode model (FK to District).

Strategy:
1. Download province.csv, city.csv, district.csv, subdistrict.csv
2. Group subdistricts by district_id -> set of postal codes
3. Build (province, city, district) -> postal_codes mapping
4. Fuzzy-match names against our database
5. Idempotent import via update_or_create
"""

import csv
import io
import logging
import re
import urllib.request
from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.regions.models import District, PostalCode

logger = logging.getLogger(__name__)

BASE_URL = 'https://raw.githubusercontent.com/detanaputra/KodePosIndonesia/master/KodePosIndonesia/contentFiles'
TIMEOUT = 30


def _normalize(name):
    """Normalize a name for matching: lowercase, strip, remove common prefixes."""
    name = name.strip().lower()
    name = re.sub(r'^(kab\.|kota)\s+', '', name)
    name = re.sub(r'\s+', ' ', name)
    return name


def _normalize_for_match(name):
    """Aggressively normalize for fuzzy matching."""
    n = name.lower().strip()
    n = re.sub(r'^(kab\.|kota)\s+', '', n)
    n = re.sub(r'\s+', ' ', n)
    n = re.sub(r'\s*\(.*?\)\s*', '', n).strip()  # strip parenthesized alternatives
    n = re.sub(r'\s*-\s*(kota|kab)\s*$', '', n).strip()  # strip - kota/kab suffix
    n = re.sub(r'[^a-z0-9\s]', '', n)  # remove remaining punctuation
    n = re.sub(r'\s+', ' ', n).strip()
    return n


# Province name aliases: CSV _normalize_for_match name -> DB _normalize name
# Needed where the two datasets use fundamentally different names for the same province.
PROVINCE_ALIASES = {
    'nanggroe aceh darussalam': 'aceh',
    'bangka belitung': 'kepulauan bangka belitung',
}


def _flatten(name):
    """Remove all spaces from a name."""
    return name.replace(' ', '')


def _match_district(csv_d_norm, our_districts):
    """Try to match a CSV district name against our database districts.

    Returns district_id or None.
    """
    # 1. Exact match
    for did, dn in our_districts:
        if dn == csv_d_norm:
            return did

    # 2. Fuzzy-normalize match
    csv_fuzzy = _normalize_for_match(csv_d_norm)
    for did, dn in our_districts:
        dn_fuzzy = _normalize_for_match(dn)
        if dn_fuzzy == csv_fuzzy:
            return did

    # 3. Space-stripped match
    csv_flat = _flatten(csv_fuzzy)
    for did, dn in our_districts:
        dn_flat = _flatten(_normalize_for_match(dn))
        if csv_flat == dn_flat:
            return did

    # 4. Containment match
    for did, dn in our_districts:
        dn_fuzzy = _normalize_for_match(dn)
        dn_flat = _flatten(dn_fuzzy)
        if csv_fuzzy and (csv_fuzzy in dn_fuzzy or dn_fuzzy in csv_fuzzy
                          or csv_flat in dn_flat or dn_flat in csv_flat):
            return did

    return None


def _match_city_fallback(csv_c_norm, our_cities_flat):
    """Try to match a CSV city name against our database cities (flattened)."""
    csv_flat = _flatten(csv_c_norm)
    return our_cities_flat.get(csv_flat)


def _fetch_csv(filename):
    url = f'{BASE_URL}/{filename}'
    req = urllib.request.Request(url, headers={'User-Agent': 'ParfuMoray/1.0'})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        raw = resp.read()
        text = raw.decode('utf-8-sig')
    reader = csv.DictReader(io.StringIO(text))
    return list(reader)


class Command(BaseCommand):
    help = 'Re-import complete Indonesian postal codes from open-source dataset'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Count matches without writing to database',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write('Downloading CSV files ...')
        provinces = _fetch_csv('province.csv')
        cities = _fetch_csv('city.csv')
        districts_csv = _fetch_csv('district.csv')
        subdistricts = _fetch_csv('subdistrict.csv')
        self.stdout.write(
            f'  provinces={len(provinces)} cities={len(cities)} '
            f'districts={len(districts_csv)} subdistricts={len(subdistricts)}'
        )

        # Build lookup: prov_id -> name
        prov_map = {
            int(p['Id']): _normalize(p['Name'])
            for p in provinces
        }
        # Build lookup: city_id -> (name, prov_id)
        city_map = {}
        for c in cities:
            city_map[int(c['Id'])] = (_normalize(c['Name']), int(c['ProvinceId']))
        # Build lookup: district_id -> (name, city_id)
        dist_map = {}
        for d in districts_csv:
            dist_map[int(d['Id'])] = (_normalize(d['Name']), int(d['CityId']))

        # Group subdistricts: district_id -> set of postal codes
        dist_postal_codes = defaultdict(set)
        for s in subdistricts:
            dist_id = int(s['DistrictId'])
            pc = s['PostalCode'].strip()
            if pc:
                dist_postal_codes[dist_id].add(pc)

        self.stdout.write(f'  Districts with postal code data: {len(dist_postal_codes)}')

        # Build (province_name, city_name, district_name) -> postal_codes
        data_map = {}  # (prov_norm, city_norm, dist_norm) -> set of postal codes
        for dist_id, pcs in dist_postal_codes.items():
            dist_name, city_id = dist_map.get(dist_id, (None, None))
            if city_id is None:
                continue
            city_name, prov_id = city_map.get(city_id, (None, None))
            if prov_id is None:
                continue
            prov_name = prov_map.get(prov_id)
            if not all([prov_name, city_name, dist_name]):
                continue
            key = (prov_name, city_name, dist_name)
            data_map[key] = pcs

        self.stdout.write(f'  Unique (prov,city,dist) keys in source: {len(data_map)}')

        # Match against our database
        # We need to match by province name -> city name -> district name
        from apps.regions.models import Province

        matched = 0
        not_matched = 0
        pcs_created = 0
        pcs_updated = 0

        # Build lookup of our districts by normalized names
        our_db = {}  # (prov_norm, city_norm) -> list of (district_id, dist_norm)
        our_cities_flat = {}  # flattened city_norm -> (prov_norm, city_norm)
        for d in District.objects.select_related('city__province').all():
            p_norm = _normalize(d.city.province.name)
            c_norm = _normalize(d.city.name)
            d_norm = _normalize(d.name)
            our_db.setdefault((p_norm, c_norm), []).append((d.id, d_norm))
            c_flat = _flatten(c_norm)
            if c_flat not in our_cities_flat:
                our_cities_flat[c_flat] = (p_norm, c_norm)

        for (p_norm, c_norm, d_norm), pcs in data_map.items():
            # Resolve province name via fuzzy match + aliases
            p_resolved = _normalize_for_match(p_norm)
            if p_resolved in PROVINCE_ALIASES:
                p_resolved = PROVINCE_ALIASES[p_resolved]

            matches = our_db.get((p_resolved, c_norm), [])

            if not matches:
                # Try city-level fallback (flattened name lookup)
                city_match = _match_city_fallback(c_norm, our_cities_flat)
                if city_match:
                    matches = our_db.get(city_match, [])

            found_id = _match_district(d_norm, matches) if not dry_run else None

            if dry_run:
                if _match_district(d_norm, matches):
                    matched += 1
                else:
                    not_matched += 1
                    if not_matched <= 10:
                        self.stdout.write(self.style.WARNING(
                            f'  NO MATCH: {p_norm}/{c_norm}/{d_norm}'
                        ))
                continue

            if found_id is None:
                not_matched += 1
                if not_matched <= 10:
                    self.stdout.write(self.style.WARNING(
                        f'  NO MATCH: {p_norm}/{c_norm}/{d_norm}'
                    ))
                continue

            matched += 1
            for pc_code in pcs:
                _, created = PostalCode.objects.update_or_create(
                    district_id=found_id,
                    code=pc_code,
                    defaults={'district_id': found_id},
                )
                if created:
                    pcs_created += 1
                else:
                    pcs_updated += 1

        self.stdout.write()
        self.stdout.write(self.style.SUCCESS('=' * 50))
        if dry_run:
            self.stdout.write(
                f'Matched: {matched} districts, '
                f'Not matched in DB: {not_matched}'
            )
            self.stdout.write(self.style.WARNING('Dry run — no changes'))
        else:
            self.stdout.write(
                f'Matched: {matched} districts, '
                f'Not matched: {not_matched}'
            )
            self.stdout.write(
                f'Postal codes created: {pcs_created}, '
                f'updated: {pcs_updated}'
            )
            total = PostalCode.objects.count()
            self.stdout.write(f'Total postal codes in DB: {total}')
