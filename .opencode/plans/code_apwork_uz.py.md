# File: jobs/management/commands/parsers/apwork_uz.py

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

    urls = [
        "https://apwork.uz/jobs",
        "https://apwork.uz/jobs?category=it",
        "https://apwork.uz/jobs?category=programming",
    ]

    for url in urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, 'lxml')
            for item in soup.select('a[href*="/job/"], .job-item, .vacancy-card, .card, div[class*="job"]'):
                href = item.get('href', '')
                if not href:
                    link = item.select_one('a[href]')
                    href = link.get('href', '') if link else ''

                if not href:
                    continue
                if not href.startswith('http'):
                    href = 'https://apwork.uz' + ('' if href.startswith('/') else '/') + href

                if Job.objects.filter(source_url=href).exists():
                    continue

                title_el = item.select_one('h2, h3, h4, .title, .job-title, .vacancy-title')
                title = title_el.get_text(strip=True) if title_el else "Noma'lum"
                title_uz = translate_to_uzbek(title)

                company_el = item.select_one('.company, .employer, .author, .organization')
                company = company_el.get_text(strip=True) if company_el else 'Apwork'
                company_uz = translate_to_uzbek(company)

                desc_el = item.select_one('.description, .desc, p, .short-description, .body')
                description = desc_el.get_text(strip=True) if desc_el else ''
                desc_uz = translate_to_uzbek(description)

                price_el = item.select_one('.price, .salary, .budget, .cost')
                price_text = price_el.get_text(strip=True) if price_el else ''
                salary_min = salary_max = None
                if price_text:
                    nums = [int(s.replace(' ', '')) for s in price_text.split() if s.replace(' ', '').isdigit()]
                    if nums:
                        salary_min = nums[0]
                        salary_max = nums[-1] if len(nums) > 1 else nums[0]

                Job.objects.create(
                    title=title_uz[:255],
                    company=company_uz[:255],
                    category=category,
                    country=country,
                    description=desc_uz[:5000],
                    job_type='full_time',
                    salary_min=salary_min,
                    salary_max=salary_max,
                    currency='UZS',
                    source_url=href,
                    source='apwork.uz',
                )
                total += 1
        except Exception as e:
            print(f"Apwork xato ({url}): {e}")
    return total
```
