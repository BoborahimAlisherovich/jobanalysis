from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from jobs.models import Job, Category, Country
from django.db.models import Count
from ai_advisor.views import ai_test_view, ai_chat_view
from jobs.views import sources_list_view, all_jobs_view, job_analytics_api
from users.views import login_view, register_view, logout_view
from django.core.paginator import Paginator

def home_view(request):
    TARGET_ROLES = [
        'Backend Developer', 'Frontend Developer', 'Mobile App Developer', 'Data Analyst',
        'Data Scientist', 'DevOps Engineer', 'AI Engineer', 'Prompt Engineer', 'UI/UX Designer',
        'Game Developer', 'Product Manager', 'Software Engineer', 'Business Intelligence (BI) Developer',
        'Cybersecurity Specialist', 'Product Designer', 'Business Analyst', 'Blockchain Developer', 'QA Engineer'
    ]

    for role in TARGET_ROLES:
        Category.objects.get_or_create(name=role)

    categories = Category.objects.filter(name__in=TARGET_ROLES).annotate(job_count=Count('jobs')).order_by('-job_count')
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
    jobs_list = category.jobs.all().order_by('-posted_at', '-id')
    paginator = Paginator(jobs_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    country_stats = jobs_list.values('country__name').annotate(cnt=Count('id')).order_by('-cnt')
    country_labels = [c['country__name'] if c['country__name'] else 'Unknown' for c in country_stats]
    country_data = [c['cnt'] for c in country_stats]

    context = {
        'category': category,
        'page_obj': page_obj,
        'country_labels': country_labels,
        'country_data': country_data,
    }
    return render(request, 'category_detail.html', context)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    path('analytics/category/<int:cat_id>/', category_analytics, name='category_analytics'),
    path('jobs/', all_jobs_view, name='all_jobs'),
    path('sources/', sources_list_view, name='sources_list'),
    path('ai-test/', ai_test_view, name='ai_test'),
    path('ai-chat/', ai_chat_view, name='ai_chat'),
    path('api/analytics/', job_analytics_api, name='job_analytics_api'),

    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
]
