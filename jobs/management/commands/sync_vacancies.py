import requests
import re
from datetime import datetime
from django.core.management.base import BaseCommand
from jobs.models import Job, Category, Country
from users.models import Skill

class Command(BaseCommand):
    help = "Sinxronizatsiya: HH va boshqa API'lardan IT vakansiyalarini olish va tozlash"

    TARGET_ROLES = [
        'Frontend Developer', 'Backend Developer', 'Fullstack Developer',
        'Mobile Developer', 'Data Scientist', 'DevOps Engineer',
        'QA Engineer', 'UI/UX Designer', 'Product Manager', 'Project Manager',
        'System Administrator', 'Database Administrator', 'Security Analyst',
        'AI/ML Engineer', 'Game Developer', 'Blockchain Developer'
    ]

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Vakansiyalarni yig'ish va tozalash jarayoni boshlandi..."))

        seen_hh_urls = []
        seen_remote_urls = []

        for role in self.TARGET_ROLES:
            self.stdout.write(f"Ma'lumotlar {role} uchun olinmoqda...")
            
            category_obj, _ = Category.objects.get_or_create(name=role)
            
            # 1. HH.ru (Rossiya) va HH.uz (O'zbekiston) dan ma'lumot olish
            # 113 - Russia, 97 - Uzbekistan
            hh_urls_ru = self.fetch_from_hh(role, category_obj, area_code=113, manba="hh.ru")
            hh_urls_uz = self.fetch_from_hh(role, category_obj, area_code=97, manba="hh.uz")
            
            seen_hh_urls.extend(hh_urls_ru)
            seen_hh_urls.extend(hh_urls_uz)

            # 2. RemoteOK (Arbeitnow yoki shunga o'xshash public API orqali) ma'lumotlarini olish 
            # LinkedIn, Upwork, Kwork kabi saytlar maxsus token (API Key) va avtorizatsiya so'raydi. (Siz ushbu joyga tokenlarni qo'shishingiz bilan to'liq ishlaydi)
            remotive_urls = self.fetch_from_remotive(role, category_obj)
            seen_remote_urls.extend(remotive_urls)

        # 3. Yopilgan / O'chirilgan vakansiyalarni tozalash (Faqatgina bizning tizimga qo'shilgan lekin hozirgi ro'yxatda yo'q bo'lganlarni o'chiramiz)
        deleted_hh_ru, _ = Job.objects.filter(source='hh.ru').exclude(source_url__in=seen_hh_urls).delete()
        deleted_hh_uz, _ = Job.objects.filter(source='hh.uz').exclude(source_url__in=seen_hh_urls).delete()
        deleted_rm, _ = Job.objects.filter(source='remotive.io').exclude(source_url__in=seen_remote_urls).delete()
        
        # Telegram parser natijalarini tozalash ham xuddi shunday qilinadi
        
        total_deleted = deleted_hh_ru + deleted_hh_uz + deleted_rm
        self.stdout.write(self.style.WARNING(f"Umumiy {total_deleted} ta yopiq yoki o'chirilgan vakansiyalar tizimdan (Big Data) tozalandi."))

        self.stdout.write(self.style.SUCCESS("Sinxronizatsiya muvaffaqiyatli yakunlandi!"))

    def fetch_from_hh(self, role, category_obj, area_code=113, manba="hh.ru"):
        """
        HH orqali berilgan rol (mansab) bo'yicha vakansiyalarni yig'adi.
        Asosan IT yo'nalishi (category 96: Programmer, developer) uchun text filter ishlatamiz.
        """
        url = f"https://api.hh.ru/vacancies"
        params = {
            'text': role,
            'search_field': 'name',
            'per_page': 100,  # Bir safarda 100 ta olish
            'page': 0,
            'area': area_code  # 97 for UZ, 113 for RU
        }

        headers = {
            # HH bloklamasligi uchun professional ro'yxatdan o'tgan nom qo'yildi
            'User-Agent': 'api-test-agent' 
        }

        seen_urls = []

        while params['page'] < 5:  # Maksimum 5 sahifa (500 ta vakansiya bitta rolga)
            try:
                response = requests.get(url, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()
            except requests.exceptions.RequestException as e:
                self.stdout.write(self.style.ERROR(f"API Xatosi ({manba}): {e}"))
                break

            items = data.get('items', [])
            if not items:
                break
                
            for item in items:
                source_url = item.get('alternate_url')
                if not source_url:
                    continue
                
                seen_urls.append(source_url)
                self.process_hh_item(item, category_obj, source_url, manba)

            params['page'] += 1

        return seen_urls

    def process_hh_item(self, item, category_obj, source_url, manba):
        # Employer
        employer = item.get('employer', {})
        company_name = employer.get('name', 'Noma\'lum kompaniya')

        # Area (davlatni vizual ravishda joy nomi bilan birlashtiramiz yoki mamlakat ID)
        area = item.get('area', {})
        country_name = area.get('name', 'Noma\'lum')
        country_obj, _ = Country.objects.get_or_create(name=country_name)
        
        # Oylik
        salary_info = item.get('salary')
        salary_min = None
        salary_max = None
        currency = 'USD'
        if salary_info:
            salary_min = salary_info.get('from')
            salary_max = salary_info.get('to')
            currency = salary_info.get('currency', 'UZS')
            
        # Ta'rif (API kichik responseni beradi tasvir snippet bilan)
        description = item.get('snippet', {}).get('requirement', '') or 'Tarif mavjud emas'
        
        # Schedule (Bandlik turi)
        schedule = item.get('schedule', {}).get('id', 'fullDay')
        if schedule == 'remote':
            job_type = 'remote'
        elif schedule == 'partDay':
            job_type = 'part_time'
        else:
            job_type = 'full_time'

        # Job modeliga kiritish yoki yangilash
        defaults = {
            'title': item.get('name'),
            'company': company_name,
            'category': category_obj,
            'country': country_obj,
            'description': self.clean_html(description),
            'job_type': job_type,
            'salary_min': salary_min,
            'salary_max': salary_max,
            'currency': currency,
            'source': manba,
            'is_active': True
        }

        # Bazada borligini url orqali tekshirib, yangilaydi (update_or_create)
        job_obj, created = Job.objects.update_or_create(
            source_url=source_url,
            defaults=defaults
        )

    def fetch_from_remotive(self, role, category_obj):
        """
        LinkedIn, Upwork yoki GitHub vakansiyalari yopiq, o'rniga Global Remote IT vakansiyalarni 
        (remotive.io bepul public API) yig'uvchi funksiya. G'oya hammasi uchun bir xil (Big Data qonuniyati)
        """
        # Remotive qattiq so'rovlarni ruxsat etadi, masalan "Software Development" da 500 ta remote job qaytadi.
        url = "https://remotive.com/api/remote-jobs"
        params = {'search': role, 'limit': 150} # Har bir rolga o'rtacha 150 ta.

        seen_urls = []
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                jobs_data = response.json().get('jobs', [])
                for item in jobs_data:
                    source_url = item.get('url')
                    if not source_url:
                        continue
                    seen_urls.append(source_url)
                    
                    # Custom mapping logic
                    company = item.get('company_name', 'No Company')
                    country_name = item.get('candidate_required_location', 'Global/Remote')
                    country_obj, _ = Country.objects.get_or_create(name=country_name)
                    
                    raw_desc = item.get('description', '')
                    cleaned_desc = self.clean_html(raw_desc)[:3000] # Ba'zi desclar HTML bilan birga keladi va juda uzun
                    
                    defaults = {
                        'title': item.get('title'),
                        'company': company,
                        'category': category_obj,
                        'country': country_obj,
                        'description': cleaned_desc,
                        'job_type': 'remote', # Remotive faqat remote beradi, Upwork/Githus singari!
                        'source': 'remotive.io',
                        'is_active': True
                    }
                    Job.objects.update_or_create(
                        source_url=source_url,
                        defaults=defaults
                    )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Remote API (Remotive) Xatosi: {e}"))
            
        return seen_urls

    def update_from_telegram_channels(self):
        """
        Telegram bot orqali ('@vacancy_uz', '@itvakansiyalar' kabi kanallaridan) ma'lumotlarni yig'ish.
        Telethon (MTProto API) ni o'rnatish ($ pip install telethon) va
        my.telegram.org'dan API_ID va API_HASH larni olgach, mana shunday shaklda integratsiya qilasiz:
        (Hozir faqat arxitektura sifatida ko'rsatilgan!)
        """
        pass
        
    def clean_html(self, raw_html):
        """Oddiygina HTML taglarini tozalash funksiyasi"""
        if not raw_html:
            return ""
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', raw_html)
        return cleantext.strip()
