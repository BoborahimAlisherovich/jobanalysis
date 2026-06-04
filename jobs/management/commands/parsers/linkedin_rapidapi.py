import os
import requests
from jobs.models import Job, Category, Country
from ..transliterate_uz import translate_to_uzbek

API_KEY = os.environ.get('RAPIDAPI_KEY', '')

KEYWORDS = [
    "developer", "software", "python", "java", "AI",
    "devops", "frontend", "data scientist", "backend",
    "mobile", "flutter", "react", "machine learning",
    "qa", "product manager", "ui ux", "cybersecurity",
    "business analyst", "prompt engineer", "blockchain",
]

def run():
    if not API_KEY:
        print("LinkedIn: RAPIDAPI_KEY topilmadi")
        return 0

    total = 0
    country, _ = Country.objects.get_or_create(name="O'zbekiston", code="UZ")
    cat, _ = Category.objects.get_or_create(name="IT / Dasturlash")
    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": "linkedin-jobs-scraper-api.p.rapidapi.com",
        "Content-Type": "application/json",
    }

    for kw in KEYWORDS:
        for page in range(1, 5):
            try:
                resp = requests.post(
                    "https://linkedin-jobs-scraper-api.p.rapidapi.com/jobs/search",
                    json={"keywords": kw, "location": "Uzbekistan", "limit": 25, "page": page},
                    headers=headers, timeout=20
                )
                if resp.status_code != 200:
                    continue
                items = resp.json()
                if isinstance(items, dict):
                    items = items.get('data', items)

                for item in items:
                    url = item.get('url', item.get('link', item.get('jobUrl', '')))
                    if not url or Job.objects.filter(source_url=url).exists():
                        continue

                    Job.objects.create(
                        title=translate_to_uzbek(item.get('title', ''))[:255],
                        company=translate_to_uzbek(item.get('company', 'LinkedIn'))[:255],
                        category=cat, country=country,
                        description=translate_to_uzbek(item.get('description', ''))[:5000],
                        job_type='full_time', source_url=url, source='linkedin',
                    )
                    total += 1
            except Exception:
                pass
    return total
