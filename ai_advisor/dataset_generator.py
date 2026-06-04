import json
import random

PAEI = {
    'P': {
        'name': 'Producer (Natijaga)',
        'cats': ['Backend Developer', 'Software Engineer', 'DevOps Engineer',
                 'Mobile App Developer', 'Game Developer', 'Python Developer',
                 'Java Developer', 'Flutter Developer', 'C++ Developer'],
        'skills': ['Python', 'Java', 'JavaScript', 'Django', 'Docker',
                   'Kubernetes', 'AWS', 'Git', 'SQL', 'Linux', 'Go', 'Rust'],
        'advice': ['Amaliy loyihalar yarating va GitHub da joylang',
                   'Algoritmik masalalarni muntazam yechib boring'],
        'future': 'Backend/DevOps dan keyin AI/ML ga otish',
        'desc': 'texnik muammolarni hal qilishga qiziqasiz',
    },
    'A': {
        'name': 'Administrator (Tizimli)',
        'cats': ['QA Engineer', 'Data Analyst', 'Business Analyst',
                 'Cybersecurity Specialist', 'System Administrator',
                 'Database Administrator', 'Data Engineer'],
        'skills': ['SQL', 'Excel', 'Tableau', 'Power BI', 'Python',
                   'Selenium', 'Jira', 'TestRail', 'Linux', 'PostgreSQL'],
        'advice': ['SQL va malumotlar tahlili kurslarini oting',
                   'ISTQB sertifikatini oling'],
        'future': 'Data Analyst dan Security mutaxassisiga',
        'desc': 'tizimli va tartibni sevasiz',
    },
    'E': {
        'name': 'Entrepreneur (Innovator)',
        'cats': ['UI/UX Designer', 'Product Manager', 'AI Engineer',
                 'Product Designer', 'Blockchain Developer',
                 'Machine Learning Engineer', 'Data Scientist'],
        'skills': ['Figma', 'Adobe XD', 'Python', 'TensorFlow', 'PyTorch',
                   'JavaScript', 'React', 'Node.js', 'UI/UX', 'Agile'],
        'advice': ['AI/ML va suniy intellekt kurslarini boshlang',
                   'UI/UX dizayn vositalarini organing'],
        'future': 'AI/Product sohasida yetakchi bolish',
        'desc': 'innovatsion goyalar generatsiya qilasiz',
    },
    'I': {
        'name': 'Integrator (Jamoa)',
        'cats': ['Project Manager', 'Scrum Master', 'HR IT',
                 'Frontend Developer', 'IT Recruiter',
                 'Business Intelligence Developer', 'Technical Writer'],
        'skills': ['JavaScript', 'React', 'Vue.js', 'HTML', 'CSS',
                   'Jira', 'Confluence', 'Agile', 'Scrum', 'Leadership'],
        'advice': ['Agile/Scrum boyicha sertifikat oling',
                   'Frontend texnologiyalarini organing'],
        'future': 'Project Manager dan IT Director ga osish',
        'desc': 'jamoa bilan ishlashni yaxshi korasiz',
    },
}

EXPERIENCES = [
    (0, "tajribam yoq, endi organyapman"),
    (1, "1 yil tajribam bor"),
    (2, "2 yil tajribam bor"),
    (3, "3-4 yil tajribam bor"),
    (5, "5+ yil tajribam bor"),
]

NAMES = ['Aziz', 'Bobur', 'Dilshod', 'Eldor', 'Farrux', 'Gulnoza',
         'Humoyun', 'Islom', 'Javohir', 'Kamola', 'Laziz', 'Madina',
         'Nodir', 'Rustam', 'Sevara', 'Shoxrux', 'Temur', 'Xurshid', 'Zafar']

QUESTIONS = {
    't': [
        "Menga eng mos kasbni tavsiya qilasizmi?",
        "Profilimga qarab nima maslahat berasiz?",
        "Qaysi yonalishda ishlashim kerak?",
    ],
    's': [
        "Bu konikma bilan qanday ish topish mumkin?",
        "Bu sohada rivojlanish uchun nima qilishim kerak?",
    ],
    '5': [
        "5 yildan keyin qaysi soha eng talabgir boladi?",
        "Kelgusi 5 yilda qaysi texnologiyalarni organishim kerak?",
    ],
    'g': [
        "IT ga endi kirdim, qayerdan boshlashim kerak?",
        "Qaysi tilni organishim kerak?",
        "IT da muvaffaqiyatli bolish uchun nima qilish kerak?",
    ],
}

MARKET_DEFAULTS = {
    "total": 53,
    "category_counts": {
        "Backend Developer": 4,
        "Software Engineer": 3,
        "DevOps Engineer": 2,
        "Mobile App Developer": 21,
        "Game Developer": 1,
        "Python Developer": 2,
        "Java Developer": 1,
        "Flutter Developer": 3,
        "C++ Developer": 1,
        "QA Engineer": 5,
        "Data Analyst": 4,
        "Business Analyst": 2,
        "Cybersecurity Specialist": 1,
        "System Administrator": 1,
        "Database Administrator": 1,
        "Data Engineer": 2,
        "UI/UX Designer": 3,
        "Product Manager": 2,
        "AI Engineer": 2,
        "Product Designer": 1,
        "Blockchain Developer": 19,
        "Machine Learning Engineer": 2,
        "Data Scientist": 2,
        "Project Manager": 4,
        "Scrum Master": 1,
        "HR IT": 1,
        "Frontend Developer": 1,
        "IT Recruiter": 1,
        "Business Intelligence Developer": 2,
        "Technical Writer": 1,
    },
    "skill_counts": {
        "Python": 1,
        "JavaScript": 1,
        "React": 2,
        "SQL": 2,
        "Figma": 3,
        "HTML": 1,
        "CSS": 0,
        "Django": 0,
        "Docker": 0,
        "Linux": 0,
        "Jira": 0,
        "Scrum": 0,
        "Agile": 0,
        "Power BI": 0,
        "Tableau": 0,
        "PostgreSQL": 0,
        "TensorFlow": 0,
        "PyTorch": 0,
    },
}


def get_market_snapshot():
    """Django mavjud bo'lsa real DB dan, aks holda statik loyiha kontekstidan foydalanadi."""
    snapshot = {
        "total": MARKET_DEFAULTS["total"],
        "category_counts": dict(MARKET_DEFAULTS["category_counts"]),
        "skill_counts": dict(MARKET_DEFAULTS["skill_counts"]),
    }

    try:
        from jobs.models import Job

        snapshot["total"] = Job.objects.filter(is_active=True).count()
        for role_data in PAEI.values():
            for category in role_data["cats"]:
                snapshot["category_counts"][category] = Job.objects.filter(
                    is_active=True,
                    category__name=category,
                ).count()
            for skill in role_data["skills"]:
                snapshot["skill_counts"][skill] = Job.objects.filter(
                    is_active=True,
                    required_skills__name__icontains=skill,
                ).count()
    except Exception:
        pass

    return snapshot


def best_category_for_role(role_data, snapshot):
    best_cat = role_data["cats"][0]
    best_count = -1
    for category in role_data["cats"]:
        count = snapshot["category_counts"].get(category, 0)
        if count > best_count:
            best_cat = category
            best_count = count
    return best_cat, max(best_count, 0)


def make_greeting(name):
    return f"Assalomu alaykum, {name}!"


def make_short_response(name, role, role_data, scenario, question, skill, snapshot):
    best_cat, best_count = best_category_for_role(role_data, snapshot)
    total = snapshot["total"]
    skill_count = snapshot["skill_counts"].get(skill, 0)

    if scenario == "t":
        return "\n".join([
            f"## {make_greeting(name)}",
            "",
            "### Karyera Tahlili",
            f"Sizning profilingiz ({role}) — {role_data['name']}. {role_data['desc']}.",
            "",
            "### Tavsiya",
            f"Sizga eng yaqin yo'nalish: **{best_cat}**. Bazada bu yo'nalishda {best_count} ta vakansiya bor.",
            "",
            "### Keyingi qadam",
            f"- {role_data['advice'][0]}",
            f"- {role_data['advice'][1]}",
        ])

    if scenario == "s":
        if skill_count > 0:
            skill_line = f"Bazada {skill} talab qilinadigan {skill_count} ta vakansiya bor."
        else:
            skill_line = f"Bazada {skill} bo'yicha vakansiya kam, lekin u {best_cat} yo'nalishida yordam beradi."
        return "\n".join([
            f"## {make_greeting(name)}",
            "",
            "### Qisqa javob",
            skill_line,
            f"Sizning profilingiz ({role}) sabab {best_cat} tomonga harakat qilish mantiqli.",
            "",
            "### Amaliy reja",
            f"- {skill} bilan kichik portfolio loyiha qiling",
            "- CV va GitHub/portfolio sahifangizni tayyorlang",
        ])

    if scenario == "5":
        return "\n".join([
            f"## {make_greeting(name)}",
            "",
            "### Prognoz",
            f"Hozir bazada {total} ta aktiv IT vakansiya bor.",
            f"Sizning ({role}) profilingiz uchun 5 yillik yo'l: {role_data['future']}.",
            "",
            "### O'rganish tartibi",
            "- 1-bosqich: asosiy ko'nikmalarni mustahkamlash",
            "- 2-bosqich: real loyiha va sertifikat",
            "- 3-bosqich: senior/yetakchi rolga tayyorlanish",
        ])

    return "\n".join([
        f"## {make_greeting(name)}",
        "",
        "### Boshlash yo'li",
        f"Siz uchun eng yaxshi start: **{best_cat}**. Bu yo'nalish profilingizga ({role}) yaqin.",
        f"Platformada jami {total} ta aktiv vakansiya bor.",
        "",
        "### Bugundan qiling",
        "- Python yoki JavaScript asoslarini tanlang",
        "- Har hafta bitta kichik loyiha qiling",
        "- Vakansiya talablarini kuzatib, yetishmayotgan skilllarni yozib boring",
    ])


def generate_dataset(num=4000, seed=42):
    random.seed(seed)
    dataset = []
    types = ['t', 's', '5', 'g']
    weights = [0.35, 0.25, 0.20, 0.20]
    snapshot = get_market_snapshot()
    seen_instructions = set()

    while len(dataset) < num:
        role = random.choice(list(PAEI.keys()))
        d = PAEI[role]
        name = random.choice(NAMES)
        exp_y, exp_t = random.choice(EXPERIENCES)
        scenario = random.choices(types, weights=weights, k=1)[0]
        q = random.choice(QUESTIONS[scenario])
        skill = random.choice(d['skills'])

        if scenario == 's':
            instruction = f"Men {name}man. {exp_t}. {skill} ni organyapman. {q}"
        elif scenario == '5':
            instruction = f"Men {name}man. Profilim {role}. {exp_t}. {q}"
        elif scenario == 'g':
            instruction = f"Ismim {name}. {exp_t}. {q}"
        else:
            skills_show = ', '.join(random.sample(
                d['skills'], k=min(3, len(d['skills']))
            ))
            instruction = f"Men {name}man. PAEI profilim {role}. {exp_t}. Konikmalarim: {skills_show}. {q}"

        if instruction in seen_instructions:
            continue
        seen_instructions.add(instruction)

        resp = make_short_response(name, role, d, scenario, q, skill, snapshot)

        dataset.append({
            "instruction": instruction,
            "response": resp,
        })

    return dataset


def save_dataset(dataset, filepath='aura_dataset.jsonl'):
    with open(filepath, 'w', encoding='utf-8') as f:
        for item in dataset:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    print(f"✅ Dataset saqlandi: {filepath} ({len(dataset)} ta)")


def run(count=4000):
    dataset = generate_dataset(count)
    save_dataset(dataset)
    return dataset


if __name__ == '__main__':
    try:
        import os, django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mmt_project.settings')
        django.setup()
    except Exception:
        pass
    run()
