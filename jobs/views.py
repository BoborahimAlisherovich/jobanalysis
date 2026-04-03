from django.shortcuts import render
from django.http import JsonResponse
from rest_framework import generics
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Job, Category
from .serializers import JobSerializer
from django.db.models import Count, Avg, Min, Max
from django.core.paginator import Paginator

def get_macro_category(role_name):
    dev_roles = ['Backend Developer', 'Frontend Developer', 'Mobile App Developer', 'Software Engineer', 'Game Developer', 'Blockchain Developer', 'QA Engineer']
    data_roles = ['Data Analyst', 'Data Scientist', 'AI Engineer', 'Prompt Engineer', 'Business Intelligence (BI) Developer']
    devops_roles = ['DevOps Engineer']
    security_roles = ['Cybersecurity Specialist']
    design_roles = ['UI/UX Designer', 'Product Designer']
    management_roles = ['Product Manager', 'Business Analyst']

    if role_name in dev_roles: return "Development"
    if role_name in data_roles: return "Data & AI"
    if role_name in devops_roles: return "DevOps & Cloud"
    if role_name in security_roles: return "Security"
    if role_name in design_roles: return "Design"
    if role_name in management_roles: return "Management"
    return "Other"

def job_analytics_api(request):
    """
    Returns clean structured JSON with job analytics.
    """
    categories = Category.objects.all()
    results = []

    for cat in categories:
        jobs = Job.objects.filter(category=cat, is_active=True)
        vacancy_count = jobs.count()

        if vacancy_count == 0:
            continue

        # Salary aggregations
        salaries = jobs.filter(salary_min__isnull=False, salary_max__isnull=False)
        sal_min_avg = salaries.aggregate(Avg('salary_min'))['salary_min__avg']
        sal_max_avg = salaries.aggregate(Avg('salary_max'))['salary_max__avg']
        
        if sal_min_avg and sal_max_avg:
            avg_salary = (sal_min_avg + sal_max_avg) / 2
            sal_min = salaries.aggregate(Min('salary_min'))['salary_min__min']
            sal_max = salaries.aggregate(Max('salary_max'))['salary_max__max']
        else:
            avg_salary = 0
            sal_min = "unknown"
            sal_max = "unknown"

        # Top companies
        top_companies_qs = jobs.values('company').annotate(cnt=Count('id')).order_by('-cnt')[:3]
        top_companies = [tc['company'] for tc in top_companies_qs] if top_companies_qs else []

        # Top skills
        top_skills_qs = jobs.exclude(required_skills=None).values('required_skills__name').annotate(cnt=Count('required_skills')).order_by('-cnt')[:3]
        skills = [ts['required_skills__name'] for ts in top_skills_qs] if top_skills_qs else []

        results.append({
            "role": cat.name,
            "category": get_macro_category(cat.name),
            "vacancies": vacancy_count,
            "average_salary": round(avg_salary) if avg_salary else "unknown",
            "salary_range": {
                "min": sal_min,
                "max": sal_max
            },
            "top_companies": top_companies,
            "skills": skills,
            "trend": "increasing" if cat.trend_score > 0 else "stable"
        })

    return JsonResponse(results, safe=False, json_dumps_params={'ensure_ascii': False, 'indent': 2})

class JobListAPIView(generics.ListAPIView):
    queryset = Job.objects.filter(is_active=True)
    serializer_class = JobSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'country', 'job_type']
    search_fields = ['title', 'company', 'required_skills__name']
    ordering_fields = ['posted_at', 'salary_max']

def all_jobs_view(request):
    query = request.GET.get('q', '')
    jobs_qs = Job.objects.filter(is_active=True).select_related('country', 'category')
    
    if query:
        jobs_qs = jobs_qs.filter(title__icontains=query)
        
    jobs_qs = jobs_qs.order_by('-id')
    
    paginator = Paginator(jobs_qs, 30) # Har sahifada 30 tadan ish
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'jobs_list.html', {'page_obj': page_obj, 'query': query})

def sources_list_view(request):
    sources = Job.objects.values('source').annotate(job_count=Count('id')).order_by('-job_count')
    # Pre-calculate top country per source
    enriched_sources = []
    for s in sources:
        top_country = Job.objects.filter(source=s['source']).values('country__name').annotate(cnt=Count('id')).order_by('-cnt').first()
        top_c_name = top_country['country__name'] if top_country else 'Noma\'lum'
        
        enriched_sources.append({
            'source': s['source'],
            'job_count': s['job_count'],
            'top_country': top_c_name
        })
        
    return render(request, 'sources.html', {'sources': enriched_sources})
