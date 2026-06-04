# AURA Career — Fayllarni yaratish uchun skript

Bu faylni `/tmp/aura_setup.sh` ga saqlang va ishga tushiring:
```bash
cp "/home/boborahim/Boborahim's/analitik loiha/.opencode/plans/create_all_files.sh.md" /tmp/aura_setup.sh
chmod +x /tmp/aura_setup.sh
bash /tmp/aura_setup.sh
```

```bash
#!/bin/bash
set -e
BASE="/home/boborahim/Boborahim's/analitik loiha"
mkdir -p "$BASE/jobs/management/commands/parsers"

# 1. transliterate_uz.py
cat > "$BASE/jobs/management/commands/transliterate_uz.py" << 'EOF'
import re
CYRILLIC_TO_LATIN = {
    'А':'A','а':'a','Б':'B','б':'b','В':'V','в':'v','Г':'G','г':'g',
    'Д':'D','д':'d','Е':'Ye','е':'ye','Ё':'Yo','ё':'yo','Ж':'J','ж':'j',
    'З':'Z','з':'z','И':'I','и':'i','Й':'Y','й':'y','К':'K','к':'k',
    'Л':'L','л':'l','М':'M','м':'m','Н':'N','н':'n','О':'O','о':'o',
    'П':'P','п':'p','Р':'R','р':'r','С':'S','с':'s','Т':'T','т':'t',
    'У':'U','у':'u','Ф':'F','ф':'f','Х':'X','х':'x','Ц':'S','ц':'s',
    'Ч':'Ch','ч':'ch','Ш':'Sh','ш':'sh','Щ':'Sh','щ':'sh',
    'Ъ':'','ъ':'','Ы':'Y','ы':'y','Ь':'','ь':'',
    'Э':'E','э':'e','Ю':'Yu','ю':'yu','Я':'Ya','я':'ya',
    'Ў':"O'",'ў':"o'",'Қ':'Q','қ':'q','Ғ':"G'",'ғ':"g'",'Ҳ':'H','ҳ':'h',
}
def cyrillic_to_latin(text): return ''.join(CYRILLIC_TO_LATIN.get(c,c) for c in text)
def to_uzbek_latin(text):
    if not text or not text.strip(): return text
    return cyrillic_to_latin(text) if re.search(r'[А-Яа-яЁёЎўҚқҒғҲҳ]', text) else text
def translate_to_uzbek(text,src='auto'):
    if not text or not text.strip(): return text
    try:
        from deep_translator import GoogleTranslator
        t = GoogleTranslator(source=src,target='uz').translate(text[:5000])
        if t: return t
    except: pass
    return to_uzbek_latin(text)
EOF

# 2. parsers/__init__.py
cat > "$BASE/jobs/management/commands/parsers/__init__.py" << 'EOF'
from . import hh_uz, olx_uz, apwork_uz, kwork_ru, teamwork_uz, linkedin_rapidapi
__all__ = ['hh_uz','olx_uz','apwork_uz','kwork_ru','teamwork_uz','linkedin_rapidapi']
EOF

# 3. parsers/hh_uz.py
cat > "$BASE/jobs/management/commands/parsers/hh_uz.py" << 'EOF'
import requests, re
from jobs.models import Job, Category, Country
from ..transliterate_uz import translate_to_uzbek
H = {"User-Agent":"AuraCareerParser/1.0"}
Q = ["Developer","Dasturchi","Backend","Frontend","Mobile","DevOps","QA","Data Scientist","Python","Java","JavaScript","React","Flutter","Android","DevOps","AI","ML","UI/UX","Product Manager","Blockchain","Security"]
def run():
    t,cc=0,{}
    c,_=Country.objects.get_or_create(name="O'zbekiston",code="UZ")
    for q in Q:
        try:
            r=requests.get("https://api.hh.ru/vacancies",params={"text":q,"area":97,"per_page":50},headers=H,timeout=15)
            if r.status_code!=200: continue
            for i in r.json().get('items',[]):
                u=i.get('alternate_url')
                if not u or Job.objects.filter(source_url=u).exists(): continue
                ti=translate_to_uzbek(i.get('name',''))[:255]
                co=translate_to_uzbek(i.get('employer',{}).get('name',"Noma'lum"))[:255]
                cn='IT / Dasturlash'
                if i.get('specializations'):
                    p=i['specializations'][0].get('profarea_name','')
                    if p: cn=p
                if cn not in cc: cc[cn]=Category.objects.get_or_create(name=cn)[0]
                d=None
                try:
                    dr=requests.get(i['url'],headers=H,timeout=10)
                    if dr.status_code==200: d=dr.json()
                except: pass
                desc=translate_to_uzbek(re.sub(r'<[^>]+>','',(d or {}).get('description','') or '').strip())[:5000] if d else ''
                sa=i.get('salary') or {}
                j=Job.objects.create(title=ti,company=co,category=cc[cn],country=c,description=desc,
                    job_type=i.get('employment',{}).get('id','full_time'),salary_min=sa.get('from'),salary_max=sa.get('to'),
                    currency=sa.get('currency','UZS'),source_url=u,source='hh.uz')
                if d and d.get('key_skills'):
                    from users.models import Skill
                    for s in [s['name'].strip() for s in d['key_skills'] if s.get('name','').strip()]:
                        sk,_=Skill.objects.get_or_create(name=s[:100]); j.required_skills.add(sk)
                t+=1
        except: pass
    return t
EOF

# 4. parsers/olx_uz.py
cat > "$BASE/jobs/management/commands/parsers/olx_uz.py" << 'EOF'
import requests
from bs4 import BeautifulSoup
from jobs.models import Job, Category, Country
from ..transliterate_uz import translate_to_uzbek
H={"User-Agent":"Mozilla/5.0 Chrome/120","Accept-Language":"uz-UZ,uz;q=0.9"}
def run():
    t=0; c,_=Country.objects.get_or_create(name="O'zbekiston",code="UZ"); ca,_=Category.objects.get_or_create(name="IT / Dasturlash")
    for u in ["https://www.olx.uz/rabota/it-kompyutery/"]:
        try:
            r=requests.get(u,headers=H,timeout=15)
            if r.status_code!=200: continue
            s=BeautifulSoup(r.text,'lxml')
            for i in s.select('div[data-cy="l-card"],li.offer-wrapper'):
                l=i.select_one('a[href]')
                if not l: continue
                h=l.get('href','')
                if not h.startswith('http'): h='https://www.olx.uz'+h
                if Job.objects.filter(source_url=h).exists(): continue
                ti=translate_to_uzbek((i.select_one('h6,.title') or i).get_text(strip=True)[:255])
                co=translate_to_uzbek((i.select_one('a[class*="seller"],span[class*="seller"]') or i).get_text(strip=True)[:255]) or 'OLX'
                de=translate_to_uzbek((i.select_one('p[class*="description"],.desc') or i).get_text(strip=True)[:5000])
                pt=(i.select_one('[data-testid="ad-price"],.price') or i).get_text(strip=True)
                sm=sl=None
                if pt:
                    n=[int(s.replace(' ','')) for s in pt.split() if s.replace(' ','').isdigit()]
                    if n: sm,sl=n[0],n[-1] if len(n)>1 else n[0]
                Job.objects.create(title=ti,company=co,category=ca,country=c,description=de,job_type='full_time',salary_min=sm,salary_max=sl,currency='UZS',source_url=h,source='olx.uz')
                t+=1
        except: pass
    return t
EOF

# 5. parsers/apwork_uz.py
cat > "$BASE/jobs/management/commands/parsers/apwork_uz.py" << 'EOF'
import requests
from bs4 import BeautifulSoup
from jobs.models import Job, Category, Country
from ..transliterate_uz import translate_to_uzbek
H={"User-Agent":"Mozilla/5.0 Chrome/120"}
def run():
    t=0; c,_=Country.objects.get_or_create(name="O'zbekiston",code="UZ"); ca,_=Category.objects.get_or_create(name="IT / Dasturlash")
    for u in ["https://apwork.uz/jobs","https://apwork.uz/jobs?category=it"]:
        try:
            r=requests.get(u,headers=H,timeout=15)
            if r.status_code!=200: continue
            s=BeautifulSoup(r.text,'lxml')
            for i in s.select('a[href*="/job/"],.job-item,.vacancy-card'):
                h=i.get('href','')
                if not h:
                    l=i.select_one('a[href]')
                    if l: h=l.get('href','')
                if not h: continue
                if not h.startswith('http'): h='https://apwork.uz'+('/' if not h.startswith('/') else '')+h
                if Job.objects.filter(source_url=h).exists(): continue
                ti=translate_to_uzbek((i.select_one('h2,h3,h4,.title,.job-title') or i).get_text(strip=True)[:255])
                co=translate_to_uzbek((i.select_one('.company,.employer,.author') or i).get_text(strip=True)[:255]) or 'Apwork'
                de=translate_to_uzbek((i.select_one('.description,.desc,p') or i).get_text(strip=True)[:5000])
                pt=(i.select_one('.price,.salary,.budget') or i).get_text(strip=True)
                sm=sl=None
                if pt:
                    n=[int(s.replace(' ','')) for s in pt.split() if s.replace(' ','').isdigit()]
                    if n: sm,sl=n[0],n[-1] if len(n)>1 else n[0]
                Job.objects.create(title=ti,company=co,category=ca,country=c,description=de,job_type='full_time',salary_min=sm,salary_max=sl,currency='UZS',source_url=h,source='apwork.uz')
                t+=1
        except: pass
    return t
EOF

# 6. parsers/kwork_ru.py
cat > "$BASE/jobs/management/commands/parsers/kwork_ru.py" << 'EOF'
import requests
from bs4 import BeautifulSoup
from jobs.models import Job, Category, Country
from ..transliterate_uz import translate_to_uzbek
H={"User-Agent":"Mozilla/5.0 Chrome/120"}
def run():
    t=0; c,_=Country.objects.get_or_create(name="O'zbekiston",code="UZ"); ca,_=Category.objects.get_or_create(name="IT / Dasturlash")
    for ct in ["razrabotka-sajtov","programmirovanie","mobile-apps","boty","skripty"]:
        for p in range(1,3):
            try:
                r=requests.get(f"https://kwork.ru/projects?category={ct}&page={p}",headers=H,timeout=15)
                if r.status_code!=200: continue
                s=BeautifulSoup(r.text,'lxml')
                for i in s.select('.project-card,.wants-card,.card,div[class*="project"]'):
                    l=i.select_one('a[href*="/projects/"],a[href*="/project/"]')
                    if not l: continue
                    h=l.get('href','')
                    if not h: continue
                    if 'kwork.ru' not in h: h='https://kwork.ru'+('/' if not h.startswith('/') else '')+h
                    if Job.objects.filter(source_url=h).exists(): continue
                    ti=translate_to_uzbek((i.select_one('.project-title,.wants-title,h2,h3') or i).get_text(strip=True)[:255])
                    de=translate_to_uzbek((i.select_one('.project-description,.wants-description,p') or i).get_text(strip=True)[:5000])
                    co=translate_to_uzbek((i.select_one('.username,.seller,.author') or i).get_text(strip=True)[:255]) or 'Kwork'
                    pt=(i.select_one('.price,.cost,.budget,span[class*="price"]') or i).get_text(strip=True)
                    sm=sl=None
                    if pt:
                        n=[int(s.replace(' ','')) for s in pt.split() if s.replace(' ','').isdigit()]
                        if n: sm,sl=n[0],n[-1] if len(n)>1 else n[0]
                    Job.objects.create(title=ti,company=co,category=ca,country=c,description=de,job_type='full_time',salary_min=sm,salary_max=sl,currency='UZS',source_url=h,source='kwork.ru')
                    t+=1
            except: pass
    return t
EOF

# 7. parsers/teamwork_uz.py
cat > "$BASE/jobs/management/commands/parsers/teamwork_uz.py" << 'EOF'
import requests
from bs4 import BeautifulSoup
from jobs.models import Job, Category, Country
from ..transliterate_uz import translate_to_uzbek
H={"User-Agent":"Mozilla/5.0 Chrome/120"}
def run():
    t=0; c,_=Country.objects.get_or_create(name="O'zbekiston",code="UZ"); ca,_=Category.objects.get_or_create(name="IT / Dasturlash")
    for u in ["https://teamwork.uz/vacancies","https://teamwork.uz/vacancies?category=it"]:
        try:
            r=requests.get(u,headers=H,timeout=15)
            if r.status_code!=200: continue
            s=BeautifulSoup(r.text,'lxml')
            for i in s.select('a[href*="/vacancy/"],.vacancy-item,.job-card'):
                h=i.get('href','')
                if not h:
                    l=i.select_one('a[href]')
                    if l: h=l.get('href','')
                if not h: continue
                if not h.startswith('http'): h='https://teamwork.uz'+('/' if not h.startswith('/') else '')+h
                if Job.objects.filter(source_url=h).exists(): continue
                ti=translate_to_uzbek((i.select_one('h2,h3,h4,.title,.vacancy-title') or i).get_text(strip=True)[:255])
                co=translate_to_uzbek((i.select_one('.company,.employer,.organization') or i).get_text(strip=True)[:255]) or 'Teamwork'
                de=translate_to_uzbek((i.select_one('.description,.desc,p,.requirements') or i).get_text(strip=True)[:5000])
                pt=(i.select_one('.salary,.price,.budget') or i).get_text(strip=True)
                sm=sl=None
                if pt:
                    n=[int(s.replace(' ','')) for s in pt.split() if s.replace(' ','').isdigit()]
                    if n: sm,sl=n[0],n[-1] if len(n)>1 else n[0]
                Job.objects.create(title=ti,company=co,category=ca,country=c,description=de,job_type='full_time',salary_min=sm,salary_max=sl,currency='UZS',source_url=h,source='teamwork.uz')
                t+=1
        except: pass
    return t
EOF

# 8. parsers/linkedin_rapidapi.py
cat > "$BASE/jobs/management/commands/parsers/linkedin_rapidapi.py" << 'EOF'
import os, requests
from jobs.models import Job, Category, Country
from ..transliterate_uz import translate_to_uzbek
K=os.environ.get('RAPIDAPI_KEY','')
def run():
    if not K: return 0
    t=0; c,_=Country.objects.get_or_create(name="O'zbekiston",code="UZ"); ca,_=Category.objects.get_or_create(name="IT / Dasturlash")
    hd={"X-RapidAPI-Key":K,"X-RapidAPI-Host":"linkedin-jobs-scraper-api.p.rapidapi.com","Content-Type":"application/json"}
    for kw in ["developer","software","python","java","AI","devops","frontend","data scientist"]:
        try:
            r=requests.post("https://linkedin-jobs-scraper-api.p.rapidapi.com/jobs/search",json={"keywords":kw,"location":"Uzbekistan","limit":25},headers=hd,timeout=20)
            if r.status_code!=200: continue
            items=r.json()
            if isinstance(items,dict): items=items.get('data',items)
            for i in items:
                u=i.get('url',i.get('link',i.get('jobUrl','')))
                if not u or Job.objects.filter(source_url=u).exists(): continue
                Job.objects.create(title=translate_to_uzbek(i.get('title',''))[:255],company=translate_to_uzbek(i.get('company','LinkedIn'))[:255],category=ca,country=c,description=translate_to_uzbek(i.get('description',''))[:5000],job_type='full_time',source_url=u,source='linkedin')
                t+=1
        except: pass
    return t
EOF

# 9. scrape_all.py
cat > "$BASE/jobs/management/commands/scrape_all.py" << 'EOF'
from django.core.management.base import BaseCommand
class Command(BaseCommand):
    help="Barcha manbalardan IT vakansiyalarini yig'ish"
    def handle(self,*a,**kw):
        from .parsers import hh_uz,olx_uz,apwork_uz,kwork_ru,teamwork_uz
        from .parsers.linkedin_rapidapi import run as ln
        total=0
        for n,f in [("HH.uz",hh_uz.run),("OLX.uz",olx_uz.run),("Apwork.uz",apwork_uz.run),("Kwork.ru",kwork_ru.run),("Teamwork.uz",teamwork_uz.run)]:
            try:
                c=f(); total+=c; self.stdout.write(self.style.SUCCESS(f"✅ {n}: {c} ta"))
            except Exception as e: self.stderr.write(self.style.ERROR(f"❌ {n}: {e}"))
        try:
            c=ln(); total+=c
            if c: self.stdout.write(self.style.SUCCESS(f"✅ LinkedIn: {c} ta"))
        except: pass
        from jobs.models import Job
        self.stdout.write(self.style.SUCCESS(f"\n📊 Jami: {total} ta | Bazada: {Job.objects.filter(is_active=True).count()} ta"))
EOF

# 10. dataset_generator.py
cat > "$BASE/ai_advisor/dataset_generator.py" << 'EOF'
import json,random
from django.db.models import Min,Max,Count,Q

P={'P':{'n':'Producer','c':['Backend Developer','Software Engineer','DevOps Engineer','Python Developer','Java Developer','Flutter Developer'],'s':['Python','Java','JavaScript','Django','Docker','AWS','Git','SQL','Linux'],'a':['Amaliy loyihalar yarating','Algoritmik masalalarni yeching'],'f':'Backend/DevOps dan AI/ML ga','d':'texnik muammolarni hal qilishga qiziqasiz'},'A':{'n':'Administrator','c':['QA Engineer','Data Analyst','Business Analyst','System Administrator','Data Engineer'],'s':['SQL','Excel','Tableau','Power BI','Python','Selenium','Jira','Linux'],'a':['SQL kurslarini o\'ting','ISTQB sertifikat oling'],'f':'Data Analyst dan Security ga','d':'tizimli va tartibni sevasiz'},'E':{'n':'Entrepreneur','c':['UI/UX Designer','Product Manager','AI Engineer','Product Designer','Machine Learning Engineer'],'s':['Figma','Python','TensorFlow','PyTorch','JavaScript','React','UI/UX'],'a':['AI/ML kurslarini boshlang','UI/UX dizaynni o\'rganing'],'f':'AI/Product sohasida yetakchi','d':'innovatsion g\'oyalar generatsiya qilasiz'},'I':{'n':'Integrator','c':['Project Manager','Scrum Master','HR IT','Frontend Developer','IT Recruiter'],'s':['JavaScript','React','Vue.js','HTML','CSS','Jira','Agile','Scrum'],'a':['Agile/Scrum sertifikat oling','Frontendni o\'rganing'],'f':'PM dan IT Director ga','d':'jamoa bilan ishlashni yaxshi ko\'rasiz'}}
EX=[(0,"tajribam yo'q"),(1,"1 yil"),(2,"2 yil"),(3,"3-4 yil"),(5,"5+ yil")]
NM=['Aziz','Bobur','Dilshod','Eldor','Farrux','Gulnoza','Humoyun','Islom','Javohir','Kamola','Madina','Nodir','Rustam','Sevara','Shoxrux','Temur','Xurshid','Zafar']
def gen(n=500):
    ds=[]
    for _ in range(n):
        r=random.choice(list(P.keys())); d=P[r]; nm=random.choice(NM); ey,et=random.choice(EX)
        sc=random.choices(['t','s','5','g'],weights=[.35,.25,.20,.20],k=1)[0]
        qs={'t':["Menga eng mos kasbni tavsiya qilasizmi?","Profilimga qarab nima maslahat berasiz?"],'s':["Bu ko'nikma bilan qanday ish topish mumkin?","Bu sohada rivojlanish uchun nima qilishim kerak?"],'5':["5 yildan keyin qaysi soha eng talabgir?","Kelgusi 5 yilda qaysi texnologiyalarni o'rganishim kerak?"],'g':["IT ga endi kirdim, qayerdan boshlashim kerak?","Qaysi tilni o'rganishim kerak?"]}
        q=random.choice(qs[sc]); sk=random.choice(d['s'])
        if sc=='s': inst=f"Men {nm}man. {et}. {sk} ni o'rganyapman. {q}"
        elif sc=='5': inst=f"Profilim {r}. {et}. {q}"
        elif sc=='g': inst=f"Ismim {nm}. {et}. {q}"
        else: inst=f"PAEI profilim {r}. {et}. Ko'nikmalarim: {', '.join(random.sample(d['s'],k=min(3,len(d['s']))))}. {q}"
        tot=0; bc=d['c'][0]; bcnt=0
        try:
            from jobs.models import Job
            tot=Job.objects.filter(is_active=True).count()
            for cn in d['c']:
                cnt=Job.objects.filter(is_active=True,category__name=cn).count()
                if cnt>bcnt: bcnt,bc=cnt,cn
        except: pass
        resp=f"## Assalomu alaykum, {nm}!\n\n### Karyera Tahlili\nSizning profilingiz ({r}) — {d['n']}. {d['d']}\n\n"
        if sc=='t': resp+=f"### Tavsiya\n**{bc}** — bazada {bcnt} ta vakansiya\n\n### Rivojlanish\n"+'\n'.join(f"- {a}" for a in d['a'])
        elif sc=='s':
            csk=0
            try: csk=Job.objects.filter(is_active=True,required_skills__name__icontains=sk).count()
            except: pass
            resp+=f"### {sk}\nBazada {csk} ta talab bor.\n\n- {sk} ni chuqur o'rganing\n- Loyihalar qiling"
        elif sc=='5': resp+=f"### 5 Yil\nBozorda {tot} ta vakansiya.\n{d['f']}\n\n1. 1-2 yil: asos\n2. 2-4 yil: sertifikatsiya\n3. 5 yil: yetakchi"
        else: resp+=f"Bozorda {tot} ta IT vakansiya.\nMos: {bc}\n\n- Python yoki JavaScript o'rganing\n- Loyihalar qiling"
        ds.append({"instruction":inst,"response":resp})
    return ds
def save(ds,fp='aura_dataset.jsonl'):
    with open(fp,'w',encoding='utf-8') as f:
        for i in ds: f.write(json.dumps({"instruction":i["instruction"],"response":i["response"]},ensure_ascii=False)+'\n')
    print(f"✅ {fp} ({len(ds)} ta)")
def run(): save(gen())
if __name__=='__main__':
    import os,django; os.environ['DJANGO_SETTINGS_MODULE']='mmt_project.settings'; django.setup(); run()
EOF

echo ""
echo "=== BARCHA FAYLLAR YARATILDI ==="
echo ""
echo "Ishga tushirish:"
echo "  source \"$VENV\""
echo "  pip install deep-translator beautifulsoup4 lxml"
echo "  python manage.py scrape_all"
echo "  python -m ai_advisor.dataset_generator"
echo "  python manage.py runserver 0.0.0.0:8001"
```
