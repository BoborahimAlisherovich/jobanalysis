"""
Mavjud joblarni to'g'ri 18 ta kategoriaga reklassifikatsiya qilish.
"""
import re
from django.core.management.base import BaseCommand
from jobs.models import Job, Category


TARGET_ROLES = [
    'Blockchain Developer', 'Backend Developer', 'Frontend Developer',
    'Mobile App Developer', 'Software Engineer', 'AI Engineer',
    'Business Analyst', 'Business Intelligence (BI) Developer',
    'Cybersecurity Specialist', 'Data Analyst', 'Data Scientist',
    'DevOps Engineer', 'Game Developer', 'Product Designer',
    'Product Manager', 'Prompt Engineer', 'QA Engineer', 'UI/UX Designer',
]


def map_category(title: str, desc: str = "") -> str:
    t = (title + " " + desc).lower()
    
    # Check specific technologies and roles
    if re.search(r'\b(blockchain|web3|solidity|smart contract|defi|nft|crypto)\b', t):
        return 'Blockchain Developer'
    if re.search(r'\b(prompt|llm|gpt|chatgpt)\b', t):
        return 'Prompt Engineer'
    if re.search(r'\b(ai|artificial intelligence|deep learning|nlp|computer vision|mlops|pytorch|tensorflow)\b', t):
        return 'AI Engineer'
    if re.search(r'\b(machine learning|data scientist|data science|ml engineer)\b', t):
        return 'Data Scientist'
    if re.search(r'\b(business intelligence|power bi|tableau|qlik|looker|bi developer)\b', t):
        return 'Business Intelligence (BI) Developer'
    if re.search(r'\b(data analyst|sql analyst|big data|data engineer|hadoop|spark)\b', t):
        return 'Data Analyst'
    if re.search(r'\b(cybersecurity|security|pentest|infosec|soc analyst|devsecops|hacker)\b', t):
        return 'Cybersecurity Specialist'
    if re.search(r'\b(devops|sre|site reliability|kubernetes|k8s|terraform|ansible|docker|aws|azure|gcp|ci/cd)\b', t):
        return 'DevOps Engineer'
    if re.search(r'\b(game|unity|unreal|3d developer|c\+\+ developer)\b', t):
        return 'Game Developer'
    if re.search(r'\b(mobile|android|ios|flutter|react native|kotlin|swift|dart)\b', t):
        return 'Mobile App Developer'
    if re.search(r'\b(frontend|front-end|front end|react|vue|angular|next\.js|svelte|nuxt|html|css|javascript|typescript)\b', t):
        return 'Frontend Developer'
    if re.search(r'\b(backend|back-end|back end|python|django|fastapi|flask|node\.js|node|laravel|spring|golang|php|ruby|java|c#|\.net)\b', t):
        return 'Backend Developer'
    if re.search(r'\b(product manager|product owner|scrum master|agile coach)\b', t):
        return 'Product Manager'
    if re.search(r'\b(product designer|product design)\b', t):
        return 'Product Designer'
    if re.search(r'\b(ui|ux|figma|graphic designer|visual design)\b', t):
        return 'UI/UX Designer'
    if re.search(r'\b(business analyst|systems analyst|ba\b)\b', t):
        return 'Business Analyst'
    if re.search(r'\b(qa|quality assurance|tester|test|selenium|playwright|cypress)\b', t):
        return 'QA Engineer'
    if re.search(r'\b(software engineer|software developer|fullstack|full-stack|full stack|programmer)\b', t):
        return 'Software Engineer'
        
    return 'Software Engineer'


class Command(BaseCommand):
    help = "Mavjud joblarni to'g'ri kategoriyaga o'tkazish"

    def handle(self, *args, **options):
        # Barcha 18 kategoriyani yaratish
        for role in TARGET_ROLES:
            Category.objects.get_or_create(name=role)

        # Noto'g'ri kategoriyalardagi joblarni topish
        bad_cats = ['IT / Dasturlash', 'IT/Dasturlash', 'Backend / Dasturlash',
                    'Frontend / Web', 'Mobile Dasturlash', "Sun'iy Intellekt / Data",
                    'Kiberxavfsizlik', 'DevOps / Cloud', 'Game Development',
                    'Dizayn / Product', 'Quality Assurance', 'Boshqaruv / Analitika',
                    'Software Engineer']

        jobs_to_fix = Job.objects.filter(category__name__in=bad_cats)
        total = jobs_to_fix.count()
        self.stdout.write(f"Tuzatiladigan joblar: {total} ta")

        fixed = 0
        for job in jobs_to_fix:
            new_cat_name = map_category(job.title, job.description or '')
            new_cat, _ = Category.objects.get_or_create(name=new_cat_name)
            if new_cat != job.category:
                job.category = new_cat
                job.save(update_fields=['category'])
                fixed += 1

        self.stdout.write(self.style.SUCCESS(f"✅ {fixed} ta job to'g'ri kategoriyaga o'tkazildi"))

        # Statistika
        from django.db.models import Count
        self.stdout.write("\n📊 Kategoriyalar bo'yicha taqsimot:")
        cats = Category.objects.filter(name__in=TARGET_ROLES).annotate(
            c=Count('jobs')
        ).order_by('-c')
        for cat in cats:
            self.stdout.write(f"  {cat.name}: {cat.c} ta")

        total_active = Job.objects.filter(is_active=True).count()
        self.stdout.write(self.style.SUCCESS(f"\n📊 JAMI AKTIV: {total_active} ta"))
