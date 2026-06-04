# File: jobs/management/commands/scrape_all.py

```python
from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = "Barcha manbalardan IT vakansiyalarini yig'ish"

    def add_arguments(self, parser):
        parser.add_argument('--source', type=str, default='all',
                          help='Qaysi manbadan olish: all, hh, olx, apwork, kwork, teamwork, linkedin')

    def handle(self, *args, **options):
        source = options['source']

        parsers_map = {
            'hh': ('HH.uz', 'jobs.management.commands.parsers.hh_uz'),
            'olx': ('OLX.uz', 'jobs.management.commands.parsers.olx_uz'),
            'apwork': ('Apwork.uz', 'jobs.management.commands.parsers.apwork_uz'),
            'kwork': ('Kwork.ru', 'jobs.management.commands.parsers.kwork_ru'),
            'teamwork': ('Teamwork.uz', 'jobs.management.commands.parsers.teamwork_uz'),
            'linkedin': ('LinkedIn', 'jobs.management.commands.parsers.linkedin_rapidapi'),
        }

        if source == 'all':
            parsers_to_run = list(parsers_map.values())
        elif source in parsers_map:
            parsers_to_run = [parsers_map[source]]
        else:
            self.stderr.write(self.style.ERROR(f"Noma'lum manba: {source}"))
            self.stderr.write(f"Mavjud: {', '.join(parsers_map.keys())}")
            return

        total = 0
        for name, module_path in parsers_to_run:
            try:
                import importlib
                mod = importlib.import_module(module_path)
                count = mod.run()
                total += count
                self.stdout.write(self.style.SUCCESS(f"✅ {name}: {count} ta qo'shildi"))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"❌ {name}: {e}"))

        # Ko'rsatkichlarni yangilash
        from jobs.models import Job
        active = Job.objects.filter(is_active=True).count()
        self.stdout.write(self.style.SUCCESS(f"\n📊 Jami qo'shilgan: {total} ta"))
        self.stdout.write(f"📊 Bazadagi aktiv vakansiyalar: {active} ta")
```
