# File: ai_advisor/dataset_generator.py

```python
import json
import random
from datetime import datetime, timedelta
from django.db.models import Min, Max, Count, Q

PAEI_ROLES = {
    'P': {
        'name': 'Producer (Natijaga yo\'naltirilgan)',
        'full_name': 'Producer',
        'categories': ['Backend Developer', 'Software Engineer', 'DevOps Engineer',
                       'Mobile App Developer', 'Game Developer', 'Python Developer',
                       'Java Developer', 'Flutter Developer', 'Android Developer',
                       'C++ Developer', 'Go Developer', 'Rust Developer'],
        'skills': ['Python', 'Java', 'JavaScript', 'Django', 'Flask', 'Spring Boot',
                   'Docker', 'Kubernetes', 'AWS', 'Git', 'SQL', 'PostgreSQL',
                   'Redis', 'Linux', 'C++', 'Go', 'Rust', 'Microservices'],
        'descriptions': [
            'texnik muammolarni hal qilishga qiziqasiz',
            'natijaga yo\'naltirilgan va mantiqiy fikrlaysiz',
            'kod yozish va texnik yechimlar sizga yoqadi',
            'algoritmik fikrlash qobiliyatingiz yuqori',
        ],
        'advice': [
            'Amaliy loyihalar yarating va GitHub da joylang',
            'Algoritmik masalalarni muntazam yechib boring',
            'Eng so\'nggi texnologiyalarni kuzatib boring',
            'Open Source loyihalarda qatnashing',
        ],
        'future': 'Backend/DevOps sohasida o\'sish, keyin AI/ML ga o\'tish',
    },
    'A': {
        'name': 'Administrator (Tizimli va tartibli)',
        'full_name': 'Administrator',
        'categories': ['QA Engineer', 'Data Analyst', 'Business Analyst',
                       'Cybersecurity Specialist', 'System Administrator',
                       'Database Administrator', 'IT Auditor',
                       'Network Administrator', 'Data Engineer'],
        'skills': ['SQL', 'Excel', 'Tableau', 'Power BI', 'Python', 'Selenium',
                   'Jira', 'TestRail', 'Linux', 'Networking', 'PostgreSQL',
                   'MongoDB', 'Docker', 'Kubernetes', 'Bash'],
        'descriptions': [
            'tizimli va tartibni sevasiz',
            'ma\'lumotlar bilan ishlashga qiziqasiz',
            'aniqlik va sifat siz uchun muhim',
            'tahlil qilish va nazorat qilish sizga yoqadi',
        ],
        'advice': [
            'SQL va ma\'lumotlar tahlili bo\'yicha kurslarni o\'ting',
            'ISTQB sertifikatini oling',
            'BI vositalarini (Power BI, Tableau) o\'rganing',
            'Audit va xavfsizlik standartlarini o\'rganing',
        ],
        'future': 'Data Analyst dan Data Engineer yoki Security mutaxassisi',
    },
    'E': {
        'name': 'Entrepreneur (Innovator va ijodkor)',
        'full_name': 'Entrepreneur',
        'categories': ['UI/UX Designer', 'Product Manager', 'AI Engineer',
                       'Product Designer', 'Blockchain Developer',
                       'Prompt Engineer', 'Creative Technologist',
                       'Machine Learning Engineer', 'Data Scientist'],
        'skills': ['Figma', 'Adobe XD', 'Sketch', 'Python', 'TensorFlow',
                   'PyTorch', 'JavaScript', 'React', 'Node.js', 'Solidity',
                   'UI/UX', 'Product Management', 'Agile', 'Scrum'],
        'descriptions': [
            'innovatsion g\'oyalar generatsiya qilasiz',
            'yangi texnologiyalarga qiziqasiz',
            'ijodiy fikrlash qobiliyatingiz yuqori',
            'startup va yangi loyihalar sizga yoqadi',
        ],
        'advice': [
            'AI/ML va sun\'iy intellekt kurslarini boshlang',
            'UI/UX dizayn vositalarini (Figma) o\'rganing',
            'Startup ekotizimida qatnashing',
            'Mahsulot boshqaruvi ni o\'rganing',
        ],
        'future': 'AI/Product sohasida yetakchi bo\'lish yoki o\'z startapini yaratish',
    },
    'I': {
        'name': 'Integrator (Jamoa va muloqotga yo\'naltirilgan)',
        'full_name': 'Integrator',
        'categories': ['Project Manager', 'Scrum Master', 'HR IT',
                       'Frontend Developer', 'Business Intelligence Developer',
                       'IT Recruiter', 'Sales Manager',
                       'Community Manager', 'Technical Writer'],
        'skills': ['JavaScript', 'React', 'Vue.js', 'HTML', 'CSS', 'Python',
                   'Jira', 'Confluence', 'Agile', 'Scrum', 'Kanban',
                   'Communication', 'Leadership', 'Negotiation'],
        'descriptions': [
            'jamoa bilan ishlashni yaxshi ko\'rasiz',
            'muloqot qobiliyatingiz yuqori',
            'loyihalarni boshqarish sizga yoqadi',
            'odamlar bilan ishlash sizning kuchli tomoningiz',
        ],
        'advice': [
            'Agile/Scrum bo\'yicha sertifikat oling',
            'Frontend texnologiyalarini o\'rganing',
            'Liderlik va muloqot treninglarida qatnashing',
            'Loyiha boshqaruvi vositalarini o\'zlashtiring',
        ],
        'future': 'Project Manager dan IT Director ga o\'sish',
    },
}

EXPERIENCES = [
    (0, "hech qanday tajribam yo'q, endi o'rganyapman"),
    (1, "1 yil tajribam bor"),
    (2, "2 yil tajribam bor"),
    (3, "3-4 yil tajribam bor"),
    (5, "5+ yil tajribam bor, yetakchi mutaxassisman"),
]

NAMES = ['Aziz', 'Bobur', 'Dilshod', 'Eldor', 'Farrux', 'Gulnoza',
         'Humoyun', 'Islom', 'Javohir', 'Kamola', 'Laziz', 'Madina',
         'Nodir', 'Odil', 'Parviz', 'Rustam', 'Sevara', 'Shoxrux',
         'Temur', 'Umida', 'Xurshid', 'Zafar']

QUESTIONS = {
    'test_analysis': [
        "Menga eng mos kasbni tavsiya qilasizmi?",
        "Qaysi yo'nalishda ishlashim kerak?",
        "Mening profilimga qarab, nima maslahat berasiz?",
        "Kelajakdagi karyeram uchun qaysi sohani tanlashim kerak?",
        "Menga mos ish topishga yordam bera olasizmi?",
        "Profilimni tahlil qilib, eng yaxshi yo'nalishni aytib bering",
    ],
    'skill_question': [
        "Bu ko'nikma bilan qanday ish topish mumkin?",
        "Bu sohada rivojlanish uchun nima qilishim kerak?",
        "Qancha maosh olishim mumkin?",
        "Bu yo'nalishda talab bormi?",
        "Qanday qo'shimcha ko'nikmalar o'rganishim kerak?",
    ],
    'five_year': [
        "5 yildan keyin qaysi soha eng talabgir bo'ladi?",
        "Uzoq muddatli karyeramni qanday rejalashtirishim kerak?",
        "Kelgusi 5 yil ichida qaysi texnologiyalarni o'rganishim kerak?",
        "5 yildan keyin IT sohasi qanday bo'ladi?",
        "Eng istiqbolli sohalar qaysilar?",
    ],
    'general_advice': [
        "IT sohasiga endi kirdim. Qayerdan boshlashim kerak?",
        "O'qishni tugatdim, IT da ish qidiryapman. Nima qilishim kerak?",
        "Dasturlashni o'rganyapman. Qaysi tilni tanlashim kerak?",
        "IT da muvaffaqiyatli bo'lish uchun nima qilish kerak?",
    ],
}


def get_stats(categories):
    from jobs.models import Job, Category
    total = Job.objects.filter(is_active=True).count()
    best_cat = None
    best_count = 0
    for cname in categories:
        cnt = Job.objects.filter(is_active=True, category__name=cname).count()
        if cnt > best_count:
            best_count = cnt
            best_cat = cname
    salary = Job.objects.filter(
        is_active=True, category__name__in=categories
    ).aggregate(mn=Min('salary_max'), mx=Max('salary_max'))
    return total, best_cat, best_count, salary['mn'], salary['mx']


def make_response(role, name, scenario, skill_name=''):
    data = PAEI_ROLES[role]
    total, best_cat, best_count, sal_min, sal_max = get_stats(data['categories'])

    if role == 'P':
        profile_desc = f"Sizning profilingiz (P) – natijaga yo'naltirilgan, texnik muammolarni hal qilishga qiziqasiz. Bu Backend, DevOps yoki injiniring sohalari uchun ideal."
    elif role == 'A':
        profile_desc = f"Sizning profilingiz (A) – tizimli va tartibni sevuvchi. Ma'lumotlar tahlili, sifat nazorati va tizim administratsiyasiga mos keladi."
    elif role == 'E':
        profile_desc = f"Sizning profilingiz (E) – innovator va g'oyalar generatori. AI, UI/UX dizayn va mahsulot boshqaruvi siz uchun eng yaxshi tanlov."
    else:
        profile_desc = f"Sizning profilingiz (I) – jamoa va muloqotga yo'naltirilgan. Loyiha boshqaruvi, Scrum yoki HR IT yo'nalishlari sizga mos."

    response = f"## Assalomu alaykum, {name}!\n\n"
    response += f"### Karyera Tahlili\n{profile_desc}\n\n"

    if scenario == 'test_analysis':
        response += f"### Tavsiya etilgan yo'nalish\n"
        if best_cat and best_count > 0:
            response += f"**{best_cat}** — bazada {best_count} ta vakansiya mavjud\n\n"
            response += f"### Nega aynan bu?\n"
            response += f"Sizning {random.choice(data['descriptions'])}. "
            response += f"Aynan {best_cat} sohasi sizning qobiliyatlaringizni to'liq namoyon qilish imkonini beradi.\n\n"
            response += "### Rivojlanish rejasi\n"
            for a in data['advice'][:2]:
                response += f"- {a}\n"
        else:
            response += f"Bazada jami {total} ta IT vakansiya mavjud. "
            response += f"Sizga eng mos yo'nalish: {data['categories'][0]}\n\n"
            response += "### Rivojlanish rejasi\n"
            for a in data['advice'][:2]:
                response += f"- {a}\n"

    elif scenario == 'skill_question':
        response += f"### {skill_name} — ajoyib tanlov!\n"
        cnt_with = 0
        try:
            from jobs.models import Job
            cnt_with = Job.objects.filter(is_active=True, required_skills__name__icontains=skill_name).count()
        except:
            pass
        if cnt_with:
            response += f"Bazada {skill_name} talab qilinadigan {cnt_with} ta vakansiya bor.\n\n"
        response += f"Sizning profilingiz ({role}) va {skill_name} bilimingiz bilan "
        response += f"{best_cat or data['categories'][0]} sohasida muvaffaqiyatli ishlashingiz mumkin.\n\n"
        response += f"### Rivojlanish rejasi\n- {skill_name} ni chuqur o'rganing\n- Amaliy loyihalar qiling\n- Sertifikat oling\n"

    elif scenario == 'five_year':
        response += f"### 5 Yillik Prognoz\n"
        response += f"Hozirgi bozor tahlili: {total} ta IT vakansiya. "
        response += f"Eng talabgir soha: {best_cat} ({best_count} ta).\n\n"
        response += f"### Sizning profilingiz ({role}) uchun tavsiya\n"
        response += f"{data['future']}\n\n"
        response += "### Rivojlanish rejasi\n"
        response += f"1. Dastlabki 1-2 yil: Asosiy ko'nikmalarni o'zlashtirish\n"
        response += f"2. 2-4 yil: Sertifikatsiya va chuqurlashtirish\n"
        response += f"3. 5-yil: Yetakchi mutaxassis yoki menejer bo'lish\n"

    else:
        response += f"### Umumiy tavsiya\n"
        response += f"Bozorda hozir {total} ta IT vakansiya mavjud. "
        response += f"O'zbekistonda IT sohasi jadal rivojlanmoqda.\n\n"
        response += f"Sizga mos yo'nalish: {best_cat or data['categories'][0]}\n\n"
        response += "### Rivojlanish rejasi\n"
        response += "- Asosiy dasturlash tilini o'rganing (Python yoki JavaScript)\n"
        response += "- Oddiy loyihalar yarating\n"
        response += "- IT community ga qo'shiling\n"
        for a in data['advice'][:1]:
            response += f"- {a}\n"

    return response


def generate_dataset(num=500):
    dataset = []
    types = ['test_analysis', 'skill_question', 'five_year', 'general_advice']
    weights = [0.35, 0.25, 0.20, 0.20]

    for _ in range(num):
        role = random.choice(list(PAEI_ROLES.keys()))
        exp_years, exp_text = random.choice(EXPERIENCES)
        name = random.choice(NAMES)
        scenario = random.choices(types, weights=weights, k=1)[0]
        skill_name = random.choice(PAEI_ROLES[role]['skills'])

        if scenario == 'skill_question':
            q = random.choice(QUESTIONS['skill_question'])
            instruction = f"Men {name}man. {exp_text}. {skill_name} ni o'rganyapman. {q}"
        elif scenario == 'five_year':
            q = random.choice(QUESTIONS['five_year'])
            instruction = f"Men {name}man. Mening profilim {role}, {exp_text}. {q}"
        elif scenario == 'general_advice':
            q = random.choice(QUESTIONS['general_advice'])
            instruction = f"Mening ismim {name}. {exp_text}. {q}"
        else:
            q = random.choice(QUESTIONS['test_analysis'])
            skills_show = ', '.join(random.sample(PAEI_ROLES[role]['skills'], k=min(3, len(PAEI_ROLES[role]['skills']))))
            instruction = f"Mening PAEI profilim {role}. {exp_text}. Ko'nikmalarim: {skills_show}. {q}"

        response = make_response(role, name, scenario, skill_name)
        dataset.append({
            "instruction": instruction,
            "response": response,
            "role": role,
            "scenario": scenario,
        })

    return dataset


def save_dataset(dataset, filepath='aura_dataset.jsonl'):
    with open(filepath, 'w', encoding='utf-8') as f:
        for item in dataset:
            line = {"instruction": item["instruction"], "response": item["response"]}
            f.write(json.dumps(line, ensure_ascii=False) + '\n')

    stats = {}
    for item in dataset:
        r = item.get('role', '?')
        stats[r] = stats.get(r, 0) + 1

    print(f"✅ Dataset saqlandi: {filepath}")
    print(f"   Jami: {len(dataset)} ta juftlik")
    print(f"   PAEI bo'yicha: {stats}")


def run(count=500):
    dataset = generate_dataset(count)
    save_dataset(dataset)
    return dataset


if __name__ == '__main__':
    import os, django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mmt_project.settings')
    django.setup()
    run()
```
