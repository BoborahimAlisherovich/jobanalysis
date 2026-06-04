# AURA Career AI hujjatlari uchun tuzatishlar

Ushbu fayl loyihadagi haqiqiy kod bazasiga mos kelishi uchun yozilgan. Maqsad - taqdimotdagi AI bo'limini ortiqcha da'volarsiz, kodda mavjud bo'lgan real yechimlar bilan moslashtirish.

## 1. Noto'g'ri yoki ortiqcha da'volar

- `ai_utils.py` moduli mavjud emas.
- `ChromaDB` ishlatilmagan.
- `SentenceTransformer` ishlatilmagan.
- `cleaned_jobs.csv` fayli repo ichida topilmadi.
- 4000+ qatorli o'zbekcha bilimlar bazasi kodda tasdiqlanmagan.
- `ollama.generate` chaqiruvi yo'q, mavjud integratsiya `ollama.chat(...)` orqali ishlaydi.
- `main.js` AI modeli bilan bog'lanmaydi; u faqat UI interaksiyalarini boshqaradi.

## 2. Kod bazasida haqiqatan nima bor

- AI mantiqi asosan `ai_advisor/services.py` ichida joylashgan.
- Foydalanuvchi chati uchun session xotira, tarix tozalash va javobni qisqartirish logikasi bor.
- AI javob oqimi `ai_advisor/views.py` dagi `ai_chat_stream` orqali `StreamingHttpResponse` sifatida qaytadi.
- Model chaqiruvi mavjud bo'lsa, `ollama.chat(...)` ishlatiladi.
- Ollama ishlamasa, tizim template-based fallback javobga o'tadi.
- Vakansiyalar `jobs` app ichidagi `Job`, `Category`, `Country`, `Skill` modellari orqali saqlanadi.
- Vakansiya yig'ish skriptlari `jobs/management/commands/parsers/` ichida joylashgan.
- IT vakansiyalar eksporti uchun `jobs/management/commands/scrape_and_export.py` qo'shilgan.

## 3. Ma'lumotlar bo'yicha to'g'ri holat

- `data/vacancies_it_train.jsonl` fayli juda kichik namunaviy dataset bo'lib, hozirda 3 ta yozuvdan iborat.
- Scraping natijasida `data/vacancies_it.json` ga 66 ta IT vakansiya eksport qilingan.
- Shuning uchun hujjatda "4000 dan ortiq qator" degan jumla hozirgi repo holatiga mos kelmaydi.

## 4. Hujjatda qanday ifodalash kerak

### To'g'ri variant

AI yechimining hozirgi bosqichi lokal Django backend, chat xotirasi va Ollama asosidagi javob yaratish qatlamidan iborat. Tizim foydalanuvchi test natijasi, profil ko'nikmalari va bazadagi real vakansiya statistikasi asosida tavsiya beradi. Model ishlamasa, fallback template javoblar orqali xizmat uzluksizligi saqlanadi.

### Bekor qilish kerak bo'lgan iboralar

- "4000 dan ortiq qatordan iborat o'zbekcha dataset"
- "ChromaDB vektor bazasi"
- "SentenceTransformer orqali embedding"
- "cleaned_jobs.csv ga eksport qilingan ETL pipeline"
- "ai_utils.py moduli"
- "ollama.generate endpointi"

## 5. Hujjatning amaldagi kodga mos qisqa tavsifi

Loyihada AI qismi quyidagicha ishlaydi:

1. Foydalanuvchi test topshiradi.
2. `ai_advisor/views.py` natijani session va bazaga saqlaydi.
3. `ai_advisor/services.py` foydalanuvchi profili va bozor kontekstini yig'adi.
4. `ollama.chat(...)` orqali lokal modeldan javob olinadi.
5. Model javobi sifatsiz bo'lsa, fallback template javob ishlatiladi.
6. Frontend `static/js/main.js` orqali UI interaksiyalarini boshqaradi.

## 6. Tavsiya etilgan tuzatilgan matn

Quyidagi jumla hozirgi kod bazaga ancha yaqin:

"AURA Career loyihasida AI qismi lokal Django backend, foydalanuvchi test natijalari, chat xotirasi va bazadagi real vakansiya statistikasi asosida ishlaydi. Tizim `ai_advisor/services.py` orqali bozor kontekstini yig'adi, `ollama.chat(...)` bilan lokal modeldan javob oladi va model mavjud bo'lmaganda yoki sifati past bo'lsa fallback mantiqdan foydalanadi."

## 7. Agar keyinchalik ChromaDB qo'shilsa

ChromaDB va SentenceTransformer keyingi bosqich sifatida qo'shilishi mumkin, lekin hozirgi hujjatda ular faqat reja yoki kelajakdagi kengaytma sifatida ko'rsatilishi kerak.

## 8. Kamchiliklar va yechimlar

Quyida hujjatdagi asosiy kamchiliklar va ularning amaliy yechimlari berilgan:

### 8.1. Kamchilik: mavjud bo'lmagan komponentlar tilga olingan

Masalan, `ai_utils.py`, `ChromaDB`, `SentenceTransformer`, `cleaned_jobs.csv` va `ollama.generate` kabi qismlar hozirgi kod bazada yo'q.

Yechim:
- Faqat repo ichida real mavjud bo'lgan fayl va funksiyalarni yozish.
- AI oqimini [ai_advisor/services.py](ai_advisor/services.py) va [ai_advisor/views.py](ai_advisor/views.py) bilan cheklash.
- Kelajakdagi reja bo'lsa, uni alohida “rejalashtirilgan kengaytma” deb belgilash.

### 8.2. Kamchilik: dataset hajmi ortiqcha kattalashtirib yozilgan

Hujjatda 4000+ qatorli bilimlar bazasi deyilgan, lekin repo ichidagi tayyor trening fayl hozircha 3 ta yozuvdan iborat.

Yechim:
- Hujjatda aniq sonlarni yozish: `data/vacancies_it_train.jsonl` = 3 yozuv, `data/vacancies_it.json` = 66 vakansiya.
- Agar katta dataset kerak bo'lsa, uni alohida yig'ish va validatsiya qilish.

### 8.3. Kamchilik: AI arxitekturasi haddan tashqari murakkab ko'rsatilgan

Matnda RAG, embedding, vektor bazasi va ETL pipeline mavjuddek yozilgan, ammo kodda hozircha lokal chat xotira, bozor konteksti yig'ish va Ollama fallback ishlaydi.

Yechim:
- Arxitekturani sodda va real holatda ta'riflash.
- Hozirgi tizimni 3 qismga bo'lib yozish: chat logika, bozor statistikasi, lokal model/fallback.
- Agar keyinchalik RAG qo'shilsa, uni alohida modul sifatida hujjatlashtirish.

### 8.4. Kamchilik: frontend va backend orasidagi bog'lanish noto'g'ri tasvirlangan

`static/js/main.js` umumiy UI interaksiyalarini boshqaradi, lekin AI modelga to'g'ridan-to'g'ri ulanmaydi.

Yechim:
- Frontend vazifasini aniq yozish: menu, animatsiya, toast, copy, scroll kabi UI funksiyalar.
- AI so'rovlari esa [ai_advisor/views.py](ai_advisor/views.py) dagi `ai_chat_stream` orqali ketishini ko'rsatish.

### 8.5. Kamchilik: vakansiya manbalari juda umumiy yozilgan

"Hamma IT kanallari" degan ibora hujjatda juda umumiy bo'lib qolgan.

Yechim:
- Aniq manbalarni sanab o'tish: HH.uz, OLX.uz, Kwork.ru, Apwork.uz, Teamwork.uz, LinkedIn.
- Qaysi biri real ishlayotganini va qaysi biri API kalit talab qilishini yozish.

### 8.6. Kamchilik: koddagi real scraping natijalari hujjatga mos tushmagan

Scraperlar ba'zi manbalardan nol natija qaytargan, faqat OLX.uz dan vakansiyalar topilgan.

Yechim:
- Hujjatda scraping natijasini aniq yozish.
- Masalan: HH.uz = 0, OLX.uz = 21, Kwork = 0, Apwork = 0, Teamwork = 0, LinkedIn = RAPIDAPI_KEY bo'lmasa ishlamaydi.

### 8.7. Kamchilik: AI bo'limida ortiqcha ilmiy atamalar bor

Hujjatda RAG, Cosine Similarity, vektor bazasi kabi tushunchalar bor, lekin ular hozirgi kodda amaliy ishlatilmagan.

Yechim:
- Faqat ishlatilayotgan texnologiyalarni yozish.
- Ilmiy terminlarni faqat agar kodda real implementatsiya bo'lsa qo'shish.

### 8.8. Kamchilik: jarayon bosqichlari aniq ajratilmagan

Hujjatda AI, dataset, scraping, frontend va fallback bir-biriga aralash yozilgan.

Yechim:
- Bo'limlarni quyidagicha ajratish:
	1. Dataset va scraping
	2. AI chat logikasi
	3. Frontend interaktivlik
	4. Fallback va xatoliklarni boshqarish

## 9. Tayyor ishlatish uchun qisqa xulosa

Agar siz topshiriqqa qo'yish uchun eng toza variantni xohlasangiz, quyidagi xulosani ishlatish mumkin:

"Loyihadagi hujjatning asosiy kamchiligi shundaki, unda mavjud bo'lmagan AI komponentlar, ortiqcha dataset hajmi va amalda ishlatilmagan texnologiyalar tilga olingan. Yechim sifatida hujjatni real kod bazaga moslashtirish, faqat mavjud modullarni yozish, scraping natijalarini aniq ko'rsatish va kelajakdagi kengaytmalarni alohida reja sifatida ajratish kerak."
