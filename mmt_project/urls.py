"""
URL configuration for mmt_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from jobs.models import Job, Category, Country
from django.db.models import Count
from ai_advisor.views import ai_test_view, ai_chat_view
from jobs.views import sources_list_view, all_jobs_view, job_analytics_api

def home_view(request):
    categories = Category.objects.annotate(job_count=Count('jobs')).order_by('-job_count')
    countries = Country.objects.annotate(job_count=Count('job')).order_by('-job_count')[:10]
    
    country_labels = [c.name for c in countries]
    country_data = [c.job_count for c in countries]

    context = {
        'categories': categories,
        'country_labels': country_labels,
        'country_data': country_data,
    }
    return render(request, 'dashboard.html', context)

def category_analytics(request, cat_id):
    category = Category.objects.get(id=cat_id)
    jobs = category.jobs.all()
    # Provide necessary data to the template
    return render(request, 'category_detail.html', {'category': category, 'jobs': jobs})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    path('analytics/category/<int:cat_id>/', category_analytics, name='category_analytics'),
    path('jobs/', all_jobs_view, name='all_jobs'),
    path('sources/', sources_list_view, name='sources_list'),
    path('ai-test/', ai_test_view, name='ai_test'),
    path('ai-chat/', ai_chat_view, name='ai_chat'),
    path('api/analytics/', job_analytics_api, name='job_analytics_api'),
]
