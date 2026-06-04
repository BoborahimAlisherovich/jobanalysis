# File: jobs/management/commands/parsers/kwork_ru.py

```python
import requests
from bs4 import BeautifulSoup
from jobs.models import Job, Category, Country
from ..transliterate_uz import translate_to_uzbek

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
}

CATEGORIES = [
    "razrabotka-sajtov",
    "programmirovanie",
    "mobile-apps",
    "boty",
    "skripty",
]

def run():
    total = 0
    country, _ = Country.objects.get_or_create(name="O'zbekiston", code="UZ")
    category, _ = Category.objects.get_or_create(name="IT / Dasturlash")

    for cat in CATEGORIES:
        for page in range(1, 4):
            try:
                url = f"https://kwork.ru/projects?category={cat}&page={page}"
                resp = requests.get(url, headers=HEADERS, timeout=15)
                if resp.status_code != 200:
                    continue
                soup = BeautifulSoup(resp.text, 'lxml')
                for item in soup.select('.project-card, .wants-card, .card, div[class*="project"], div[class*="want"]'):
                    link = item.select_one('a[href*="/projects/"], a[href*="/project/"]')
                    if not link:
                        continue
                    href = link.get('href', '')
                    if not href or 'kwork.ru' not in href:
                        href = 'https://kwork.ru' + ('' if href.startswith('/') else '/') + href

                    if Job.objects.filter(source_url=href).exists():
                        continue

                    title_el = item.select_one('.project-title, .wants-title, h2, h3, .card-title, .name')
                    title = title_el.get_text(strip=True) if title_el else "Noma'lum"
                    title_uz = translate_to_uzbek(title)

                    desc_el = item.select_one('.project-description, .wants-description, p, .description, .text')
                    description = desc_el.get_text(strip=True) if desc_el else ''
                    desc_uz = translate_to_uzbek(description)

                    price_el = item.select_one('.price, .cost, .budget, span[class*="price"], .amount')
                    price_text = price_el.get_text(strip=True) if price_el else ''
                    salary_min = salary_max = None
                    if price_text:
                        nums = [int(s.replace(' ', '')) for s in price_text.split() if s.replace(' ', '').isdigit()]
                        if nums:
                            salary_min = nums[0]
                            salary_max = nums[-1] if len(nums) > 1 else nums[0]

                    username_el = item.select_one('.username, .seller, .author, .user-name, .employer')
                    company = username_el.get_text(strip=True) if username_el else 'Kwork foydalanuvchisi'
                    company_uz = translate_to_uzbek(company)

                    job_type = 'remote'
                    if 'full' in (title + description).lower() or 'to\'liq' in (title + description).lower():
                        job_type = 'full_time'
                    elif 'part' in (title + description).lower():
                        job_type = 'part_time'

                    Job.objects.create(
                        title=title_uz[:255],
                        company=company_uz[:255],
                        category=category,
                        country=country,
                        description=desc_uz[:5000],
                        job_type=job_type,
                        salary_min=salary_min,
                        salary_max=salary_max,
                        currency='UZS',
                        source_url=href,
                        source='kwork.ru',
                    )
                    total += 1
            except Exception as e:
                print(f"Kwork xato ({cat}): {e}")
    return total
```
