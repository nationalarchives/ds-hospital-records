from unittest.mock import Mock, patch

import requests
from django.core.cache import cache
from django.template import engines
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from app.lib.constants import WAGTAIL_NOTIFICATIONS_CACHE_KEY
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


class WagtailNotificationPagesTestCase(TestCase):
    @patch("app.lib.context_processors.get_wagtail_api_notifications")
    def test_processor_runs_for_main_and_search_pages(self, get_notifications):
        get_notifications.return_value = {"global_alert": {"title": "Alert"}}

        for route in ("main:index", "hospitaldetails:search"):
            with self.subTest(route=route):
                get_notifications.reset_mock()
                self.assertEqual(self.client.get(reverse(route)).status_code, 200)
                get_notifications.assert_called_once_with()
