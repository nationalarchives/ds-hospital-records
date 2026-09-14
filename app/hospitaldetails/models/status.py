from django.db import models

from app.hospitaldetails.mixins import NH3CleanSaveMixin


class Pre1948Status(NH3CleanSaveMixin, models.Model):
    value = models.CharField(max_length=50)

    def __str__(self):
        return self.value

    class Meta:
        ordering = ["value"]
        verbose_name = "Pre-1948 Status"
        verbose_name_plural = "Pre-1948 Statuses"


class Post1948Status(NH3CleanSaveMixin, models.Model):
    value = models.CharField(max_length=50)

    def __str__(self):
        return self.value

    class Meta:
        ordering = ["value"]
        verbose_name = "Post-1948 Status"
        verbose_name_plural = "Post-1948 Statuses"
