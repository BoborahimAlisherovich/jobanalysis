from django.core.management.base import BaseCommand
from jobs.models import Job
import requests

class Command(BaseCommand):
    help = 'Barcha faol vakansiyalarni tekshirib, yopilgan (404) bo\'lsa is_active=False qilish (Real-time sinxronizatsiya)'

    def handle(self, *args, **kwargs):
        active_jobs = Job.objects.filter(is_active=True)
        total_checked = 0
        total_deactivated = 0
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        self.stdout.write(self.style.SUCCESS(f"Vakansiyalarni tekshirish boshlandi... (Jami: {active_jobs.count()})"))
        
        for job in active_jobs:
            total_checked += 1
            url = job.source_url
            
            try:
                # FAQAT bosh sahifasiga so'rov tashlab 404 ni tekshiramiz
                response = requests.head(url, headers=headers, timeout=10, allow_redirects=True)
                
                # Agar 404 qaytsa demak vakansiya yopilgan (o'chirilgan)
                if response.status_code == 404:
                    job.is_active = False
                    job.save()
                    total_deactivated += 1
                    self.stdout.write(self.style.WARNING(f"Yopilgan: {job.title} - {url}"))
                elif response.status_code != 200:
                    # Ehtiyotkorlik yuzasidan GET so'rov orqali qayta tekshiramiz
                    resp_get = requests.get(url, headers=headers, timeout=10)
                    if resp_get.status_code == 404 or "vakansiya topilmadi" in resp_get.text.lower():
                        job.is_active = False
                        job.save()
                        total_deactivated += 1
                        self.stdout.write(self.style.WARNING(f"Yopilgan: {job.title} - {url}"))
                        
            except requests.exceptions.RequestException:
                # Xatolik bersa teginmaymiz, ehtimol sayt vaqtincha ishlamayapti
                continue
                
        self.stdout.write(self.style.SUCCESS(f"Tekshiruv yakunlandi! Tekshirildi: {total_checked}. O'chirildi (Yopildi): {total_deactivated}"))
