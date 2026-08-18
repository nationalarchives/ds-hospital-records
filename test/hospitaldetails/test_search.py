import datetime

from django.test import TestCase
from django.urls import reverse

from app.hospitaldetails.models.hospital import Hospital
from app.hospitaldetails.models.status import Post1948Status, Pre1948Status
from app.hospitaldetails.models.type import Post1948Type, Pre1948Type


class SearchBackendTestCase(TestCase):
    def setUp(self):
        self.search_url = reverse("hospitaldetails:search")

    def test_empty_query_returns_all_results(self):
        Hospital.objects.create(name="Alpha Hospital")

        response = self.client.get(self.search_url)
        self.assertContains(response, "Search hospitals", status_code=200)
        self.assertContains(response, "Search results")
        self.assertContains(response, "Alpha Hospital")

    def test_search_matches_name_previous_name_and_town(self):
        Hospital.objects.create(name="St Marys", town="York")
        Hospital.objects.create(name="South General", previous_names="Old General")
        Hospital.objects.create(name="Riverside Clinic", town="Bath")

        response = self.client.get(self.search_url, {"q": "general"})
        self.assertContains(response, "Search results", status_code=200)
        self.assertContains(response, "South General")
        self.assertNotContains(response, "St Marys")
        self.assertNotContains(response, "Riverside Clinic")

        response = self.client.get(self.search_url, {"q": "  yOrK  "})
        self.assertContains(response, "St Marys")

    def test_search_matches_historic_location(self):
        Hospital.objects.create(
            name="Old Infirmary",
            previous_locations="Old Road, Sheffield",
        )
        Hospital.objects.create(name="Coastal Clinic", previous_locations="Harbour Way")

        response = self.client.get(self.search_url, {"q": "sheffield"})
        self.assertContains(response, "Old Infirmary", status_code=200)
        self.assertNotContains(response, "Coastal Clinic")

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

    def test_sort_name_desc(self):
        Hospital.objects.create(name="Zeta Hospital")
        Hospital.objects.create(name="Alpha Hospital")
        Hospital.objects.create(name="Beta Hospital")

        response = self.client.get(self.search_url, {"sort": "name_desc"})
        content = response.content.decode("utf-8")
        self.assertLess(content.index("Zeta Hospital"), content.index("Beta Hospital"))
        self.assertLess(content.index("Beta Hospital"), content.index("Alpha Hospital"))

    def test_sort_foundation_year_asc_puts_unknown_last(self):
        Hospital.objects.create(name="Unknown Year", foundation_year=None)
        Hospital.objects.create(name="Older", foundation_year=1900)
        Hospital.objects.create(name="Newer", foundation_year=1950)

        response = self.client.get(self.search_url, {"sort": "foundation_year_asc"})
        content = response.content.decode("utf-8")
        self.assertLess(content.index("Older"), content.index("Newer"))
        self.assertLess(content.index("Newer"), content.index("Unknown Year"))

    def test_sort_foundation_year_desc_puts_unknown_last(self):
        Hospital.objects.create(name="Unknown Year", foundation_year=None)
        Hospital.objects.create(name="Older", foundation_year=1900)
        Hospital.objects.create(name="Newer", foundation_year=1950)

        response = self.client.get(self.search_url, {"sort": "foundation_year_desc"})
        content = response.content.decode("utf-8")
        self.assertLess(content.index("Newer"), content.index("Older"))
        self.assertLess(content.index("Older"), content.index("Unknown Year"))

    def test_sort_last_updated_desc(self):
        older = Hospital.objects.create(name="Older Updated")
        newer = Hospital.objects.create(name="Newer Updated")

        older.last_updated_at = datetime.datetime(2020, 1, 1, 12, 0, 0)
        older.save(update_fields=["last_updated_at"])
        newer.last_updated_at = datetime.datetime(2021, 1, 1, 12, 0, 0)
        newer.save(update_fields=["last_updated_at"])

        response = self.client.get(self.search_url, {"sort": "last_updated_desc"})
        content = response.content.decode("utf-8")
        self.assertLess(content.index("Newer Updated"), content.index("Older Updated"))

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

        Hospital.objects.create(name="Non Matching Status Hospital")

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

        Hospital.objects.create(name="Non Matching Type Hospital")

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

    def test_form_renders_sort_select_and_selected_value(self):
        response = self.client.get(self.search_url, {"sort": "foundation_year_desc"})
        self.assertContains(response, 'name="sort"')
        self.assertContains(response, 'option value="foundation_year_desc" selected')

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


class HospitalDetailOrderingTestCase(TestCase):
    def test_status_and_type_are_alphabetical_with_other_last(self):
        hospital = Hospital.objects.create(name="Ordering Test Hospital")

        hospital.pre_1948_status.add(
            Pre1948Status.objects.create(value="Zeta"),
            Pre1948Status.objects.create(value="alpha"),
            Pre1948Status.objects.create(value="Other"),
        )
        hospital.post_1948_status.add(
            Post1948Status.objects.create(value="Gamma"),
            Post1948Status.objects.create(value="beta"),
            Post1948Status.objects.create(value="Other"),
        )
        hospital.pre_1948_type.add(
            Pre1948Type.objects.create(value="Maternity"),
            Pre1948Type.objects.create(value="Asylum"),
            Pre1948Type.objects.create(value="Other"),
        )
        hospital.post_1948_type.add(
            Post1948Type.objects.create(value="Special"),
            Post1948Type.objects.create(value="Acute"),
            Post1948Type.objects.create(value="Other"),
        )

        response = self.client.get(
            reverse("hospitaldetails:hospital_detail", kwargs={"id": hospital.id})
        )

        content = response.content.decode("utf-8")

        self.assertContains(response, "alpha, Zeta, Other")
        self.assertContains(response, "beta, Gamma, Other")
        self.assertContains(response, "Asylum, Maternity, Other")
        self.assertContains(response, "Acute, Special, Other")

        self.assertLess(
            content.index("alpha, Zeta, Other"), content.index("beta, Gamma, Other")
        )
        self.assertLess(
            content.index("Asylum, Maternity, Other"),
            content.index("Acute, Special, Other"),
        )
