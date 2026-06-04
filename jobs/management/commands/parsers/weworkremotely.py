import requests
from bs4 import BeautifulSoup
from jobs.models import Job, Category, Country
from ..transliterate_uz import translate_to_uzbek

HEADERS = {'User-Agent': 'Mozilla/5.0'}

CAT_PAGES = [
    'https://weworkremotely.com/categories/remote-full-stack-programming-jobs',
    'https://weworkremotely.com/categories/remote-back-end-programming-jobs',
    'https://weworkremotely.com/categories/remote-front-end-programming-jobs',
    'https://weworkremotely.com/categories/remote-devops-sysadmin-jobs',
    'https://weworkremotely.com/categories/remote-data-jobs',
]

def run():
    total = 0
    country, _ = Country.objects.get_or_create(name="Global/Remote", code="GLB")
    cat, _ = Category.objects.get_or_create(name="IT / Dasturlash")

    for base in CAT_PAGES:
        for page in range(1, 6):
            try:
                url = base if page == 1 else f"{base}?page={page}"
                r = requests.get(url, timeout=20, headers=HEADERS)
                if r.status_code != 200:
                    break
                soup = BeautifulSoup(r.text, 'html.parser')
                links = [a.get('href') for a in soup.select('a[href*="/remote-jobs/"]')]
                for href in set(links):
                    if not href:
                        continue
                    full = href if href.startswith('http') else 'https://weworkremotely.com' + href
                    if Job.objects.filter(source_url=full).exists():
                        continue
                    try:
                        jr = requests.get(full, timeout=15, headers=HEADERS)
                        if jr.status_code != 200:
                            continue
                        jsoup = BeautifulSoup(jr.text, 'html.parser')
                        title_el = jsoup.select_one('h1')
                        company_el = jsoup.select_one('.company')
                        desc_el = jsoup.select_one('div.listing-container') or jsoup.select_one('div.listing')
                        title = translate_to_uzbek(title_el.get_text(strip=True) if title_el else '')[:255]
                        company = translate_to_uzbek(company_el.get_text(strip=True) if company_el else '')[:255] or 'WWR'
                        desc = ''
                        if desc_el:
                            desc = translate_to_uzbek(desc_el.get_text('\n', strip=True)[:5000])

                        Job.objects.create(
                            title=title,
                            company=company,
                            category=cat,
                            country=country,
                            description=desc,
                            job_type='remote',
                            source_url=full,
                            source='weworkremotely',
                            is_active=True,
                        )
                        total += 1
                    except Exception:
                        continue
            except Exception:
                break

    return total
