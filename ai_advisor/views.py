from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from jobs.models import Job, Category
from django.db.models import Count, Avg
import json
from .questions import TEST_QUESTIONS

@login_required(login_url='/login/')
def ai_test_view(request):
    if request.method == "POST":
        scores = { 'A': 0, 'B': 0, 'C': 0, 'D': 0 }
        
        # Talab qilingan 30 ta savolni tahlil qilish
        for i in range(1, 31):
            answer = request.POST.get(f'q{i}')
            if answer in scores:
                scores[answer] += 1

        best_match = max(scores, key=scores.get)
        
        # A - Software Engineer, B - Data Scientist, C - AI Engineer, D - Product Manager
        match_table = {
            'A': {
                'title': "Software Engineer / Backend Dasturchi",
                'advice': "Sizga murakkab serverlar, dasturiy axitekturalar va tizimlar qurish mos keladi. Siz logikaga va jarayonlarni avtomatlashtirishga moyilsiz."
            },
            'B': {
                'title': "Data Analyst / Data Scientist",
                'advice': "Sizning diqqatingiz tafsilotlarda va matematik isbotlarda. Katta ma'lumotlar bilan ishlash va faktlar asosida biznes analitikasi – sizning kuchingiz."
            },
            'C': {
                'title': "AI & ML Engineer / AI Researcher",
                'advice': "Siz innovatsiyalarga va abstrakt nazariyalarni amaliyotga tadbiq qilishga chanqoqsiz. Intellektual tizimlar (Neyrotarmoqlar) bilan ishlashni tavsiya qilaman."
            },
            'D': {
                'title': "Product Manager / IT Strateg / Analitik",
                'advice': "Siz yaxshi texnik asosga ega rahbar va tizimli fikrlovchi biznesmensiz. Asosiy maqsad texnologiya emas, muammoga eng yaxshi yechim berish."
            }
        }
        
        result = match_table.get(best_match, match_table['A'])
        
        mock_ai_resp = json.dumps({
            "recommended_job": result['title'],
            "reason": f"Hurmatli {request.user.first_name or request.user.username}, sizning test natijalaringiz quyidagi kasb sizga 99% mosligini ko'rsatdi: {result['title']}. AI Tavsiyasi: {result['advice']}"
        })
        request.session['ai_recommendation'] = mock_ai_resp
        return redirect('ai_chat')

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
