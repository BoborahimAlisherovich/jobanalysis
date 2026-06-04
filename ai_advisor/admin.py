from django.contrib import admin
from .models import TestResult, ChatSession

@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'short_recommendation', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('user', 'answers_data', 'ai_recommendation', 'created_at')

    def short_recommendation(self, obj):
        rec = obj.ai_recommendation or {}
        return rec.get('recommended_job', '-')[:60]
    short_recommendation.short_description = 'Tavsiya'

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'message_count', 'updated_at')
    list_filter = ('updated_at',)
    search_fields = ('user__username',)

    def message_count(self, obj):
        return len(obj.message_history)
    message_count.short_description = 'Xabarlar soni'
