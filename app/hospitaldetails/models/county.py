from django.db import models

class Pre1974County(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Post1974County(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name
    
class Post1996County(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name