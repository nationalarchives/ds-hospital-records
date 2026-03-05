"""
Management command to connect to the Discovery API and pull ARCHON data for repositories.

Currently just updates the name of Repositories, but could be expanded to pull more data in the future.

We are only updating the name of Repositories at current, because it'd be a better user experience to just link to
ARCHON pages which are the source of truth for the data, rather than updating the database here.
"""

import requests
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Pull ARCHON data for repositories from the Discovery API"

    def handle(self, *args, **options):
        from app.hospitaldetails.models import Repository

        # Get all repositories with an ARCHON code
        repositories = Repository.objects.filter(
            archon_code__isnull=False,
        ).exclude(archon_code=0)
        for repository in repositories:
            try:
                new_name = self.get_name_from_archon_code(repository.archon_code)
                if new_name and new_name != repository.name:
                    self.update_repository_name(repository, new_name)
            except Exception as e:
                self.stderr.write(f"Error processing repository {repository.name}: {e}")

    def get_name_from_archon_code(self, archon_code):
        """
        Call Discovery API to get the name of the Repository for a given ARCHON code.
        """
        response = requests.get(
            f"https://discovery.nationalarchives.gov.uk/API/search/v1/archive/{archon_code}"
        )
        try:
            response.raise_for_status()
            data = response.json()
            return data.get("repositories", [{}])[0].get("title")
        except Exception as e:
            raise CommandError(
                f"Failed to retrieve name for ARCHON code: {archon_code}, error: {e}"
            )

    def update_repository_name(self, repository, new_name):
        """
        Update the name of a repository and save it to the database.
        """
        old_name = repository.name
        repository.name = new_name
        repository.save(update_fields=["name"])
        self.stdout.write(f"Updated repository name from: {old_name} to: {new_name}")
