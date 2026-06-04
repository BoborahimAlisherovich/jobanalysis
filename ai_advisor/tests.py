from django.test import TestCase

from ai_advisor.models import ChatSession
from ai_advisor.services import (
    _local_chat_answer,
    get_ai_chat_response_stream,
)
from jobs.models import Category, Country, Job
from users.models import CustomUser, Skill


class AiAdvisorResponseTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="ali",
            password="test-pass-123",
            first_name="Ali",
        )
        self.category = Category.objects.create(name="Backend Developer")
        self.country = Country.objects.create(name="Uzbekistan")
        self.skill_python = Skill.objects.create(name="Python")
        self.skill_django = Skill.objects.create(name="Django")
        self.job = Job.objects.create(
            title="Junior Django Backend Developer",
            company="AURA Tech",
            category=self.category,
            country=self.country,
            description="Python Django REST API SQL",
            source_url="https://example.com/jobs/backend-1",
            source="test",
        )
        self.job.required_skills.add(self.skill_python, self.skill_django)
        self.recommendation = {
            "recommended_job": "Producer (Natijaga yo'naltirilgan - Dasturchi, DevOps, Injinir)",
            "reason": "Backend va texnik muammolarni hal qilishga mos.",
        }

    def test_local_answer_uses_question_topic_and_profile(self):
        answer = _local_chat_answer(
            "Ali",
            self.recommendation,
            "Jami aktiv vakansiyalar: 1 ta.",
            "Django bo'yicha qanday roadmap kerak?",
        )

        self.assertIn("Backend Developer", answer)
        self.assertIn("roadmap", answer.lower())
        self.assertIn("Django", answer)

    def test_greeting_stream_returns_once_and_saves_history(self):
        response = "".join(get_ai_chat_response_stream(self.user, "salom", self.recommendation))

        self.assertIn("Assalomu alaykum", response)
        self.assertNotIn("Mos vakansiya yo'nalishi", response)

        session = ChatSession.objects.get(user=self.user)
        assistant_messages = [
            msg for msg in session.message_history if msg.get("role") == "assistant"
        ]
        self.assertEqual(len(assistant_messages), 1)
