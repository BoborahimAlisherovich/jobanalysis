import requests
from bs4 import BeautifulSoup
from django.conf import settings
from .models import Job, Category, Country
import re

def clean_job_category(raw_title):
    """
    Qanday nomdagi ish kelishidan qatiy nazar (katta-kichik harflarda yozilgan bo'lsa ham),
    API dan kelgan ma'lumotni olib (cleaning) uni markaziy ro'yxatdagi kasblarga tirkash funksiyasi.
    """
    title = raw_title.lower()
    
    # Tartib bo'yicha filterlarni solishtirib chiqamiz
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
    elif re.search(r'\b(ux|ui/ux|web designer|product designer)\b', title):
        return 'UI/UX Designer'
    elif re.search(r'\b(game|unity|unreal|c\+\+ developer)\b', title):
        return 'Game Developer'
    elif re.search(r'\b(product manager|po|pm)\b', title):
        return 'Product Manager'
    elif re.search(r'\b(software engineer|software developer|c#|.net)\b', title):
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
        
    return 'Software Engineer' # Agar mos tushmasa umumiy qilib oladi

def scrape_hh_uz_jobs():
    url = "https://api.hh.ru/vacancies?area=97&text=IT" # O'zbekiston (97) IT vakansiyalari
    response = requests.get(url).json()
    
    country, _ = Country.objects.get_or_create(name='Uzbekistan')

    for item in response.get('items', []):
        raw_title = item['name']
        cleaned_category_name = clean_job_category(raw_title)
        
        # Tozalanan kategoriyani bazadan oladi yoki kerakli nomda bilsa yaratadi.
        category, _ = Category.objects.get_or_create(name=cleaned_category_name)
        
        # Agar bu vakansiya bazada bo'lsa, o'tkazib yuboramiz (Ignore duplicate)
        if Job.objects.filter(source_url=item['alternate_url']).exists():
            continue
            
        Job.objects.create(
            title=raw_title, # Original nom saqlanamiz, lekin kategoriya qattiq biriktirildi
            company=item['employer']['name'],
            category=category,
            source='hh.uz',
            country=country,
            source_url=item['alternate_url'],
            salary_min=item['salary']['from'] if item['salary'] else None,
            salary_max=item['salary']['to'] if item['salary'] else None,
            description=item.get('snippet', {}).get('requirement', '') or 'Izohsiz'
        )
    return "Scraping yakunlandi!"