# Colab Notebook: aura_finetune_tinyllama.ipynb

Google Colab da yangi notebook oching va quyidagi kodlarni hujayralarga joylashtiring.

## Hujayra 1: Kutubxonalarni o'rnatish

```python
!pip install -q transformers peft trl bitsandbytes datasets accelerate huggingface_hub
```

## Hujayra 2: Datasetni yuklash

```python
from google.colab import files
import json

print("aura_dataset.jsonl faylini yuklang:")
uploaded = files.upload()

dataset = []
for fn in uploaded:
    with open(fn, 'r') as f:
        for line in f:
            dataset.append(json.loads(line))

print(f"✅ {len(dataset)} ta misol yuklandi")
```

## Hujayra 3: Model va tokenizator

```python
import torch
from transformers import (
    AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
)
from peft import LoraConfig, prepare_model_for_kbit_training
from trl import SFTTrainer
from datasets import Dataset

MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True,
)

model = prepare_model_for_kbit_training(model)
print("✅ Model yuklandi")
```

## Hujayra 4: Datasetni formatlash

```python
def format_example(ex):
    messages = [
        {"role": "user", "content": ex["instruction"]},
        {"role": "assistant", "content": ex["response"]},
    ]
    return tokenizer.apply_chat_template(messages, tokenize=False)

texts = [format_example(ex) for ex in dataset]
hf_dataset = Dataset.from_dict({"text": texts})
print(f"✅ {len(hf_dataset)} ta formatted")
print("Namuna:")
print(texts[0][:300])
```

## Hujayra 5: LoRA sozlamalari

```python
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)
print("✅ LoRA konfiguratsiyasi tayyor")
```

## Hujayra 6: Trainer

```python
from transformers import TrainingArguments

args = TrainingArguments(
    output_dir="./aura-tinyllama",
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    num_train_epochs=3,
    learning_rate=2e-4,
    fp16=True,
    logging_steps=10,
    save_steps=100,
    save_total_limit=2,
    remove_unused_columns=True,
    report_to="none",
    max_grad_norm=0.3,
    warmup_ratio=0.03,
)

trainer = SFTTrainer(
    model=model,
    args=args,
    train_dataset=hf_dataset,
    tokenizer=tokenizer,
    peft_config=lora_config,
    dataset_text_field="text",
    max_seq_length=1024,
)

print("✅ Trainer tayyor!")
```

## Hujayra 7: O'QITISHNI BOSHLASH

```python
trainer.train()
trainer.save_model("./aura-tinyllama-final")
tokenizer.save_pretrained("./aura-tinyllama-final")
print("✅ Fine-tuning tugadi! Model saqlandi.")
```

## Hujayra 8: Modelni sinash

```python
from transformers import pipeline

pipe = pipeline(
    "text-generation",
    model="./aura-tinyllama-final",
    tokenizer=tokenizer,
    device=0 if torch.cuda.is_available() else -1,
)

test_prompt = tokenizer.apply_chat_template(
    [{"role": "user", "content": "Mening PAEI profilim P, 2 yil tajribam bor. Qaysi yo'nalishni maslahat berasiz?"}],
    tokenize=False,
)

result = pipe(test_prompt, max_new_tokens=300, temperature=0.7, do_sample=True)
print(result[0]['generated_text'])
```

## Hujayra 9: Hugging Face ga yuklash

```python
from huggingface_hub import HfApi, notebook_login

notebook_login()  # tokenni kiritish

api = HfApi()
username = input("HF username: ")
repo_id = f"{username}/aura-tinyllama-uzbek"

api.create_repo(repo_id, exist_ok=True)
api.upload_folder(
    folder_path="./aura-tinyllama-final",
    repo_id=repo_id,
)
print(f"✅ Model: https://huggingface.co/{repo_id}")
```

## Hujayra 10: (Ixtiyoriy) GGUF ga export

```python
# llama.cpp ni o'rnatish va GGUF ga o'tkazish
!git clone https://github.com/ggerganov/llama.cpp
!cd llama.cpp && make -j2

# Hugging Face dan yuklab, GGUF ga convert
!python llama.cpp/convert_hf_to_gguf.py ./aura-tinyllama-final --outfile aura-tinyllama-q4.gguf

# Yuklab olish
from google.colab import files
files.download("aura-tinyllama-q4.gguf")
print("✅ GGUF yuklab olindi!")
```
