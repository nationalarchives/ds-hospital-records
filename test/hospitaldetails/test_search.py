from django.test import TestCase
from django.urls import reverse

from app.hospitaldetails.models.hospital import Hospital
from app.hospitaldetails.models.status import Post1948Status, Pre1948Status
from app.hospitaldetails.models.type import Post1948Type, Pre1948Type


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

    def test_filter_open_closed_status(self):
        Hospital.objects.create(name="Open Hospital", closed=False)
        Hospital.objects.create(name="Closed Hospital", closed=True)

        response = self.client.get(
            self.search_url,
            {"open_closed_status": "open"},
        )
        self.assertContains(response, "Open Hospital")
        self.assertNotContains(response, "Closed Hospital")

        response = self.client.get(
            self.search_url,
            {"open_closed_status": "closed"},
        )
        self.assertContains(response, "Closed Hospital")
        self.assertNotContains(response, "Open Hospital")

    def test_filter_foundation_year_range(self):
        Hospital.objects.create(
            name="Founded before range",
            foundation_year=1900,
            closed=False,
        )
        Hospital.objects.create(
            name="Founded in range",
            foundation_year=1930,
            closed=True,
            closure_date=1980,
        )
        Hospital.objects.create(
            name="Founded after range",
            foundation_year=1960,
            closed=True,
            closure_date=1990,
        )

        response = self.client.get(
            self.search_url,
            {
                "foundation_year_from": "1920",
                "foundation_year_to": "1950",
            },
        )

        self.assertNotContains(response, "Founded before range")
        self.assertContains(response, "Founded in range")
        self.assertNotContains(response, "Founded after range")

    def test_filter_foundation_year_with_only_to(self):
        Hospital.objects.create(name="Ancient", foundation_year=1200, closed=False)
        Hospital.objects.create(name="Modern", foundation_year=2000, closed=False)

        response = self.client.get(
            self.search_url,
            {
                "foundation_year_to": "1500",
            },
        )

        self.assertContains(response, "Ancient")
        self.assertNotContains(response, "Modern")

    def test_filter_pre_and_post_1948_status(self):
        pre_local = Pre1948Status.objects.create(value="Local Authority")
        post_nhs = Post1948Status.objects.create(value="NHS")

        matching = Hospital.objects.create(name="Matching Status Hospital")
        matching.pre_1948_status.add(pre_local)
        matching.post_1948_status.add(post_nhs)

        non_matching = Hospital.objects.create(name="Non Matching Status Hospital")

        response = self.client.get(
            self.search_url,
            {
                "pre_1948_status": [str(pre_local.id)],
            },
        )
        self.assertContains(response, "Matching Status Hospital")
        self.assertNotContains(response, "Non Matching Status Hospital")

        response = self.client.get(
            self.search_url,
            {
                "post_1948_status": [str(post_nhs.id)],
            },
        )
        self.assertContains(response, "Matching Status Hospital")
        self.assertNotContains(response, "Non Matching Status Hospital")

    def test_filter_pre_and_post_1948_type(self):
        pre_voluntary = Pre1948Type.objects.create(value="Voluntary")
        post_special = Post1948Type.objects.create(value="Special")

        matching = Hospital.objects.create(name="Matching Type Hospital")
        matching.pre_1948_type.add(pre_voluntary)
        matching.post_1948_type.add(post_special)

        non_matching = Hospital.objects.create(name="Non Matching Type Hospital")

        response = self.client.get(
            self.search_url,
            {
                "pre_1948_type": [str(pre_voluntary.id)],
            },
        )
        self.assertContains(response, "Matching Type Hospital")
        self.assertNotContains(response, "Non Matching Type Hospital")

        response = self.client.get(
            self.search_url,
            {
                "post_1948_type": [str(post_special.id)],
            },
        )
        self.assertContains(response, "Matching Type Hospital")
        self.assertNotContains(response, "Non Matching Type Hospital")


class SearchFrontendTestCase(TestCase):
    def setUp(self):
        self.search_url = reverse("hospitaldetails:search")

    def test_form_renders_and_preserves_query(self):
        response = self.client.get(self.search_url, {"q": "York"})
        self.assertContains(response, "Hospital Records search")
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
