# File: jobs/management/commands/parsers/hh_uz.py

```python
import requests
import re
from jobs.models import Job, Category, Country
from ..transliterate_uz import translate_to_uzbek

HEADERS = {"User-Agent": "AuraCareerParser/1.0 (info@auracareer.uz)"}

IT_QUERIES = [
    "Developer", "Dasturchi", "Backend", "Frontend",
    "Mobile", "DevOps", "QA", "Data Scientist",
    "AI", "Machine Learning", "Python", "Java",
    "JavaScript", "React", "Flutter", "Android",
    "iOS", "UI/UX", "Product Manager", "Scrum",
    "1C", "System Administrator", "Network Engineer",
    "Security", "Game Developer", "Blockchain",
]

def run():
    total = 0
    country, _ = Country.objects.get_or_create(name="O'zbekiston", code="UZ")
    cat_cache = {}

    for q in IT_QUERIES:
        try:
            resp = requests.get(
                "https://api.hh.ru/vacancies",
                params={"text": q, "area": 97, "per_page": 50},
                headers=HEADERS, timeout=15
            )
            if resp.status_code != 200:
                continue
            data = resp.json()
            for item in data.get('items', []):
                post_url = item.get('alternate_url')
                if not post_url or Job.objects.filter(source_url=post_url).exists():
                    continue

                title = item.get('name', '')
                company = item.get('employer', {}).get('name', "Noma'lum")
                title_uz = translate_to_uzbek(title)
                company_uz = translate_to_uzbek(company)

                cat_name = 'IT / Dasturlash'
                spec = item.get('specializations', [])
                if spec:
                    profarea = spec[0].get('profarea_name', '')
                    if profarea:
                        cat_name_uz = translate_to_uzbek(profarea)
                        cat_name = cat_name_uz if cat_name_uz and len(cat_name_uz) < 100 else profarea

                if cat_name not in cat_cache:
                    cat_cache[cat_name] = Category.objects.get_or_create(name=cat_name)[0]
                category = cat_cache[cat_name]

                detail_resp = requests.get(item['url'], headers=HEADERS, timeout=10)
                detail_data = detail_resp.json() if detail_resp.status_code == 200 else {}
                desc = detail_data.get('description', '')
                desc_clean = re.sub(r'<[^>]+>', '', desc or '').strip()
                desc_uz = translate_to_uzbek(desc_clean)

                salary = item.get('salary') or {}
                salary_min = salary.get('from')
                salary_max = salary.get('to')
                currency = salary.get('currency', 'UZS')

                job_type = item.get('employment', {}).get('id', 'full_time')
                if job_type == 'full': job_type = 'full_time'
                elif job_type == 'part': job_type = 'part_time'
                elif job_type == 'remote': job_type = 'remote'
                else: job_type = 'full_time'

                keys = detail_data.get('key_skills', [])
                skills_text = ', '.join([s.get('name', '') for s in keys])

                job = Job.objects.create(
                    title=title_uz[:255],
                    company=company_uz[:255],
                    category=category,
                    country=country,
                    description=desc_uz[:5000] if desc_uz else '',
                    job_type=job_type,
                    salary_min=salary_min,
                    salary_max=salary_max,
                    currency=currency,
                    source_url=post_url,
                    source='hh.uz',
                )
                if skills_text:
                    from users.models import Skill
                    for sname in [s.strip() for s in skills_text.split(',') if s.strip()]:
                        skill, _ = Skill.objects.get_or_create(name=sname[:100])
                        job.required_skills.add(skill)
                total += 1
        except Exception as e:
            print(f"HH.uz xato ({q}): {e}")
    return total
```
