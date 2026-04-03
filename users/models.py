from django.contrib.auth.models import AbstractUser
from django.db import models

class Skill(models.Model):
    name = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.name

class CustomUser(AbstractUser):
    phone = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    experience_years = models.FloatField(default=0.0)
    skills = models.ManyToManyField(Skill, blank=True)
    saved_jobs = models.ManyToManyField('jobs.Job', blank=True, related_name='saved_by_users')

    def __str__(self):
        return self.username

