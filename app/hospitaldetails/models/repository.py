from django.db import models


class Repository(models.Model):
    name = models.CharField(max_length=90)
    archon_code = models.IntegerField(null=True, blank=True)
    street_1 = models.CharField(max_length=100, null=True, blank=True)
    street_2 = models.CharField(max_length=100, null=True, blank=True)
    town = models.CharField(max_length=30, null=True, blank=True)
    postcode = models.CharField(max_length=8, null=True, blank=True)
    county = models.CharField(max_length=30, null=True, blank=True)
    contact_details = models.CharField(max_length=250, null=True, blank=True)
    mailshot = models.BooleanField(default=False)
    more_research_required = models.BooleanField(default=False)
    researcher_comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
