# Modelfile for Ollama

File: `Modelfile` (loyiha ildizida)

```
FROM ./aura-tinyllama-q4.gguf

TEMPLATE """{{ if .System }}<|system|>
{{ .System }}</s>
{{ end }}<|user|>
{{ .Prompt }}</s>
<|assistant|>"""

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER stop "</s>"
```

# Installation and run script

File: `setup_and_run.sh` (ixtiyoriy)

```bash
#!/bin/bash
echo "=== AURA CAREER: To'liq o'rnatish ==="

# 1. Bog'liqliklar
source venv/bin/activate
pip install deep-translator curl_cffi beautifulsoup4 lxml ollama

# 2. Parserlar
echo "Vakansiyalarni yig'ish..."
python manage.py scrape_all

# 3. Dataset
echo "Dataset generatsiya..."
python -m ai_advisor.dataset_generator

# 4. Agar GGUF fayl bo'lsa, Ollama ga import
if [ -f "aura-tinyllama-q4.gguf" ]; then
    echo "Model import qilinmoqda..."
    ollama create aura-agent -f Modelfile
    echo "✅ Fine-tuned model tayyor: aura-agent"
else
    echo "⚠️ GGUF fayl topilmadi. Original TinyLlama ishlatiladi."
fi

# 5. Server
echo "Serverni ishga tushirish..."
python manage.py runserver 0.0.0.0:8001
```

# services.py yangilash (get_ai_chat_response_stream)

`ai_advisor/services.py` faylida stream_generator funksiyasini quyidagiga almashtiring:

```python
    full_response_holder = [""]

    def stream_generator():
        try:
            import ollama
            models = ['aura-agent', 'tinyllama', 'llama3.2:1b']
            used_model = None
            for m in models:
                try:
                    stream = ollama.chat(
                        model=m,
                        messages=messages,
                        stream=True,
                        options={'temperature': 0.7, 'num_predict': -1, 'num_ctx': 4096}
                    )
                    used_model = m
                    break
                except Exception:
                    continue

            if used_model:
                for chunk in stream:
                    token = chunk.get('message', {}).get('content', '')
                    if token:
                        full_response_holder[0] += token
                        yield token
            else:
                raise Exception("No model available")
        except Exception:
            fallback = generate_fallback_response(full_name, test_recommendation, bozor_data)
            full_response_holder[0] = fallback
            yield fallback

        updated_history = list(chat_session.message_history)
        updated_history.append({"role": "assistant", "content": full_response_holder[0]})
        chat_session.message_history = updated_history
        chat_session.save()

    return stream_generator()
```
