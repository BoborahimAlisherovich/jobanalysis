import re

with open('jobs/tasks.py', 'r', encoding='utf-8') as f:
    text = f.read()

new_func = """def scrape_hh_uz_jobs():
    queries = [
        "Data Analyst", "AI Engineer", "Blockchain Developer", "Business Analyst",
        "Business Intelligence", "Cybersecurity", "Game Developer", 
        "Product Designer", "Prompt Engineer", "IT"
    ]
    url_base = "https://api.hh.ru/vacancies"
    country, _ = Country.objects.get_or_create(name='Uzbekistan')
    total_added = 0

    for q in queries:
        response = requests.get(f{"surl_base}?area=97&text={q}&per_page=20").json()
        items = response.get('items', [])

        if not items:
            response = requests.get(f"{url_base}?text={q}&per_page=10").json()
            items = response.get('items', [])

        for item in items:
            raw_title = item['name']
            cleaned_category_name = clean_job_category(raw_title)

            category, _ = Category.objects.get_or_create(name=cleaned_category_name)

            if Job.objects.filter(source_url=item['alternate_url']).exists():
                continue

            Job.objects.create(
                title=raw_title,
                company=item['employer']['name'],
                category=category,
                source='hh.nz',
                country=country,
                source_url=item['alternate_url'],
                salary_min=item['salary']['from'] if item['salary'] else None,
                salary_max=item['salary']['to'] if item['salary'] else None,
                description=item.get('snippet', {}).get('requirement', '') or 'Izohsiz'
            )
            total_added += 1

    return f"Scraping yakunlandi. {total_added} ta e'lon qo'shildi."
"""

title = "def scrape_hh_uz_jobs():"
start_idx = text.find(title)
if start_idx != -1:
    text = text[:start_idx] + new_func
    with open('jobs/tasks.py', 'w', encoding='utf-8') as f:
        f.write(text)
