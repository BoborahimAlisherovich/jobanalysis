import requests
from jobs.models import Job, Category, Country
from ..transliterate_uz import translate_to_uzbek

API = 'https://www.arbeitnow.com/api/job-board-api'

HEADERS = {'User-Agent': 'Mozilla/5.0'}

def run():
    total = 0
    country, _ = Country.objects.get_or_create(name="Global/Remote", code="GLB")
    cat, _ = Category.objects.get_or_create(name="IT / Dasturlash")

    url = API
    seen_slugs = set()
    while url:
        try:
            r = requests.get(url, timeout=20, headers=HEADERS)
            if r.status_code != 200:
                break
            data = r.json()
            jobs = data.get('data', [])
            for item in jobs:
                slug = item.get('slug')
                src_url = item.get('url') or item.get('job_url') or ''
                if not src_url or Job.objects.filter(source_url=src_url).exists():
                    continue
                title = translate_to_uzbek(item.get('title', ''))[:255]
                company = translate_to_uzbek(item.get('company_name', ''))[:255] or 'ArbeitNow'
                desc = translate_to_uzbek(item.get('description', ''))[:5000]

                Job.objects.create(
                    title=title,
                    company=company,
                    category=cat,
                    country=country,
                    description=desc,
                    job_type='remote' if item.get('remote') else 'full_time',
                    source_url=src_url,
                    source='arbeitnow',
                    is_active=True,
                )
                total += 1
                seen_slugs.add(slug)

            url = data.get('links', {}).get('next')
        except Exception:
            break

    return total
