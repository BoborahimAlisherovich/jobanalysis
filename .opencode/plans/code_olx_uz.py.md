# File: jobs/management/commands/parsers/olx_uz.py

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
                    if '$' in price_text:
                        currency = 'USD'
                    elif 'som' in price_text.lower() or 'so\'m' in price_text.lower():
                        currency = 'UZS'

                desc_el = item.select_one('p[class*="description"], div[class*="description"], .desc')
                description = desc_el.get_text(strip=True) if desc_el else ''
                desc_uz = translate_to_uzbek(description)

                company_el = item.select_one('a[class*="seller"], span[class*="seller"], div[class*="seller"]')
                company = company_el.get_text(strip=True) if company_el else 'OLX foydalanuvchisi'
                company_uz = translate_to_uzbek(company)

                Job.objects.create(
                    title=title_uz[:255],
                    company=company_uz[:255],
                    category=category,
                    country=country,
                    description=desc_uz[:5000] if desc_uz else '',
                    job_type='full_time',
                    salary_min=salary_min,
                    salary_max=salary_max,
                    currency=currency,
                    source_url=href,
                    source='olx.uz',
                )
                total += 1
        except Exception as e:
            print(f"OLX xato ({url}): {e}")
    return total
```
