# Analitik Loyiha (MMT Project)

Ushbu loyiha tahlillar, sun'iy intellekt maslahatchisi (AI Advisor) va bo'sh ish o'rinlarini (Jobs) boshqarish hamda tahlil qilish imkonini beruvchi yagona platformadir. Dastur Django va Django REST Framework (DRF) asosida toza arxitektura tamoyillariga muvofiq ishlab chiqilgan.

## Asosiy imkoniyatlar (Features)

- **Foydalanuvchilar tizimi (Users App):** Xavfsiz avtorizatsiya va autentifikatsiya (JWT orqali), foydalanuvchi profillari, rollarga asoslangan ruxsatlar.
- **AI Maslahatchi (AI Advisor):** Dastur orqali sun'iy intellekt yordamida savollarga javob berish va foydalanuvchilarga maslahat berish.
- **Tahlillar bo'limi (Analytics):** Platformadagi ma'lumotlarni yig'ish, qayta ishlash, pandas yordamida statistik ko'rsatkichlarni shakllantirish va vizualizatsiyaga tayyorlash.
- **Ish o'rinlari (Jobs App):** Vakansiyalarni ro'yxatdan o'tkazish, turkumlashtirish va ishlarni boshqarish uchun backend yechimlar.

## Texnologik stek

- **Backend Framework:** Django 5, Django REST Framework
- **Ma'lumotlar bazasi:** PostgreSQL (`psycopg2-binary`) va SQLite (Rivojlantirish muhiti uchun)
- **Avtentifikatsiya:** Simple JWT
- **Ma'lumotlar tahlili:** Pandas, Numpy
- **Admin Panel:** Django Jazzmin (chiroyli va zamonaviy admin interfeys)
- **Tashqi kutubxonalar:** Qisqa havolalar uchun, `python-dotenv` & `python-decouple` (ma'lumotlar xavfsizligini ta'minlash va sozlamalarni o'qish), CORS Headers va h.k.

## Loyihani o'rnatish (O'z kompyuteringizda ishga tushirish)

### 1-qadam. Loyihani yuklab oling
```bash
git clone <REPOSITORIY_HAVOLASI>
cd analitik-loiha
```

### 2-qadam. Virtual muhit (Virtual environment) yaratish va faollashtirish
**Windows uchun:**
```bash
python -m venv venv
venv\Scripts\activate
```
**Linux / macOS uchun:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3-qadam. Kerakli paketlarni o'rnatish
```bash
pip install -r requirements.txt
```

### 4-qadam. .env faylini yaratish
Loyiha asosiy papkasida (manage.py turgan joyda) `.env` nomli fayl yarating (o'rnak sifatida `.env.example` dan foydalanish mumkin) va kerakli o'zgaruvchilarni kiriting:
```ini
SECRET_KEY=sizning_maxfiy_kalitingiz
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3 # Yoki PostgreSQL uchun maxsus URL
```

### 5-qadam. Migratsiyalarni amalga oshirish
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6-qadam. Superuser (Admin) yaratish
```bash
python manage.py createsuperuser
```

### 7-qadam. Loyihani ishga tushirish
```bash
python manage.py runserver
```
Admin panelga kirish uchun brauzerda http://127.0.0.1:8000/admin manziliga kiring.
API endpointlarga murojaat qilish uchun odatda http://127.0.0.1:8000/api v.h. manzillaridan foydalaniladi.

## Qisqacha papkalar tuzilishi
```
analitik-loiha/
│
├── ai_advisor/         # AI maslahatchisi va savolarni boshqarish
├── analytics/          # Analitik va statistik mantiq
├── jobs/               # Ish o'rinlari, category va skill turlari
├── mmt_project/        # Asosiy sozlamalar (settings, urls)
├── users/              # Foydalanuvchi abstraksiyasi, autentifikatsiya
├── db.sqlite3          # SQLite bazasi (Local muhit uchun)
├── manage.py           # Django loyihani boshqarish utilitasidir
├── requirements.txt    # O'rnatilgan kutubxonalar ro'yxati
└── README.md           # Dasturiy ta'minot hujjatlari
```

## Litsenziya
Ushbu loyiha shaxsiy manfaatlarni aks ettiradi.
