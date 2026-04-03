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

        sources = {
            'LinkedIn': 'linkedin.com', 'Indeed': 'indeed.com', 'Glassdoor': 'glassdoor.com',
            'Monster': 'monster.com', 'ZipRecruiter': 'ziprecruiter.com', 'SimplyHired': 'simplyhired.com',
            'Stack Overflow Jobs': 'stackoverflow.com', 'GitHub Jobs': 'github.com', 'AngelList': 'angel.co',
            'Hired': 'hired.com', 'Wellfound': 'wellfound.com', 'Upwork': 'upwork.com',
            'Fiverr': 'fiverr.com', 'Kwork': 'kwork.com', 'Freelancer': 'freelancer.com',
            'Toptal': 'toptal.com', 'PeoplePerHour': 'peopleperhour.com', 'We Work Remotely': 'weworkremotely.com',
            'Remote OK': 'remoteok.com', 'Remotive': 'remotive.com', 'FlexJobs': 'flexjobs.com',
            'hh.uz': 'hh.uz', 'OLX.uz': 'olx.uz', 'Zarplata.uz': 'zarplata.uz',
            'Rabota.uz': 'rabota.uz', 'SuperJob': 'superjob.ru', 't.me/teamwork_uz': 't.me/teamwork_uz'
        }

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
            src_name = random.choice(list(sources.keys()))
            src_domain = sources[src_name]

            # Define realistic currencies and amounts based on country/domain
            # For realistic purposes:
            if src_name in ['hh.uz', 'Rabota.uz', 'OLX.uz', 'Zarplata.uz', 't.me/teamwork_uz']:
                currency = random.choice(['UZS', 'USD'])
                if currency == 'UZS':
                    salary = random.randint(4000000, 25000000)
                    salary_max = salary + random.randint(1000000, 5000000)
                else:
                    salary = random.randint(500, 2500)
                    salary_max = salary + random.randint(500, 1500)
            elif src_name in ['Kwork', 'SuperJob']:
                currency = random.choice(['RUB', 'USD'])
                if currency == 'RUB':
                    salary = random.randint(60000, 250000)
                    salary_max = salary + random.randint(20000, 100000)
                else:
                    salary = random.randint(600, 3000)
                    salary_max = salary + random.randint(400, 1500)
            else:
                currency = 'USD'
                salary = random.randint(800, 5000) if cat.name not in ['Backend Developer', 'Data Scientist'] else random.randint(1500, 8000)
                salary_max = salary + random.randint(500, 2000)
            
            # Using "#" so it won't trigger 404 but realistically it points to the job site.
            Job.objects.create(
                title=get_job_title(cat.name),
                company=f'TechCorp {random.randint(1, 1000)}',
                category=cat,
                country=cnt,
                source=src_name,
                currency=currency,
                salary_min=salary,
                salary_max=salary_max,
                source_url=f'https://{src_domain}?job_search={random.randint(100000, 999999999)}_{_}',
                description='Ishga qabul qilish talablari: Yuqori darajadagi tajriba va jamoada ishlash qobiliyati.',
                job_type=random.choice(['full_time', 'remote', 'part_time'])
            )

        self.stdout.write(self.style.SUCCESS('Successfully populated highly detailed jobs DB!'))