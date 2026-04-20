import requests
from bs4 import BeautifulSoup
from django.conf import settings
from .models import Job, Category, Country
import re

def clean_job_category(raw_title):
    title = raw_title.lower()
    if re.search(r'\b(backend|python|django|node|php|ruby|java backend|golang)\b', title):
        return 'Backend Developer'
    elif re.search(r'\b(frontend|react|vue|angular|html|css|ui dev)\b', title): 
        return 'Frontend Developer'
    elif re.search(r'\b(mobile|flutter|ios|android|swift|kotlin|react native)\b', title):
        return 'Mobile App Developer'
    elif re.search(r'\b(data analyst|analyst|data analiz)\b', title):
        return 'Data Analyst'
    elif re.search(r'\b(data scientist|machine learning|ml engineer)\b', title):
        return 'Data Scientist'
    elif re.search(r'\b(devops|sre|system admin|sysadmin|docker|kubernetes)\b', title):
        return 'DevOps Engineer'
    elif re.search(r'\b(ai engineer|artificial intelligence|deep learning|nlp|cv engineer)\b', title):
        return 'AI Engineer'
    elif re.search(r'\b(prompt|promt|gpt|llm engineer)\b', title):
        return 'Prompt Engineer'
    elif re.search(r'\b(product designer)\b', title):
        return 'Product Designer'
    elif re.search(r'\b(ux|ui/ux|web designer)\b', title):
        return 'UI/UX Designer'
    elif re.search(r'\b(game|unity|unreal|c\+\+ developer)\b', title):
        return 'Game Developer'
    elif re.search(r'\b(product manager|po|pm)\b', title):
        return 'Product Manager'
    elif re.search(r'\b(software engineer|software developer|c#|\.net)\b', title):
        return 'Software Engineer'
    elif re.search(r'\b(bi developer|business intelligence|power bi|tableau)\b', title):
        return 'Business Intelligence (BI) Developer'
    elif re.search(r'\b(cybersecurity|security|pentester|infosec)\b', title):   
        return 'Cybersecurity Specialist'
    elif re.search(r'\b(business analyst|ba)\b', title):
        return 'Business Analyst'
    elif re.search(r'\b(blockchain|web3|solidity|smart contract)\b', title):    
        return 'Blockchain Developer'
    elif re.search(r'\b(qa|tester|quality assurance|avtotest)\b', title):       
        return 'QA Engineer'

    return 'Software Engineer'

def scrape_hh_uz_jobs():
    queries = [
        'Data Analyst', 'AI Engineer', 'Blockchain Developer', 'Business Analyst',
        'Business Intelligence', 'Cybersecurity', 'Game Developer', 
        'Product Designer', 'Prompt Engineer', 'IT'
    ]
    url_base = 'https://api.hh.ru/vacancies'
    country, _ = Country.objects.get_or_create(name='Uzbekistan')
    total_added = 0
    
    # HeadHunter API botlarni bloklamasligi uchun User-Agent yuboramiz
    headers = {
        'User-Agent': 'AnalitikLoyiha/1.0 (info@example.com)'
    }

    for q in queries:
        try:
            response = requests.get(url_base + '?area=97&text=' + q + '&per_page=20', headers=headers).json()
            items = response.get('items', [])
            if not items:
                response = requests.get(url_base + '?text=' + q + '&per_page=10', headers=headers).json()
                items = response.get('items', [])

            for item in items:
                raw_title = item['name']
                cleaned_category_name = clean_job_category(raw_title)

                category, _ = Category.objects.get_or_create(name=cleaned_category_name)
                alt_url = item.get('alternate_url')
                if not alt_url or Job.objects.filter(source_url=alt_url).exists():
                    continue

                job_kwargs = {
                    'title': raw_title,
                    'company': item.get('employer', {}).get('name', 'Noma\'lum'),  
                    'category': category,
                    'source': 'hh.uz',
                    'country': country,
                    'source_url': alt_url,
                    'description': item.get('snippet', {}).get('requirement', '') or 'Izohsiz'
                }
                
                if item.get('salary'):
                    job_kwargs['salary_min'] = item['salary'].get('from')
                    job_kwargs['salary_max'] = item['salary'].get('to')
                    job_kwargs['currency'] = item['salary'].get('currency', 'USD')
                else:
                    job_kwargs['salary_min'] = None
                    job_kwargs['salary_max'] = None
                    job_kwargs['currency'] = 'USD'

                Job.objects.create(**job_kwargs)
                total_added += 1
        except Exception as e:
            print('Xato:', e)

    return 'Scraping yakunlandi. ' + str(total_added) + ' ta elon qoshildi.'
