from app.hospitaldetails.mixins import NH3CleanSaveMixin
from django.db import models


class FindingAids(NH3CleanSaveMixin, models.Model):
    value = models.CharField(max_length=25)

    def __str__(self):
        return self.value

    class Meta:
        verbose_name = "Finding Aid"
        verbose_name_plural = "Finding Aids"


class FindingAidsLocation(NH3CleanSaveMixin, models.Model):
    value = models.CharField(max_length=50)

    def __str__(self):
        return self.value

    class Meta:
        verbose_name = "Finding Aids Location"
        verbose_name_plural = "Finding Aids Locations"
