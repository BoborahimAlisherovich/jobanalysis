from django.core.management.base import BaseCommand
from jobs.models import Category, Country, Job
import random

class Command(BaseCommand):
    help = 'Generate fake data to populate dashboard'

    def handle(self, *args, **kwargs):
        Category.objects.all().delete()
        Country.objects.all().delete()
        Job.objects.all().delete()

        categories = [
            'Backend Developer', 'Frontend Developer', 'Mobile App Developer',
            'Data Analyst', 'Data Scientist', 'DevOps Engineer', 'AI Engineer',
            'Prompt Engineer', 'UI/UX Designer', 'Game Developer', 'Product Manager',
            'Software Engineer', 'Business Intelligence (BI) Developer',
            'Cybersecurity Specialist', 'Product Designer', 'Business Analyst',
            'Blockchain Developer', 'QA Engineer'
        ]
        
        countries = [
            'Uzbekistan', 'United States', 'Germany', 'United Kingdom', 
            'Canada', 'Australia', 'Bengaluru, India', 'Remote'
        ]
        
        sources = ['hh.uz', 'LinkedIn', 'OLX.uz', 'Telegram Jobs', 'Indeed', 'Glassdoor']

        cat_objs = []
        for cat in categories:
            cat_objs.append(Category.objects.create(name=cat, trend_score=random.randint(40, 98)))

        country_objs = []
        for cnt in countries:
            country_objs.append(Country.objects.create(name=cnt))

        # Generate details for titles based on categories
        def get_job_title(cat_name):
            prefixes = ['Senior', 'Middle', 'Junior', 'Lead', '']
            if cat_name == 'Backend Developer':
                tech = random.choice(['Python/Django', 'Node.js', 'Java', 'Golang', 'PHP'])
                return f"{random.choice(prefixes)} {tech} Backend Developer".strip()
            elif cat_name == 'Frontend Developer':
                tech = random.choice(['React', 'Vue.js', 'Angular', 'Next.js'])
                return f"{random.choice(prefixes)} {tech} Frontend Developer".strip()
            elif cat_name == 'Mobile App Developer':
                tech = random.choice(['Flutter', 'iOS/Swift', 'Android/Kotlin', 'React Native'])
                return f"{random.choice(prefixes)} {tech} Developer".strip()
            elif cat_name == 'Data Scientist':
                return f"{random.choice(prefixes)} Data Scientist / ML Engineer".strip()
            elif cat_name == 'AI Engineer':
                return f"{random.choice(prefixes)} AI / Computer Vision Engineer".strip()
            elif cat_name == 'Prompt Engineer':
                return f"{random.choice(prefixes)} AI Prompt Engineer".strip()
            elif cat_name == 'Cybersecurity Specialist':
                return f"{random.choice(prefixes)} Information Security Analyst".strip()
            elif cat_name == 'Game Developer':
                tech = random.choice(['Unity', 'Unreal Engine', 'C++'])
                return f"{random.choice(prefixes)} {tech} Game Developer".strip()
            else:
                return f"{random.choice(prefixes)} {cat_name}".strip()

        # Generate ~1000 jobs
        for _ in range(1200):
            cat = random.choices(cat_objs, weights=[18, 16, 10, 8, 5, 5, 4, 3, 5, 3, 4, 5, 2, 3, 2, 4, 1, 2])[0]
            cnt = random.choice(country_objs)
            src = random.choice(sources)
            
            salary = random.randint(800, 5000) if cat.name not in ['Backend Developer', 'Data Scientist'] else random.randint(1500, 8000)
            
            Job.objects.create(
                title=get_job_title(cat.name),
                company=f'TechCorp {random.randint(1, 100)}',
                category=cat,
                country=cnt,
                source=src,
                salary_min=salary,
                salary_max=salary + random.randint(500, 2000),
                source_url=f'https://{src.lower().replace(" ", "")}/job/{random.randint(100000, 999999999)}_{_}',
                description='Ishga qabul qilish talablari: Yuqori darajadagi tajriba va jamoada ishlash qobiliyati.',
                job_type=random.choice(['full_time', 'remote', 'part_time'])
            )

        self.stdout.write(self.style.SUCCESS('Successfully populated highly detailed jobs DB!'))