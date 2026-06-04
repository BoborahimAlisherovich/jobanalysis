from django.core.management.base import BaseCommand
from jobs.models import Job, Category, Country
import requests
import re

class Command(BaseCommand):
    help = 'HH.uz dan IT va Dasturlash vakansiyalarini pars qilish'

    def handle(self, *args, **kwargs):
        country, _ = Country.objects.get_or_create(name='Uzbekistan')
        category, _ = Category.objects.get_or_create(name='IT / Dasturlash')
        
        # IT ga mos keladigan qidiruv so'zlari
        queries = ["Developer", "Programmer", "Dasturchi", "Backend", "Frontend", "Mobile", "DevOps", "QA", "Data Scientist"]
        
        headers = {"User-Agent": "AuraCareerParser/1.0 (info@auracareer.uz)"}
        
        total_added = 0
        self.stdout.write(self.style.SUCCESS("HH.uz skraper ishga tushdi (Faqat IT vakansiyalar)..."))
        
        for q in queries:
            self.stdout.write(f"Qidirilmoqda: {q}")
            url = "https://api.hh.ru/vacancies"
            params = {
                "text": q,
                "area": 97, # 97 - O'zbekiston
                "per_page": 50
            }
            
            try:
                resp = requests.get(url, params=params, headers=headers, timeout=15)
                if resp.status_code != 200:
                    self.stderr.write(self.style.ERROR(f"API xatosi: {resp.status_code} - {q}"))
                    continue
                    
                data = resp.json()
                items = data.get('items', [])
                
                for item in items:
                    post_url = item.get('alternate_url')
                    if not post_url or Job.objects.filter(source_url=post_url).exists():
                        continue # Duplikat
                        
                    # Batafsil ma'lumot olish
                    detail_resp = requests.get(item['url'], headers=headers, timeout=10)
                    detail_data = detail_resp.json() if detail_resp.status_code == 200 else {}
                    
                    salary = item.get('salary') or {}
                    salary_min = salary.get('from')
                    salary_max = salary.get('to')
                    currency = salary.get('currency', 'UZS')
                    
                    # HTML teglarni tozalash
                    desc = detail_data.get('description', '')
                    desc_clean = re.sub('<[^<]+>', '', desc).strip()
                    
                    job_type = item.get('employment', {}).get('id', 'full_time')
                    if job_type == 'full': job_type = 'full_time'
                    elif job_type == 'part': job_type = 'part_time'
                    else: job_type = 'full_time'
                    
                    Job.objects.create(
                        title=item.get('name'),
                        company=item.get('employer', {}).get('name', 'Noma\'lum'),
                        category=category,
                        country=country,
                        description=desc_clean[:2000], 
                        job_type=job_type,
                        salary_min=salary_min,
                        salary_max=salary_max,
                        currency=currency,
                        source_url=post_url,
                        source='hh.uz'
                    )
                    total_added += 1
                    
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Xato ({q}): {str(e)}"))
                
        self.stdout.write(self.style.SUCCESS(f"HH.uz skraping yakunlandi! Qo'shilgan IT elonlar: {total_added}"))
