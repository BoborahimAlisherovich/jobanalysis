from django.shortcuts import render, redirect
import json

def ai_test_view(request):
    if request.method == "POST":
        answers = {
            "interest": request.POST.get("q1", ""),
            "skills": request.POST.get("q2", ""),
        }
        
        q2_lower = answers['skills'].lower() + answers['interest'].lower()
        if "python" in q2_lower or "django" in q2_lower or "backend" in q2_lower or "server" in q2_lower:
            rec = "Backend Developer"
            reason = "Sizning vizualga emas, logikaga bo'lgan qiziqishingiz va ma'lumotlar bilan ishlash malakangiz yuqori baholandi."
        elif "react" in q2_lower or "css" in q2_lower or "figma" in q2_lower or "dizayn" in q2_lower:
            rec = "Frontend / UI/UX Designer"
            reason = "Sizda arxitekturadan ko'ra ko'z bilan ko'rinadigan qulay interfeyslarni yaratishga nisbatan kuchli ishtiyoq mavjud."
        elif "data" in q2_lower or "math" in q2_lower or "analiz" in q2_lower or "sun'iy" in q2_lower:
            rec = "Data Scientist / ML Engineer"
            reason = "Raqamlar, ma'lumotlar massivi va bashorat algoritmlariga e'tiboringiz sizni eng yaxshi Data-Muhandis qila oladi."
        else:
            rec = "Product Manager / DevOps"
            reason = "Siz alohida bir jarayonga qotib qolishni xohlamaysiz, tizimli ishlash va jamoani yo'naltirishga xohishingiz kuchli."
            
        mock_ai_resp = json.dumps({"recommended_job": rec, "reason": reason})
        request.session['ai_recommendation'] = mock_ai_resp
        return redirect('ai_chat')
        
    return render(request, 'ai_test.html')

def ai_chat_view(request):
    rec_json = request.session.get('ai_recommendation', '{}')
    
    context = {}
    if rec_json != '{}':
        data = json.loads(rec_json)
        context['rec_job'] = data.get('recommended_job')
        context['rec_reason'] = data.get('reason')
    
    return render(request, 'ai_chat.html', context)
