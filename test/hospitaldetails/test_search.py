from app.hospitaldetails.models.hospital import Hospital
from django.test import TestCase
from django.urls import reverse


class SearchBackendTestCase(TestCase):
    def setUp(self):
        self.search_url = reverse("hospitaldetails:search")

    def test_empty_query_returns_no_results(self):
        response = self.client.get(self.search_url)
        self.assertContains(response, "Search Hospitals", status_code=200)
        self.assertNotContains(response, "Search Results")

    def test_search_matches_name_previous_name_and_town(self):
        Hospital.objects.create(name="St Marys", town="York")
        Hospital.objects.create(name="South General", previous_names="Old General")
        Hospital.objects.create(name="Riverside Clinic", town="Bath")

        response = self.client.get(self.search_url, {"q": "general"})
        self.assertContains(response, "Search Results", status_code=200)
        self.assertContains(response, "South General")
        self.assertNotContains(response, "St Marys")
        self.assertNotContains(response, "Riverside Clinic")

        response = self.client.get(self.search_url, {"q": "  yOrK  "})
        self.assertContains(response, "St Marys")

    def test_search_orders_results_by_name(self):
        Hospital.objects.create(name="Zeta Hospital")
        Hospital.objects.create(name="Alpha Hospital")
        Hospital.objects.create(name="Beta Hospital")

        response = self.client.get(self.search_url, {"q": "hospital"})
        content = response.content.decode("utf-8")
        self.assertLess(
            content.index("Alpha Hospital"),
            content.index("Beta Hospital"),
        )
        self.assertLess(
            content.index("Beta Hospital"),
            content.index("Zeta Hospital"),
        )


class SearchFrontendTestCase(TestCase):
    def setUp(self):
        self.search_url = reverse("hospitaldetails:search")

    def test_form_renders_and_preserves_query(self):
        response = self.client.get(self.search_url, {"q": "York"})
        self.assertContains(response, "Search by hospital name or town")
        self.assertContains(response, 'name="q"')
        self.assertContains(response, 'value="York"')

    def test_results_include_hospital_links(self):
        hospital = Hospital.objects.create(name="North Clinic", town="Leeds")

        response = self.client.get(self.search_url, {"q": "north"})
        detail_url = reverse(
            "hospitaldetails:hospital_detail", kwargs={"id": hospital.id}
        )
        self.assertContains(response, detail_url)

    def test_no_results_message(self):
        response = self.client.get(self.search_url, {"q": "missing"})
        self.assertContains(response, "No hospitals found matching")
