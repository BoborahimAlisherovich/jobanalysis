from django.core.management.base import BaseCommand
import os
import json
import signal

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException()


class Command(BaseCommand):
    help = "Run all scrapers and export IT vacancies to a JSON fixture"

    def add_arguments(self, parser):
        parser.add_argument('--output', default='data/vacancies_it.json', help='Output fixture path')
        parser.add_argument('--no-scrape', action='store_true', help='Do not run scrapers, only export existing DB records')

    def handle(self, *args, **options):
        output = options['output']
        no_scrape = options['no_scrape']

        if not no_scrape:
            from .parsers import hh_uz, olx_uz, apwork_uz, kwork_ru, teamwork_uz
            from .parsers.linkedin_rapidapi import run as ln_run

            parsers = [
                ('HH.uz', hh_uz.run),
                ('OLX.uz', olx_uz.run),
                ('Kwork.ru', kwork_ru.run),
                ('Apwork.uz', apwork_uz.run),
                ('Teamwork.uz', teamwork_uz.run),
            ]

            total = 0
            for name, func in parsers:
                try:
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(30)
                    count = func()
                    signal.alarm(0)
                    total += count
                    self.stdout.write(self.style.SUCCESS(f"✅ {name}: {count} ta"))
                except TimeoutException:
                    self.stderr.write(self.style.WARNING(f"⏱️ {name}: vaqt tugadi (30s)"))
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"❌ {name}: {e}"))

            try:
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(20)
                ln = ln_run()
                signal.alarm(0)
                total += ln
                if ln:
                    self.stdout.write(self.style.SUCCESS(f"✅ LinkedIn: {ln} ta"))
            except TimeoutException:
                self.stderr.write(self.style.WARNING(f"⏱️ LinkedIn: vaqt tugadi"))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"❌ LinkedIn: {e}"))

            self.stdout.write(self.style.SUCCESS(f"\n📊 Scrapers added total: {total} records"))

        # Export IT category jobs
        from jobs.models import Job

        qs = Job.objects.filter(category__name__icontains='IT')
        fixtures = []
        for j in qs:
            skills = [s.name for s in j.required_skills.all()]
            fixtures.append({
                'model': 'jobs.job',
                'pk': j.pk,
                'fields': {
                    'title': j.title,
                    'company': j.company,
                    'category': j.category.name if j.category else None,
                    'country': j.country.name if j.country else None,
                    'description': j.description,
                    'job_type': j.job_type,
                    'salary_min': j.salary_min,
                    'salary_max': j.salary_max,
                    'currency': j.currency,
                    'required_skills': skills,
                    'source_url': j.source_url,
                    'source': j.source,
                    'is_active': j.is_active,
                    'posted_at': j.posted_at.isoformat() if j.posted_at else None,
                }
            })

        out_dir = os.path.dirname(output)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)

        with open(output, 'w', encoding='utf-8') as f:
            json.dump(fixtures, f, ensure_ascii=False, indent=2)

        self.stdout.write(self.style.SUCCESS(f"📦 Exported {len(fixtures)} IT vacancies to {output}"))
