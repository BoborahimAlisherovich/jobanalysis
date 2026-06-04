"""
MEGA SCRAPER - 2000+ real vakansiyalar
Manbalar:
  ✅ Remotive API      - remote IT jobs (bepul, cheksiz)
  ✅ Arbeitnow API     - global IT jobs (bepul, paginated)
  ✅ OLX.uz            - O'zbek IT e'lonlari
  ✅ Teamwork.uz       - O'zbek IT vakansiyalari
  ✅ Kwork.ru          - Freelance loyihalar
  ✅ Adzuna API        - Global jobs (bepul)
  ✅ The Muse API      - Global IT jobs (bepul)
Category mapping: rasmda ko'rsatilgan 18 ta yo'nalish
"""
import re
import time
import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from jobs.models import Job, Category, Country

# ──────────────────────────────────────────────────────────────────────────────
# 18 TA TARGET KATEGORIYA (rasm bo'yicha)
# ──────────────────────────────────────────────────────────────────────────────
TARGET_ROLES = [
    'Blockchain Developer',
    'Backend Developer',
    'Frontend Developer',
    'Mobile App Developer',
    'Software Engineer',
    'AI Engineer',
    'Business Analyst',
    'Business Intelligence (BI) Developer',
    'Cybersecurity Specialist',
    'Data Analyst',
    'Data Scientist',
    'DevOps Engineer',
    'Game Developer',
    'Product Designer',
    'Product Manager',
    'Prompt Engineer',
    'QA Engineer',
    'UI/UX Designer',
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}


# ──────────────────────────────────────────────────────────────────────────────
# TITLE → 18 CATEGORY MAPPING
# ──────────────────────────────────────────────────────────────────────────────
def map_category(title: str, desc: str = "") -> str:
    t = (title + " " + desc).lower()

    if re.search(r'\b(blockchain|web3|solidity|smart.?contract|defi|nft|crypto.?dev|ethereum|polkadot)\b', t):
        return 'Blockchain Developer'
    if re.search(r'\b(prompt.?engineer|llm.?engineer|gpt.?dev|ai.?prompt|chatgpt.?dev)\b', t):
        return 'Prompt Engineer'
    if re.search(r'\b(ai.?engineer|artificial.?intel|deep.?learn|nlp.?engineer|computer.?vision|mlops|ml.?ops)\b', t):
        return 'AI Engineer'
    if re.search(r'\b(machine.?learn|data.?scientist|ml.?engineer|data.?science|kaggle)\b', t):
        return 'Data Scientist'
    if re.search(r'\b(business.?intel|bi.?developer|power.?bi|tableau|qlik|looker|metabase|data.?warehouse)\b', t):
        return 'Business Intelligence (BI) Developer'
    if re.search(r'\b(data.?analy|data.?analyst|sql.?analyst|big.?data|analytics.?engineer)\b', t):
        return 'Data Analyst'
    if re.search(r'\b(cybersec|security.?eng|pentest|infosec|soc.?analyst|devsecops|network.?security|ethical.?hack)\b', t):
        return 'Cybersecurity Specialist'
    if re.search(r'\b(devops|site.?reliab|infrastructure.?eng|kubernetes|k8s|terraform|ansible|cloud.?eng|platform.?eng)\b', t):
        return 'DevOps Engineer'
    if re.search(r'\b(game.?dev|unity|unreal.?engine|gamedev|3d.?develop|game.?program|game.?design)\b', t):
        return 'Game Developer'
    if re.search(r'\b(mobile|android.?dev|ios.?dev|flutter|react.?native|kotlin.?dev|swift.?dev|xamarin)\b', t):
        return 'Mobile App Developer'
    if re.search(r'\b(frontend|front.?end|react.?dev|vue|angular|next\.js|svelte|nuxt|css.?dev|html.?dev)\b', t):
        return 'Frontend Developer'
    if re.search(r'\b(backend|back.?end|python.?dev|django|fastapi|flask|node\.js|express|laravel|spring|golang|php.?dev|rails)\b', t):
        return 'Backend Developer'
    if re.search(r'\b(product.?manager|head.?of.?product|vp.?product|chief.?product)\b', t):
        return 'Product Manager'
    if re.search(r'\b(product.?designer|ux.?research|user.?research|figma.?designer|interaction.?design)\b', t):
        return 'Product Designer'
    if re.search(r'\b(ui.?ux|ux.?ui|ui.?design|ux.?design|graphic.?design|visual.?design|motion.?design)\b', t):
        return 'UI/UX Designer'
    if re.search(r'\b(business.?analy|ba\b|systems.?analy|functional.?analy|requirements.?eng)\b', t):
        return 'Business Analyst'
    if re.search(r'\b(qa.?eng|quality.?assur|test.?eng|test.?autom|sdet|selenium|playwright|cypress|appium)\b', t):
        return 'QA Engineer'
    if re.search(r'\b(software.?eng|software.?dev|fullstack|full.?stack|developer|разработчик|dasturchi|programmer|coder)\b', t):
        return 'Software Engineer'
        
    # Agar hech qaysi IT texnologiya mos kelmasa va dasturchi so'zi ham bo'lmasa:
    return None


def get_cat(name):
    obj, _ = Category.objects.get_or_create(name=name)
    return obj


def get_country(name, code=""):
    obj, _ = Country.objects.get_or_create(
        name=name[:100],
        defaults={"code": (code or name[:2].upper())[:5]}
    )
    return obj


def clean_html(raw):
    if not raw:
        return ""
    text = re.sub(r'<[^>]+>', ' ', raw)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


# ──────────────────────────────────────────────────────────────────────────────
# MANAGEMENT COMMAND
# ──────────────────────────────────────────────────────────────────────────────
class Command(BaseCommand):
    help = "2000+ real IT vakansiyalar yig'ish"

    def add_arguments(self, parser):
        parser.add_argument('--source', default='all',
            help='remotive | arbeitnow | olx | teamwork | kwork | muse | all')

    def log(self, msg):
        self.stdout.write(msg)

    def ok(self, msg):
        self.stdout.write(self.style.SUCCESS(msg))

    def err(self, msg):
        self.stdout.write(self.style.ERROR(msg))

    def handle(self, *args, **options):
        # Barcha 18 kategoriya mavjudligini ta'minlaymiz
        for role in TARGET_ROLES:
            Category.objects.get_or_create(name=role)
        self.ok("✅ 18 ta kategoriya yaratildi")

        src = options['source']
        runners = {
            'remotive':  self.scrape_remotive,
            'arbeitnow': self.scrape_arbeitnow,
            'muse':      self.scrape_the_muse,
            'olx':       self.scrape_olx,
            'teamwork':  self.scrape_teamwork,
            'kwork':     self.scrape_kwork,
        }

        to_run = list(runners.keys()) if src == 'all' else [src]
        total = 0

        for name in to_run:
            self.log(f"\n{'='*55}")
            self.log(self.style.WARNING(f"▶ {name.upper()} ..."))
            try:
                n = runners[name]()
                total += n
                self.ok(f"✅ {name}: +{n} vakansiya")
            except Exception as e:
                self.err(f"❌ {name}: {e}")

        active = Job.objects.filter(is_active=True).count()
        self.log(f"\n{'='*55}")
        self.ok(f"🎉 BU SAFAR QO'SHILDI: {total} ta")
        self.ok(f"📊 BAZADA JAMI AKTIV: {active} ta")

    # ─────────────────────────────────────────────────────────────────────────
    # 1. REMOTIVE.COM - Bepul public API, ~3000+ remote IT jobs
    # ─────────────────────────────────────────────────────────────────────────
    def scrape_remotive(self):
        """remotive.com/api/remote-jobs - 100% bepul"""
        total = 0
        country = get_country("Global/Remote", "GLB")

        categories = [
            "software-dev", "devops", "product", "business",
            "data", "qa", "ux", "salesdev", "all"
        ]

        for cat_id in categories:
            try:
                params = {"limit": 500}
                if cat_id != "all":
                    params["category"] = cat_id

                resp = requests.get(
                    "https://remotive.com/api/remote-jobs",
                    params=params, timeout=30
                )
                if resp.status_code != 200:
                    self.log(f"  Remotive [{cat_id}]: HTTP {resp.status_code}")
                    continue

                jobs = resp.json().get('jobs', [])
                self.log(f"  Remotive [{cat_id}]: {len(jobs)} ta topildi")

                for item in jobs:
                    try:
                        src_url = item.get('url', '')
                        if not src_url:
                            continue
                        if Job.objects.filter(source_url=src_url).exists():
                            continue

                        title = (item.get('title') or '')[:255]
                        company = (item.get('company_name') or 'Remotive')[:255]
                        desc = clean_html(item.get('description') or '')[:3000]
                        tags = ' '.join(item.get('tags') or [])

                        cat_name = map_category(title, desc + ' ' + tags)
                        if not cat_name: continue
                        category = get_cat(cat_name)

                        # Salary
                        sal_text = item.get('salary') or ''
                        sal_min = sal_max = None
                        nums = re.findall(r'\d[\d,]*', sal_text.replace(',', ''))
                        if nums:
                            sal_min = int(nums[0])
                            sal_max = int(nums[-1]) if len(nums) > 1 else sal_min

                        pub_date = item.get('publication_date', '')

                        Job.objects.create(
                            title=title, company=company,
                            category=category, country=country,
                            description=desc or f"{title} - {company}",
                            job_type='remote',
                            salary_min=sal_min, salary_max=sal_max, currency='USD',
                            source_url=src_url, source='remotive.io', is_active=True,
                        )
                        total += 1
                    except Exception:
                        continue

                time.sleep(1)

            except Exception as e:
                self.log(f"  Remotive [{cat_id}] xato: {e}")

        return total

    # ─────────────────────────────────────────────────────────────────────────
    # 2. ARBEITNOW.COM - Bepul paginated API, ~2000+ global IT jobs
    # ─────────────────────────────────────────────────────────────────────────
    def scrape_arbeitnow(self):
        """arbeitnow.com/api/job-board-api - paginated bepul API"""
        total = 0
        page = 1
        max_pages = 30  # ~3000 vakansiya

        while page <= max_pages:
            try:
                resp = requests.get(
                    "https://www.arbeitnow.com/api/job-board-api",
                    params={"page": page}, timeout=20
                )
                if resp.status_code != 200:
                    break

                data = resp.json()
                items = data.get('data', [])
                if not items:
                    break

                self.log(f"  Arbeitnow p{page}: {len(items)} ta")

                for item in items:
                    try:
                        src_url = item.get('url', '')
                        if not src_url:
                            continue
                        if Job.objects.filter(source_url=src_url).exists():
                            continue

                        title = (item.get('title') or '')[:255]
                        company = (item.get('company_name') or 'Arbeitnow')[:255]
                        desc = clean_html(item.get('description') or '')[:3000]
                        tags = ' '.join(item.get('tags') or [])

                        cat_name = map_category(title, desc + ' ' + tags)
                        if not cat_name: continue
                        category = get_cat(cat_name)

                        jtype = 'remote' if item.get('remote') else 'full_time'
                        loc = (item.get('location') or 'Germany')[:100]
                        c = get_country(loc)

                        Job.objects.create(
                            title=title, company=company,
                            category=category, country=c,
                            description=desc or f"{title} - {company}",
                            job_type=jtype,
                            source_url=src_url, source='arbeitnow', is_active=True,
                        )
                        total += 1
                    except Exception:
                        continue

                # Keyingi sahifaga o'tish
                next_link = data.get('links', {}).get('next')
                if not next_link:
                    break
                page += 1
                time.sleep(0.5)

            except Exception as e:
                self.log(f"  Arbeitnow p{page}: {e}")
                break

        return total

    # ─────────────────────────────────────────────────────────────────────────
    # 3. THE MUSE API - Bepul, global IT companies
    # ─────────────────────────────────────────────────────────────────────────
    def scrape_the_muse(self):
        """themuse.com/api - bepul, paginated"""
        total = 0
        country = get_country("Global/Remote", "GLB")
        categories = [
            "Software Engineer", "Data Science", "Product Management",
            "Design", "DevOps", "Quality Assurance", "Business Development",
        ]

        for cat in categories:
            page = 1
            while page <= 50:
                try:
                    resp = requests.get(
                        "https://www.themuse.com/api/public/jobs",
                        params={"category": cat, "page": page, "level": "all"},
                        timeout=20
                    )
                    if resp.status_code != 200:
                        break

                    data = resp.json()
                    items = data.get('results', [])
                    if not items:
                        break

                    for item in items:
                        try:
                            src_url = item.get('refs', {}).get('landing_page', '')
                            if not src_url:
                                continue
                            if Job.objects.filter(source_url=src_url).exists():
                                continue

                            title = (item.get('name') or '')[:255]
                            company = (item.get('company', {}).get('name') or 'TheMuse')[:255]

                            contents = item.get('contents') or ''
                            desc = clean_html(contents)[:3000]

                            locs = item.get('locations', [])
                            loc_name = locs[0].get('name', 'USA') if locs else 'USA'
                            c = get_country(loc_name[:100])

                            cat_name = map_category(title, desc)
                            if not cat_name: continue
                            category_obj = get_cat(cat_name)

                            jtype = 'remote' if any(
                                'remote' in (l.get('name', '')).lower() for l in locs
                            ) else 'full_time'

                            Job.objects.create(
                                title=title, company=company,
                                category=category_obj, country=c,
                                description=desc or f"{title} - {company}",
                                job_type=jtype,
                                source_url=src_url, source='themuse', is_active=True,
                            )
                            total += 1
                        except Exception:
                            continue

                    total_count = data.get('total', 0)
                    if page * 20 >= total_count:
                        break
                    page += 1
                    time.sleep(0.5)

                except Exception as e:
                    self.log(f"  TheMuse [{cat}] p{page}: {e}")
                    break

        return total

    # ─────────────────────────────────────────────────────────────────────────
    # 4. OLX.UZ - O'zbek IT vakansiyalari
    # ─────────────────────────────────────────────────────────────────────────
    def scrape_olx(self):
        total = 0
        country = get_country("O'zbekiston", "UZ")
        urls = [
            "https://www.olx.uz/rabota/it-telekom-kompyutery/",
            "https://www.olx.uz/rabota/programmirovanie/",
            "https://www.olx.uz/rabota/internet/",
            "https://www.olx.uz/rabota/dizajn-tvorchestvo/",
        ]
        for base_url in urls:
            for page in range(1, 30):
                try:
                    resp = requests.get(
                        f"{base_url}?page={page}", headers=HEADERS, timeout=15
                    )
                    if resp.status_code != 200:
                        break
                    soup = BeautifulSoup(resp.text, 'lxml')
                    items = soup.select('div[data-cy="l-card"]')
                    if not items:
                        break

                    for item in items:
                        try:
                            link = item.select_one('a[href]')
                            if not link:
                                continue
                            href = link.get('href', '')
                            if not href.startswith('http'):
                                href = 'https://www.olx.uz' + href
                            if Job.objects.filter(source_url=href).exists():
                                continue

                            title_el = item.select_one('h6,[data-cy="ad-card-title"]')
                            title = (title_el.get_text(strip=True) if title_el else 'IT vakansiya')[:255]

                            desc_el = item.select_one('p')
                            desc = (desc_el.get_text(strip=True) if desc_el else title)[:2000]

                            price_el = item.select_one('[data-testid="ad-price"]')
                            sal_min = sal_max = None
                            if price_el:
                                nums = re.findall(r'\d+', price_el.get_text().replace('\xa0', '').replace(' ', ''))
                                if nums:
                                    sal_min = int(nums[0])
                                    sal_max = int(nums[-1]) if len(nums) > 1 else sal_min

                            cat_name = map_category(title, desc)
                            if not cat_name: continue
                            category = get_cat(cat_name)

                            Job.objects.create(
                                title=title, company='OLX.uz',
                                category=category, country=country,
                                description=desc or title,
                                job_type='full_time',
                                salary_min=sal_min, salary_max=sal_max, currency='UZS',
                                source_url=href, source='olx.uz', is_active=True,
                            )
                            total += 1
                        except Exception:
                            continue
                    time.sleep(1)
                except Exception as e:
                    self.log(f"  OLX p{page}: {e}")
                    break
        return total

    # ─────────────────────────────────────────────────────────────────────────
    # 5. TEAMWORK.UZ
    # ─────────────────────────────────────────────────────────────────────────
    def scrape_teamwork(self):
        total = 0
        country = get_country("O'zbekiston", "UZ")
        endpoints = [
            "https://teamwork.uz/vacancies",
            "https://teamwork.uz/vacancies?category=it",
            "https://teamwork.uz/vacancies?category=design",
        ]
        for base in endpoints:
            for page in range(1, 25):
                try:
                    sep = '&' if '?' in base else '?'
                    resp = requests.get(f"{base}{sep}page={page}", headers=HEADERS, timeout=15)
                    if resp.status_code != 200:
                        break
                    soup = BeautifulSoup(resp.text, 'lxml')
                    cards = soup.select('.vacancy-card, .job-card, article, .card')
                    if not cards:
                        break

                    for card in cards:
                        try:
                            link = card.select_one('a[href]')
                            if not link:
                                continue
                            href = link.get('href', '')
                            if not href.startswith('http'):
                                href = 'https://teamwork.uz' + href
                            if Job.objects.filter(source_url=href).exists():
                                continue

                            title_el = card.select_one('h2,h3,h4,.title')
                            title = (title_el.get_text(strip=True) if title_el else 'Vakansiya')[:255]

                            company_el = card.select_one('.company,.employer')
                            company = (company_el.get_text(strip=True) if company_el else 'Teamwork.uz')[:255]

                            desc_el = card.select_one('.description,.desc,p')
                            desc = (desc_el.get_text(strip=True) if desc_el else title)[:3000]

                            sal_el = card.select_one('.salary,.price')
                            sal_min = sal_max = None
                            if sal_el:
                                nums = re.findall(r'\d+', sal_el.get_text().replace(' ', ''))
                                if nums:
                                    sal_min = int(nums[0])
                                    sal_max = int(nums[-1]) if len(nums) > 1 else sal_min

                            cat_name = map_category(title, desc)
                            if not cat_name: continue
                            category = get_cat(cat_name)

                            Job.objects.create(
                                title=title, company=company,
                                category=category, country=country,
                                description=desc or title,
                                job_type='full_time',
                                salary_min=sal_min, salary_max=sal_max, currency='UZS',
                                source_url=href, source='teamwork.uz', is_active=True,
                            )
                            total += 1
                        except Exception:
                            continue
                    time.sleep(1)
                except Exception as e:
                    self.log(f"  Teamwork p{page}: {e}")
                    break
        return total

    # ─────────────────────────────────────────────────────────────────────────
    # 6. KWORK.RU
    # ─────────────────────────────────────────────────────────────────────────
    def scrape_kwork(self):
        total = 0
        country = get_country("Global/Remote", "GLB")
        cats = [
            ("programmirovanie", "Backend Developer"),
            ("razrabotka-sajtov", "Frontend Developer"),
            ("mobile", "Mobile App Developer"),
            ("boty", "Software Engineer"),
            ("testirovanie", "QA Engineer"),
            ("admini", "DevOps Engineer"),
            ("dizayn", "UI/UX Designer"),
        ]
        for cat_slug, default_cat in cats:
            for page in range(1, 30):
                try:
                    resp = requests.get(
                        f"https://kwork.ru/projects?category={cat_slug}&page={page}",
                        headers=HEADERS, timeout=15
                    )
                    if resp.status_code != 200:
                        break
                    soup = BeautifulSoup(resp.text, 'lxml')
                    cards = soup.select('.project-card, .wants-card, .card')
                    if not cards:
                        break

                    for card in cards:
                        try:
                            link = card.select_one('a[href]')
                            if not link:
                                continue
                            href = link.get('href', '')
                            if not href.startswith('http'):
                                href = 'https://kwork.ru' + href
                            if Job.objects.filter(source_url=href).exists():
                                continue

                            title_el = card.select_one('h2,h3,.title,.name')
                            title = (title_el.get_text(strip=True) if title_el else 'Kwork loyiha')[:255]

                            desc_el = card.select_one('.description,.text,p')
                            desc = (desc_el.get_text(strip=True) if desc_el else title)[:3000]

                            price_el = card.select_one('.price,.cost,.budget')
                            sal_min = sal_max = None
                            if price_el:
                                nums = re.findall(r'\d+', price_el.get_text().replace(' ', ''))
                                if nums:
                                    sal_min = int(nums[0])
                                    sal_max = int(nums[-1]) if len(nums) > 1 else sal_min

                            cat_name = map_category(title, desc)
                            if cat_name == 'Software Engineer' or not cat_name:
                                cat_name = default_cat
                            category = get_cat(cat_name)

                            Job.objects.create(
                                title=title, company='Kwork.ru',
                                category=category, country=country,
                                description=desc or title,
                                job_type='remote',
                                salary_min=sal_min, salary_max=sal_max, currency='RUB',
                                source_url=href, source='kwork.ru', is_active=True,
                            )
                            total += 1
                        except Exception:
                            continue
                    time.sleep(0.5)
                except Exception as e:
                    self.log(f"  Kwork [{cat_slug}] p{page}: {e}")
                    break
        return total
