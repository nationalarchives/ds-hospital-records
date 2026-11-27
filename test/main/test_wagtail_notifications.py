from unittest.mock import Mock, patch

import requests
from django.core.cache import cache
from django.template import engines
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from app.hospitaldetails.models import Hospital
from app.lib.constants import WAGTAIL_NOTIFICATIONS_CACHE_KEY
from app.lib.context_processors import wagtail_notifications
from app.lib.wagtail_api import get_wagtail_api_notifications


@override_settings(
    WAGTAIL_API_URL="https://wagtail.example/api",
    WAGTAIL_API_KEY="test-key",
    WAGTAIL_API_CACHE_TIMEOUT=60,
)
class WagtailNotificationsTestCase(SimpleTestCase):
    def setUp(self):
        cache.delete(WAGTAIL_NOTIFICATIONS_CACHE_KEY)
        self.addCleanup(cache.delete, WAGTAIL_NOTIFICATIONS_CACHE_KEY)

    @patch("app.lib.wagtail_api.get")
    def test_fetches_and_caches_notifications(self, get):
        get.return_value.json.return_value = {"global_alert": {"title": "Alert"}}

        notifications = get_wagtail_api_notifications()
        self.assertEqual(notifications, {"global_alert": {"title": "Alert"}})
        self.assertEqual(get_wagtail_api_notifications(), notifications)
        get.assert_called_once_with(
            "https://wagtail.example/api/globals/notifications",
            headers={"Authorization": "Token test-key"},
            timeout=5,
        )

    @patch("app.lib.wagtail_api.get")
    def test_empty_response_is_cached(self, get):
        get.return_value.json.return_value = {}

        self.assertEqual(get_wagtail_api_notifications(), {})
        self.assertEqual(get_wagtail_api_notifications(), {})
        get.assert_called_once()

    @patch("app.lib.wagtail_api.get")
    def test_api_errors_are_logged_and_do_not_break_rendering(self, get):
        get.side_effect = requests.Timeout("timeout")
        with self.assertLogs("app.lib.wagtail_api", level="ERROR"):
            self.assertIsNone(get_wagtail_api_notifications())

        get.side_effect = None
        get.return_value = Mock()
        get.return_value.raise_for_status.side_effect = requests.HTTPError("bad status")
        with self.assertLogs("app.lib.wagtail_api", level="ERROR"):
            self.assertIsNone(get_wagtail_api_notifications())

        get.return_value.raise_for_status.side_effect = None
        get.return_value.json.side_effect = ValueError("invalid JSON")
        with self.assertLogs("app.lib.wagtail_api", level="ERROR"):
            self.assertIsNone(get_wagtail_api_notifications())

    @override_settings(WAGTAIL_API_KEY="")
    @patch("app.lib.wagtail_api.get")
    def test_missing_configuration_is_logged(self, get):
        with self.assertLogs("app.lib.wagtail_api", level="ERROR"):
            self.assertIsNone(get_wagtail_api_notifications())
        get.assert_not_called()

    @patch("app.lib.context_processors.get_wagtail_api_notifications")
    def test_notifications_are_available_in_jinja_templates(self, get_notifications):
        get_notifications.return_value = {"global_alert": {"title": "Alert"}}
        template = engines["jinja2"].from_string(
            "{{ wagtail_notifications.global_alert.title }}"
        )

        self.assertEqual(template.render({}, RequestFactory().get("/")), "Alert")
        get_notifications.assert_called_once_with()

    @patch("app.lib.context_processors.get_wagtail_api_notifications")
    def test_reads_both_legacy_and_shared_cookies(self, get_notifications):
        request = RequestFactory().get(
            "/",
            HTTP_COOKIE=(
                "dismissed_notifications=%5B%22123%22%5D; "
                "dismissed_notifications=%5B456%5D"
            ),
        )
        self.assertEqual(
            wagtail_notifications(request)["dismissed_notifications"], ["123", "456"]
        )


class WagtailNotificationPagesTestCase(TestCase):
    @patch("app.lib.context_processors.get_wagtail_api_notifications")
    def test_detail_back_link_precedes_notifications_and_hospital(
        self, get_notifications
    ):
        hospital = Hospital.objects.create(name="Example Hospital")
        get_notifications.return_value = {
            "global_alert": {
                "title": "Global alert",
                "message": "<p>Message</p>",
                "alert_level": "high",
                "cascade": True,
                "uid": 123,
            },
            "mourning_notice": {"title": "Mourning notice", "message": "<p>Notice</p>"},
        }

        response = self.client.get(
            reverse("hospitaldetails:hospital_detail", kwargs={"id": hospital.id}),
            {"q": "general", "page": "2"},
        )
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertEqual(content.count("Back to search results"), 1)
        self.assertIn("?q=general&amp;page=2", content)
        self.assertLess(
            content.index("Back to search results"), content.index("Mourning notice")
        )
        self.assertLess(content.index("Mourning notice"), content.index("Global alert"))
        self.assertLess(
            content.index("Global alert"), content.index(">Example Hospital</h1>")
        )

    @patch("app.lib.context_processors.get_wagtail_api_notifications")
    def test_processor_runs_for_main_and_search_pages(self, get_notifications):
        get_notifications.return_value = {"global_alert": {"title": "Alert"}}

        for route in ("main:index", "hospitaldetails:search"):
            with self.subTest(route=route):
                get_notifications.reset_mock()
                self.assertEqual(self.client.get(reverse(route)).status_code, 200)
                get_notifications.assert_called_once_with()

    @patch("app.lib.context_processors.get_wagtail_api_notifications")
    def test_banners_render_rich_text_safely_on_multiple_pages(self, get_notifications):
        get_notifications.return_value = {
            "global_alert": {
                "title": "Global alert",
                "message": "<p>Important <strong>news</strong><script>alert(1)</script></p>",
                "alert_level": "high",
                "cascade": True,
                "uid": "alert-1",
            },
            "mourning_notice": {
                "title": "Mourning notice",
                "message": '<p>More <a href="https://example.com/">information</a></p>',
            },
        }

        for route in ("main:index", "hospitaldetails:search"):
            with self.subTest(route=route):
                response = self.client.get(reverse(route))
                self.assertContains(response, "Global alert")
                self.assertContains(response, "Mourning notice")
                self.assertContains(response, "<strong>news</strong>", html=True)
                self.assertContains(response, 'href="https://example.com/"')
                self.assertNotContains(response, "<script>alert(1)</script>")
                self.assertContains(response, "etna-global-alert--high")
                self.assertContains(response, 'value="alert-1"')

    @patch("app.lib.context_processors.get_wagtail_api_notifications")
    def test_dismissed_or_non_cascading_alert_does_not_hide_mourning_notice(
        self, get_notifications
    ):
        alert = {
            "title": "Global alert",
            "message": "<p>Message</p>",
            "alert_level": "low",
            "cascade": True,
            "uid": "alert-1",
        }
        get_notifications.return_value = {
            "global_alert": alert,
            "mourning_notice": {"title": "Mourning notice", "message": "<p>Notice</p>"},
        }
        self.client.cookies["dismissed_notifications"] = "%5B%22alert-1%22%5D"
        response = self.client.get(reverse("main:index"))
        self.assertNotContains(response, "Global alert")
        self.assertContains(response, "Mourning notice")

        alert["uid"] = 12345
        self.client.cookies["dismissed_notifications"] = "%5B12345%5D"
        response = self.client.get(reverse("main:index"))
        self.assertNotContains(response, "Global alert")
        self.assertContains(response, "Mourning notice")

        self.client.cookies["dismissed_notifications"] = "%5B%2212345%22%5D"
        response = self.client.get(reverse("main:index"))
        self.assertNotContains(response, "Global alert")
        self.assertContains(response, "Mourning notice")

        del self.client.cookies["dismissed_notifications"]
        alert["cascade"] = False
        response = self.client.get(reverse("main:index"))
        self.assertNotContains(response, "Global alert")
        self.assertContains(response, "Mourning notice")

    @patch("app.lib.context_processors.get_wagtail_api_notifications")
    def test_missing_notifications_and_invalid_cookie_do_not_break_pages(
        self, get_notifications
    ):
        get_notifications.return_value = None
        self.client.cookies["dismissed_notifications"] = "%7Bbad-json"
        with self.assertLogs("app.lib.context_processors", level="WARNING"):
            response = self.client.get(reverse("main:index"))
        self.assertEqual(response.status_code, 200)
