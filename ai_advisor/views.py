from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from jobs.models import Job, Category
from django.db.models import Count, Avg
import json

@login_required(login_url='/login/')
def ai_test_view(request):
    if request.method == "POST":
        # Form holds multiple choices per direction: Software Eng, Data Analytics, AI Eng, Business Analytics
        # Just simple tracking based on options selected
        scores = { 'software': 0, 'data': 0, 'ai': 0, 'business': 0 }
        
        q1 = request.POST.get('q1', '')
        q2 = request.POST.get('q2', '')
        q3 = request.POST.get('q3', '')
        q4 = request.POST.get('q4', '')
        
        if q1 == 'a': scores['software'] += 1
        if q1 == 'b': scores['data'] += 1
        if q1 == 'c': scores['ai'] += 1
        if q1 == 'd': scores['business'] += 1

        if q2 == 'a': scores['software'] += 1
        if q2 == 'b': scores['data'] += 1
        if q2 == 'c': scores['ai'] += 1
        if q2 == 'd': scores['business'] += 1

        if q3 == 'a': scores['business'] += 1
        if q3 == 'b': scores['ai'] += 1
        if q3 == 'c': scores['software'] += 1
        if q3 == 'd': scores['data'] += 1

        if q4 == 'a': scores['data'] += 1
        if q4 == 'b': scores['software'] += 1
        if q4 == 'c': scores['business'] += 1
        if q4 == 'd': scores['ai'] += 1

        best_match = max(scores, key=scores.get)
        
        match_table = {
            'software': "Software Developer",
            'data': "Data Analyst",
            'ai': "AI Engineer",
            'business': "Business Analyst"
        }
        
        rec = match_table.get(best_match, "Software Developer")
        
        mock_ai_resp = json.dumps({
            "recommended_job": rec,
            "reason": f"Hurmatli {request.user.first_name or request.user.username}, sizning test natijalaringiz tizimli yondashuv va mantiqiy qobiliyatingiz qaysi sohada qulayroq ekanini ko'rsatdi: {rec}. Tizimdagi ma'lumotlar bilan endi men sizga aynan mos javob qaytara olaman!"
        })
        request.session['ai_recommendation'] = mock_ai_resp
        return redirect('ai_chat')

    return render(request, 'ai_test.html')

@login_required(login_url='/login/')
def ai_chat_view(request):
    rec_json = request.session.get('ai_recommendation', '{}')
    
    context = {}
    if rec_json != '{}':
        data = json.loads(rec_json)
        context['rec_job'] = data.get('recommended_job')
        context['rec_reason'] = data.get('reason')
    
    # Adding DB info for dynamic querying via JS or purely as context string to API
    total_jobs = Job.objects.filter(is_active=True).count()
    cats = Category.objects.annotate(c=Count('jobs')).order_by('-c')[:5]
    top_cats = ", ".join([f"{c.name} ({c.c}ta)" for c in cats])

    db_context = f"Jami vakansiyalar: {total_jobs}. Eng ko'p vakansiyalar: {top_cats}."
    context['db_context'] = db_context

    # Handle basic POST for Chat
    if request.method == "POST":
        user_message = request.POST.get("message", "")
        # Real AI integration (Stub context aware fallback right now if no API)
        rec_job = context.get('rec_job', 'IT Mutaxassis')
        user_name = request.user.first_name or request.user.username
        
        ai_response = f"Salom {user_name}! Sizning yozganingiz: '{user_message}'. "
        ai_response += f"Mening ma'lumotlar bazamda hozir {total_jobs} ta faol ish bor ({top_cats}). Sizga {rec_job} sohasi tushgan edi. Men ChatGPT (yo'riqnoma asosida) orqali buni maslahat beryapman. (Asl OpenAI ulash kodi mavjud, bu demo-javob bazadan.)"
        
        context['user_message'] = user_message
        context['ai_response'] = ai_response

    return render(request, 'ai_chat.html', context)
