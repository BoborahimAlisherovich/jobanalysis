from django.core.management.base import BaseCommand
import signal

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException()

class Command(BaseCommand):
    help = "Barcha manbalardan IT vakansiyalarini yig'ish"

    def handle(self, *args, **options):
        from .parsers import hh_uz, olx_uz, apwork_uz, kwork_ru, teamwork_uz
        from .parsers.linkedin_rapidapi import run as ln_run

        parsers = [
            ("HH.uz", hh_uz.run),
            ("OLX.uz", olx_uz.run),
            ("Kwork.ru", kwork_ru.run),
            ("Apwork.uz", apwork_uz.run),
            ("Teamwork.uz", teamwork_uz.run),
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

        from jobs.models import Job
        active = Job.objects.filter(is_active=True).count()
        self.stdout.write(self.style.SUCCESS(f"\n📊 Jami qo'shilgan: {total} ta"))
        self.stdout.write(f"📊 Bazadagi aktiv vakansiyalar: {active} ta")
