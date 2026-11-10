from unittest.mock import patch

from django.test import TestCase

from app.hospitaldetails.management.commands.update_repository_names import Command
from app.hospitaldetails.models.repository import Repository


class UpdateRepositoryNamesCommandTestCase(TestCase):
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
