from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from jobs.models import Job, Category
from django.db.models import Count, Avg
import json
from .questions import TEST_QUESTIONS

@login_required(login_url='/login/')
def ai_test_view(request):
    from .models import TestResult
    
    # Agar foydalanuvchi "Qayta topshirish" tugmasini bossa, eski test natijasini o'chiramiz
    if request.GET.get('retake') == '1':
        TestResult.objects.filter(user=request.user).delete()
        if 'ai_recommendation' in request.session:
            del request.session['ai_recommendation']
        return redirect('ai_test')

    # Agar test oldin yechilgan bo'lsa, to'g'ridan-to'g'ri chatga yo'naltirish
    existing_result = TestResult.objects.filter(user=request.user).order_by('-created_at').first()
    if existing_result and request.method == "GET":
        request.session['ai_recommendation'] = json.dumps(existing_result.ai_recommendation)
        return redirect('ai_chat')

    if request.method == "POST":
        # A - Producer (Ishlab chiqaruvchi - Natijaga yo'naltirilgan)
        # B - Administrator (Ma'mur - Tizim va tartib)
        # C - Entrepreneur (Tadbirkor - G'oyalar)
        # D - Integrator (Birlashtiruvchi - Jamoa)
        scores = { 'A': 0, 'B': 0, 'C': 0, 'D': 0 }

        answers = {}
        for i in range(1, 31):
            answer = request.POST.get(f'q{i}')
            if answer in scores:
                scores[answer] += 1
                answers[f'q{i}'] = answer

        best_match = max(scores, key=scores.get)

        match_table = {
            'A': {
                'title': "Producer (Natijaga yo'naltirilgan - Dasturchi, DevOps, Injinir)",
                'advice': "Siz (P) roliga ko'proq mos tushasiz. Sizga aniq vazifalar, natijaga qaratilgan ishlar va texnik xatolarni hal qilish juda yoqadi. Backend, Frontend, yoki DevOps kabi rollar aynan siz uchun yaratilgan."
            },
            'B': {
                'title': "Administrator (Tizimli va tartibli - QA, Data Analyst, SysAdmin)",
                'advice': "Siz (A) roliga ko'proq mos tushasiz. Tafsilotlarga e'tibor berasiz, hamma narsa tizimli va qoidalarga muvofiq ishlashini xohlaysiz. Dasturiy ta'minotni test qilish (QA), tizim ma'murligi yoki Data Analitikasi sizga juda mos."
            },
            'C': {
                'title': "Entrepreneur (Innovator - AI Engineer, Product Manager, UX/UI)",
                'advice': "Siz (E) roliga ko'proq mos tushasiz. Siz yangi g'oyalarni yaxshi ko'rasiz, xavflarni o'zingizga ola bilasiz. AI modellari yaratish, yangi IT mahsulotlar o'ylab topish yoki tizimlar dizaynini (UX/UI) chizish sizni ilhomlantiradi."
            },
            'D': {
                'title': "Integrator (Jamoa odami - Scrum Master, Project Manager, HR in IT)",
                'advice': "Siz (I) roliga ko'proq mos tushasiz. Siz uchun odamlararo munosabatlar, konfliktlarni hal qilish va jamoani bitta maqsad sari birlashtirish juda muhim. IT loyihalarni boshqarish, HR yoki Scrum Master lavozimlari ayni muddao."
            }
        }

        result = match_table.get(best_match, match_table['A'])
        
        recommendation_data = {
            "recommended_job": result['title'],
            "reason": f"Hurmatli {request.user.first_name or request.user.username}, PAEI modeli bo'yicha tahlil natijasida sizga eng mos kasb: {result['title']}. AI Tavsiyasi: {result['advice']}"
        }

        # Natijani bazaga saqlash
        TestResult.objects.create(
            user=request.user,
            answers_data=answers,
            ai_recommendation=recommendation_data
        )

        request.session['ai_recommendation'] = json.dumps(recommendation_data)
    context = {
        'questions': TEST_QUESTIONS
    }
    return render(request, 'ai_test.html', context)

@login_required(login_url='/login/')
def ai_chat_view(request):
    from .services import get_ai_chat_response
    rec_json = request.session.get('ai_recommendation', '{}')
    test_recommendation = {}
    
    context = {}
    if rec_json != '{}':
        test_recommendation = json.loads(rec_json)
        context['rec_job'] = test_recommendation.get('recommended_job')
        context['rec_reason'] = test_recommendation.get('reason')
    
    # Bazasining umumiy statistikasi (JS orqali ham chaqirilishi tayyor turshi uchun)
    total_jobs = Job.objects.filter(is_active=True).count()
    cats = Category.objects.annotate(c=Count('jobs')).order_by('-c')[:5]
    top_cats = ", ".join([f"{c.name} ({c.c}ta)" for c in cats])

    context['db_context'] = f"Jami vakansiyalar: {total_jobs}. Eng ko'p vakansiyalar: {top_cats}."

    # Handle basic POST for Chat
    if request.method == "POST":
        user_message = request.POST.get("message", "")
        # Real AI integration call (via services.py)
        
        ai_response = get_ai_chat_response(request.user, user_message, test_recommendation)
        
        context['user_message'] = user_message
        context['ai_response'] = ai_response

    return render(request, 'ai_chat.html', context)
