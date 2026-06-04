import requests
from bs4 import BeautifulSoup
from time import sleep
from jobs.models import Job, Category, Country
from ..transliterate_uz import translate_to_uzbek

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

def run():
    total = 0
    country, _ = Country.objects.get_or_create(name="O'zbekiston", code="UZ")
    category, _ = Category.objects.get_or_create(name="IT / Dasturlash")
    
    # YUQORIDAGI TO'LIQ RO'YXATNI SHU YERGA QO'YING
    search_keywords = [
    # BACKEND & ASOSIY DEVELOPMENT
    "python developer",
    "backend developer",
    "django developer",
    "flask developer",
    "fastapi developer",
    "node.js developer",
    "php developer",
    "laravel developer",
    "symfony developer",
    "ruby on rails developer",
    "java developer",
    "spring boot developer",
    "golang developer",
    "rust developer",
    "c# developer",
    ".net developer",
    "c++ developer",
    
    # FRONTEND
    "frontend developer",
    "react developer",
    "angular developer",
    "vue.js developer",
    "javascript developer",
    "typescript developer",
    "next.js developer",
    "nuxt.js developer",
    "html css developer",
    
    # MOBILE
    "mobile app developer",
    "android developer",
    "ios developer",
    "flutter developer",
    "react native developer",
    "kotlin developer",
    "swift developer",
    "cross platform mobile developer",
    
    # SOFTWARE ENGINEERING
    "software engineer",
    "software developer",
    "full stack developer",
    "mean stack developer",
    "mern stack developer",
    "desktop application developer",
    "embedded software engineer",
    
    # DATA & AI
    "ai engineer",
    "machine learning engineer",
    "data scientist",
    "data analyst",
    "data engineer",
    "prompt engineer",
    "nlp engineer",
    "computer vision engineer",
    "ai researcher",
    "deep learning engineer",
    "business intelligence developer",
    "data architect",
    "mlops engineer",
    
    # SECURITY
    "cybersecurity specialist",
    "information security analyst",
    "penetration tester",
    "security engineer",
    "devsecops engineer",
    "network security specialist",
    "application security engineer",
    
    # DEVOPS & INFRASTRUCTURE
    "devops engineer",
    "system administrator",
    "cloud engineer",
    "aws developer",
    "azure developer",
    "google cloud engineer",
    "kubernetes specialist",
    "docker engineer",
    "site reliability engineer",
    "infrastructure engineer",
    
    # GAME DEVELOPMENT
    "game developer",
    "unity developer",
    "unreal engine developer",
    "3d game developer",
    "mobile game developer",
    
    # DESIGN
    "product designer",
    "ui designer",
    "ux designer",
    "ui/ux designer",
    "product manager",
    "graphic designer",
    "motion designer",
    "interaction designer",
    "user researcher",
    "design system designer",
    "creative director",
    "product owner",
    
    # QA & TESTING
    "qa engineer",
    "quality assurance engineer",
    "test automation engineer",
    "manual tester",
    "performance tester",
    "security tester",
    
    # BUSINESS & MANAGEMENT
    "business analyst",
    "it project manager",
    "scrum master",
    "product owner",
    "technical project manager",
    "delivery manager",
    "agile coach",
    "product analyst",
    
    # OTHER IT ROLES
    "database administrator",
    "database developer",
    "sql developer",
    "system architect",
    "technical lead",
    "it consultant",
    "technical writer",
    "it support specialist",
    "network engineer",
    "help desk technician",
    "systems analyst",
    "erp consultant",
    
    # BLOCKCHAIN & WEB3
    "blockchain developer",
    "smart contract developer",
    "solidity developer",
    "web3 developer",
    "cryptocurrency developer",
    
    # EMERGING TECH
    "iot developer",
    "robotics engineer",
    "ar developer",
    "vr developer",
    "metaverse developer",
    "low code developer",
    "no code developer"
]
    
    for keyword in search_keywords:
        for page in range(1, 3):  # Har bir kalit so'z uchun 2 sahifa
            try:
                # Upwork qidiruv URL
                keyword_formatted = keyword.replace(' ', '-').lower()
                url = f"https://www.upwork.com/freelance-jobs/{keyword_formatted}/"
                
                if page > 1:
                    url += f"?page={page}"
                
                print(f"🔍 Qidirilmoqda: {keyword} - {url}")
                
                response = requests.get(url, headers=HEADERS, timeout=30)
                
                if response.status_code != 200:
                    print(f"⚠️ {keyword} bo'yicha ma'lumot topilmadi (status: {response.status_code})")
                    # Alternativ qidiruv
                    alt_url = f"https://www.upwork.com/o/jobs/browse/?q={keyword.replace(' ', '+')}"
                    response = requests.get(alt_url, headers=HEADERS, timeout=30)
                    if response.status_code != 200:
                        continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Upwork job elementlarini topish
                job_cards = soup.select('[data-test="JobTile"], .job-tile, .up-card-section, article')
                
                if not job_cards:
                    print(f"❌ {keyword} - hech qanday vakansiya topilmadi")
                    continue
                
                for card in job_cards:
                    try:
                        # Link topish
                        link = card.find('a', href=True)
                        if not link:
                            continue
                        
                        href = link.get('href')
                        if href.startswith('/'):
                            job_url = f"https://www.upwork.com{href}"
                        elif href.startswith('http'):
                            job_url = href
                        else:
                            continue
                        
                        # Takrorlanmaslik
                        if Job.objects.filter(source_url=job_url).exists():
                            continue
                        
                        # Title
                        title_elem = card.select_one('[data-test="JobTitle"], h4, .job-title, h3')
                        title = translate_to_uzbek(title_elem.get_text(strip=True)[:255]) if title_elem else keyword
                        
                        # Company
                        company_elem = card.select_one('[data-test="client-name"], .client-name, .company-name')
                        company = translate_to_uzbek(company_elem.get_text(strip=True)[:255]) if company_elem else "Upwork Client"
                        
                        # Description
                        desc_elem = card.select_one('[data-test="description"], .job-description, .description')
                        description = translate_to_uzbek(desc_elem.get_text(strip=True)[:5000]) if desc_elem else title
                        
                        # Budget
                        budget_elem = card.select_one('[data-test="budget"], .budget, .job-budget, [data-test="job-type"]')
                        salary_min = salary_max = None
                        currency = "USD"
                        
                        if budget_elem:
                            budget_text = budget_elem.get_text(strip=True)
                            numbers = []
                            for word in budget_text.split():
                                clean = ''.join(filter(str.isdigit, word))
                                if clean:
                                    numbers.append(int(clean))
                            
                            if numbers:
                                salary_min = numbers[0]
                                salary_max = numbers[-1] if len(numbers) > 1 else None
                            
                            if 'hourly' in budget_text.lower():
                                job_type = 'freelance'
                            else:
                                job_type = 'remote'
                        
                        # Yo'nalishni aniqlash
                        job_category = determine_category(keyword)
                        
                        # Saqlash
                        Job.objects.create(
                            title=title,
                            company=company,
                            category=job_category,
                            country=country,
                            description=description,
                            job_type='remote',
                            salary_min=salary_min,
                            salary_max=salary_max,
                            currency=currency,
                            source_url=job_url,
                            source='upwork.com',
                        )
                        total += 1
                        print(f"✅ [{total}] {title[:50]} - {company[:30]} ({keyword})")
                        
                    except Exception as e:
                        print(f"⚠️ Xato: {e}")
                        continue
                
                print(f"📊 {keyword}: {len(job_cards)} ta e'lon topildi\n")
                sleep(2)  # Upwork bloklamasligi uchun
                
            except Exception as e:
                print(f"❌ {keyword} xatosi: {e}")
                continue
    
    print(f"\n🎉 JAMI: {total} ta vakansiya qo'shildi!")
    return total


def determine_category(keyword):
    """Yo'nalishga qarab category aniqlash"""
    keyword_lower = keyword.lower()
    
    if any(word in keyword_lower for word in ['python', 'backend', 'django', 'flask', 'node', 'php', 'java', 'golang', 'rust', 'c#', '.net', 'c++']):
        name = "Backend / Dasturlash"
    elif any(word in keyword_lower for word in ['frontend', 'react', 'angular', 'vue', 'javascript', 'typescript', 'next.js', 'html', 'css']):
        name = "Frontend / Web"
    elif any(word in keyword_lower for word in ['mobile', 'android', 'ios', 'flutter', 'react native', 'kotlin', 'swift']):
        name = "Mobile Dasturlash"
    elif any(word in keyword_lower for word in ['ai', 'machine learning', 'data scientist', 'data analyst', 'prompt', 'nlp', 'computer vision', 'deep learning']):
        name = "Sun'iy Intellekt / Data"
    elif any(word in keyword_lower for word in ['security', 'cybersecurity', 'penetration', 'devsecops']):
        name = "Kiberxavfsizlik"
    elif any(word in keyword_lower for word in ['devops', 'cloud', 'aws', 'azure', 'kubernetes', 'docker']):
        name = "DevOps / Cloud"
    elif any(word in keyword_lower for word in ['game', 'unity', 'unreal']):
        name = "Game Development"
    elif any(word in keyword_lower for word in ['design', 'ui', 'ux', 'product designer', 'product manager']):
        name = "Dizayn / Product"
    elif any(word in keyword_lower for word in ['qa', 'quality', 'test']):
        name = "Quality Assurance"
    elif any(word in keyword_lower for word in ['analyst', 'project manager', 'scrum', 'product owner']):
        name = "Boshqaruv / Analitika"
    else:
        name = "IT / Dasturlash"
    
    category, _ = Category.objects.get_or_create(name=name)
    return category