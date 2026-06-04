from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html
from .models import Job, Category, Country

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'job_count')
    search_fields = ('name',)

    def job_count(self, obj):
        return obj.job_set.count()
    job_count.short_description = 'Vakansiyalar soni'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'trend_score', 'job_count')
    search_fields = ('name',)
    list_editable = ('trend_score',)

    def job_count(self, obj):
        return obj.jobs.filter(is_active=True).count()
    job_count.short_description = 'Aktiv vakansiyalar'

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'category', 'country', 'salary_range', 'source', 'job_type', 'is_active', 'posted_at')
    list_filter = ('source', 'is_active', 'job_type', 'category', 'country', 'currency')
    search_fields = ('title', 'company', 'description')
    list_editable = ('is_active',)
    date_hierarchy = 'posted_at'
    readonly_fields = ('source_url',)

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('title', 'company', 'category', 'country', 'description')
        }),
        ('Ish haqi', {
            'fields': ('salary_min', 'salary_max', 'currency')
        }),
        ('Tafsilotlar', {
            'fields': ('job_type', 'source', 'source_url', 'is_active')
        }),
    )

    def salary_range(self, obj):
        if obj.salary_min and obj.salary_max:
            return f"{obj.salary_min:,} - {obj.salary_max:,} {obj.currency}"
        elif obj.salary_min:
            return f"from {obj.salary_min:,} {obj.currency}"
        return "-"
    salary_range.short_description = 'Ish haqi'
