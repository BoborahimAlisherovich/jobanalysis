# Implementation Plan: Full Implementation

## Phase 1: Parsers + Transliteration

### 1. Install dependencies
```bash
source "/home/boborahim/Boborahim's/analitik loiha/venv/bin/activate"
pip install deep-translator curl_cffi beautifulsoup4 lxml
```

### 2. Create `transliterate_uz.py`
Path: `jobs/management/commands/transliterate_uz.py`

```python
import re

CYRILLIC_TO_LATIN = {
    'А': 'A', 'а': 'a', 'Б': 'B', 'б': 'b', 'В': 'V', 'в': 'v',
    'Г': 'G', 'г': 'g', 'Д': 'D', 'д': 'd', 'Е': 'Ye', 'е': 'ye',
    'Ё': 'Yo', 'ё': 'yo', 'Ж': 'J', 'ж': 'j', 'З': 'Z', 'з': 'z',
    'И': 'I', 'и': 'i', 'Й': 'Y', 'й': 'y', 'К': 'K', 'к': 'k',
    'Л': 'L', 'л': 'l', 'М': 'M', 'м': 'm', 'Н': 'N', 'н': 'n',
    'О': 'O', 'о': 'o', 'П': 'P', 'п': 'p', 'Р': 'R', 'р': 'r',
    'С': 'S', 'с': 's', 'Т': 'T', 'т': 't', 'У': 'U', 'у': 'u',
    'Ф': 'F', 'ф': 'f', 'Х': 'X', 'х': 'x', 'Ц': 'S', 'ц': 's',
    'Ч': 'Ch', 'ч': 'ch', 'Ш': 'Sh', 'ш': 'sh', 'Щ': 'Sh', 'щ': 'sh',
    'Ъ': '', 'ъ': '', 'Ы': 'Y', 'ы': 'y', 'Ь': '', 'ь': '',
    'Э': 'E', 'э': 'e', 'Ю': 'Yu', 'ю': 'yu', 'Я': 'Ya', 'я': 'ya',
    'Ў': "O'", 'ў': "o'", 'Қ': 'Q', 'қ': 'q', 'Ғ': "G'", 'ғ': "g'",
    'Ҳ': 'H', 'ҳ': 'h',
}

def cyrillic_to_latin(text):
    result = []
    for c in text:
        result.append(CYRILLIC_TO_LATIN.get(c, c))
    return ''.join(result)

def to_uzbek_latin(text):
    if not text or not text.strip():
        return text
    has_cyrillic = bool(re.search(r'[А-Яа-яЁёЎўҚқҒғҲҳ]', text))
    if has_cyrillic:
        return cyrillic_to_latin(text)
    return text
```

### 3. Create all 6 parsers

#### a) `parsers/hh_uz.py`
- Uses official hh.ru API (`https://api.hh.ru/vacancies`)
- Search IT keywords: "Developer", "Dasturchi", "Backend", "Frontend", etc.
- Area: 97 (Uzbekistan)
- Fields: name, employer.name, salary.from/to, employment, description
- Transliterate via `to_uzbek_latin()`
- Save to `Job` model (source_url unique dedup)

#### b) `parsers/olx_uz.py`
- URL: `https://www.olx.uz/rabota/it-kompyutery/`
- Use `curl_cffi` or `requests + random User-Agent`
- Parse HTML with BeautifulSoup
- Extract: title, price (salary), description, company
- Job type: IT category
- Transliterate

#### c) `parsers/linkedin_rapidapi.py`
- RapidAPI "LinkedIn Jobs Scraper" endpoint
- API key from environment variable `RAPIDAPI_KEY`
- Search: "developer", "engineer", "dasturchi" for Uzbekistan
- Parse JSON response → save to Job model
- Transliterate

#### d) `parsers/apwork_uz.py`
- URL: `https://apwork.uz` (scrape job listings)
- Parse HTML with BeautifulSoup
- Extract: title, company, salary, description
- Transliterate

#### e) `parsers/kwork_ru.py`
- URL: `https://kwork.ru/projects`
- Parse HTML/JSON
- Focus on IT categories: "Разработка", "Программирование"
- Extract: title, price, description
- Transliterate (Russian → Uzbek Latin)

#### f) `parsers/teamwork_uz.py`
- URL: `https://teamwork.uz`
- Parse HTML
- Extract job listings
- Transliterate

### 4. Create `scrape_all.py`

```python
from django.core.management.base import BaseCommand
from .parsers import hh_uz, olx_uz, apwork_uz, kwork_ru, teamwork_uz

class Command(BaseCommand):
    help = 'Barcha manbalardan vakansiyalarni yig\'ish'
    
    def handle(self, *args, **options):
        parsers = [
            hh_uz.run,
            olx_uz.run,
            apwork_uz.run,
            kwork_ru.run,
            teamwork_uz.run,
        ]
        # linkedin_rapidapi.run only if RAPIDAPI_KEY set
        total = 0
        for parser in parsers:
            try:
                count = parser()
                total += count
                print(f"✅ {parser.__module__}: {count} ta qo'shildi")
            except Exception as e:
                print(f"❌ {parser.__module__}: {e}")
        print(f"Jami qo'shilgan: {total}")
```

Each parser function returns count of new jobs added.
Transliteration applied to title, description, company name.

---

## Phase 2: Dataset Generator

### File: `ai_advisor/dataset_generator.py`

Generate 500+ instruction-response pairs:

```
PAEI profiles (P/A/E/I) × experience levels (0/1/3/5 years) × 
skills combinations × dialog scenarios
```

Each response pulls REAL data from DB:
```python
def generate_response(profile, experience, skills):
    category = get_category_for_profile(profile)
    jobs = Job.objects.filter(category=category, is_active=True)
    count = jobs.count()
    salary_min = jobs.aggregate(Min('salary_min'))['salary_min__min']
    salary_max = jobs.aggregate(Max('salary_max'))['salary_max__max']
    return f"Bazada {category.name}: {count} ta vakansiya ({salary_min}-{salary_max} so'm)..."
```

Save as JSONL format:
```json
{"instruction": "...", "response": "..."}
```

---

## Phase 3: Colab Fine-tuning Notebook

### File: `aura_colab_finetune.ipynb`

```
1. Install: transformers, peft, trl, bitsandbytes, datasets, accelerate
2. Load dataset from JSONL
3. Load TinyLlama-1.1B-Chat in 4-bit
4. LoRA config: r=16, alpha=32, target_modules="all-linear"
5. Training args: epoch=3, lr=2e-4, batch=4, grad_accum=4
6. Train (~2-3 hours on T4)
7. Merge adapter + base model
8. Export to GGUF (llama.cpp)
9. Upload to Google Drive
```

---

## Phase 4: Django Integration

1. Download GGUF from Google Drive
2. Import to Ollama:
```bash
ollama create aura-agent -f Modelfile
# Modelfile:
# FROM ./aura-agent-q4.gguf
```
3. Update `services.py`:
```python
try:
    import ollama
    stream = ollama.chat(model='aura-agent', messages=messages, stream=True)
    yield from stream
except:
    try:
        stream = ollama.chat(model='tinyllama', messages=messages, stream=True)
        yield from stream
    except:
        yield generate_fallback_response(...)
```
4. Set `RAPIDAPI_KEY` in `.env` for LinkedIn parser
5. Run: `python manage.py scrape_all`
6. Run: `python manage.py runserver 0.0.0.0:8001`
7. Test AI chat with fine-tuned model
