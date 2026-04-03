from django.db import models
from users.models import Skill

class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=5, blank=True) # UZ, US, DE

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    trend_score = models.FloatField(default=0.0) # Analitika uchun o'sish treki

    def __str__(self):
        return self.name

class Job(models.Model):
    JOB_TYPES = (('full_time', 'Full Time'), ('part_time', 'Part Time'), ('remote', 'Remote'))
    
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='jobs')
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
    
    description = models.TextField()
    job_type = models.CharField(max_length=20, choices=JOB_TYPES, default='full_time')
    
    salary_min = models.IntegerField(null=True, blank=True)
    salary_max = models.IntegerField(null=True, blank=True)
    currency = models.CharField(max_length=10, default='USD')
    
    required_skills = models.ManyToManyField(Skill, blank=True)
    source_url = models.URLField(unique=True) # Duplikatlarni taqiqlash
    source = models.CharField(max_length=50, default='hh.uz') # Manba platformasi nomi
    is_active = models.BooleanField(default=True)
    posted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
