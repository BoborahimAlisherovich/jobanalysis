import openai
from django.conf import settings
from .models import TestResult, ChatSession
from jobs.models import Job, Category, Country
from django.db.models import Count

openai.api_key = getattr(settings, 'OPENAI_API_KEY', '')

def get_platform_context():
    """Baza bo'yicha platformamizdagi real vaqt (live) statistikasini yig'ish"""
    total_jobs = Job.objects.filter(is_active=True).count()
    
    top_categories = Category.objects.annotate(c=Count('jobs')).order_by('-c')[:5]
    cat_str = ", ".join([f"{c.name} ({c.c} ta vakansiya)" for c in top_categories])
    
    top_countries = Country.objects.annotate(c=Count('job')).order_by('-c')[:3]
    country_str = ", ".join([f"{c.name} ({c.c} ta ish)" for c in top_countries])
    
    avg_salary = 0
    # O'rtacha maoshni topish kabi qo'shimcha statistikalar ham imkoni boricha yig'iladi. (Hozircha raqamlardan)

    return {
        "total_jobs": total_jobs,
        "top_cats": cat_str,
        "top_countries": country_str
    }

def get_ai_chat_response(user, user_message, test_recommendation=None):
    """
    Kiritilgan xabarni OpenAI (ChatGPT) ga yoki Local Fallback mexanizmiga uzatib,
    fayl/bazadagi statistika bilan boyitgan holda javob qaytaradi.
    """
    stats = get_platform_context()
    user_full_name = f"{user.first_name} {user.last_name}".strip()
    if not user_full_name:
        user_full_name = user.username

    rec_job = test_recommendation.get('recommended_job', 'Noma\'lum') if test_recommendation else "Hali testdan o'tmagan"

    system_prompt = f"""Siz MMT (Mening Mutaxassislik Tanlovim) platformasining rasmiy va aqlli karyera maslahatchisisiz. 
Siz doimo foydalanuvchiga ism-familiyasi bilan chiroyli, motivatsion va aniq muomala qilishingiz kerak. 

Foydalanuvchi ma'lumotlari:
- Ism-familiyasi: {user_full_name}
- Test natijalariga ko'ra tavsiya etilgan kasb: {rec_job}

Sizning bilimlar bazangizdagi MMT platformamiz holati (Real Time DB):
- Saytdagi jami faol vakansiyalar soni: {stats['total_jobs']} ta
- Eng ko'p vakansiyalar qaysi sohalarda: {stats['top_cats']} 
- Asosiy ish bo'layotgan davlatlar: {stats['top_countries']}

Qoidalar:
1. Agar foydalanuvchi "qaysi kasbga talab ko'p?", "platformada nima bor?" deb so'rasa, yuqoridagi ma'lumotlardan aniq raqamlarni olib ko'rsating.
2. Tavsiyalarni global bozor trendlari bilan bog'lang (masalan, AI va Data sohasiga butun dunyoda o'sib borayotgan talab haqida).
3. Foydalanuvchini platformada ko'proq analitika pultidan foydalanishga undab turing.
4. Har bir maslahat sof, professional va raqamlarga asoslangan bo'lishi kerak.
"""

    if openai.api_key:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4", # yoki 3.5-turbo
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=500,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            pass # API xato bersa, pastdagi Local logic ishga tushadi

    # ==========================
    # OFFLINE / MOCK AI FALLBACK (Agar API-KALIT bo'lmasa)
    # ==========================
    user_msg_lower = user_message.lower()
    
    if "platformada" in user_msg_lower or "ko'p" in user_msg_lower or "qaysi kasb" in user_msg_lower:
        return (f"Hurmatli {user_full_name}, hozirgi vaqtda platformamizda umumiy {stats['total_jobs']} ta faol vakansiya mavjud. "
                f"Eng ko'p ehtiyoj quyidagi sohalarga: {stats['top_cats']}. \n"
                f"Shuningdek davlatlar kesimida olib qarasak, {stats['top_countries']} bo'yicha e'lonlar yetakchilik qilmoqda. "
                f"Sizning test natijangiz ({rec_job}) ga suyanib aytishim mumkinki, IT bozori aynan shu sohalar sari odimlamoqda.")
    
    if "rahmat" in user_msg_lower:
        return f"Sizga ham rahmat, {user_full_name}! Platformamizda o'zingizga mos profilni shakllantiring va ish topishda omad tilayman."

    return (f"Salom, {user_full_name}!\n\n"
            f"Mening ismim MMT-AI. Sizning qiziqishingiz {rec_job} yo'nalishiga tushgan. "
            f"Xozirda bazamizdagi vakansiyalar soni {stats['total_jobs']} ta bo'lib, eng trenddagi kasblar sifatida {stats['top_cats']} o'rin olgan. "
            f"Sizning savolingizni tahlil qilish uchun hozircha ochiq OpenAI kaliti kiritilmagan. Davom etish uchun maxsus AI API ulanishini sozlash mumkin!\n"
            f"(Savolingiz: '{user_message}')")

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