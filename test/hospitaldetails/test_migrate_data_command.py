from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone

from app.hospitaldetails.management.commands.migrate_data import Command
from app.hospitaldetails.models import (
    FindingAids,
    FindingAidsLocation,
    Post1948Status,
    Post1948Type,
    Pre1948Status,
    Pre1948Type,
    Pre1974County,
)


class MigrateDataCommandHelperTestCase(TestCase):
    def setUp(self):
        self.command = Command()

    def test_handle_raises_for_missing_required_connection_parameters(self):
        with self.assertRaises(CommandError) as exc:
            self.command.handle(
                host=None,
                port=1433,
                database=None,
                user=None,
                password=None,
                dry_run=True,
                clear=False,
            )

        self.assertIn("Missing required parameters", str(exc.exception))

    def test_prepare_timestamps_makes_naive_values_timezone_aware(self):
        created = datetime(2020, 1, 1, 10, 0, 0)
        updated = datetime(2021, 1, 1, 10, 0, 0)

        timestamps = self.command.prepare_timestamps(created, updated)

        self.assertTrue(timezone.is_aware(timestamps["created_at"]))
        self.assertTrue(timezone.is_aware(timestamps["last_updated_at"]))
        self.assertEqual(timestamps["created_at"].year, 2020)
        self.assertEqual(timestamps["last_updated_at"].year, 2021)

    def test_prepare_timestamps_uses_last_updated_when_created_missing(self):
        updated = datetime(2021, 1, 1, 10, 0, 0)

        timestamps = self.command.prepare_timestamps(None, updated)

        self.assertEqual(timestamps["created_at"].year, 2021)
        self.assertEqual(timestamps["last_updated_at"].year, 2021)

    def test_set_foreign_key_if_valid_handles_valid_skipped_and_missing_ids(self):
        county = Pre1974County.objects.create(id=10, name="Yorkshire")
        target = SimpleNamespace()

        self.command.set_foreign_key_if_valid(
            target,
            "pre_1974_county_id",
            county.id,
            Pre1974County,
            "County",
        )
        self.assertEqual(target.pre_1974_county_id, county.id)

        self.command.set_foreign_key_if_valid(
            target,
            "pre_1974_county_id",
            1,
            Pre1974County,
            "County",
        )
        self.assertIsNone(target.pre_1974_county_id)

        self.command.set_foreign_key_if_valid(
            target,
            "pre_1974_county_id",
            999,
            Pre1974County,
            "County",
        )
        self.assertIsNone(target.pre_1974_county_id)

    def test_migrate_lookup_table_dry_run_does_not_write_records(self):
        cursor = MagicMock()
        cursor.fetchall.return_value = [
            {"CountyPre74ID": 100, "CountyPre74": "Dry Run County"}
        ]

        self.command.migrate_lookup_table(
            cursor,
            dry_run=True,
            config={
                "label": "Pre-1974 Counties",
                "query": "SELECT CountyPre74ID, CountyPre74 FROM dbo.tblRefCountyPre74",
                "id_field": "CountyPre74ID",
                "name_field": "CountyPre74",
                "model": Pre1974County,
            },
        )

        self.assertEqual(Pre1974County.objects.count(), 0)

    def test_populate_lookup_tables_is_idempotent(self):
        self.command.populate_lookup_tables()
        first_counts = {
            "pre_status": Pre1948Status.objects.count(),
            "post_status": Post1948Status.objects.count(),
            "pre_type": Pre1948Type.objects.count(),
            "post_type": Post1948Type.objects.count(),
            "finding_aids": FindingAids.objects.count(),
            "finding_aids_location": FindingAidsLocation.objects.count(),
        }

        self.command.populate_lookup_tables()
        second_counts = {
            "pre_status": Pre1948Status.objects.count(),
            "post_status": Post1948Status.objects.count(),
            "pre_type": Pre1948Type.objects.count(),
            "post_type": Post1948Type.objects.count(),
            "finding_aids": FindingAids.objects.count(),
            "finding_aids_location": FindingAidsLocation.objects.count(),
        }

        self.assertEqual(first_counts, second_counts)
