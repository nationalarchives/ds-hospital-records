from django.test import TestCase
from django.urls import reverse

from app.hospitaldetails.models import Hospital, RecordsInfo, Repository
from app.hospitaldetails.views import (
    _build_page_numbers,
    decode_search_params,
    encode_search_params,
)


class HospitalDetailsViewHelpersTestCase(TestCase):
    def test_build_page_numbers_collapses_middle_with_ellipsis(self):
        page_numbers = _build_page_numbers(current_page=6, total_pages=12)
        self.assertEqual(page_numbers, [1, None, 5, 6, 7, None, 12])

    def test_encode_and_decode_search_params_roundtrip(self):
        original = {"q": "North General", "page": 2}

        encoded = encode_search_params(original)
        decoded = decode_search_params(encoded)

        self.assertEqual(decoded, original)

    def test_decode_search_params_invalid_hash_returns_empty_dict(self):
        self.assertEqual(decode_search_params("not-valid"), {})


class HospitalHomeViewTestCase(TestCase):
    def test_home_page_renders(self):
        response = self.client.get(reverse("hospitaldetails:home_page"))
        self.assertContains(response, "Hospital records", status_code=200)
        self.assertContains(response, reverse("hospitaldetails:search"))


class HospitalDetailViewTestCase(TestCase):
    def setUp(self):
        self.hospital = Hospital.objects.create(name="North Infirmary", town="Leeds")

    def test_hospital_detail_defaults_back_link_to_search(self):
        response = self.client.get(
            reverse("hospitaldetails:hospital_detail", kwargs={"id": self.hospital.id})
        )

        self.assertContains(response, "Back to search results page", status_code=200)
        self.assertContains(response, reverse("hospitaldetails:search"))

    def test_hospital_detail_uses_legacy_query_and_page_back_link(self):
        response = self.client.get(
            reverse("hospitaldetails:hospital_detail", kwargs={"id": self.hospital.id}),
            {"q": "north", "page": "2"},
        )

        self.assertContains(response, "?q=north&amp;page=2")

    def test_hospital_detail_prefers_encoded_search_hash_for_back_link(self):
        search_hash = encode_search_params({"q": "north", "page": 3})

        response = self.client.get(
            reverse("hospitaldetails:hospital_detail", kwargs={"id": self.hospital.id}),
            {"search": search_hash, "q": "ignored", "page": "99"},
        )

        self.assertContains(response, "?page=3&amp;q=north")
        self.assertNotContains(response, "?q=ignored&amp;page=99")

    def test_hospital_detail_includes_related_record_locations(self):
        repository = Repository.objects.create(name="Leeds City Archives")
        RecordsInfo.objects.create(
            hospital=self.hospital,
            repository=repository,
            repository_code="LCA/1",
        )

        response = self.client.get(
            reverse("hospitaldetails:hospital_detail", kwargs={"id": self.hospital.id})
        )

        self.assertContains(response, "Record locations")
        self.assertContains(response, "Leeds City Archives")


class RepositoryDetailViewTestCase(TestCase):
    def test_repository_detail_redirects_to_archon_url_when_available(self):
        repository = Repository.objects.create(
            name="National Archive", archon_code=1234
        )

        response = self.client.get(
            reverse("hospitaldetails:repository_detail", kwargs={"id": repository.id})
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            "https://discovery.nationalarchives.gov.uk/details/a?_ref=1234",
        )

    def test_repository_detail_renders_local_page_and_records_when_no_archon_code(self):
        repository = Repository.objects.create(name="Local Studies Library")
        hospital = Hospital.objects.create(name="South Hospital")
        RecordsInfo.objects.create(
            hospital=hospital,
            repository=repository,
            administrative_start=1900,
            administrative_finish=1920,
            records_notes="Bound admission ledgers",
        )

        response = self.client.get(
            reverse("hospitaldetails:repository_detail", kwargs={"id": repository.id})
        )

        self.assertContains(response, "Local Studies Library", status_code=200)
        self.assertContains(response, "Hospital Records Held")
        self.assertContains(response, "South Hospital")
        self.assertContains(response, "Administrative")
        self.assertContains(response, "1900 - 1920")
        self.assertContains(response, "Bound admission ledgers")


class SearchPaginationViewTestCase(TestCase):
    def test_search_second_page_has_results_and_hash(self):
        for i in range(1, 12):
            Hospital.objects.create(name=f"General Hospital {i}")

        response = self.client.get(
            reverse("hospitaldetails:search"), {"q": "general", "page": 2}
        )

        self.assertContains(response, "Search Results", status_code=200)
        self.assertContains(response, "Found 11 hospitals")
        self.assertContains(response, "Showing 11-11 of 11")
        self.assertContains(response, "page=2")

    def test_search_results_link_to_detail_with_search_hash(self):
        hospital = Hospital.objects.create(name="Western General")

        response = self.client.get(reverse("hospitaldetails:search"), {"q": "western"})
        detail_url = reverse(
            "hospitaldetails:hospital_detail", kwargs={"id": hospital.id}
        )

        self.assertContains(response, detail_url + "?search=")


class SearchEdgeCasesViewTestCase(TestCase):
    def setUp(self):
        self.search_url = reverse("hospitaldetails:search")

    def test_search_whitespace_query_behaves_like_empty_query(self):
        response = self.client.get(self.search_url, {"q": "    "})

        self.assertContains(response, "Search Hospitals", status_code=200)
        self.assertNotContains(response, "Search Results")

    def test_search_page_not_a_number_falls_back_to_first_page(self):
        for i in range(1, 12):
            Hospital.objects.create(name=f"City Hospital {i}")

        response = self.client.get(self.search_url, {"q": "city", "page": "abc"})

        self.assertContains(response, "Showing 1-10 of 11")

    def test_search_negative_page_falls_back_to_last_page(self):
        for i in range(1, 12):
            Hospital.objects.create(name=f"County Hospital {i}")

        response = self.client.get(self.search_url, {"q": "county", "page": "-1"})

        self.assertContains(response, "Showing 11-11 of 11")

    def test_search_out_of_range_page_falls_back_to_last_page(self):
        for i in range(1, 12):
            Hospital.objects.create(name=f"Central Hospital {i}")

        response = self.client.get(self.search_url, {"q": "central", "page": "999"})

        self.assertContains(response, "Showing 11-11 of 11")


class DetailNegativePathViewTestCase(TestCase):
    def test_hospital_detail_returns_404_for_missing_hospital(self):
        response = self.client.get(
            reverse("hospitaldetails:hospital_detail", kwargs={"id": 99999})
        )

        self.assertEqual(response.status_code, 404)

    def test_repository_detail_returns_404_for_missing_repository(self):
        response = self.client.get(
            reverse("hospitaldetails:repository_detail", kwargs={"id": 99999})
        )

        self.assertEqual(response.status_code, 404)

    def test_hospital_detail_invalid_search_hash_falls_back_to_base_search_link(self):
        hospital = Hospital.objects.create(name="Fallback General")

        response = self.client.get(
            reverse("hospitaldetails:hospital_detail", kwargs={"id": hospital.id}),
            {"search": "invalid-hash"},
        )

        self.assertContains(response, 'href="/hospital-records/hospitals/"')
        self.assertNotContains(response, "?q=")

    def test_repository_detail_renders_when_no_records_exist(self):
        repository = Repository.objects.create(name="No Records Repository")

        response = self.client.get(
            reverse("hospitaldetails:repository_detail", kwargs={"id": repository.id})
        )

        self.assertContains(response, "No Records Repository", status_code=200)
