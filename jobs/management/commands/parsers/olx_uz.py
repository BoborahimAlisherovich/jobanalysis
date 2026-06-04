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
    cat, _ = Category.objects.get_or_create(name="IT / Dasturlash")

    urls = [
        "https://www.olx.uz/rabota/it-telekom-kompyutery/",
        "https://www.olx.uz/rabota/programmirovanie/",
        "https://www.olx.uz/rabota/internet/",
    ]

    for url in urls:
        for page in range(1, 6):
            try:
                page_url = f"{url}?page={page}"
                resp = requests.get(page_url, headers=HEADERS, timeout=15)
                if resp.status_code != 200:
                    continue
                soup = BeautifulSoup(resp.text, 'lxml')
                items = soup.select('div[data-cy="l-card"], li.offer-wrapper')

                for item in items:
                    link = item.select_one('a[href]')
                    if not link:
                        continue
                    href = link.get('href', '')
                    if not href.startswith('http'):
                        href = 'https://www.olx.uz' + href
                    if Job.objects.filter(source_url=href).exists():
                        continue

                    title = translate_to_uzbek(
                        (item.select_one('h6, .title') or item).get_text(strip=True)[:255]
                    )
                    company = translate_to_uzbek(
                        (item.select_one('a[class*="seller"], span[class*="seller"]') or item).get_text(strip=True)[:255]
                    ) or 'OLX'
                    desc = translate_to_uzbek(
                        (item.select_one('p[class*="description"], .desc') or item).get_text(strip=True)[:5000]
                    )

                    price_text = (item.select_one('[data-testid="ad-price"], .price') or item).get_text(strip=True)
                    salary_min = salary_max = None
                    if price_text:
                        nums = [int(s.replace(' ', '')) for s in price_text.split() if s.replace(' ', '').isdigit()]
                        if nums:
                            salary_min = nums[0]
                            salary_max = nums[-1] if len(nums) > 1 else nums[0]

                    Job.objects.create(
                        title=title, company=company, category=cat, country=country,
                        description=desc, job_type='full_time',
                        salary_min=salary_min, salary_max=salary_max, currency='UZS',
                        source_url=href, source='olx.uz',
                    )
                    total += 1
            except Exception:
                pass
    return total
