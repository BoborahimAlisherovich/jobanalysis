from django.core.management.base import BaseCommand
import json
import os
import re

from jobs.models import Job, Category


DEFAULT_ROLES = [
    "Mobile App Developer",
    "Blockchain Developer",
    "Backend Developer",
    "Frontend Developer",
    "Software Engineer",
    "AI Engineer",
    "Business Analyst",
    "Business Intelligence (BI) Developer",
    "Cybersecurity Specialist",
    "Data Analyst",
    "Data Scientist",
    "DevOps Engineer",
    "Game Developer",
    "Product Designer",
    "Product Manager",
    "Prompt Engineer",
    "QA Engineer",
    "UI/UX Designer",
]


def slugify(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')


ROLE_KEYWORDS = {
    "Mobile App Developer": ["mobile", "android", "ios", "flutter", "react native", "kotlin", "swift"],
    "Blockchain Developer": ["blockchain", "web3", "smart contract", "solidity", "crypto"],
    "Backend Developer": ["backend", "api", "django", "flask", "fastapi", "node", "spring", "golang", "java"],
    "Frontend Developer": ["frontend", "react", "vue", "angular", "next.js", "html", "css", "javascript"],
    "Software Engineer": ["software engineer", "engineering", "system design", "architecture"],
    "AI Engineer": ["ai", "ml", "machine learning", "llm", "nlp", "prompt", "computer vision", "data science"],
    "Business Analyst": ["business analyst", "requirements", "process", "stakeholder", "analysis"],
    "Business Intelligence (BI) Developer": ["bi", "power bi", "tableau", "dashboard", "etl", "analytics"],
    "Cybersecurity Specialist": ["security", "cyber", "soc", "siem", "pentest", "penetration", "incident"],
    "Data Analyst": ["data analyst", "sql", "excel", "power bi", "dashboard", "reporting"],
    "Data Scientist": ["data scientist", "statistics", "modeling", "pandas", "numpy", "sklearn"],
    "DevOps Engineer": ["devops", "docker", "kubernetes", "ci/cd", "linux", "aws", "gcp", "azure"],
    "Game Developer": ["game", "unity", "unreal", "c++", "godot"],
    "Product Designer": ["product designer", "ux", "ui", "figma", "prototype", "design"],
    "Product Manager": ["product manager", "roadmap", "discovery", "prioritization", "product"],
    "Prompt Engineer": ["prompt", "llm", "chatgpt", "agent", "copilot"],
    "QA Engineer": ["qa", "test", "testing", "automation", "selenium", "playwright", "cypress"],
    "UI/UX Designer": ["ui", "ux", "figma", "wireframe", "design system"],
}


def job_text(job):
    parts = [job.title or "", job.company or "", job.description or ""]
    parts.extend(s.name for s in job.required_skills.all())
    return " ".join(parts).lower()


def role_matches_job(role, job):
    text = job_text(job)
    for keyword in ROLE_KEYWORDS.get(role, []):
        if keyword in text:
            return True
    return role.lower() in text


class Command(BaseCommand):
    help = 'Export vacancies grouped by provided role names (default list from UI)'

    def add_arguments(self, parser):
        parser.add_argument('--out-dir', default='data/roles', help='Output directory')
        parser.add_argument('--roles', nargs='*', help='List of role names to export (overrides default)')

    def handle(self, *args, **options):
        out_dir = options['out_dir']
        roles = options['roles'] if options.get('roles') else DEFAULT_ROLES

        os.makedirs(out_dir, exist_ok=True)

        summary = {}
        for role in roles:
            qs = Job.objects.filter(is_active=True).select_related('category', 'country').prefetch_related('required_skills')
            matched = [job for job in qs if role_matches_job(role, job)]
            count = len(matched)
            summary[role] = count

            role_slug = slugify(role)
            json_path = os.path.join(out_dir, f"{role_slug}.json")
            jsonl_path = os.path.join(out_dir, f"{role_slug}.jsonl")

            records = []
            with open(jsonl_path, 'w', encoding='utf-8') as jl:
                for j in matched:
                    rec = {
                        'title': j.title,
                        'company': j.company,
                        'category': j.category.name if j.category else None,
                        'country': j.country.name if j.country else None,
                        'description': j.description,
                        'source': j.source,
                        'source_url': j.source_url,
                        'posted_at': j.posted_at.isoformat() if j.posted_at else None,
                        'salary_min': j.salary_min,
                        'salary_max': j.salary_max,
                        'currency': j.currency,
                        'required_skills': [s.name for s in j.required_skills.all()],
                    }
                    records.append(rec)
                    jl.write(json.dumps(rec, ensure_ascii=False) + '\n')

            with open(json_path, 'w', encoding='utf-8') as jf:
                json.dump(records, jf, ensure_ascii=False, indent=2)

            self.stdout.write(self.style.SUCCESS(f"{role}: {count} vacancies -> {json_path}"))

        self.stdout.write(self.style.SUCCESS(f"Exported roles summary: {summary}"))
