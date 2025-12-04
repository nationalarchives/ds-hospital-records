from django.db import models

class Pre1948Type(models.Model):
    value = models.CharField(max_length=50)

    def __str__(self):
        return self.value

class Post1948Type(models.Model):
    value = models.CharField(max_length=50)

    def __str__(self):
        return self.value