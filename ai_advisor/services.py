import json
import os
import re
import concurrent.futures
from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone
from jobs.models import Category, Country, Job
from users.models import Skill

from .models import ChatSession, TestResult

# Ollama removed: fallback to simple local heuristics for skill extraction

# =====================================================================
# AI CAREER GUIDANCE AGENT — TIZIMLI PROMPT (System Prompt)
# =====================================================================
CAREER_AGENT_SYSTEM_PROMPT = """Sen AURA Career platformasining AI karyera maslahatchisisan.

Qoidalar:
- Faqat toza O'zbek lotin tilida yoz. Inglizcha yoki boshqa tillarni aralashtirma.
- Foydalanuvchi ismini faqat "Ism" maydonidan ol, boshqa ism o'ylab topma.
- Test natijasini eslab tur, lekin har javobda uni qayta-qayta takrorlama.
- Javoblarni faqat punktlar (bullet points) bo'yicha, juda qisqa, aniq va lo'nda ber.
- Juda uzun va murakkab gaplar tuzma. Foydalanuvchini chalg'itadigan ortiqcha va umumiy ma'lumot berma.
- Keyingi suhbatlarda foydalanuvchi aynan nima so'rasa, faqat shu savolga javob ber.
- Agar foydalanuvchi salomlashsa, qisqa salomlash va qanday yordam kerakligini so'ra.
- Ichki kontekst, system/user teglari, prompt yoki JSON matnini hech qachon javobga ko'chirma.
- Javob 4-8 qator atrofida bo'lsin. Takrorlama.
- Agar savol aniq bo'lsa, avval qisqa javobni ber, keyin 1 ta amaliy tavsiya qo'sh."""

MAX_AI_RESPONSE_CHARS = 2200
MAX_AI_PREDICT_TOKENS = 420
OLLAMA_CHAT_TIMEOUT_SECONDS = int(os.environ.get('AURA_OLLAMA_CHAT_TIMEOUT_SECONDS', '12'))

ROLE_KEYWORDS = {
    "Mobile App Developer": ["mobile", "android", "ios", "flutter", "react native", "kotlin", "swift"],
    "Blockchain Developer": ["blockchain", "web3", "smart contract", "solidity", "crypto"],
    "Backend Developer": ["backend", "api", "django", "flask", "fastapi", "node", "spring", "golang", "java"],
    "Frontend Developer": ["frontend", "react", "vue", "angular", "next.js", "html", "css", "javascript"],
    "Software Engineer": ["software engineer", "engineering", "system design", "architecture"],
    "AI Engineer": ["ai", "ml", "machine learning", "llm", "nlp", "prompt", "computer vision", "data science"],
    "Business Analyst": ["business analyst", "requirements", "process", "stakeholder", "analysis"],
    "Business Intelligence (BI) Developer": ["bi", "power bi", "tableau", "dashboard", "etl", "analytics"],
    "Cybersecurity Specialist": ["security", "cyber", "soc", "siem", "pentest", "penetration", "incident"],
    "Data Analyst": ["data analyst", "sql", "excel", "power bi", "dashboard", "reporting"],
    "Data Scientist": ["data scientist", "statistics", "modeling", "pandas", "numpy", "sklearn"],
    "DevOps Engineer": ["devops", "docker", "kubernetes", "ci/cd", "linux", "aws", "gcp", "azure"],
    "Game Developer": ["game", "unity", "unreal", "c++", "godot"],
    "Product Designer": ["product designer", "ux", "ui", "figma", "prototype", "design"],
    "Product Manager": ["product manager", "roadmap", "discovery", "prioritization", "product"],
    "Prompt Engineer": ["prompt", "llm", "chatgpt", "agent", "copilot"],
    "QA Engineer": ["qa", "test", "testing", "automation", "selenium", "playwright", "cypress"],
    "UI/UX Designer": ["ui", "ux", "figma", "wireframe", "design system"],
}

UZ_HINTS = {
    "backend": "Backend Developer",
    "back-end": "Backend Developer",
    "frontend": "Frontend Developer",
    "front-end": "Frontend Developer",
    "mobil": "Mobile App Developer",
    "android": "Mobile App Developer",
    "ios": "Mobile App Developer",
    "devops": "DevOps Engineer",
    "qa": "QA Engineer",
    "test": "QA Engineer",
    "data": "Data Analyst",
    "analyst": "Data Analyst",
    "analitika": "Data Analyst",
    "dizayn": "UI/UX Designer",
    "ux": "UI/UX Designer",
    "ui": "UI/UX Designer",
    "product": "Product Manager",
    "ai": "AI Engineer",
    "llm": "Prompt Engineer",
    "security": "Cybersecurity Specialist",
    "blockchain": "Blockchain Developer",
    "game": "Game Developer",
}


def get_user_full_name(user):
    """Ro'yxatdan o'tgan foydalanuvchi ismini yagona joyda aniqlaydi."""
    return f"{user.first_name} {user.last_name}".strip() or user.username


def get_latest_test_recommendation(user):
    """Foydalanuvchining oxirgi test natijasini bazadan oladi."""
    result = TestResult.objects.filter(user=user).order_by('-created_at').first()
    return result.ai_recommendation if result else None


def get_chat_session(user):
    """Har bir user uchun alohida chat xotirasini qaytaradi."""
    session = ChatSession.objects.filter(user=user).order_by('-updated_at', '-id').first()
    if session:
        return session
    return ChatSession.objects.create(user=user)


def _normalize_repetition_unit(text):
    """Takrorlanishni aniqlash uchun matnni ixcham normallashtiradi."""
    return re.sub(r'\s+', ' ', text).strip().lower()


def _normalize_text(text):
    return _normalize_repetition_unit(text or "")


def _looks_uzbek(text):
    if not text:
        return False
    low = text.lower()
    uz_markers = [
        "salom", "rahmat", "kerak", "qanday", "qayerdan", "boshlash", "ko'nik", "vakansiya",
        "yo'nalish", "maslahat", "tavsiya", "qisqa", "javob", "o'rgan", "mos", "talab", "bozor", "roadmap"
    ]
    hits = sum(1 for marker in uz_markers if marker in low)
    alpha_count = sum(1 for ch in low if ch.isalpha())
    latin_count = sum(1 for ch in low if 'a' <= ch <= 'z')
    latin_ratio = latin_count / max(1, alpha_count)
    return hits >= 1 or latin_ratio > 0.8


def _infer_role_hint(text, test_recommendation=None):
    low = _normalize_text(text)
    if test_recommendation:
        rec_job = test_recommendation.get('recommended_job', '')
        for role_name in ROLE_KEYWORDS:
            if role_name.lower() in rec_job.lower():
                return role_name

    for keyword, role_name in UZ_HINTS.items():
        if keyword in low:
            return role_name
    return None


def _intent_from_text(text):
    low = _normalize_text(text)
    if any(word in low for word in ["roadmap", "yo'l xarita", "reja", "qanday o'rgan", "qanday organ"]):
        return "roadmap"
    if any(word in low for word in ["vakansiya", "ish", "topish", "mos", "lavozim"]):
        return "vacancy"
    if any(word in low for word in ["bozor", "talab", "trend", "statistika"]):
        return "market"
    if any(word in low for word in ["skill", "konikma", "ko'nikma", "nima o'rgan", "nima organ", "qaysi", "python", "django", "drf", "react", "java", "node", "flutter", "c++", "c#", "golang", "php"]):
        return "skills"
    if any(word in low for word in ["salom", "assalomu alaykum", "hello", "hi"]):
        return "greeting"
    return "general"


def _compose_role_context(role_hint, bozor_data):
    if not role_hint:
        return bozor_data
    role_lines = []
    for line in bozor_data.splitlines():
        if role_hint.lower() in line.lower():
            role_lines.append(line)
    if role_lines:
        return "\n".join(role_lines[:6])
    return bozor_data


def _should_stop_generation(text):
    """Kichik lokal modellarda uchraydigan cheksiz takrorlanishni erta to'xtatadi."""
    if len(text) >= MAX_AI_RESPONSE_CHARS:
        return True

    if text.count("Savol:") > 3:
        return True

    units = []
    units.extend(re.split(r'[\n\r]+', text))
    units.extend(re.split(r'(?<=[.!?])\s+', text))

    seen = {}
    for unit in units:
        normalized = _normalize_repetition_unit(unit)
        if len(normalized) < 35:
            continue
        seen[normalized] = seen.get(normalized, 0) + 1
        if seen[normalized] >= 3:
            return True

    return False


def _clean_ai_response(text):
    """Tarixga saqlashdan oldin javobni qisqartirib, ortiqcha takrorlarni olib tashlaydi."""
    if not text:
        return text

    text = re.sub(r'</?(system|user|assistant|s)>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\[(Kontekst|Context):[^\n]*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^\s*(Kontekst|Context)\s*:[^\n]*$', '', text, flags=re.IGNORECASE | re.MULTILINE)
    text = re.sub(r'^\s*(system|user|assistant)\s*[:|].*$', '', text, flags=re.IGNORECASE | re.MULTILINE)
    text = re.sub(r'^\s*MUHIM\s*:[^\n]*$', '', text, flags=re.IGNORECASE | re.MULTILINE)
    text = text.replace('|system|', '').replace('|user|', '').replace('|assistant|', '')

    cleaned_lines = []
    seen_lines = {}
    for line in text.splitlines():
        normalized = _normalize_repetition_unit(line)
        if len(normalized) >= 35:
            seen_lines[normalized] = seen_lines.get(normalized, 0) + 1
            if seen_lines[normalized] > 2:
                continue
        cleaned_lines.append(line)

    cleaned = "\n".join(cleaned_lines).strip()
    if len(cleaned) > MAX_AI_RESPONSE_CHARS:
        cut_at = cleaned.rfind("\n", 0, MAX_AI_RESPONSE_CHARS)
        if cut_at < 800:
            cut_at = MAX_AI_RESPONSE_CHARS
        cleaned = cleaned[:cut_at].rstrip()

    return cleaned


def _is_low_quality_model_response(text):
    markers = [
        '<system', '<user', '</s>', '|system|', '|user|', '[Kontekst:', 'Kontekst: Foydala',
        'vazifa:', 'savol turi:', 'role hint:', 'ichki kontekst', 'kontekstni', 'prompt', 'system prompt'
    ]
    if any(marker.lower() in text.lower() for marker in markers):
        return True
    if len(_clean_ai_response(text)) < 20:
        return True
    if text.count('Ichki') > 2 or text.count('kontekst') > 3:
        return True
    return False


def _is_response_relevant(user_message, response_text, threshold=0.18):
    """Simple heuristic: check token overlap between user question and response.
    If overlap ratio is below threshold, consider response not relevant.
    """
    if not user_message or not response_text:
        return False

    def tokens(s):
        return set(re.findall(r"\w{4,}", s.lower()))

    u = tokens(user_message)
    r = tokens(response_text)
    if not u:
        return True
    overlap = u.intersection(r)
    ratio = len(overlap) / max(1, len(u))
    return ratio >= threshold


def _is_good_ai_response(user_message, response_text):
    if not response_text:
        return False
    if _is_low_quality_model_response(response_text):
        return False
    if not _looks_uzbek(response_text):
        return False
    if not _is_response_relevant(user_message, response_text):
        return False
    # Require at least one strong topical keyword overlap to avoid generic hallucinations.
    msg_tokens = set(re.findall(r"\w{4,}", _normalize_text(user_message)))
    resp_tokens = set(re.findall(r"\w{4,}", _normalize_text(response_text)))
    strong_overlap = msg_tokens.intersection(resp_tokens)
    return bool(strong_overlap) or len(resp_tokens.intersection({'backend', 'frontend', 'skill', 'vakansiya', 'roadmap', 'bozor', 'tavsiya'})) > 0


def _simple_local_reply(full_name, user_message, test_recommendation):
    """Oddiy suhbatlarda modelni chaqirmasdan tez va toza javob beradi."""
    msg = (user_message or "").strip().lower()
    greetings = {'salom', 'assalomu alaykum', 'assalom', 'hello', 'hi'}
    if msg in greetings:
        return (
            f"Assalomu alaykum, {full_name}!\n"
            "Men sizga roadmap, vakansiya, ko'nikma yoki bozor tahlili bo'yicha aniq yordam beraman."
        )

    if msg in {'rahmat', 'raxmat', 'tashakkur'}:
        return f"Arzimaydi, {full_name}! Yana karyera yoki vakansiyalar bo'yicha savolingiz bo'lsa, yozing."

    return None


def _call_ollama_with_timeout(callable_obj, timeout_seconds=OLLAMA_CHAT_TIMEOUT_SECONDS):
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = executor.submit(callable_obj)
    try:
        return future.result(timeout=timeout_seconds)
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


# =====================================================================
# MA'LUMOTLAR BAZASIDAN REAL BOZOR KONTEKSTINI YIG'ISH
# =====================================================================
def build_market_context():
    """
    Ma'lumotlar bazasidan real vaqt bozor statistikasini olib,
    AI agentiga beriladigan strukturali 'bozor_data' matnini shakllantiradi.
    """
    total_jobs = Job.objects.filter(is_active=True).count()

    # So'nggi 30 kundagi yangi vakansiyalar
    thirty_days_ago = timezone.now() - timedelta(days=30)
    new_jobs_30d = Job.objects.filter(
        is_active=True, posted_at__gte=thirty_days_ago
    ).count()

    # Kategoriyalar bo'yicha vakansiyalar soni (top 8) — trend bilan
    top_cats = Category.objects.annotate(
        job_count=Count('jobs', filter=Q(jobs__is_active=True))
    ).order_by('-job_count')[:8]

    cat_lines = []
    for cat in top_cats:
        if cat.job_count == 0:
            continue
        trend_label = ""
        if hasattr(cat, 'trend_score'):
            if cat.trend_score > 0.5:
                trend_label = " [O'sish trendida ↑]"
            elif cat.trend_score < -0.5:
                trend_label = " [Pasayish trendida ↓]"
        cat_lines.append(f"  - {cat.name}: {cat.job_count} ta vakansiya{trend_label}")

    # Eng ko'p talab qilinadigan ko'nikmalar
    top_skills = Skill.objects.annotate(
        demand=Count('job', filter=Q(job__is_active=True))
    ).order_by('-demand')[:10]
    skill_parts = [f"{s.name} ({s.demand} ta)" for s in top_skills if s.demand > 0]
    skill_str = ", ".join(skill_parts) if skill_parts else "Ma'lumot yo'q"

    # Mamlakat bo'yicha taqsimot
    top_countries = Country.objects.annotate(
        c=Count('job', filter=Q(job__is_active=True))
    ).order_by('-c')[:3]
    country_parts = [f"{c.name} ({c.c} ta)" for c in top_countries if c.c > 0]
    country_str = ", ".join(country_parts) if country_parts else "Ma'lumot yo'q"

    lines = [
        f"Jami aktiv vakansiyalar: {total_jobs} ta.",
        f"So'nggi 30 kunda qo'shilgan: {new_jobs_30d} ta.",
        "Kategoriyalar bo'yicha taqsimot:",
    ]
    lines.extend(cat_lines if cat_lines else ["  - Ma'lumot yo'q"])
    lines.append(f"Eng ko'p talab qilinadigan ko'nikmalar: {skill_str}.")
    lines.append(f"Geografik taqsimot: {country_str}.")

    return "\n".join(lines)


# =====================================================================
# FOYDALANUVCHI PROFILI VA TEST NATIJASINI YIG'ISH
# =====================================================================
def build_user_context(user, test_recommendation):
    """
    Foydalanuvchining profili va test natijasi asosida
    strukturali 'test_data' matnini shakllantiradi.
    """
    full_name = get_user_full_name(user)
    experience = getattr(user, 'experience_years', 0)

    # Foydalanuvchi ko'nikmalarini olish
    user_skills = list(user.skills.values_list('name', flat=True))
    skills_str = ", ".join(user_skills) if user_skills else "Ko'rsatilmagan"

    # PAEI test natijasi
    rec_job = "Hali testdan o'tmagan"
    paei_reason = ""
    if test_recommendation:
        rec_job = test_recommendation.get('recommended_job', "Noma'lum")
        paei_reason = test_recommendation.get('reason', '')

    lines = [
        f"Ism: {full_name}",
        f"Tajriba: {experience} yil",
        f"Profildagi ko'nikmalar: {skills_str}",
        f"PAEI test natijasi: {rec_job}",
    ]
    if paei_reason:
        lines.append(f"PAEI tahlili: {paei_reason[:300]}")

    return full_name, "\n".join(lines)


# =====================================================================
# ASOSIY STREAMING FUNKSIYA
# =====================================================================
def get_ai_chat_response_stream(user, user_message, test_recommendation=None):
    """
    AI Career Guidance Agent — ma'lumotlar bazasidan real bozor va foydalanuvchi
    ma'lumotlarini olib, Ollama orqali shaxsiylashtirilgan karyera tavsiyasi beradi.
    """
    # 1. Ma'lumotlar bazasidan kontekst yig'ish
    if test_recommendation is None:
        test_recommendation = get_latest_test_recommendation(user)
    full_name, test_data = build_user_context(user, test_recommendation)
    bozor_data = build_market_context()
    intent = _intent_from_text(user_message)
    role_hint = _infer_role_hint(user_message, test_recommendation)
    role_market_context = _compose_role_context(role_hint, bozor_data)

    # 2. Chat tarixini olish
    chat_session = get_chat_session(user)
    history = list(chat_session.message_history)

    # 3. AI ga yuboriladigan user xabarini tuzish
    # Birinchi avtomatik xabarda test natijasini tushuntiramiz.
    # Keyingi xabarlarda esa faqat foydalanuvchi so'ragan mavzuga javob beramiz.
    is_first_message = len(history) == 0
    is_initial_analysis = is_first_message and not user_message.strip()
    local_reply = _simple_local_reply(full_name, user_message, test_recommendation)

    if is_initial_analysis:
        context_block = (
            f"Ism: {full_name}\n"
            f"{test_data}\n\n"
            f"Bozor konteksti:\n{role_market_context}\n\n"
        )
        actual_user_msg = (
            context_block +
            "Vazifa: foydalanuvchiga birinchi marta test natijasini qisqa tushuntir. "
            "Mos yo'nalish, 1-2 sabab va 2 ta keyingi qadam yoz. Ichki kontekstni ko'chirma."
        )
    else:
        rec_job_short = test_recommendation.get('recommended_job', "Noma'lum") if test_recommendation else "N/A"
        total_jobs_count = Job.objects.filter(is_active=True).count()
        actual_user_msg = (
            f"Ism: {full_name}\n"
            f"Oxirgi PAEI/test natijasi: {rec_job_short}\n"
            f"Jami aktiv vakansiyalar: {total_jobs_count} ta\n"
            f"Foydalanuvchi savoli: {user_message}\n\n"
            f"Savol turi: {intent}\n"
            f"Role hint: {role_hint or 'yoq'}\n\n"
            "Vazifa: faqat foydalanuvchi savoliga javob ber. "
            "Javob qisqa, aniq va O'zbek lotinida bo'lsin. Ichki kontekstni ko'chirma."
        )

    # 4. Xabarlar ro'yxatini tayyorlash
    messages = [{"role": "system", "content": CAREER_AGENT_SYSTEM_PROMPT}]

    # So'nggi 6 ta xabarni tarixdan qo'shamiz va uzun/takroriy javoblarni qisqartiramiz.
    for msg in history[-6:]:
        content = msg.get("content", "")
        if msg.get("role") == "assistant":
            content = _clean_ai_response(content)[:1200]
        elif len(content) > 500:
            content = content[:500]
        if content.strip():
            messages.append({"role": msg.get("role", "user"), "content": content})

    messages.append({"role": "user", "content": actual_user_msg})

    # 5. Foydalanuvchi xabarini tarixga saqlaymiz (original, kontekstsiz)
    history.append({"role": "user", "content": user_message})
    chat_session.message_history = history
    chat_session.save()

    # =====================================================================
    # AI javob yaratish — Fine-tuned > Ollama > Fallback
    # =====================================================================
    full_response_holder = [""]

    def stream_generator():
        # Intercept greetings or common intents to give high-quality perfect Uzbek instantly
        if local_reply:
            full_response_holder[0] = local_reply
            yield local_reply
            updated_history = list(chat_session.message_history)
            updated_history.append({"role": "assistant", "content": local_reply})
            chat_session.message_history = updated_history
            chat_session.save()
            return
            
        # Kichik modellar o'zbek tilida yomon javob bergani uchun,
        # muhim so'rovlarda (roadmap, ish, ko'nikma) to'g'ridan-to'g'ri Python shablonlarini ishlatamiz.
        if intent in ['roadmap', 'vacancy', 'market', 'skills']:
            perfect_uzbek_reply = generate_fallback_response(
                full_name, test_recommendation, role_market_context, user_message=user_message, initial=False
            )
            full_response_holder[0] = perfect_uzbek_reply
            yield perfect_uzbek_reply
            updated_history = list(chat_session.message_history)
            updated_history.append({"role": "assistant", "content": perfect_uzbek_reply})
            chat_session.message_history = updated_history
            chat_session.save()
            return

        try:
            import ollama
            # Llama3.2:1b eng aqllisi, uni birinchi qo'yamiz.
            models_to_try = ['llama3.2:1b', 'qwen2:0.5b', 'aura-agent', 'tinyllama']
            chosen_model = None
            for model_name in models_to_try:
                try:
                    ollama.show(model_name)
                    chosen_model = model_name
                    break
                except Exception:
                    continue

            if chosen_model:
                try:
                    stream = ollama.chat(
                        model=chosen_model,
                        messages=messages,
                        stream=True,
                        options={
                            'temperature': 0.3, # Pastroq harorat (kamroq xato)
                            'top_p': 0.85,
                            'repeat_penalty': 1.15,
                            'num_predict': MAX_AI_PREDICT_TOKENS,
                            'num_ctx': 2048,
                            'stop': ['\nSavol:', '\nUser:', '\nFoydalanuvchi:'],
                        }
                    )
                    
                    full_resp = ""
                    for chunk in stream:
                        word = chunk.get('message', {}).get('content', '')
                        if word:
                            full_resp += word
                            yield word
                    
                    # Save to history
                    cleaned_resp = _clean_ai_response(full_resp)
                    full_response_holder[0] = cleaned_resp
                    
                except Exception as e:
                    print("Ollama error:", e)
                    fallback = generate_fallback_response(
                        full_name, test_recommendation, role_market_context, user_message=user_message, initial=is_initial_analysis
                    )
                    full_response_holder[0] = fallback
                    yield fallback
            else:
                raise Exception("Hech qanday model mavjud emas")
        except Exception:
            fallback = generate_fallback_response(
                full_name,
                test_recommendation,
                role_market_context,
                user_message=user_message,
                initial=is_initial_analysis,
            )
            full_response_holder[0] = fallback
            yield fallback

        updated_history = list(chat_session.message_history)
        updated_history.append({"role": "assistant", "content": full_response_holder[0]})
        chat_session.message_history = updated_history
        chat_session.save()

    return stream_generator()


def generate_fallback_response(full_name, test_recommendation, bozor_data, user_message="", initial=False):
    """Ollama ishlamaganda ishlatiladigan template-based javob (data/vacancies_it.json dan statistika)"""
    import os, json
    from django.conf import settings
    from django.db.models import Count, Q
    from jobs.models import Category, Job

    # vacancies_it.json orqali 66 ta real vakansiyadan tahlil olish
    json_path = os.path.join(settings.BASE_DIR, 'data', 'vacancies_it.json')
    fallback_job_count = 66
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                fallback_job_count = len(data) if isinstance(data, list) else 66
        except:
            pass

    rec_job_title = ""
    paei_role = ""
    if test_recommendation:
        rec_job_title = test_recommendation.get('recommended_job', '')
        reason = test_recommendation.get('reason', '')

    if 'Producer' in rec_job_title or 'Dasturchi' in rec_job_title or 'DevOps' in rec_job_title:
        paei_role = 'P'
    elif 'Administrator' in rec_job_title or 'QA' in rec_job_title or 'Data Analyst' in rec_job_title:
        paei_role = 'A'
    elif 'Entrepreneur' in rec_job_title or 'AI' in rec_job_title or 'Product Manager' in rec_job_title:
        paei_role = 'E'
    elif 'Integrator' in rec_job_title or 'Scrum' in rec_job_title or 'Project Manager' in rec_job_title:
        paei_role = 'I'

    role_categories = {
        'P': ['Backend Developer', 'Software Engineer', 'DevOps Engineer', 'Mobile App Developer', 'Game Developer'],
        'A': ['QA Engineer', 'Data Analyst', 'Business Analyst', 'Cybersecurity Specialist'],
        'E': ['AI Engineer', 'Prompt Engineer', 'UI/UX Designer', 'Product Manager', 'Product Designer', 'Blockchain Developer'],
        'I': ['Project Manager', 'Business Intelligence (BI) Developer', 'Frontend Developer'],
    }

    matched_cats = role_categories.get(paei_role, [])
    matched_jobs = Job.objects.filter(is_active=True, category__name__in=matched_cats)
    total_matched = matched_jobs.count()

    best_category = None
    best_count = 0
    for cat_name in matched_cats:
        cnt = matched_jobs.filter(category__name=cat_name).count()
        if cnt > best_count:
            best_count = cnt
            best_category = cat_name

    test_analysis = ""
    if paei_role == 'P':
        test_analysis = "Sizning profilingiz (P) – natijaga yo'naltirilgan, texnik muammolarni hal qilishga qiziqasiz. Bu Backend, DevOps yoki injiniring sohalari uchun ideal."
    elif paei_role == 'A':
        test_analysis = "Sizning profilingiz (A) – tizimli va tartibni sevuvchi. Siz ma'lumotlar tahlili, sifat nazorati va tizim administratsiyasiga mos keladi."
    elif paei_role == 'E':
        test_analysis = "Sizning profilingiz (E) – innovator va g'oyalar generatori. AI, UI/UX dizayn va mahsulot boshqaruvi siz uchun eng yaxshi tanlov."
    elif paei_role == 'I':
        test_analysis = "Sizning profilingiz (I) – jamoa va muloqotga yo'naltirilgan. Loyiha boshqaruvi, Scrum yoki HR IT yo'nalishlari sizga mos."
    else:
        test_analysis = reason[:200] if (test_recommendation and reason) else "Test natijalari tahlil qilindi."

    user_msg = (user_message or "").lower()
    role_hint = _infer_role_hint(user_message, test_recommendation)
    intent = _intent_from_text(user_message)

    if not initial:
        if intent == "roadmap":
            suggestions = {
                'P': ["1. Python/JavaScript asoslarini mustahkamlang", "2. Backend yoki DevOps bo'yicha 2 ta amaliy loyiha qiling", "3. GitHub va CV ni vakansiya talablariga moslang"],
                'A': ["1. SQL va Excel/Power BI bilan ishlang", "2. Test case yoki data dashboard portfolio qiling", "3. QA/Data Analyst vakansiya talablarini solishtiring"],
                'E': ["1. Product, UI/UX yoki AI bo'yicha bitta loyiha tanlang", "2. Figma/Python bilan demo portfolio qiling", "3. G'oyani real muammo bilan bog'lab taqdim eting"],
                'I': ["1. Agile/Scrum asoslarini o'rganing", "2. Jamoaviy loyiha yoki task-management portfolio qiling", "3. Project Manager/Scrum Master vakansiya talablarini yig'ing"],
            }
            lines = [f"## {full_name} uchun roadmap", ""]
            if role_hint:
                lines.append(f"Yo'nalish: {role_hint}")
                lines.append("")
            lines.extend(suggestions.get(paei_role, ["1. Asosiy skill tanlang", "2. Portfolio qiling", "3. Vakansiyalarga mos CV tayyorlang"]))
            return "\n".join(lines)

        if intent == "vacancy":
            if best_category and total_matched > 0:
                return (
                    f"## Mos vakansiya yo'nalishi\n\n"
                    f"{full_name}, test natijangizga qarab eng yaqin yo'nalish: **{best_category}**.\n"
                    f"Bazada bu guruhda {best_count} ta mos vakansiya bor.\n\n"
                    f"CVingizda shu yo'nalishga kerakli 3-4 skillni aniq ko'rsating."
                )
            return f"{full_name}, hozir mos vakansiyalarni aniqlash uchun test natijangiz bor, lekin bazada bu yo'nalish bo'yicha aktiv e'lon kam."

        if intent == "market":
            return f"## Bozor tahlili\n\n{bozor_data}\n\n{full_name}, test natijangizga mos yo'nalishni shu trendlar bilan solishtirib tanlash yaxshi."

        if intent == "skills":
            skill_advice = {
                'P': "Python, JavaScript, SQL, Git va Docker",
                'A': "SQL, Excel/Power BI, Jira, test yozish va tahlil",
                'E': "Figma, product thinking, Python/AI asoslari va UX research",
                'I': "Agile, Scrum, Jira, kommunikatsiya va frontend asoslari",
            }
            role_text = f" ({role_hint})" if role_hint else ""
            return f"{full_name}{role_text}, siz uchun hozir eng foydali skilllar: {skill_advice.get(paei_role, 'Python, SQL va Git')}."

        return (
            f"{full_name}, savolingiz bo'yicha qisqa javob: test natijangizni hisobga olib, aniq bitta yo'nalishni tanlang va shu yo'nalish vakansiyalaridagi talablar asosida portfolio qiling."
        )

    lines = [f"## Assalomu alaykum, {full_name}!", "", "### Karyera Tahlili", test_analysis, ""]

    if best_category and total_matched > 0:
        lines.append(f"**{best_category}** — bazada {best_count} ta hamda zaxira (JSON) da {fallback_job_count} ta vakansiya asosida tahlil:")
        lines.append("")
        lines.append("### Nega aynan bu?")
        args = {
            'P': f"Mantiqiy fikrlashingiz {best_category} sohasida texnik muammolarni hal qilishga yordam beradi.",
            'A': f"Tizimli yondashuvingiz {best_category} sohasida aniqlik va sifat kafolatini ta'minlaydi.",
            'E': f"Innovatsion fikrlashingiz {best_category} sohasida yangi yechimlar joriy etishga imkon beradi.",
            'I': f"Jamoa bilan ishlash ko'nikmalaringiz {best_category} sohasida loyihalarni muvaffaqiyatli boshqarishga yordam beradi.",
        }
        lines.append(args.get(paei_role, "Sizning profilingiz ushbu yo'nalishga mos keladi."))
        lines.append("")
        lines.append("### Rivojlanish rejasi")
        suggestions = {
            'P': ["Amaliy loyihalar yarating", "Algoritmik masalalarni yeching"],
            'A': ["SQL va tahlil vositalarini o'rganing", "Sertifikat oling"],
            'E': ["AI/ML kurslarini boshlang", "Dizayn vositalarini o'rganing"],
            'I': ["Agile/Scrum ni o'rganing", "Liderlik treninglarida qatnashing"],
        }
        for s in suggestions.get(paei_role, ["Trendlarni kuzatib boring", "Amaliyot orttiring"]):
            lines.append(f"- {s}")
    else:
        lines.append(bozor_data)

    return "\n".join(lines)


# =====================================================================
# PARSER UCHUN KO'NIKMA AJRATUVCHI (parse_hh.py ishlatadi)
# =====================================================================
def extract_skills_with_ollama(text, max_skills=20):
    """Legacy name retained for compatibility: use local DB-driven heuristic to
    extract known skills from text instead of calling an external model.
    """
    if not text or not text.strip():
        return []
    text_low = text.lower()
    # Use Skill table if populated; otherwise fallback to simple tokenization
    try:
        db_skills = list(Skill.objects.values_list('name', flat=True))
    except Exception:
        db_skills = []

    found = []
    for s in db_skills:
        if s and s.lower() in text_low:
            found.append(s)
            if len(found) >= max_skills:
                break

    if not found:
        # fallback: simple regex-based split of words/phrases
        tokens = [t.strip() for t in re.split(r'[\s,;|/\-()]+', text) if len(t) > 2]
        # return top unique tokens
        seen = set()
        for t in tokens:
            tl = t.lower()
            if tl not in seen:
                seen.add(tl)
                found.append(t)
            if len(found) >= max_skills:
                break

    return found[:max_skills]


# =====================================================================
# LEGACY FUNKSIYA (views.py context uchun)
# =====================================================================
def get_platform_context():
    """Baza bo'yicha platformamizdagi real vaqt statistikasini yig'ish"""
    total_jobs = Job.objects.filter(is_active=True).count()
    top_categories = Category.objects.annotate(c=Count('jobs')).order_by('-c')[:5]
    cat_str = ", ".join([f"{c.name} ({c.c} ta vakansiya)" for c in top_categories])
    top_countries = Country.objects.annotate(c=Count('job')).order_by('-c')[:3]
    country_str = ", ".join([f"{c.name} ({c.c} ta ish)" for c in top_countries])
    return {
        "total_jobs": total_jobs,
        "top_cats": cat_str,
        "top_countries": country_str,
    }
