from django.db import models

from app.hospitaldetails.mixins import NH3CleanSaveMixin


class Pre1974County(NH3CleanSaveMixin, models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Post1974County(NH3CleanSaveMixin, models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Post1996County(NH3CleanSaveMixin, models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name
