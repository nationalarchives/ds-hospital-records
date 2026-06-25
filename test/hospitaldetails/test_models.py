import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase

from app.hospitaldetails.models import Hospital, RecordsInfo, Repository


class HospitalModelTestCase(TestCase):
    def test_full_address_omits_empty_parts(self):
        hospital = Hospital.objects.create(
            name="Address General",
            street_1="1 Main Street",
            town="York",
            postcode="YO1 1AA",
        )

        self.assertEqual(hospital.full_address, "1 Main Street, York, YO1 1AA")

    def test_str_returns_name(self):
        hospital = Hospital.objects.create(name="Name General")
        self.assertEqual(str(hospital), "Name General")

    def test_full_clean_rejects_year_before_minimum(self):
        hospital = Hospital(name="Old General", foundation_year=999)

        with self.assertRaises(ValidationError):
            hospital.full_clean()

    def test_full_clean_rejects_year_after_current_year(self):
        hospital = Hospital(
            name="Future General",
            foundation_year=datetime.date.today().year + 1,
        )

        with self.assertRaises(ValidationError):
            hospital.full_clean()


class RepositoryModelTestCase(TestCase):
    def test_full_address_omits_empty_parts(self):
        repository = Repository.objects.create(
            name="City Archives",
            street_1="2 Archive Road",
            county="West Yorkshire",
            postcode="LS1 1AA",
        )

        self.assertEqual(
            repository.full_address,
            "2 Archive Road, West Yorkshire, LS1 1AA",
        )

    def test_archon_url_returns_none_when_no_archon_code(self):
        repository = Repository.objects.create(name="Local Archive")
        self.assertIsNone(repository.archon_url)

    def test_archon_url_returns_expected_url_when_archon_code_present(self):
        repository = Repository.objects.create(name="Archive", archon_code=1234)
        self.assertEqual(
            repository.archon_url,
            "https://discovery.nationalarchives.gov.uk/details/a?_ref=1234",
        )

    def test_str_returns_name(self):
        repository = Repository.objects.create(name="County Archive")
        self.assertEqual(str(repository), "County Archive")


class RecordsInfoModelTestCase(TestCase):
    def test_str_uses_hospital_and_repository_name(self):
        hospital = Hospital.objects.create(name="Str General")
        repository = Repository.objects.create(name="Str Repository")
        record = RecordsInfo.objects.create(hospital=hospital, repository=repository)

        self.assertEqual(
            str(record),
            "Records Info for Str General at Str Repository",
        )
