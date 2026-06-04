import requests
from bs4 import BeautifulSoup
from jobs.models import Job, Category, Country
from ..transliterate_uz import translate_to_uzbek

HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"}

def run():
    total = 0
    country, _ = Country.objects.get_or_create(name="O'zbekiston", code="UZ")
    cat, _ = Category.objects.get_or_create(name="IT / Dasturlash")

    for base_url in ["https://teamwork.uz/vacancies", "https://teamwork.uz/vacancies?category=it", "https://teamwork.uz/vacancies?category=developer"]:
        for page in range(1, 4):
            try:
                url = f"{base_url}&page={page}" if "?" in base_url else f"{base_url}?page={page}"
                resp = requests.get(url, headers=HEADERS, timeout=15)
                if resp.status_code != 200:
                    continue
                soup = BeautifulSoup(resp.text, 'lxml')
                for item in soup.select('a[href*="/vacancy/"], .vacancy-item, .job-card, .card'):
                    href = item.get('href', '')
                    if not href:
                        lnk = item.select_one('a[href]')
                        if lnk:
                            href = lnk.get('href', '')
                    if not href:
                        continue
                    if not href.startswith('http'):
                        href = 'https://teamwork.uz' + ('/' if not href.startswith('/') else '') + href
                    if Job.objects.filter(source_url=href).exists():
                        continue

                    title = translate_to_uzbek(
                        (item.select_one('h2, h3, h4, .title, .vacancy-title') or item).get_text(strip=True)[:255]
                    )
                    company = translate_to_uzbek(
                        (item.select_one('.company, .employer, .organization') or item).get_text(strip=True)[:255]
                    ) or 'Teamwork'
                    desc = translate_to_uzbek(
                        (item.select_one('.description, .desc, p, .requirements') or item).get_text(strip=True)[:5000]
                    )

                    price_text = (item.select_one('.salary, .price, .budget') or item).get_text(strip=True)
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
                        source_url=href, source='teamwork.uz',
                    )
                    total += 1
            except Exception:
                pass
    return total
