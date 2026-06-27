"""
Clean up duplicate districts created by the reimport process.

Strategy:
1. Find duplicate district names per city (old 7-char code + new 6-char BPS code)
2. Keep the new BPS-coded district (shorter code)
3. Reassign any postal codes from the old district to the new district
4. Update any CustomerAddress references from old district to new district
5. Delete the old district
"""

import logging

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count

from apps.accounts.models import CustomerAddress
from apps.regions.models import District, PostalCode

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Remove duplicate districts, migrating postal codes to the correct district'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without actually changing',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        dupes = (
            District.objects.values('city_id', 'name')
            .annotate(cnt=Count('id'))
            .filter(cnt__gt=1)
        )

        self.stdout.write(f'Found {dupes.count()} duplicate district names\n')

        migrated_pc = 0
        updated_addr = 0
        deleted = 0
        would_migrate_pc = 0
        would_update_addr = 0
        would_delete = 0

        for dup in dupes:
            districts = list(
                District.objects.filter(city_id=dup['city_id'], name=dup['name']).order_by('code')
            )
            districts.sort(key=lambda d: len(d.code))
            keep = districts[0]

            for old in districts[1:]:
                # Handle postal codes
                pcs = PostalCode.objects.filter(district=old)
                pc_count = pcs.count()
                if pc_count:
                    if dry_run:
                        would_migrate_pc += pc_count
                    else:
                        pcs.update(district=keep)
                        migrated_pc += pc_count
                    self._log('MIGRATE', pc_count, 'postal codes', old, keep, dry_run)

                # Handle CustomerAddress references
                addrs = CustomerAddress.objects.filter(district=old)
                addr_count = addrs.count()
                if addr_count:
                    if dry_run:
                        would_update_addr += addr_count
                    else:
                        addrs.update(district=keep)
                        updated_addr += addr_count
                    self._log('REPOINT', addr_count, 'CustomerAddress', old, keep, dry_run)

                # Delete old district
                if dry_run:
                    would_delete += 1
                    self.stdout.write(f'  WOULD DELETE: {old.code}/{old.name} (keep: {keep.code})')
                else:
                    old.delete()
                    deleted += 1

        self.stdout.write()
        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'WOULD migrate {would_migrate_pc} postal codes, '
                f'repoint {would_update_addr} addresses, '
                f'delete {would_delete} old districts'
            ))
            self.stdout.write(self.style.WARNING('Dry run — no changes made'))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'Migrated {migrated_pc} postal codes, '
                f'repointed {updated_addr} addresses, '
                f'deleted {deleted} old districts'
            ))
            remaining = District.objects.count()
            self.stdout.write(self.style.SUCCESS(f'Districts remaining: {remaining}'))

    def _log(self, action, count, obj, old, keep, dry_run):
        prefix = 'WOULD' if dry_run else ''
        self.stdout.write(
            f'  {prefix}{action} {count} {obj}: {old.code}/{old.name} -> {keep.code}'
        )
