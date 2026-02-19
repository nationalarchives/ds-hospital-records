from app.hospitaldetails.mixins import NH3CleanSaveMixin
from django.db import models


class Pre1948Type(NH3CleanSaveMixin, models.Model):
    value = models.CharField(max_length=50)

    def __str__(self):
        return self.value


class Post1948Type(NH3CleanSaveMixin, models.Model):
    value = models.CharField(max_length=50)

    def __str__(self):
        return self.value
