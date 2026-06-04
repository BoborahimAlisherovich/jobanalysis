import requests
from bs4 import BeautifulSoup
from jobs.models import Job, Category, Country
from ..transliterate_uz import translate_to_uzbek

HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"}

CATEGORIES = [
    ("programmirovanie", "Программирование"),
    ("razrabotka-sajtov", "Разработка сайтов"),
    ("mobile", "Мобильные приложения"),
    ("boty", "Боты"),
    ("testirovanie", "Тестирование"),
    ("admini", "Администрирование"),
    ("dizayn", "Дизайн"),
]

def run():
    total = 0
    country, _ = Country.objects.get_or_create(name="O'zbekiston", code="UZ")
    cat, _ = Category.objects.get_or_create(name="IT / Dasturlash")

    for cat_slug, cat_name in CATEGORIES:
        for page in range(1, 7):
            try:
                url = f"https://kwork.ru/projects?category={cat_slug}&page={page}"
                resp = requests.get(url, headers=HEADERS, timeout=15)
                if resp.status_code != 200:
                    continue
                soup = BeautifulSoup(resp.text, 'lxml')

                for item in soup.select('.project-card, .wants-card, .card, div[class*="project"], div[class*="want"]'):
                    link = item.select_one('a[href*="/projects/"], a[href*="/project/"]')
                    if not link:
                        continue
                    href = link.get('href', '')
                    if not href:
                        continue
                    if not href.startswith('http'):
                        href = 'https://kwork.ru' + ('/' if not href.startswith('/') else '') + href
                    if Job.objects.filter(source_url=href).exists():
                        continue

                    title = translate_to_uzbek(
                        (item.select_one('.project-title, .wants-title, h2, h3, .card-title, .name') or item)
                        .get_text(strip=True)[:255]
                    )
                    desc = translate_to_uzbek(
                        (item.select_one('.project-description, .wants-description, p, .description, .text') or item)
                        .get_text(strip=True)[:5000]
                    )
                    company = translate_to_uzbek(
                        (item.select_one('.username, .seller, .author, .user-name') or item)
                        .get_text(strip=True)[:255]
                    ) or 'Kwork'

                    price_el = item.select_one('.price, .cost, .budget, span[class*="price"], .amount')
                    price_text = price_el.get_text(strip=True) if price_el else ''
                    salary_min = salary_max = None
                    if price_text:
                        nums = [int(s.replace(' ', '')) for s in price_text.split() if s.replace(' ', '').isdigit()]
                        if nums:
                            salary_min = nums[0]
                            salary_max = nums[-1] if len(nums) > 1 else nums[0]

                    job_type = 'remote'
                    desc_lower = (title + ' ' + desc).lower()
                    if 'full' in desc_lower or "to'liq" in desc_lower:
                        job_type = 'full_time'
                    elif 'part' in desc_lower:
                        job_type = 'part_time'

                    Job.objects.create(
                        title=title, company=company, category=cat, country=country,
                        description=desc, job_type=job_type,
                        salary_min=salary_min, salary_max=salary_max, currency='UZS',
                        source_url=href, source='kwork.ru',
                    )
                    total += 1
            except Exception:
                pass
    return total
