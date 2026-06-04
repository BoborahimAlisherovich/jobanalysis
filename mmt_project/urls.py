from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from jobs.models import Job, Category, Country
from ai_advisor.views import ai_test_view, ai_chat_view, ai_chat_stream
from jobs.views import sources_list_view, all_jobs_view, job_analytics_api
from users.models import CustomUser
from users.views import login_view, register_view, logout_view
from django.core.paginator import Paginator


@staff_member_required
def admin_dashboard_view(request):
    total_jobs = Job.objects.count()
    active_jobs = Job.objects.filter(is_active=True).count()
    
    sources = Job.objects.values('source').annotate(count=Count('id')).order_by('-count')
    
    categories = Category.objects.annotate(job_count=Count('jobs')).order_by('-job_count')[:10]
    
    recent_jobs = Job.objects.order_by('-posted_at')[:10]
    
    countries = Country.objects.annotate(job_count=Count('job')).order_by('-job_count')[:5]
    
    context = {
        'total_jobs': total_jobs,
        'active_jobs': active_jobs,
        'sources': sources,
        'categories': categories,
        'recent_jobs': recent_jobs,
        'countries': countries,
    }
    return render(request, 'admin_dashboard.html', context)


@staff_member_required
def admin_panel_main_view(request):
    from ai_advisor.models import TestResult
    from django.utils import timezone
    from datetime import timedelta
    import json
    
    total_users = CustomUser.objects.count()
    total_tests = TestResult.objects.count()
    total_jobs = Job.objects.count()
    active_jobs = Job.objects.filter(is_active=True).count()
    
    # Test natijalari bo'yicha taqsimot (PAEI)
    test_distribution = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
    for tr in TestResult.objects.all():
        rec = tr.ai_recommendation or {}
        job_title = rec.get('recommended_job', '')
        if 'Producer' in job_title or 'Dasturchi' in job_title or 'DevOps' in job_title or 'Injinir' in job_title:
            test_distribution['A'] += 1
        elif 'Administrator' in job_title or 'QA' in job_title or 'Data Analyst' in job_title or 'SysAdmin' in job_title:
            test_distribution['B'] += 1
        elif 'Entrepreneur' in job_title or 'AI' in job_title or 'Product Manager' in job_title or 'UX/UI' in job_title:
            test_distribution['C'] += 1
        elif 'Integrator' in job_title or 'Scrum' in job_title or 'Project Manager' in job_title or 'HR' in job_title:
            test_distribution['D'] += 1
    
    # Manbalar bo'yicha vakansiyalar
    sources = Job.objects.values('source').annotate(count=Count('id')).order_by('-count')
    
    # Kategoriyalar bo'yicha
    categories = Category.objects.annotate(job_count=Count('jobs')).order_by('-job_count')[:10]
    
    # Oxirgi 7 kunlik statistika
    week_ago = timezone.now() - timedelta(days=7)
    new_users_week = CustomUser.objects.filter(date_joined__gte=week_ago).count()
    new_jobs_week = Job.objects.filter(posted_at__gte=week_ago).count()
    new_tests_week = TestResult.objects.filter(created_at__gte=week_ago).count()
    
    context = {
        'total_users': total_users,
        'total_tests': total_tests,
        'total_jobs': total_jobs,
        'active_jobs': active_jobs,
        'test_distribution': test_distribution,
        'sources': sources,
        'categories': categories,
        'new_users_week': new_users_week,
        'new_jobs_week': new_jobs_week,
        'new_tests_week': new_tests_week,
    }
    return render(request, 'admin_panel_main.html', context)


@staff_member_required
def admin_panel_users_view(request):
    from ai_advisor.models import TestResult
    from django.db.models import OuterRef, Subquery
    
    latest_test = TestResult.objects.filter(
        user=OuterRef('pk')
    ).order_by('-created_at').values('ai_recommendation')[:1]
    
    users = CustomUser.objects.annotate(
        latest_result=Subquery(latest_test)
    ).order_by('-date_joined')
    
    user_list = []
    for u in users:
        rec = u.latest_result
        rec_job = ""
        if rec:
            try:
                import json
                if isinstance(rec, str):
                    rec_data = json.loads(rec)
                else:
                    rec_data = rec
                rec_job = rec_data.get('recommended_job', '')
            except:
                rec_job = ""
        
        user_list.append({
            'id': u.id,
            'username': u.username,
            'first_name': u.first_name,
            'last_name': u.last_name,
            'email': u.email,
            'phone': u.phone,
            'country': u.country,
            'experience_years': u.experience_years,
            'date_joined': u.date_joined,
            'recommended_job': rec_job,
            'skills': ', '.join(u.skills.values_list('name', flat=True)),
        })
    
    context = {
        'users': user_list,
        'total_users': len(user_list),
    }
    return render(request, 'admin_panel_users.html', context)


@staff_member_required
def admin_panel_user_detail_view(request, user_id):
    from ai_advisor.models import TestResult
    import json
    
    try:
        u = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        from django.http import Http404
        raise Http404("Foydalanuvchi topilmadi")
    
    test_results = TestResult.objects.filter(user=u).order_by('-created_at')
    
    tests_data = []
    for tr in test_results:
        rec = tr.ai_recommendation or {}
        answers = tr.answers_data or {}
        scores = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
        for q, a in answers.items():
            if a in scores:
                scores[a] += 1
        
        tests_data.append({
            'id': tr.id,
            'date': tr.created_at,
            'scores': scores,
            'recommended_job': rec.get('recommended_job', ''),
            'reason': rec.get('reason', ''),
            'answers': answers,
        })
    
    context = {
        'profile': u,
        'tests': tests_data,
        'skills': ', '.join(u.skills.values_list('name', flat=True)),
    }
    return render(request, 'admin_panel_user_detail.html', context)

def home_view(request):
    TARGET_ROLES = [
        'Backend Developer', 'Frontend Developer', 'Mobile App Developer', 'Data Analyst',
        'Data Scientist', 'DevOps Engineer', 'AI Engineer', 'Prompt Engineer', 'UI/UX Designer',
        'Game Developer', 'Product Manager', 'Software Engineer', 'Business Intelligence (BI) Developer',
        'Cybersecurity Specialist', 'Product Designer', 'Business Analyst', 'Blockchain Developer', 'QA Engineer'
    ]

    for role in TARGET_ROLES:
        Category.objects.get_or_create(name=role)

    from django.db.models import Count, Avg

    categories = Category.objects.filter(name__in=TARGET_ROLES).annotate(
        job_count=Count('jobs'),
        avg_min=Avg('jobs__salary_min'),
        avg_max=Avg('jobs__salary_max')
    ).order_by('-job_count')
    
    # Calculate avg_salary dynamically for each category
    for cat in categories:
        cat_avg = 0
        if cat.avg_min and cat.avg_max:
            cat_avg = (cat.avg_min + cat.avg_max) / 2
        elif cat.avg_min:
            cat_avg = cat.avg_min
        elif cat.avg_max:
            cat_avg = cat.avg_max
        cat.avg_salary = int(cat_avg)
            
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

    # Calculate average salary
    salary_jobs = jobs_list.exclude(salary_min__isnull=True).exclude(salary_min=0)
    total_salary = 0
    salary_count = 0
    for job in salary_jobs:
        if job.salary_max:
            total_salary += (job.salary_min + job.salary_max) / 2
        else:
            total_salary += job.salary_min
        salary_count += 1
        
    avg_salary = int(total_salary / salary_count) if salary_count > 0 else 0

    context = {
        'category': category,
        'page_obj': page_obj,
        'country_labels': country_labels,
        'country_data': country_data,
        'avg_salary': avg_salary,
    }
    return render(request, 'category_detail.html', context)

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('admin/', admin_panel_main_view, name='admin_panel_main'),
    path('admin/users/', admin_panel_users_view, name='admin_panel_users'),
    path('admin/users/<int:user_id>/', admin_panel_user_detail_view, name='admin_panel_user_detail'),
    path('', home_view, name='home'),
    path('analytics/category/<int:cat_id>/', category_analytics, name='category_analytics'),
    path('jobs/', all_jobs_view, name='all_jobs'),
    path('sources/', sources_list_view, name='sources_list'),
    path('ai-test/', ai_test_view, name='ai_test'),
    path('ai-chat/', ai_chat_view, name='ai_chat'),
    path('ai-chat-stream/', ai_chat_stream, name='ai_chat_stream'),
    path('api/analytics/', job_analytics_api, name='job_analytics_api'),

    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
]
