from io import StringIO
from unittest.mock import patch

import requests
from django.core.management.base import CommandError
from django.db import DatabaseError
from django.test import TestCase

from app.hospitaldetails.management.commands.update_repository_names import Command
from app.hospitaldetails.models.repository import Repository


class UpdateRepositoryNamesCommandTestCase(TestCase):
    def test_update_preserves_ampersands_and_sanitizes_angle_brackets(self):
        repository = Repository.objects.create(name="Old name", archon_code=1)

        Command().update_repository_name(repository, "R&D < D")

        repository.refresh_from_db()
        self.assertEqual(repository.name, "R&D &lt; D")

    @patch(
        "app.hospitaldetails.management.commands.update_repository_names.requests.get"
    )
    def test_api_errors_are_chained(self, get):
        for error in (
            requests.ConnectionError("Connection failed"),
            requests.HTTPError("HTTP error"),
            ValueError("Invalid JSON"),
        ):
            with self.subTest(error=error):
                get.reset_mock()
                get.side_effect = None
                get.return_value.raise_for_status.side_effect = None
                get.return_value.json.side_effect = None
                if isinstance(error, requests.ConnectionError):
                    get.side_effect = error
                elif isinstance(error, requests.HTTPError):
                    get.return_value.raise_for_status.side_effect = error
                else:
                    get.return_value.json.side_effect = error

                with self.assertRaisesMessage(
                    CommandError, "Failed to retrieve name for ARCHON code: 1"
                ) as raised:
                    Command().get_name_from_archon_code(1)

                self.assertIs(raised.exception.__cause__, error)

    @patch("app.hospitaldetails.management.commands.update_repository_names.time.sleep")
    @patch.object(Command, "get_name_from_archon_code", return_value="Updated name")
    @patch.object(Command, "update_repository_name")
    def test_expected_errors_do_not_stop_processing(self, update_name, get_name, sleep):
        Repository.objects.bulk_create(
            [
                Repository(name=f"Repository {archon_code}", archon_code=archon_code)
                for archon_code in range(1, 4)
            ]
        )
        get_name.side_effect = [
            CommandError("API failed"),
            "Updated name",
            "Updated name",
        ]
        update_name.side_effect = [DatabaseError("Save failed"), None]
        stderr = StringIO()

        Command(stderr=stderr).handle()

        self.assertEqual(get_name.call_count, 3)
        self.assertEqual(update_name.call_count, 2)
        self.assertIn("API failed", stderr.getvalue())
        self.assertIn("Save failed", stderr.getvalue())

    @patch("app.hospitaldetails.management.commands.update_repository_names.time.sleep")
    @patch.object(Command, "get_name_from_archon_code", return_value=None)
    def test_waits_between_discovery_api_requests(self, get_name, sleep):
        Repository.objects.bulk_create(
            [
                Repository(name=f"Repository {archon_code}", archon_code=archon_code)
                for archon_code in range(1, 4)
            ]
        )

        Command().handle()

        self.assertEqual(get_name.call_count, 3)
        self.assertEqual(sleep.call_count, 2)
        sleep.assert_called_with(1)
