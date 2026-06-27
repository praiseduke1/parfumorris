import os

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

FIXTURE_FILE = os.path.join(PROJECT_ROOT, 'data_export_utf8.json')
REFERENCE_FILE = os.path.join(PROJECT_ROOT, 'reference_data.json')
LEGACY_FILE = os.path.join(PROJECT_ROOT, 'data_export.json')


def get_table_count(table_name):
    with connection.cursor() as cursor:
        cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
        return cursor.fetchone()[0]


REFERENCE_TABLES = [
    'products_product',
    'products_category',
    'products_brand',
    'products_fragrancefamily',
    'regions_province',
    'regions_city',
    'regions_district',
    'regions_postalcode',
]

FULL_TABLES = REFERENCE_TABLES + [
    'orders_order',
    'auth_user',
]

IMPORTANT_TABLES = FULL_TABLES


class Command(BaseCommand):
    help = 'Restore production data from fixture files. Used during deploy via build_files.sh.'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Force restore even if data exists')

    def handle(self, *args, **options):
        force = options.get('force', False)

        tables_with_data = []
        for table in IMPORTANT_TABLES:
            try:
                cnt = get_table_count(table)
                if cnt > 0:
                    tables_with_data.append((table, cnt))
            except Exception:
                pass

        if tables_with_data and not force:
            self.stdout.write(self.style.WARNING(
                'Data already exists in database — use --force to restore anyway.'
            ))
            for table, cnt in tables_with_data:
                self.stdout.write(f'  {table}: {cnt} rows')
            self.stdout.write(self.style.WARNING('Skipping restore to preserve existing data.'))
            return

        # Try fixture files in priority order
        loaded = False
        for fpath, label in [
            (FIXTURE_FILE, 'full fixture'),
            (REFERENCE_FILE, 'reference data'),
            (LEGACY_FILE, 'legacy export'),
        ]:
            if os.path.exists(fpath):
                self.stdout.write(f'Loading {label}: {fpath} ...')
                try:
                    call_command('loaddata', fpath, verbosity=1)
                    self.stdout.write(self.style.SUCCESS(f'Data restored from {label}'))
                    loaded = True
                    break
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'{label} load failed: {e}'))

        if loaded:
            return

        # Fall back to seed commands
        self.stdout.write(self.style.WARNING('No data files found. Running seed commands...'))
        try:
            call_command('seed_admin')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'seed_admin: {e}'))

        try:
            call_command('seed_data')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'seed_data: {e}'))

        self.stdout.write(self.style.SUCCESS('Seed commands completed'))
