from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Skill

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'phone', 'country', 'experience_years', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'country', 'skills')
    search_fields = ('username', 'email', 'phone')
    fieldsets = UserAdmin.fieldsets + (
        ('Qo\'shimcha ma\'lumotlar', {'fields': ('phone', 'country', 'experience_years', 'skills')}),
    )

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
