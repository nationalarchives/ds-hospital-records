from django.db import models

from app.hospitaldetails.mixins import NH3CleanSaveMixin


class Pre1974County(NH3CleanSaveMixin, models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]
        verbose_name = "Pre-1974 County"
        verbose_name_plural = "Pre-1974 Counties"


class Post1974County(NH3CleanSaveMixin, models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]
        verbose_name = "Post-1974 County"
        verbose_name_plural = "Post-1974 Counties"


class Post1996County(NH3CleanSaveMixin, models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]
        verbose_name = "Post-1996 County"
        verbose_name_plural = "Post-1996 Counties"
