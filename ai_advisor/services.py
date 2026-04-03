import openai
from django.conf import settings
from .models import TestResult, ChatSession

openai.api_key = getattr(settings, 'OPENAI_API_KEY', '')

def analyze_career_test(user, answers_dict):
    prompt = f"Foydalanuvchi javoblari: {answers_dict}. Uning xarakteri va qiziqishlaridan kelib chiqib, 3 ta eng mos keluvchi zamonaviy kasbni va nima uchunligini JSON formatida qaytar."
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "You are an expert career advisor."},
                  {"role": "user", "content": prompt}]
    )
    
    ai_data = response.choices[0].message.content
    
    # Natijani saqlash
    result = TestResult.objects.create(user=user, answers_data=answers_dict, ai_recommendation=ai_data)
    return result

def chat_step(user, user_message):
    session, created = ChatSession.objects.get_or_create(user=user)
    
    if created:
        session.message_history.append({"role": "system", "content": "Siz AI karera maslahatchisisiz."})
        
    session.message_history.append({"role": "user", "content": user_message})
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=session.message_history
    )
    ai_reply = response.choices[0].message.content
    session.message_history.append({"role": "assistant", "content": ai_reply})
    session.save()
    
    return ai_reply