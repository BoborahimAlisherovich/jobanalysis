import requests
from bs4 import BeautifulSoup
from jobs.models import Job, Category, Country
from ..transliterate_uz import translate_to_uzbek

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "ru-RU,ru;q=0.9",
}

QUERIES = [
    "Python", "Django", "Flask", "JavaScript", "React", "Vue", "Angular",
    "Node", "Node.js", "Go", "Golang", "Java", "C++", "C#", "PHP", "Rust",
    "DevOps", "Kubernetes", "Docker", "AWS", "Azure", "GCP",
    "Data", "Data Scientist", "Machine Learning", "ML", "AI", "Mobile", "Android",
    "iOS", "Flutter", "Backend", "Frontend", "Fullstack", "Dasturchi",
]

def run():
    total = 0
    country, _ = Country.objects.get_or_create(name="O'zbekiston", code="UZ")
    cat, _ = Category.objects.get_or_create(name="IT / Dasturlash")

    for q in QUERIES:
        for page in range(0, 5):
            try:
                resp = requests.get(
                    "https://hh.uz/search/vacancy",
                    params={"text": q, "area": 1741, "items_on_page": 20, "page": page},
                    headers=HEADERS, timeout=10
                )
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, 'lxml')

                for card in soup.select('[data-qa*="vacancy"]'):
                    link = card.select_one('a[href*="/vacancy/"]')
                    if not link:
                        continue
                    href = link.get('href', '')
                    if not href or 'clusters' in href:
                        continue
                    full_url = href if href.startswith('http') else 'https://hh.uz' + href
                    if Job.objects.filter(source_url=full_url).exists():
                        continue

                    title = link.get_text(strip=True)[:255]

                    company_el = card.select_one('[data-qa*="employer"], .vacancy-company-name, span.bloko-text')
                    company = company_el.get_text(strip=True)[:255] if company_el else "Noma'lum"

                    salary_el = card.select_one('[data-qa*="salary"], .vacancy-salary')
                    salary_text = salary_el.get_text(strip=True) if salary_el else ''
                    salary_min = salary_max = None
                    if salary_text:
                        nums = [int(s.replace('\u202f', '').replace(' ', '')) for s in salary_text.split() if s.replace('\u202f', '').replace(' ', '').isdigit()]
                        if nums:
                            salary_min = nums[0]
                            salary_max = nums[-1] if len(nums) > 1 else nums[0]

                    Job.objects.create(
                        title=translate_to_uzbek(title)[:255],
                        company=translate_to_uzbek(company)[:255],
                        category=cat, country=country,
                        description='', job_type='full_time',
                        salary_min=salary_min, salary_max=salary_max, currency='UZS',
                        source_url=full_url, source='hh.uz',
                    )
                    total += 1
            except Exception:
                pass
    return total
