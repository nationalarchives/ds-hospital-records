from django.db import models

from app.hospitaldetails.mixins import NH3CleanSaveMixin


class RegionalBoard(NH3CleanSaveMixin, models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]
        verbose_name = "Regional Board"
        verbose_name_plural = "Regional Boards"


class ManagementCommittee(NH3CleanSaveMixin, models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]
        verbose_name = "Management Committee"
        verbose_name_plural = "Management Committees"


class Pre1982RegionalAuthority(NH3CleanSaveMixin, models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]
        verbose_name = "Pre-1982 Regional Authority"
        verbose_name_plural = "Pre-1982 Regional Authorities"


class Post1982RegionalAuthority(NH3CleanSaveMixin, models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]
        verbose_name = "Post-1982 Regional Authority"
        verbose_name_plural = "Post-1982 Regional Authorities"


class Pre1982DistrictAuthority(NH3CleanSaveMixin, models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]
        verbose_name = "Pre-1982 District Authority"
        verbose_name_plural = "Pre-1982 District Authorities"


class Post1982DistrictAuthority(NH3CleanSaveMixin, models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]
        verbose_name = "Post-1982 District Authority"
        verbose_name_plural = "Post-1982 District Authorities"
