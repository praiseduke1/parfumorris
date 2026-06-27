"""
Re-import complete Indonesian regions data from open-source reference dataset.

This command fetches district and postal code data from the ibnux/data-indonesia
repository (https://github.com/ibnux/data-indonesia), which provides comprehensive
administrative divisions for all 38 provinces of Indonesia.

Usage:
    python manage.py reimport_regions
    python manage.py reimport_regions --provinces=51,32,33  (specific provinces only)

The command is idempotent — it uses update_or_create and will not duplicate data.
Existing user data (CustomerAddress, Order) is preserved because all FK references
are based on the 'code' field which remains stable across import runs.
"""

import json
import logging
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.regions.models import City, District, PostalCode

logger = logging.getLogger(__name__)

BASE_URL = 'https://ibnux.github.io/data-indonesia/kecamatan'
MAX_WORKERS = 10
TIMEOUT = 15


class Command(BaseCommand):
    help = 'Re-import complete Indonesian regions data from open-source reference'

    def add_arguments(self, parser):
        parser.add_argument(
            '--provinces',
            type=str,
            default='',
            help='Comma-separated list of province codes to import (default: all)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Fetch and display counts without writing to database',
        )

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        province_filter = options.get('provinces', '')

        city_qs = City.objects.all()
        if province_filter:
            codes = [c.strip() for c in province_filter.split(',')]
            city_qs = city_qs.filter(province__code__in=codes)

        total_cities = city_qs.count()
        self.stdout.write(f'Fetching districts for {total_cities} cities ...')

        results = {'created': 0, 'updated': 0, 'skipped': 0, 'errors': 0}
        city_batches = list(city_qs.values_list('code', 'id', 'name'))

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_map = {
                executor.submit(self._fetch_districts, code): (code, city_id, name)
                for code, city_id, name in city_batches
            }

            for future in as_completed(future_map):
                code, city_id, name = future_map[future]
                try:
                    district_list = future.result()
                except Exception as e:
                    self.stderr.write(self.style.ERROR(
                        f'  ERR {code} {name}: {e}'
                    ))
                    results['errors'] += 1
                    continue

                if district_list is None:
                    results['skipped'] += 1
                    continue

                if not self.dry_run:
                    created, updated = self._save_districts(city_id, district_list)
                    results['created'] += created
                    results['updated'] += updated

                self.stdout.write(self.style.SUCCESS(
                    f'  OK  {code} {name}: {len(district_list)} districts'
                ))

        self._print_summary(results)

    def _fetch_districts(self, city_code):
        url = f'{BASE_URL}/{city_code}.json'
        req = urllib.request.Request(url, headers={'User-Agent': 'ParfuMoray/1.0'})
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                return data
        except urllib.error.HTTPError as e:
            if e.code == 404:
                logger.warning('No district data for city %s (404)', city_code)
                return []
            raise
        except (urllib.error.URLError, json.JSONDecodeError) as e:
            raise CommandError(str(e))

    @transaction.atomic
    def _save_districts(self, city_id, district_list):
        created_count = 0
        updated_count = 0

        for item in district_list:
            district_code = str(item['id'])
            district_name = str(item['nama']).strip()

            district, created = District.objects.update_or_create(
                code=district_code,
                defaults={
                    'city_id': city_id,
                    'name': district_name,
                },
            )
            if created:
                created_count += 1
            else:
                # Ensure FK is correct even if it was previously wrong
                if district.city_id != city_id:
                    district.city_id = city_id
                    district.save(update_fields=['city_id'])
                updated_count += 1

        return created_count, updated_count

    def _print_summary(self, results):
        self.stdout.write()
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS(
            f'Districts: {results["created"]} created, '
            f'{results["updated"]} updated, '
            f'{results["skipped"]} skipped, '
            f'{results["errors"]} errors'
        ))

        if not self.dry_run:
            from apps.regions.models import District
            total = District.objects.count()
            self.stdout.write(self.style.SUCCESS(f'Total districts in DB: {total}'))
