import datetime

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from app.hospitaldetails.mixins import NH3CleanSaveMixin


class Hospital(NH3CleanSaveMixin, models.Model):
    name = models.CharField(max_length=100)
    name_since = models.IntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(1000),
            MaxValueValidator(datetime.date.today().year),
        ],
        help_text="Year the hospital has had this name since (YYYY)",
    )
    previous_names = models.TextField(null=True, blank=True)
    street_1 = models.CharField(max_length=100, null=True, blank=True)
    street_2 = models.CharField(max_length=100, null=True, blank=True)
    town = models.CharField(max_length=30, null=True, blank=True)
    postcode = models.CharField(max_length=8, null=True, blank=True)
    address_since = models.IntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(1000),
            MaxValueValidator(datetime.date.today().year),
        ],
        help_text="Year the hospital moved to this address (YYYY)",
    )
    previous_locations = models.TextField(null=True, blank=True)
    trust = models.CharField(max_length=200, null=True, blank=True)
    trust_since = models.CharField(max_length=100, null=True, blank=True)
    previous_trusts = models.TextField(null=True, blank=True)
    foundation_year = models.IntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(1000),
            MaxValueValidator(datetime.date.today().year),
        ],
        help_text="Year the hospital was founded (YYYY)",
    )
    foundation_year_approximate = models.BooleanField(default=False)
    closed = models.BooleanField(default=False)
    closure_date = models.IntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(1000),
            MaxValueValidator(datetime.date.today().year),
        ],
        help_text="Year the hospital closed (YYYY)",
    )
    closure_year_approximate = models.BooleanField(default=False)
    pre_1948_status = models.ManyToManyField(
        "hospitaldetails.Pre1948Status",
        blank=True,
        related_name="hospitals_pre_1948_status",
    )
    pre_1948_status_info = models.TextField(null=True, blank=True)
    post_1948_status = models.ManyToManyField(
        "hospitaldetails.Post1948Status",
        blank=True,
        related_name="hospitals_post_1948_status",
    )
    post_1948_status_info = models.TextField(null=True, blank=True)
    pre_1948_type = models.ManyToManyField(
        "hospitaldetails.Pre1948Type",
        blank=True,
        related_name="hospitals_pre_1948_type",
    )
    pre_1948_type_info = models.TextField(null=True, blank=True)
    post_1948_type = models.ManyToManyField(
        "hospitaldetails.Post1948Type",
        blank=True,
        related_name="hospitals_post_1948_type",
    )
    post_1948_type_info = models.TextField(null=True, blank=True)
    other_information = models.TextField(null=True, blank=True)
    pre_1974_county = models.ForeignKey(
        "hospitaldetails.Pre1974County",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="hospitals_pre_1974_county",
    )
    post_1974_county = models.ForeignKey(
        "hospitaldetails.Post1974County",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="hospitals_post_1974_county",
    )
    post_1996_county = models.ForeignKey(
        "hospitaldetails.Post1996County",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="hospitals_post_1996_county",
    )
    regional_board = models.ForeignKey(
        "hospitaldetails.RegionalBoard",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="hospitals_regional_board",
    )
    management_committee = models.ForeignKey(
        "hospitaldetails.ManagementCommittee",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="hospitals_management_committee",
    )
    pre_1982_regional_authority = models.ForeignKey(
        "hospitaldetails.Pre1982RegionalAuthority",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="hospitals_pre_1982_regional_authority",
    )
    post_1982_regional_authority = models.ForeignKey(
        "hospitaldetails.Post1982RegionalAuthority",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="hospitals_post_1982_regional_authority",
    )
    pre_1982_district_authority = models.ForeignKey(
        "hospitaldetails.Pre1982DistrictAuthority",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="hospitals_pre_1982_district_authority",
    )
    post_1982_district_authority = models.ForeignKey(
        "hospitaldetails.Post1982DistrictAuthority",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="hospitals_post_1982_district_authority",
    )
    more_research_required = models.BooleanField(default=False)
    researcher_comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)

    @property
    def full_address(self):
        parts = [self.street_1, self.street_2, self.town, self.postcode]
        return ", ".join(part for part in parts if part)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]
        verbose_name = "Hospital"
        verbose_name_plural = "Hospitals"
