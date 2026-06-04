# File: jobs/management/commands/transliterate_uz.py

```python
import re
import os

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

def translate_to_uzbek(text, src='auto'):
    if not text or not text.strip():
        return text
    try:
        from deep_translator import GoogleTranslator
        translated = GoogleTranslator(source=src, target='uz').translate(text[:5000])
        if translated:
            return translated
    except Exception as e:
        print(f"Translate xato: {e}")
    return to_uzbek_latin(text)
```
