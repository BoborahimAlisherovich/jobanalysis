from django.db import models
from users.models import CustomUser

class TestResult(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    answers_data = models.JSONField() # Foydalanuvchi javoblari
    ai_recommendation = models.JSONField() # AI bergan top kasblar va izohlar
    created_at = models.DateTimeField(auto_now_add=True)

class ChatSession(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    message_history = models.JSONField(default=list) # [{role: 'user', content: '...'}, {role: 'ai',...}]
    updated_at = models.DateTimeField(auto_now=True)
