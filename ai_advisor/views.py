from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from jobs.models import Job, Category
from django.db.models import Count, Avg
import json
from .questions import TEST_QUESTIONS

@login_required(login_url='/login/')
def ai_test_view(request):
    from .models import ChatSession, TestResult
    
    # Agar foydalanuvchi "Qayta topshirish" tugmasini bossa, eski test natijasini o'chiramiz
    if request.GET.get('retake') == '1':
        TestResult.objects.filter(user=request.user).delete()
        ChatSession.objects.filter(user=request.user).delete()
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
        ChatSession.objects.filter(user=request.user).delete()

        request.session['ai_recommendation'] = json.dumps(recommendation_data)
        
        # Test natijasi saqlangach, avtomatik chat sahifasiga o'tkazish
        return redirect('ai_chat')
        
    context = {
        'questions': TEST_QUESTIONS
    }
    return render(request, 'ai_test.html', context)

@login_required(login_url='/login/')
def ai_chat_view(request):
    from .models import TestResult
    
    rec_json = request.session.get('ai_recommendation', '{}')
    test_recommendation = {}
    
    # Agar foydalanuvchi tizimdan chiqib ketgan bo'lsa (session tozalangan bo'lsa),
    # ma'lumotlarni bazadan tortib olamiz:
    if rec_json == '{}':
        existing_result = TestResult.objects.filter(user=request.user).order_by('-created_at').first()
        if existing_result:
            test_recommendation = existing_result.ai_recommendation
            # Kelgusida foydalanishi uchun sessionga ham yozib qo'yamiz
            request.session['ai_recommendation'] = json.dumps(test_recommendation)
    else:
        test_recommendation = json.loads(rec_json)
        
    context = {}
    if test_recommendation:
        context['rec_job'] = test_recommendation.get('recommended_job')
        context['rec_reason'] = test_recommendation.get('reason')
    
    # Bazasining umumiy statistikasi (JS orqali ham chaqirilishi tayyor turshi uchun)
    total_jobs = Job.objects.filter(is_active=True).count()
    cats = Category.objects.annotate(c=Count('jobs')).order_by('-c')[:5]
    top_cats = ", ".join([f"{c.name} ({c.c}ta)" for c in cats])

    context['db_context'] = f"Jami vakansiyalar: {total_jobs}. Eng ko'p vakansiyalar: {top_cats}."

    # Chat xotirasini olish (eski xabarlarni ekranda ko'rsatish)
    from .services import _clean_ai_response, get_chat_session
    chat_session = get_chat_session(request.user)
    cleaned_history = []
    history_changed = False
    for msg in chat_session.message_history:
        content = msg.get('content', '')
        if msg.get('role') == 'assistant':
            cleaned_content = _clean_ai_response(content)
            if cleaned_content != content:
                history_changed = True
            content = cleaned_content
        if content.strip():
            cleaned_history.append({**msg, 'content': content})
        else:
            history_changed = True

    if history_changed:
        chat_session.message_history = cleaned_history
        chat_session.save(update_fields=['message_history', 'updated_at'])

    context['chat_history'] = chat_session.message_history

    return render(request, 'ai_chat.html', context)

from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

@login_required(login_url='/login/')
def ai_chat_stream(request):
    from .services import get_ai_chat_response_stream, get_latest_test_recommendation

    if request.method == "POST":
        user_message = request.POST.get("message", "")
        
        # Olingan test natijalarini yig'ish
        test_recommendation = get_latest_test_recommendation(request.user)
        
        # Streaming response generatsiya qilish
        response_generator = get_ai_chat_response_stream(request.user, user_message, test_recommendation)
        
        return StreamingHttpResponse(response_generator, content_type='text/plain')
        
    return JsonResponse({"error": "Faqat POST so'rov qabul qilinadi"}, status=400)
