import re
import json
import time
import random
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from curl_cffi import requests as curl_requests
from django.core.management.base import BaseCommand
from django.utils import timezone as tz_util
from jobs.models import Job, Category, Country
from users.models import Skill

SKILL_PATTERNS = {
    "Python": r'(?i)\bPython\b',
    "JavaScript": r'(?i)\bJavaScript\b|\bJS\b',
    "React": r'(?i)\bReact\b|\bReact\.js\b',
    "Django": r'(?i)\bDjango\b',
    "SQL": r'(?i)\bSQL\b',
    "AWS": r'(?i)\bAWS\b|\bAmazon Web Services\b',
    "Docker": r'(?i)\bDocker\b',
    "Kubernetes": r'(?i)\bK8s\b|\bKubernetes\b',
    "Node.js": r'(?i)\bNode\.js\b|\bNodeJS\b',
    "TypeScript": r'(?i)\bTypeScript\b|\bTS\b',
    "Flutter": r'(?i)\bFlutter\b',
    "Dart": r'(?i)\bDart\b',
    "React Native": r'(?i)\bReact Native\b',
    "Swift": r'(?i)\bSwift\b',
    "Kotlin": r'(?i)\bKotlin\b',
    "Java": r'(?i)\bJava\b(?!\s*Script)',
    "Android": r'(?i)\bAndroid\b',
    "iOS": r'(?i)\biOS\b',
    "Firebase": r'(?i)\bFirebase\b',
    "REST API": r'(?i)\bREST\b|\bAPI\b',
    "GraphQL": r'(?i)\bGraphQL\b',
    "Git": r'(?i)\bGit\b',
    "CI/CD": r'(?i)\bCI/CD\b',
    "PostgreSQL": r'(?i)\bPostgreSQL\b|\bPostgres\b',
    "MongoDB": r'(?i)\bMongoDB\b',
    "Redis": r'(?i)\bRedis\b',
    "HTML": r'(?i)\bHTML\b',
    "CSS": r'(?i)\bCSS\b',
    "Figma": r'(?i)\bFigma\b',
    "C++": r'(?i)\bC\+\+\b',
    "C#": r'(?i)\bC#\b',
    "PHP": r'(?i)\bPHP\b',
    "Ruby": r'(?i)\bRuby\b',
    "Go": r'(?i)\bGo\b(?:lang)?',
    "Rust": r'(?i)\bRust\b',
}


class Command(BaseCommand):
    help = "HH.UZ dan vakansiyalarni yig'ish (Web Scraping)"

    def add_arguments(self, parser):
        parser.add_argument('--query', type=str, default='Mobile App Developer', help='Qidiruv so\'zi')
        parser.add_argument('--count', type=int, default=20, help='Necha ta vakansiya olish')
        parser.add_argument('--save', action='store_true', default=True, help='Bazaga saqlash')
        parser.add_argument('--json-output', action='store_true', help='JSON chiqarish')
        # Ollama integration removed; skill extraction uses local heuristics.

    def handle(self, *args, **options):
        query = options['query']
        count = options['count']
        save_to_db = options['save']
        json_output = options['json_output']
        # Ollama removed; no external skill extraction flag

        self.stdout.write(self.style.SUCCESS(f"[*] HH.UZ dan '{query}' bo'yicha {count} ta vakansiya olinmoqda..."))

        session = curl_requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "uz-UZ,uz;q=0.9,ru;q=0.8,en;q=0.7",
        })

        self.stdout.write("[*] HH.UZ ga ulanmoqda...")
        try:
            resp = session.get("https://hh.uz/", impersonate="chrome131", timeout=30)
            if resp.status_code != 200:
                self.stdout.write(self.style.ERROR(f"[-] Ulanish xatosi: {resp.status_code}"))
                return
            self.stdout.write("[+] Ulanish muvaffaqiyatli")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"[-] Ulanish xatosi: {e}"))
            return

        results = self.search_and_scrape(session, query, count)

        self.stdout.write(self.style.SUCCESS(f"[+] Jami {len(results)} ta vakansiya olindi"))

        if save_to_db:
            saved = self.save_to_database(results)
            self.stdout.write(self.style.SUCCESS(f"[+] {saved} ta vakansiya bazaga saqlandi"))

        if json_output:
            output = {
                "status": "success",
                "total_jobs": len(results),
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "jobs": results,
                "errors": [],
            }
            self.stdout.write(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            self.print_summary(results)

    def search_and_scrape(self, session, query, count_needed):
        results = []
        page = 0

        search_queries = [
            query,
            "Mobile Developer",
            "Android Developer",
            "iOS Developer",
            "Flutter Developer",
            "Mobile dasturchi",
            "Мобильный разработчик",
        ]

        for search_q in search_queries:
            if len(results) >= count_needed:
                break

            self.stdout.write(f"  Qidiruv: '{search_q}'")
            page = 0

            while len(results) < count_needed and page < 3:
                params = {
                    "area": 97,
                    "text": search_q,
                    "search_field": "name",
                    "items_on_page": 100,
                    "page": page,
                }

                try:
                    time.sleep(random.uniform(1.0, 2.0))
                    resp = session.get(
                        "https://hh.uz/search/vacancy",
                        params=params,
                        impersonate="chrome131",
                        timeout=30,
                    )

                    if resp.status_code != 200:
                        self.stdout.write(f"  HTTP {resp.status_code}, keyingi qidiruv...")
                        break

                    soup = BeautifulSoup(resp.text, 'html.parser')

                    cards = self.find_cards(soup)
                    if not cards:
                        self.stdout.write("  Vakansiyalar topilmadi, keyingi qidiruv...")
                        break

                    self.stdout.write(f"  Sahifa {page + 1}: {len(cards)} ta vakansiya")

                    for card in cards:
                        if len(results) >= count_needed:
                            break

                        job_data = self.parse_card(card, session)
                        if job_data:
                            source_urls = {j['source_url'] for j in results}
                            if job_data['source_url'] not in source_urls:
                                results.append(job_data)

                    page += 1

                    pager = soup.find('a', attrs={'data-qa': 'pager-next'})
                    if not pager:
                        break

                except Exception as e:
                    self.stdout.write(f"  Xato: {e}")
                    break

        return results[:count_needed]

    def find_cards(self, soup):
        cards = soup.find_all('div', attrs={'data-qa': 'vacancy-serp__vacancy'})
        if not cards:
            cards = soup.find_all('div', class_=re.compile(r'vacancy-serp-item'))
        if not cards:
            cards = soup.find_all('div', class_=re.compile(r'vacancy-card--'))
        if not cards:
            cards = soup.find_all('div', attrs={'data-qa': 'vacancy-serp__vacancy vacancy-serp__vacancy_geocoder'})
        return cards

    def parse_card(self, card, session):
        try:
            title_tag = card.find('a', attrs={'data-qa': 'serp-item__title'})
            if not title_tag:
                title_tag = card.find('a', class_=re.compile(r'serp-item__title'))
            if not title_tag:
                title_tag = card.find('a', href=re.compile(r'/vacancy/\d+'))
            if not title_tag:
                return None

            title = title_tag.get_text(strip=True)
            href = title_tag.get('href', '')
            if href and not href.startswith('http'):
                href = 'https://hh.uz' + href

            employer_tag = card.find('a', attrs={'data-qa': 'vacancy-serp__vacancy-employer'})
            if not employer_tag:
                employer_tag = card.find('div', class_=re.compile(r'employer'))
            company = employer_tag.get_text(strip=True) if employer_tag else 'Noma\'lum'

            salary_text = None
            for span in card.find_all('span'):
                stext = span.get_text(strip=True)
                if stext and any(c in stext for c in ['$', '₽', 'сум', 'so\'m', 'сом', 'eur', '€']):
                    salary_text = stext
                    break
            if not salary_text:
                salary_text_tag = card.find('span', class_=re.compile(r'bloko-header-section-3'))
                if salary_text_tag:
                    salary_text = salary_text_tag.get_text(strip=True)

            salary_min, salary_max, currency = self.parse_salary(salary_text)

            location_tag = card.find('span', attrs={'data-qa': 'vacancy-serp__vacancy-address'})
            if not location_tag:
                location_tag = card.find('span', class_=re.compile(r'address'))
            if not location_tag:
                location_tag = card.find('span', attrs={'data-qa': 'vacancy-serp__vacancy-address-nested'})
            country_name = 'O\'zbekiston'
            if location_tag:
                loc_text = location_tag.get_text(strip=True)
                if loc_text:
                    country_name = loc_text

            employment_type = self.detect_job_type(title, card)

            skills, description = self.get_vacancy_details(href, session)

            clean_desc = description or f"{title} bo'yicha vakansiya. {company} kompaniyasiga xodim izlanmoqda."
            if len(clean_desc) < 50:
                clean_desc = f"{title} - {company}. Batafsil ma'lumot uchun vakansiya sahifasiga o'ting."

            category = self.map_category(title, skills)

            return {
                "title": title,
                "company": company,
                "category": category,
                "country": country_name,
                "description": clean_desc[:3000],
                "job_type": employment_type,
                "salary_min": salary_min,
                "salary_max": salary_max,
                "currency": currency,
                "required_skills": skills[:15],
                "source_url": href,
                "source": "hh.uz",
                "posted_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }

        except Exception as e:
            self.stdout.write(f"  Card parse xatosi: {e}")
            return None

    def parse_salary(self, salary_text):
        if not salary_text or not salary_text.strip():
            return None, None, 'USD'

        text = salary_text.strip().lower()

        if 'сум' in text or "so'm" in text or 'som' in text:
            currency = 'UZS'
        elif '$' in text or 'usd' in text:
            currency = 'USD'
        elif '€' in text or 'eur' in text:
            currency = 'EUR'
        elif '₽' in text or 'rub' in text:
            currency = 'RUB'
        else:
            currency = 'USD'

        for ch in ['\u202f', '\u2009', '\u00a0', ' ', '\u2000', '\u2001', '\u2002', '\u2003']:
            text = text.replace(ch, '')
        numbers = [int(n) for n in re.findall(r'\d+', text)]

        if not numbers:
            return None, None, currency

        if 'от' in text or 'dan' in text:
            return numbers[0], None, currency
        if 'до' in text or 'gacha' in text:
            return None, numbers[0], currency

        if len(numbers) == 1:
            return numbers[0], numbers[0], currency
        else:
            return min(numbers[:2]), max(numbers[:2]), currency

    def detect_job_type(self, title, card):
        title_lower = title.lower()
        if any(kw in title_lower for kw in ['remote', 'work from home', 'wfh', 'online', 'masofaviy']):
            return 'remote'
        if any(kw in title_lower for kw in ['part-time', 'part time', 'yarim', 'soatlik']):
            return 'part_time'

        text = card.get_text(strip=True).lower()
        if any(kw in text for kw in ['remote', 'work from home', 'wfh', 'online', 'masofaviy', 'udalёnka']):
            return 'remote'
        if any(kw in text for kw in ['part-time', 'yarim', 'soatlik']):
            return 'part_time'

        return 'full_time'

    def get_vacancy_details(self, url, session):
        skills = set()
        description = ''

        if not url:
            return [], ''

        try:
            time.sleep(random.uniform(0.5, 1.0))
            resp = session.get(url, impersonate="chrome131", timeout=30)
            if resp.status_code != 200:
                return [], ''

            soup = BeautifulSoup(resp.text, 'html.parser')

            desc_tag = soup.find('div', attrs={'data-qa': 'vacancy-description'})
            if not desc_tag:
                desc_tag = soup.find('div', class_=re.compile(r'vacancy-description'))
            if not desc_tag:
                desc_tag = soup.find('div', attrs={'data-qa': 'vacancy-description-text'})
            if desc_tag:
                description = desc_tag.get_text(separator=' ', strip=True)

            skill_tags = soup.find_all('div', class_=re.compile(r'magritte-tag___'))
            if not skill_tags:
                skill_tags = soup.find_all('span', attrs={'data-qa': 'bloko-tag__text'})
            if not skill_tags:
                skill_tags = soup.find_all('a', class_=re.compile(r'bloko-tag'))
            if not skill_tags:
                skill_tags = soup.find_all('li', attrs={'data-qa': 'vacancy-skill'})

            for tag in skill_tags:
                text = tag.get_text(strip=True)
                if text and len(text) < 60:
                    skills.add(text)

            full_text = f"{description}"
            for skill_name, pattern in SKILL_PATTERNS.items():
                if re.search(pattern, full_text):
                    skills.add(skill_name)

        except Exception as e:
            self.stdout.write(f"  Detail xatosi: {e}")

        return sorted(skills) if skills else [], description

    def map_category(self, title, skills):
        title_lower = title.lower()
        skills_lower = {s.lower() for s in skills}

        mobile_kw = ['mobile', 'android', 'ios', 'flutter', 'dart', 'swift', 'kotlin', 'react native',
                     'мобильный', 'андроид']
        if any(kw in title_lower for kw in mobile_kw):
            return 'DEV'

        frontend_kw = ['frontend', 'front end', 'react', 'vue', 'angular', 'css', 'html', 'jquery']
        if any(kw in title_lower for kw in frontend_kw):
            return 'DEV'

        backend_kw = ['backend', 'back end', 'django', 'node', 'express', 'spring', 'laravel', 'api']
        if any(kw in title_lower for kw in backend_kw):
            return 'DEV'

        if any(kw in title_lower for kw in ['fullstack', 'full stack', 'программист', 'developer', 'разработчик']):
            return 'DEV'

        if any(kw in title_lower for kw in ['data', 'analyst', 'analytics', 'scientist', 'ml', 'ai',
                                             'machine learning', 'deep learning', 'prompt', 'биг дата']):
            return 'DATA/AI'

        if any(kw in title_lower for kw in ['devops', 'sre', 'infrastructure', 'cloud', 'aws', 'azure']):
            return 'DEVOPS'

        if any(kw in title_lower for kw in ['security', 'cyber', 'soc', 'pentest', 'infosec', 'безопасн']):
            return 'SECURITY'

        if any(kw in title_lower for kw in ['designer', 'design', 'ui', 'ux', 'figma', 'sketch', 'дизайн']):
            return 'DESIGN'

        if any(kw in title_lower for kw in ['manager', 'product', 'project', 'scrum', 'agile', 'product owner']):
            return 'MGMT'

        return 'DEV'

    def save_to_database(self, results):
        saved_count = 0
        for job_data in results:
            try:
                category_map = {
                    'DEV': 'Mobile App Developer',
                    'DATA/AI': 'Data Analyst',
                    'DEVOPS': 'DevOps Engineer',
                    'SECURITY': 'Cybersecurity Specialist',
                    'DESIGN': 'UI/UX Designer',
                    'MGMT': 'Product Manager',
                    'OTHER': 'Software Engineer',
                }
                cat_namr',
                    'SECURITY': 'Cybersecurity Specialist',
                    'DESIGN': 'UI/UX Designer',
                    'MGMT': 'Product Manager',
                    'OTHER': 'Software Engineer',
                }
                cat_name = category_map.get(job_data['category'], 'Software Engineer')
                category_obj, _ = Category.objects.get_or_create(name=cat_name)

                country_name = job_data['country']
                if ',' in country_name:
                    country_name = country_name.split(',')[0].strip()
                country_obj, _ = Country.objects.get_or_create(
                    name=country_name,
                    defaults={'code': country_name[:2].upper()}
                )

                defaults = {
                    'title': job_data['title'],
                    'company': job_data['company'],
                    'category': category_obj,
                    'country': country_obj,
                    'description': job_data['description'],
                    'job_type': job_data['job_type'],
                    'salary_min': job_data['salary_min'],
                    'salary_max': job_data['salary_max'],
                    'currency': job_data['currency'],
                    'source': job_data['source'],
                    'is_active': True,
                }

                job_obj, created = Job.objects.update_or_create(
                    source_url=job_data['source_url'],
                    defaults=defaults,
                )

                for skill_name in job_data['required_skills']:
                    skill_obj, _ = Skill.objects.get_or_create(name=skill_name)
                    job_obj.required_skills.add(skill_obj)

                saved_count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"[-] DB save: {e}"))

        return saved_count

    def print_summary(self, results):
        self.stdout.write("\n" + "=" * 65)
        self.stdout.write(f"  JAMI: {len(results)} ta vakansiya")
        self.stdout.write("=" * 65)

        cats = {}
        for j in results:
            cats[j['category']] = cats.get(j['category'], 0) + 1
        self.stdout.write("\n  Kategoriyalar:")
        for c, n in sorted(cats.items(), key=lambda x: -x[1]):
            self.stdout.write(f"    {c:15s}: {n} ta")

        skills = {}
        for j in results:
            for s in j['required_skills']:
                skills[s] = skills.get(s, 0) + 1
        if skills:
            self.stdout.write("\n  Top ko'nikmalar:")
            for s, n in sorted(skills.items(), key=lambda x: -x[1])[:10]:
                self.stdout.write(f"    {s:20s}: {n} ta")

        with_salary = sum(1 for j in results if j['salary_min'] or j['salary_max'])
        self.stdout.write(f"\n  Maoshli: {with_salary}/{len(results)}")
        self.stdout.write("=" * 65)
        self.stdout.write("")
