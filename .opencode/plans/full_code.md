# AURA Career — To'liq kod

## Fayl 1: jobs/management/commands/transliterate_uz.py

```python
import re

CYRILLIC_TO_LATIN = {
    'А': 'A', 'а': 'a', 'Б': 'B', 'б': 'b', 'В': 'V', 'в': 'v',
    'Г': 'G', 'г': 'g', 'Д': 'D', 'д': 'd', 'Е': 'Ye', 'е': 'ye',
    'Ё': 'Yo', 'ё': 'yo', 'Ж': 'J', 'ж': 'j', 'З': 'Z', 'з': 'z',
    'И': 'I', 'и': 'i', 'Й': 'Y', 'й': 'y', 'К': 'K', 'к': 'k',
    'Л': 'L', 'л': 'l', 'М': 'M', 'м': 'm', 'Н': 'N', 'н': 'n',
    'О': 'O', 'о': 'o', 'П': 'P', 'п': 'p', 'Р': 'R', 'р': 'r',
    'С': 'S', 'с': 's', 'Т': 'T', 'т': 't', 'У': 'U', 'у': 'u',
    'Ф': 'F', 'ф': 'f', 'Х': 'X', 'х': 'x', 'Ц': 'S', 'ц': 's',
    'Ч': 'Ch', 'ч': 'ch', 'Ш': 'Sh', 'ш': 'sh', 'Щ': 'Sh', 'щ': 'sh',
    'Ъ': '', 'ъ': '', 'Ы': 'Y', 'ы': 'y', 'Ь': '', 'ь': '',
    'Э': 'E', 'э': 'e', 'Ю': 'Yu', 'ю': 'yu', 'Я': 'Ya', 'я': 'ya',
    'Ў': "O'", 'ў': "o'", 'Қ': 'Q', 'қ': 'q', 'Ғ': "G'", 'ғ': "g'",
    'Ҳ': 'H', 'ҳ': 'h',
}

def cyrillic_to_latin(text):
    result = []
    for c in text:
        result.append(CYRILLIC_TO_LATIN.get(c, c))
    return ''.join(result)

def to_uzbek_latin(text):
    if not text or not text.strip():
        return text
    has_cyrillic = bool(re.search(r'[А-Яа-яЁёЎўҚқҒғҲҳ]', text))
    if has_cyrillic:
        return cyrillic_to_latin(text)
    return text

def translate_to_uzbek(text, src='auto'):
    if not text or not text.strip():
        return text
    try:
        from deep_translator import GoogleTranslator
        translated = GoogleTranslator(source=src, target='uz').translate(text[:5000])
        if translated:
            return translated
    except Exception:
        pass
    return to_uzbek_latin(text)
```

## Fayl 2: jobs/management/commands/parsers/__init__.py

```python
from . import hh_uz
from . import olx_uz
from . import apwork_uz
from . import kwork_ru
from . import teamwork_uz
from . import linkedin_rapidapi

__all__ = ['hh_uz', 'olx_uz', 'apwork_uz', 'kwork_ru', 'teamwork_uz', 'linkedin_rapidapi']
```

## Fayl 3: jobs/management/commands/parsers/hh_uz.py

```python
import requests
import re
from jobs.models import Job, Category, Country
from ..transliterate_uz import translate_to_uzbek

HEADERS = {"User-Agent": "AuraCareerParser/1.0 (info@auracareer.uz)"}

IT_QUERIES = [
    "Developer", "Dasturchi", "Backend", "Frontend",
    "Mobile", "DevOps", "QA", "Data Scientist",
    "AI", "Machine Learning", "Python", "Java",
    "JavaScript", "React", "Flutter", "Android",
    "iOS", "UI/UX", "Product Manager", "Scrum",
    "1C", "System Administrator", "Network Engineer",
    "Security", "Game Developer", "Blockchain",
]

def run():
    total = 0
    country, _ = Country.objects.get_or_create(name="O'zbekiston", code="UZ")
    cat_cache = {}

    for q in IT_QUERIES:
        try:
            resp = requests.get(
                "https://api.hh.ru/vacancies",
                params={"text": q, "area": 97, "per_page": 50},
                headers=HEADERS, timeout=15
            )
            if resp.status_code != 200:
                continue
            data = resp.json()
            for item in data.get('items', []):
                post_url = item.get('alternate_url')
                if not post_url or Job.objects.filter(source_url=post_url).exists():
                    continue

                title = item.get('name', '')
                company = item.get('employer', {}).get('name', "Noma'lum")
                title_uz = translate_to_uzbek(title)
                company_uz = translate_to_uzbek(company)

                cat_name = 'IT / Dasturlash'
                spec = item.get('specializations', [])
                if spec:
                    profarea = spec[0].get('profarea_name', '')
                    if profarea:
                        cat_name_uz = translate_to_uzbek(profarea)
                        cat_name = cat_name_uz if cat_name_uz and len(cat_name_uz) < 100 else profarea

                if cat_name not in cat_cache:
                    cat_cache[cat_name] = Category.objects.get_or_create(name=cat_name)[0]
                category = cat_cache[cat_name]

                detail_resp = requests.get(item['url'], headers=HEADERS, timeout=10)
                detail_data = detail_resp.json() if detail_resp.status_code == 200 else {}
                desc = detail_data.get('description', '')
                desc_clean = re.sub(r'<[^>]+>', '', desc or '').strip()
                desc_uz = translate_to_uzbek(desc_clean)

                salary = item.get('salary') or {}
                salary_min = salary.get('from')
                salary_max = salary.get('to')
                currency = salary.get('currency', 'UZS')

                job_type = item.get('employment', {}).get('id', 'full_time')
                if job_type == 'full': job_type = 'full_time'
                elif job_type == 'part': job_type = 'part_time'
                elif job_type == 'remote': job_type = 'remote'
                else: job_type = 'full_time'

                keys = detail_data.get('key_skills', [])
                skills_text = ', '.join([s.get('name', '') for s in keys])

                job = Job.objects.create(
                    title=title_uz[:255],
                    company=company_uz[:255],
                    category=category,
                    country=country,
                    description=desc_uz[:5000] if desc_uz else '',
                    job_type=job_type,
                    salary_min=salary_min,
                    salary_max=salary_max,
                    currency=currency,
                    source_url=post_url,
                    source='hh.uz',
                )
                if skills_text:
                    from users.models import Skill
                    for sname in [s.strip() for s in skills_text.split(',') if s.strip()]:
                        skill, _ = Skill.objects.get_or_create(name=sname[:100])
                        job.required_skills.add(skill)
                total += 1
        except Exception as e:
            print(f"HH.uz xato ({q}): {e}")
    return total
```

## Fayl 4: jobs/management/commands/parsers/olx_uz.py

```python
import requests
from bs4 import BeautifulSoup
from jobs.models import Job, Category, Country
from ..transliterate_uz import translate_to_uzbek

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "uz-UZ,uz;q=0.9",
}

URLS = [
    "https://www.olx.uz/rabota/it-kompyutery/",
    "https://www.olx.uz/rabota/it-kompyutery/programmirovanie/",
    "https://www.olx.uz/rabota/it-kompyutery/sistemnoe-administrirovanie/",
]

def run():
    total = 0
    country, _ = Country.objects.get_or_create(name="O'zbekiston", code="UZ")
    category, _ = Category.objects.get_or_create(name="IT / Dasturlash")

    for url in URLS:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, 'lxml')
            items = soup.select('div[data-cy="l-card"], li.offer-wrapper, div[class*="offer"]')

            for item in items:
                link = item.select_one('a[href]')
                if not link:
                    continue
                href = link.get('href', '')
                if not href.startswith('http'):
                    href = 'https://www.olx.uz' + href

                if Job.objects.filter(source_url=href).exists():
                    continue

                title_el = item.select_one('h6, .title, a[data-cy="listing-ad-title"], span[class*="title"]')
                title = title_el.get_text(strip=True) if title_el else "Noma'lum"
                title_uz = translate_to_uzbek(title)

                price_el = item.select_one('[data-testid="ad-price"], .price, p[class*="price"], h3[class*="price"]')
                price_text = price_el.get_text(strip=True) if price_el else ''
                salary_min = salary_max = None
                currency = 'UZS'
                if price_text:
                    nums = [int(s.replace(' ', '')) for s in price_text.split() if s.replace(' ', '').isdigit()]
                    if nums:
                        salary_min = nums[0]
                        salary_max = nums[-1] if len(nums) > 1 else nums[0]
                    if '$' in price_text: currency = 'USD'
                    elif 'som' in price_text.lower() or "so'm" in price_text.lower(): currency = 'UZS'

                desc_el = item.select_one('p[class*="description"], div[class*="description"], .desc')
                description = desc_el.get_text(strip=True) if desc_el else ''
                desc_uz = translate_to_uzbek(description)

                company_el = item.select_one('a[class*="seller"], span[class*="seller"], div[class*="seller"]')
                company = company_el.get_text(strip=True) if company_el else 'OLX foydalanuvchisi'
                company_uz = translate_to_uzbek(company)

                Job.objects.create(
                    title=title_uz[:255], company=company_uz[:255], category=category,
                    country=country, description=desc_uz[:5000] if desc_uz else '',
                    job_type='full_time', salary_min=salary_min, salary_max=salary_max,
                    currency=currency, source_url=href, source='olx.uz',
                )
                total += 1
        except Exception as e:
            print(f"OLX xato ({url}): {e}")
    return total
```

## Fayl 5: jobs/management/commands/parsers/apwork_uz.py

```python
import requests
from bs4 import BeautifulSoup
from jobs.models import Job, Category, Country
from ..transliterate_uz import translate_to_uzbek

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "uz-UZ,uz;q=0.9",
}

def run():
    total = 0
    country, _ = Country.objects.get_or_create(name="O'zbekiston", code="UZ")
    category, _ = Category.objects.get_or_create(name="IT / Dasturlash")

    for url in ["https://apwork.uz/jobs", "https://apwork.uz/jobs?category=it"]:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code != 200: continue
            soup = BeautifulSoup(resp.text, 'lxml')
            for item in soup.select('a[href*="/job/"], .job-item, .vacancy-card, .card, div[class*="job"]'):
                href = item.get('href', '')
                if not href:
                    link = item.select_one('a[href]')
                    href = link.get('href', '') if link else ''
                if not href: continue
                if not href.startswith('http'):
                    href = 'https://apwork.uz' + ('/' if not href.startswith('/') else '') + href
                if Job.objects.filter(source_url=href).exists(): continue

                title = (item.select_one('h2, h3, h4, .title, .job-title') or item).get_text(strip=True)[:255]
                company = (item.select_one('.company, .employer, .author') or item).get_text(strip=True)[:255] or 'Apwork'
                desc = (item.select_one('.description, .desc, p, .short-description') or item).get_text(strip=True)[:5000]

                price_el = item.select_one('.price, .salary, .budget')
                price_text = price_el.get_text(strip=True) if price_el else ''
                salary_min = salary_max = None
                if price_text:
                    nums = [int(s.replace(' ', '')) for s in price_text.split() if s.replace(' ', '').isdigit()]
                    if nums: salary_min, salary_max = nums[0], nums[-1] if len(nums) > 1 else nums[0]

                Job.objects.create(
                    title=translate_to_uzbek(title)[:255], company=translate_to_uzbek(company)[:255],
                    category=category, country=country, description=translate_to_uzbek(desc)[:5000],
                    job_type='full_time', salary_min=salary_min, salary_max=salary_max,
                    currency='UZS', source_url=href, source='apwork.uz',
                )
                total += 1
        except Exception as e:
            print(f"Apwork xato ({url}): {e}")
    return total
```

## Fayl 6: jobs/management/commands/parsers/kwork_ru.py

```python
import requests
from bs4 import BeautifulSoup
from jobs.models import Job, Category, Country
from ..transliterate_uz import translate_to_uzbek

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
}

CATEGORIES = ["razrabotka-sajtov", "programmirovanie", "mobile-apps", "boty", "skripty"]

def run():
    total = 0
    country, _ = Country.objects.get_or_create(name="O'zbekiston", code="UZ")
    category, _ = Category.objects.get_or_create(name="IT / Dasturlash")

    for cat in CATEGORIES:
        for page in range(1, 4):
            try:
                resp = requests.get(f"https://kwork.ru/projects?category={cat}&page={page}", headers=HEADERS, timeout=15)
                if resp.status_code != 200: continue
                soup = BeautifulSoup(resp.text, 'lxml')
                for item in soup.select('.project-card, .wants-card, .card, div[class*="project"]'):
                    link = item.select_one('a[href*="/projects/"], a[href*="/project/"]')
                    if not link: continue
                    href = link.get('href', '')
                    if not href or 'kwork.ru' not in href:
                        href = 'https://kwork.ru' + ('/' if not href.startswith('/') else '') + href
                    if Job.objects.filter(source_url=href).exists(): continue

                    title = (item.select_one('.project-title, .wants-title, h2, h3, .card-title') or item).get_text(strip=True)[:255]
                    desc = (item.select_one('.project-description, .wants-description, p') or item).get_text(strip=True)[:5000]
                    company = (item.select_one('.username, .seller, .author') or item).get_text(strip=True)[:255] or 'Kwork'

                    price_el = item.select_one('.price, .cost, .budget, span[class*="price"]')
                    price_text = price_el.get_text(strip=True) if price_el else ''
                    salary_min = salary_max = None
                    if price_text:
                        nums = [int(s.replace(' ', '')) for s in price_text.split() if s.replace(' ', '').isdigit()]
                        if nums: salary_min, salary_max = nums[0], nums[-1] if len(nums) > 1 else nums[0]

                    Job.objects.create(
                        title=translate_to_uzbek(title)[:255], company=translate_to_uzbek(company)[:255],
                        category=category, country=country, description=translate_to_uzbek(desc)[:5000],
                        job_type='remote', salary_min=salary_min, salary_max=salary_max,
                        currency='UZS', source_url=href, source='kwork.ru',
                    )
                    total += 1
            except Exception as e:
                print(f"Kwork xato ({cat}): {e}")
    return total
```

## Fayl 7: jobs/management/commands/parsers/teamwork_uz.py

```python
import requests
from bs4 import BeautifulSoup
from jobs.models import Job, Category, Country
from ..transliterate_uz import translate_to_uzbek

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
}

def run():
    total = 0
    country, _ = Country.objects.get_or_create(name="O'zbekiston", code="UZ")
    category, _ = Category.objects.get_or_create(name="IT / Dasturlash")

    for url in ["https://teamwork.uz/vacancies", "https://teamwork.uz/vacancies?category=it"]:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code != 200: continue
            soup = BeautifulSoup(resp.text, 'lxml')
            for item in soup.select('a[href*="/vacancy/"], .vacancy-item, .job-card, .card, tr'):
                href = item.get('href', '')
                if not href:
                    link = item.select_one('a[href]')
                    href = link.get('href', '') if link else ''
                if not href: continue
                if not href.startswith('http'):
                    href = 'https://teamwork.uz' + ('/' if not href.startswith('/') else '') + href
                if Job.objects.filter(source_url=href).exists(): continue

                title = (item.select_one('h2, h3, h4, .title, .vacancy-title') or item).get_text(strip=True)[:255]
                company = (item.select_one('.company, .employer, .organization') or item).get_text(strip=True)[:255] or 'Teamwork'
                desc = (item.select_one('.description, .desc, p, .requirements') or item).get_text(strip=True)[:5000]

                price_el = item.select_one('.salary, .price, .budget')
                price_text = price_el.get_text(strip=True) if price_el else ''
                salary_min = salary_max = None
                if price_text:
                    nums = [int(s.replace(' ', '')) for s in price_text.split() if s.replace(' ', '').isdigit()]
                    if nums: salary_min, salary_max = nums[0], nums[-1] if len(nums) > 1 else nums[0]

                Job.objects.create(
                    title=translate_to_uzbek(title)[:255], company=translate_to_uzbek(company)[:255],
                    category=category, country=country, description=translate_to_uzbek(desc)[:5000],
                    job_type='full_time', salary_min=salary_min, salary_max=salary_max,
                    currency='UZS', source_url=href, source='teamwork.uz',
                )
                total += 1
        except Exception as e:
            print(f"Teamwork xato ({url}): {e}")
    return total
```

## Fayl 8: jobs/management/commands/parsers/linkedin_rapidapi.py

```python
import os, requests
from jobs.models import Job, Category, Country
from ..transliterate_uz import translate_to_uzbek

RAPIDAPI_KEY = os.environ.get('RAPIDAPI_KEY', '')
RAPIDAPI_HOST = "linkedin-jobs-scraper-api.p.rapidapi.com"

SEARCH_KEYWORDS = [
    "developer", "engineer", "software", "python", "java",
    "javascript", "react", "flutter", "devops", "data scientist",
    "AI", "machine learning", "product manager", "backend", "frontend",
]

def run():
    if not RAPIDAPI_KEY:
        print("LinkedIn: RAPIDAPI_KEY topilmadi, o'tkazib yuborildi")
        return 0

    total = 0
    country, _ = Country.objects.get_or_create(name="O'zbekiston", code="UZ")
    cat, _ = Category.objects.get_or_create(name="IT / Dasturlash")
    headers = {"X-RapidAPI-Key": RAPIDAPI_KEY, "X-RapidAPI-Host": RAPIDAPI_HOST, "Content-Type": "application/json"}

    for keyword in SEARCH_KEYWORDS[:5]:
        try:
            resp = requests.post(
                f"https://{RAPIDAPI_HOST}/jobs/search",
                json={"keywords": keyword, "location": "Uzbekistan", "limit": 25},
                headers=headers, timeout=20
            )
            if resp.status_code != 200: continue

            items = resp.json()
            if isinstance(items, dict): items = items.get('data', items)

            for item in items:
                post_url = item.get('url', item.get('link', item.get('jobUrl', '')))
                if not post_url or Job.objects.filter(source_url=post_url).exists(): continue

                title = translate_to_uzbek(item.get('title', item.get('jobTitle', "Noma'lum")))[:255]
                company = translate_to_uzbek(item.get('company', item.get('companyName', 'LinkedIn')))[:255]
                desc = translate_to_uzbek(item.get('description', item.get('jobDescription', '')))[:5000]

                salary_text = item.get('salary', item.get('salaryRange', ''))
                salary_min = salary_max = None
                if salary_text:
                    nums = [int(s.replace(',', '')) for s in salary_text.split() if s.replace(',', '').isdigit()]
                    if nums: salary_min, salary_max = nums[0], nums[-1] if len(nums) > 1 else nums[0]

                Job.objects.create(
                    title=title, company=company, category=cat, country=country,
                    description=desc, job_type='full_time',
                    salary_min=salary_min, salary_max=salary_max, currency='USD',
                    source_url=post_url, source='linkedin',
                )
                total += 1
        except Exception as e:
            print(f"LinkedIn xato ({keyword}): {e}")
    return total
```

## Fayl 9: jobs/management/commands/scrape_all.py

```python
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Barcha manbalardan IT vakansiyalarini yig'ish"

    def handle(self, *args, **options):
        from .parsers import hh_uz, olx_uz, apwork_uz, kwork_ru, teamwork_uz
        from .parsers.linkedin_rapidapi import run as linkedin_run

        parsers = [
            ("HH.uz", hh_uz.run), ("OLX.uz", olx_uz.run),
            ("Apwork.uz", apwork_uz.run), ("Kwork.ru", kwork_ru.run),
            ("Teamwork.uz", teamwork_uz.run),
        ]

        total = 0
        for name, func in parsers:
            try:
                count = func()
                total += count
                self.stdout.write(self.style.SUCCESS(f"✅ {name}: {count} ta"))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"❌ {name}: {e}"))

        try:
            ln = linkedin_run()
            total += ln
            if ln: self.stdout.write(self.style.SUCCESS(f"✅ LinkedIn: {ln} ta"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"❌ LinkedIn: {e}"))

        from jobs.models import Job
        active = Job.objects.filter(is_active=True).count()
        self.stdout.write(self.style.SUCCESS(f"\n📊 Jami qo'shilgan: {total} ta"))
        self.stdout.write(f"📊 Bazadagi aktiv vakansiyalar: {active} ta")
```

## Fayl 10: ai_advisor/dataset_generator.py

```python
import json, random
from django.db.models import Min, Max, Count, Q

PAEI_ROLES = {
    'P': {
        'name': 'Producer (Natijaga yo\'naltirilgan)',
        'categories': ['Backend Developer', 'Software Engineer', 'DevOps Engineer',
                       'Mobile App Developer', 'Game Developer', 'Python Developer',
                       'Java Developer', 'Flutter Developer', 'Android Developer',
                       'C++ Developer', 'Go Developer', 'Rust Developer'],
        'skills': ['Python', 'Java', 'JavaScript', 'Django', 'Flask', 'Spring Boot',
                   'Docker', 'Kubernetes', 'AWS', 'Git', 'SQL', 'Linux', 'C++', 'Go', 'Rust'],
        'descriptions': [
            'texnik muammolarni hal qilishga qiziqasiz',
            'natijaga yo\'naltirilgan va mantiqiy fikrlaysiz',
            'kod yozish va texnik yechimlar sizga yoqadi',
        ],
        'advice': [
            'Amaliy loyihalar yarating va GitHub da joylang',
            'Algoritmik masalalarni muntazam yechib boring',
            'Eng so\'nggi texnologiyalarni kuzatib boring',
        ],
        'future': 'Backend/DevOps sohasida o\'sish, keyin AI/ML ga o\'tish',
    },
    'A': {
        'name': 'Administrator (Tizimli va tartibli)',
        'categories': ['QA Engineer', 'Data Analyst', 'Business Analyst',
                       'Cybersecurity Specialist', 'System Administrator',
                       'Database Administrator', 'IT Auditor', 'Data Engineer'],
        'skills': ['SQL', 'Excel', 'Tableau', 'Power BI', 'Python', 'Selenium',
                   'Jira', 'TestRail', 'Linux', 'Networking', 'PostgreSQL', 'MongoDB'],
        'descriptions': [
            'tizimli va tartibni sevasiz',
            'ma\'lumotlar bilan ishlashga qiziqasiz',
            'aniqlik va sifat siz uchun muhim',
        ],
        'advice': [
            'SQL va ma\'lumotlar tahlili bo\'yicha kurslarni o\'ting',
            'ISTQB sertifikatini oling',
            'BI vositalarini (Power BI, Tableau) o\'rganing',
        ],
        'future': 'Data Analyst dan Data Engineer yoki Security mutaxassisi',
    },
    'E': {
        'name': 'Entrepreneur (Innovator va ijodkor)',
        'categories': ['UI/UX Designer', 'Product Manager', 'AI Engineer',
                       'Product Designer', 'Blockchain Developer', 'Prompt Engineer',
                       'Machine Learning Engineer', 'Data Scientist'],
        'skills': ['Figma', 'Adobe XD', 'Python', 'TensorFlow', 'PyTorch',
                   'JavaScript', 'React', 'Node.js', 'Solidity', 'UI/UX', 'Agile'],
        'descriptions': [
            'innovatsion g\'oyalar generatsiya qilasiz',
            'yangi texnologiyalarga qiziqasiz',
            'ijodiy fikrlash qobiliyatingiz yuqori',
        ],
        'advice': [
            'AI/ML va sun\'iy intellekt kurslarini boshlang',
            'UI/UX dizayn vositalarini (Figma) o\'rganing',
            'Startup ekotizimida qatnashing',
        ],
        'future': 'AI/Product sohasida yetakchi bo\'lish yoki o\'z startapini yaratish',
    },
    'I': {
        'name': 'Integrator (Jamoa va muloqotga yo\'naltirilgan)',
        'categories': ['Project Manager', 'Scrum Master', 'HR IT',
                       'Frontend Developer', 'Business Intelligence Developer',
                       'IT Recruiter', 'Technical Writer'],
        'skills': ['JavaScript', 'React', 'Vue.js', 'HTML', 'CSS', 'Python',
                   'Jira', 'Confluence', 'Agile', 'Scrum', 'Kanban', 'Leadership'],
        'descriptions': [
            'jamoa bilan ishlashni yaxshi ko\'rasiz',
            'muloqot qobiliyatingiz yuqori',
            'loyihalarni boshqarish sizga yoqadi',
        ],
        'advice': [
            'Agile/Scrum bo\'yicha sertifikat oling',
            'Frontend texnologiyalarini o\'rganing',
            'Liderlik va muloqot treninglarida qatnashing',
        ],
        'future': 'Project Manager dan IT Director ga o\'sish',
    },
}

EXPERIENCES = [
    (0, "hech qanday tajribam yo'q, endi o'rganyapman"),
    (1, "1 yil tajribam bor"), (2, "2 yil tajribam bor"),
    (3, "3-4 yil tajribam bor"), (5, "5+ yil tajribam bor"),
]

NAMES = ['Aziz', 'Bobur', 'Dilshod', 'Eldor', 'Farrux', 'Gulnoza',
         'Humoyun', 'Islom', 'Javohir', 'Kamola', 'Laziz', 'Madina',
         'Nodir', 'Odil', 'Parviz', 'Rustam', 'Sevara', 'Shoxrux',
         'Temur', 'Umida', 'Xurshid', 'Zafar']

QUESTIONS = {
    'test_analysis': [
        "Menga eng mos kasbni tavsiya qilasizmi?", "Qaysi yo'nalishda ishlashim kerak?",
        "Mening profilimga qarab, nima maslahat berasiz?", "Profilimni tahlil qilib, eng yaxshi yo'nalishni aytib bering",
    ],
    'skill_question': [
        "Bu ko'nikma bilan qanday ish topish mumkin?", "Bu sohada rivojlanish uchun nima qilishim kerak?",
        "Qancha maosh olishim mumkin?", "Bu yo'nalishda talab bormi?",
    ],
    'five_year': [
        "5 yildan keyin qaysi soha eng talabgir bo'ladi?",
        "Kelgusi 5 yil ichida qaysi texnologiyalarni o'rganishim kerak?",
        "Eng istiqbolli sohalar qaysilar?",
    ],
    'general_advice': [
        "IT sohasiga endi kirdim. Qayerdan boshlashim kerak?",
        "O'qishni tugatdim, IT da ish qidiryapman. Nima qilishim kerak?",
        "Dasturlashni o'rganyapman. Qaysi tilni tanlashim kerak?",
    ],
}

def get_stats(categories):
    from jobs.models import Job
    total = Job.objects.filter(is_active=True).count()
    best_cat, best_count = None, 0
    for cname in categories:
        cnt = Job.objects.filter(is_active=True, category__name=cname).count()
        if cnt > best_count: best_count, best_cat = cnt, cname
    salary = Job.objects.filter(is_active=True, category__name__in=categories).aggregate(mn=Min('salary_max'), mx=Max('salary_max'))
    return total, best_cat, best_count, salary['mn'], salary['mx']

def make_response(role, name, scenario, skill_name=''):
    data = PAEI_ROLES[role]
    total, best_cat, best_count, sal_min, sal_max = get_stats(data['categories'])
    role_desc = f"Sizning profilingiz ({role}) — {data['name']}. {random.choice(data['descriptions'])}"
    response = f"## Assalomu alaykum, {name}!\n\n### Karyera Tahlili\n{role_desc}\n\n"
    if scenario == 'test_analysis':
        response += f"### Tavsiya etilgan yo'nalish\n"
        if best_cat and best_count > 0:
            response += f"**{best_cat}** — bazada {best_count} ta vakansiya mavjud\n\n### Nega aynan bu?\n"
            response += f"Aynan {best_cat} sohasi sizning qobiliyatlaringizni to'liq namoyon qilish imkonini beradi.\n\n"
        else:
            response += f"Bazada jami {total} ta IT vakansiya mavjud. Sizga eng mos: {data['categories'][0]}\n\n"
        response += "### Rivojlanish rejasi\n" + '\n'.join(f"- {a}" for a in data['advice'][:2]) + '\n'
    elif scenario == 'skill_question':
        cnt_with = Job.objects.filter(is_active=True, required_skills__name__icontains=skill_name).count() if skill_name else 0
        response += f"### {skill_name} — ajoyib tanlov!\n"
        if cnt_with: response += f"Bazada {skill_name} talab qilinadigan {cnt_with} ta vakansiya bor.\n\n"
        response += f"Sizning profilingiz ({role}) va {skill_name} bilimingiz bilan {best_cat or data['categories'][0]} sohasida muvaffaqiyatli ishlashingiz mumkin.\n\n"
        response += f"### Rivojlanish rejasi\n- {skill_name} ni chuqur o'rganing\n- Amaliy loyihalar qiling\n"
    elif scenario == 'five_year':
        response += f"### 5 Yillik Prognoz\nHozirgi bozor tahlili: {total} ta IT vakansiya.\n\n"
        response += f"### Sizning profilingiz ({role}) uchun tavsiya\n{data['future']}\n\n"
        response += "### Rivojlanish rejasi\n1. 1-2 yil: Asosiy ko'nikmalarni o'zlashtirish\n2. 2-4 yil: Sertifikatsiya\n3. 5-yil: Yetakchi mutaxassis\n"
    else:
        response += f"Bozorda hozir {total} ta IT vakansiya mavjud.\n\n"
        response += f"Sizga mos yo'nalish: {best_cat or data['categories'][0]}\n\n"
        response += "### Rivojlanish rejasi\n- Asosiy dasturlash tilini o'rganing (Python yoki JavaScript)\n- Oddiy loyihalar yarating\n- IT community ga qo'shiling\n"
    return response

def generate_dataset(num=500):
    dataset, types, weights = [], ['test_analysis', 'skill_question', 'five_year', 'general_advice'], [0.35, 0.25, 0.20, 0.20]
    for _ in range(num):
        role = random.choice(list(PAEI_ROLES.keys()))
        exp_years, exp_text = random.choice(EXPERIENCES)
        name = random.choice(NAMES)
        scenario = random.choices(types, weights=weights, k=1)[0]
        skill = random.choice(PAEI_ROLES[role]['skills'])
        q = random.choice(QUESTIONS[scenario])
        if scenario == 'skill_question':
            instruction = f"Men {name}man. {exp_text}. {skill} ni o'rganyapman. {q}"
        elif scenario == 'five_year':
            instruction = f"Men {name}man. Mening profilim {role}, {exp_text}. {q}"
        elif scenario == 'general_advice':
            instruction = f"Mening ismim {name}. {exp_text}. {q}"
        else:
            skills_show = ', '.join(random.sample(PAEI_ROLES[role]['skills'], k=min(3, len(PAEI_ROLES[role]['skills']))))
            instruction = f"Mening PAEI profilim {role}. {exp_text}. Ko'nikmalarim: {skills_show}. {q}"
        dataset.append({"instruction": instruction, "response": make_response(role, name, scenario, skill), "role": role, "scenario": scenario})
    return dataset

def save_dataset(dataset, filepath='aura_dataset.jsonl'):
    with open(filepath, 'w', encoding='utf-8') as f:
        for item in dataset:
            f.write(json.dumps({"instruction": item["instruction"], "response": item["response"]}, ensure_ascii=False) + '\n')
    stats = {}
    for item in dataset: stats[item.get('role', '?')] = stats.get(item.get('role', '?'), 0) + 1
    print(f"✅ Dataset saqlandi: {filepath} ({len(dataset)} ta)")
    print(f"   PAEI bo'yicha: {stats}")

def run(count=500):
    save_dataset(generate_dataset(count))

if __name__ == '__main__':
    import os, django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mmt_project.settings')
    django.setup()
    run()
```

## Fayl 11: services.py — yangi stream_generator qismi (replace section)

`ai_advisor/services.py` faylida `stream_generator` funksiyasini quyidagiga almashtiring:

```python
    full_response_holder = [""]
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')

    def stream_generator():
        try:
            if GROQ_API_KEY:
                import httpx
                groq_payload = {
                    "model": "llama3-70b-8192",
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 1024,
                    "stream": True,
                }
                with httpx.Client(timeout=60) as client:
                    with client.stream("POST", "https://api.groq.com/openai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                        json=groq_payload) as resp:
                        for line in resp.iter_lines():
                            if line.startswith("data: "):
                                data_str = line[6:]
                                if data_str == "[DONE]": break
                                try:
                                    data = json.loads(data_str)
                                    token = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                    if token:
                                        full_response_holder[0] += token
                                        yield token
                                except json.JSONDecodeError: continue
            else:
                raise Exception("Groq kaliti yo'q")
        except Exception:
            try:
                import ollama
                models_to_try = ['aura-agent', 'tinyllama', 'llama3.2:1b', 'qwen2:0.5b']
                for model_name in models_to_try:
                    try:
                        stream = ollama.chat(model=model_name, messages=messages, stream=True,
                            options={'temperature': 0.7, 'num_predict': -1, 'num_ctx': 4096})
                        for chunk in stream:
                            token = chunk.get('message', {}).get('content', '')
                            if token:
                                full_response_holder[0] += token
                                yield token
                        break
                    except Exception: continue
                else:
                    raise Exception("Hech qanday model ishlamadi")
            except Exception:
                fallback = generate_fallback_response(full_name, test_recommendation, bozor_data)
                full_response_holder[0] = fallback
                yield fallback

        updated_history = list(chat_session.message_history)
        updated_history.append({"role": "assistant", "content": full_response_holder[0]})
        chat_session.message_history = updated_history
        chat_session.save()

    return stream_generator()
```

## Colab Notebook — Google Colab da ochish

Google Colab (https://colab.research.google.com) da yangi notebook yarating va har bir hujayraga quyidagilarni joylashtiring:

### Hujayra 1:
```python
!pip install -q transformers peft trl bitsandbytes datasets accelerate huggingface_hub
```

### Hujayra 2:
```python
from google.colab import files
import json
print("aura_dataset.jsonl faylini yuklang:")
uploaded = files.upload()
dataset = []
for fn in uploaded:
    with open(fn, 'r') as f:
        for line in f: dataset.append(json.loads(line))
print(f"✅ {len(dataset)} ta misol yuklandi")
```

### Hujayra 3:
```python
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import LoraConfig, prepare_model_for_kbit_training
from trl import SFTTrainer
from datasets import Dataset

MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
bnb_config = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, quantization_config=bnb_config, device_map="auto", trust_remote_code=True)
model = prepare_model_for_kbit_training(model)
print("✅ Model yuklandi")
```

### Hujayra 4:
```python
def fmt(ex):
    return tokenizer.apply_chat_template([{"role":"user","content":ex["instruction"]},{"role":"assistant","content":ex["response"]}], tokenize=False)
texts = [fmt(ex) for ex in dataset]
hf_dataset = Dataset.from_dict({"text": texts})
print(f"✅ {len(hf_dataset)} ta formatted")
```

### Hujayra 5:
```python
lora_config = LoraConfig(r=16, lora_alpha=32, target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"], lora_dropout=0.05, bias="none", task_type="CAUSAL_LM")
```

### Hujayra 6:
```python
from transformers import TrainingArguments
args = TrainingArguments(output_dir="./aura-tinyllama", per_device_train_batch_size=2, gradient_accumulation_steps=4, num_train_epochs=3, learning_rate=2e-4, fp16=True, logging_steps=10, save_steps=100, save_total_limit=2, remove_unused_columns=True, report_to="none")
trainer = SFTTrainer(model=model, args=args, train_dataset=hf_dataset, tokenizer=tokenizer, peft_config=lora_config, dataset_text_field="text", max_seq_length=1024)
print("✅ Trainer tayyor!")
```

### Hujayra 7:
```python
trainer.train()
trainer.save_model("./aura-tinyllama-final")
tokenizer.save_pretrained("./aura-tinyllama-final")
print("✅ Fine-tuning tugadi!")
```

### Hujayra 8:
```python
from transformers import pipeline
pipe = pipeline("text-generation", model="./aura-tinyllama-final", tokenizer=tokenizer, device=0 if torch.cuda.is_available() else -1)
test = tokenizer.apply_chat_template([{"role":"user","content":"Mening PAEI profilim P, 2 yil tajribam bor. Qaysi yo'nalishni maslahat berasiz?"}], tokenize=False)
result = pipe(test, max_new_tokens=300, temperature=0.7, do_sample=True)
print(result[0]['generated_text'])
```

### Hujayra 9:
```python
from huggingface_hub import notebook_login, HfApi
notebook_login()
api = HfApi()
username = input("HF username: ")
repo_id = f"{username}/aura-tinyllama-uzbek"
api.create_repo(repo_id, exist_ok=True)
api.upload_folder(folder_path="./aura-tinyllama-final", repo_id=repo_id)
print(f"✅ Model: https://huggingface.co/{repo_id}")
```

### Hujayra 10 (ixtiyoriy — GGUF export):
```python
!git clone https://github.com/ggerganov/llama.cpp
!cd llama.cpp && make -j2
!python llama.cpp/convert_hf_to_gguf.py ./aura-tinyllama-final --outfile aura-tinyllama-q4.gguf
from google.colab import files
files.download("aura-tinyllama-q4.gguf")
```

## Ishga tushirish

```bash
# 0. Papkalarni yaratish
cd "/home/boborahim/Boborahim's/analitik loiha"
mkdir -p jobs/management/commands/parsers
source venv/bin/activate
pip install deep-translator beautifulsoup4 lxml

# 1. Alohida fayllarni yaratish (yuqoridagi kodlarni ko'chiring)
# Fayllarni yaratish uchun: nano yoki vim orqali, yoki:
# touch jobs/management/commands/transliterate_uz.py
# ... har bir fayl uchun yuqoridagi kodlarni joylang

# 2. Parserlarni ishga tushirish
python manage.py scrape_all

# 3. Dataset yaratish
python -m ai_advisor.dataset_generator

# 4. Colab Notebook ni oching va fine-tuning qiling
#    (aura_dataset.jsonl faylini yuklang)

# 5. Modelni Ollama ga import qilish
#    Hugging Face dan yuklab oling va:
#    ollama create aura-agent -f Modelfile

# 6. Server
python manage.py runserver 0.0.0.0:8001
```
