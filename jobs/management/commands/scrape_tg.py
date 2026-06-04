from django.core.management.base import BaseCommand
from jobs.models import Job, Category, Country
from jobs.tasks import clean_job_category
import requests
from bs4 import BeautifulSoup
import re
import datetime

class Command(BaseCommand):
    help = 'Telegram kanallaridan vakansiyalarni yig\'ish (Web Preview orqali)'

    def handle(self, *args, **kwargs):
        channels = ['it_vakansiya_uz']
        country, _ = Country.objects.get_or_create(name='Uzbekistan')
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        total_added = 0
        
        self.stdout.write(self.style.SUCCESS("Telegram skraper ishga tushdi..."))
        
        for channel in channels:
            url = f"https://t.me/s/{channel}"
            self.stdout.write(f"Kanal tekshirilmoqda: @{channel}")
            
            try:
                response = requests.get(url, headers=headers, timeout=15)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                messages = soup.find_all('div', class_='tgme_widget_message_text')
                message_links = soup.find_all('a', class_='tgme_widget_message_date')
                
                # Zip messages and their links
                for msg, link_tag in zip(messages, message_links):
                    text = msg.get_text(separator='\n')
                    post_url = link_tag.get('href')
                    
                    if not text or not post_url:
                        continue
                        
                    # Dublicate tekshiruvi
                    if Job.objects.filter(source_url=post_url).exists():
                        continue
                        
                    text_lower = text.lower()
                    # Aniq struktura bormi tekshiramiz
                    if "idora:" in text_lower or "maosh:" in text_lower or "texnologiya:" in text_lower or "xodim kerak:" in text_lower:
                        
                        # Regex orqali qirqib olish
                        idora_match = re.search(r'(?:🏢\s*)?Idora:\s*([^\n]+)', text, re.IGNORECASE)
                        idora = idora_match.group(1).strip() if idora_match else f"Telegram: @{channel}"
                        
                        maosh_match = re.search(r'(?:💰\s*)?Maosh:\s*([^\n]+)', text, re.IGNORECASE)
                        maosh_text = maosh_match.group(1).strip() if maosh_match else ""
                        
                        hudud_match = re.search(r'(?:🌐\s*)?Hudud:\s*([^\n]+)', text, re.IGNORECASE)
                        hudud = hudud_match.group(1).strip() if hudud_match else "Noma'lum"
                        
                        # Lavozim nomi odatda birinchi qatorda yoki idora yonida bo'ladi
                        lines = [line.strip() for line in text.split('\n') if line.strip()]
                        raw_title = lines[0][:255]
                        if "xodim kerak" in raw_title.lower() and len(lines) > 1:
                            raw_title = lines[1][:255] # keyingi qatorni olamiz
                        
                        # Kategoriyani aniqlash
                        cleaned_category_name = clean_job_category(text)
                        category, _ = Category.objects.get_or_create(name=cleaned_category_name)
                        
                        # Maoshni formatlash (masalan "3-7 mln" -> 3000000, 7000000)
                        salary_min = None
                        salary_max = None
                        currency = 'UZS'
                        
                        if maosh_text:
                            if '$' in maosh_text:
                                currency = 'USD'
                            
                            nums = re.findall(r'\d+', maosh_text.replace(' ', ''))
                            if nums:
                                if len(nums) >= 2:
                                    s_min, s_max = int(nums[0]), int(nums[1])
                                    if 'mln' in maosh_text.lower() or 'million' in maosh_text.lower():
                                        s_min *= 1000000
                                        s_max *= 1000000
                                    salary_min, salary_max = s_min, s_max
                                elif len(nums) == 1:
                                    s_min = int(nums[0])
                                    if 'mln' in maosh_text.lower() or 'million' in maosh_text.lower():
                                        s_min *= 1000000
                                    salary_min = s_min
                        
                        Job.objects.create(
                            title=raw_title,
                            company=idora,
                            category=category,
                            country=country,
                            description=text[:2000] + f"\n\nHudud: {hudud}",
                            job_type='full_time',
                            salary_min=salary_min,
                            salary_max=salary_max,
                            currency=currency,
                            source_url=post_url,
                            source='telegram'
                        )
                        total_added += 1
                        
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Xato (@{channel}): {str(e)}"))
                
        self.stdout.write(self.style.SUCCESS(f"Skraping yakunlandi! Qo'shilgan elonlar: {total_added}"))
