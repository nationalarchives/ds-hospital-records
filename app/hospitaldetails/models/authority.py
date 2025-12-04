from django.db import models

class RegionalBoard(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
class ManagementCommittee(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
class Pre1982RegionalAuthority(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
class Post1982RegionalAuthority(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
class Pre1982DistrictAuthority(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
class Post1982DistrictAuthority(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name