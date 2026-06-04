from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from ai_advisor.services import get_ai_chat_response_stream


class Command(BaseCommand):
    help = 'Run a quick end-to-end AI response test using the first active user or a test user.'

    def handle(self, *args, **options):
        User = get_user_model()
        user = User.objects.filter(is_active=True).first()
        if not user:
            user = User.objects.create_user(username='ai_test_user', password='testpass', first_name='Test', last_name='User')
            self.stdout.write(self.style.WARNING('Created test user: ai_test_user'))

        self.stdout.write(self.style.NOTICE(f'Using user: {user.username}'))

        question = "Salom, menga backend uchun qaysi ko'nikmalar kerak va qayerdan boshlash kerak?"
        stream = get_ai_chat_response_stream(user, question)
        full = []
        for chunk in stream:
            full.append(chunk)
            self.stdout.write(chunk)

        self.stdout.write(self.style.SUCCESS('AI test completed.'))
