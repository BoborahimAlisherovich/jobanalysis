from django.core.management.base import BaseCommand
from django.utils import timezone
import json
import os

from jobs.models import Job, Category


class Command(BaseCommand):
    help = 'Export strict IT-category vacancies to JSON and JSONL. Filters categories by common IT keywords.'

    def add_arguments(self, parser):
        parser.add_argument('--out-json', default='data/vacancies_it_only.json')
        parser.add_argument('--out-jsonl', default='data/vacancies_it_only.jsonl')

    def handle(self, *args, **options):
        out_json = options['out_json']
        out_jsonl = options['out_jsonl']

        # Determine IT categories present in DB
        it_cats = Category.objects.filter(
            name__icontains='it'
        ) | Category.objects.filter(name__icontains='dastur')

        if not it_cats.exists():
            # Fallback: try slug contains 'it'
            it_cats = Category.objects.filter(slug__icontains='it')

        self.stdout.write(f"Found {it_cats.count()} candidate IT categories.")

        jobs_qs = Job.objects.filter(is_active=True, category__in=it_cats).select_related('category', 'country')
        self.stdout.write(f"Exporting {jobs_qs.count()} IT jobs to {out_json} and {out_jsonl}.")

        os.makedirs(os.path.dirname(out_json), exist_ok=True)

        records = []
        with open(out_jsonl, 'w', encoding='utf-8') as jl:
            for j in jobs_qs:
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

        with open(out_json, 'w', encoding='utf-8') as jf:
            json.dump(records, jf, ensure_ascii=False, indent=2)

        self.stdout.write(self.style.SUCCESS(f"Export complete: {len(records)} records."))
