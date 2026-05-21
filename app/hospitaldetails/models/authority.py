from django.db import models

from app.hospitaldetails.mixins import NH3CleanSaveMixin


class RegionalBoard(NH3CleanSaveMixin, models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class ManagementCommittee(NH3CleanSaveMixin, models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Pre1982RegionalAuthority(NH3CleanSaveMixin, models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Post1982RegionalAuthority(NH3CleanSaveMixin, models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Pre1982DistrictAuthority(NH3CleanSaveMixin, models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Post1982DistrictAuthority(NH3CleanSaveMixin, models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
