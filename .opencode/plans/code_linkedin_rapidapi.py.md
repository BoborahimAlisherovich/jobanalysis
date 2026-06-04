# File: jobs/management/commands/parsers/linkedin_rapidapi.py

```python
import os
import requests
from jobs.models import Job, Category, Country
from ..transliterate_uz import translate_to_uzbek

RAPIDAPI_KEY = os.environ.get('RAPIDAPI_KEY', '')
RAPIDAPI_HOST = "linkedin-jobs-scraper-api.p.rapidapi.com"

SEARCH_KEYWORDS = [
    "developer", "engineer", "programmer", "software",
    "backend", "frontend", "devops", "data scientist",
    "python", "java", "javascript", "react", "flutter",
    "mobile", "AI", "machine learning", "product manager",
    "designer", "analyst", "security", "blockchain",
]

def run():
    if not RAPIDAPI_KEY:
        print("LinkedIn: RAPIDAPI_KEY topilmadi, o'tkazib yuborildi")
        return 0

    total = 0
    country, _ = Country.objects.get_or_create(name="O'zbekiston", code="UZ")
    cat_cache = {}
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST,
        "Content-Type": "application/json"
    }

    for keyword in SEARCH_KEYWORDS[:5]:
        try:
            payload = {
                "keywords": keyword,
                "location": "Uzbekistan",
                "limit": 25
            }
            resp = requests.post(
                f"https://{RAPIDAPI_HOST}/jobs/search",
                json=payload,
                headers=headers,
                timeout=20
            )
            if resp.status_code != 200:
                print(f"LinkedIn API xato ({keyword}): {resp.status_code}")
                continue

            data = resp.json()
            jobs_data = data if isinstance(data, list) else data.get('data', [])

            for item in jobs_data:
                post_url = item.get('url', item.get('link', item.get('jobUrl', '')))
                if not post_url or Job.objects.filter(source_url=post_url).exists():
                    continue

                title = item.get('title', item.get('jobTitle', "Noma'lum"))
                title_uz = translate_to_uzbek(title)

                company = item.get('company', item.get('companyName', 'LinkedIn'))
                company_uz = translate_to_uzbek(company)

                description = item.get('description', item.get('jobDescription', ''))
                desc_uz = translate_to_uzbek(description)

                cat_name = 'IT / Dasturlash'
                if cat_name not in cat_cache:
                    cat_cache[cat_name] = Category.objects.get_or_create(name=cat_name)[0]

                salary_text = item.get('salary', item.get('salaryRange', ''))
                salary_min = salary_max = None
                currency = 'USD'
                if salary_text:
                    nums = [int(s.replace(',', '')) for s in salary_text.split() if s.replace(',', '').isdigit()]
                    if nums:
                        salary_min = nums[0]
                        salary_max = nums[-1] if len(nums) > 1 else nums[0]

                Job.objects.create(
                    title=title_uz[:255],
                    company=company_uz[:255],
                    category=cat_cache[cat_name],
                    country=country,
                    description=desc_uz[:5000],
                    job_type='full_time',
                    salary_min=salary_min,
                    salary_max=salary_max,
                    currency=currency,
                    source_url=post_url,
                    source='linkedin',
                )
                total += 1
        except Exception as e:
            print(f"LinkedIn xato ({keyword}): {e}")
    return total
```
