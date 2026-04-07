from PIL import Image
import os

input_path = "logo.png"
output_path = "static/img/logo.png"

# Agar 'static/img/' papkasi yo'q bo'lsa uni yaratamiz
os.makedirs(os.path.dirname(output_path), exist_ok=True)

try:
    img = Image.open(input_path).convert("RGBA")
    datas = img.getdata()

    new_data = []
    for item in datas:
        # Oq rangga o'xshash (240 dan yuqori) piksellarni shaffof qilish
        if item[0] > 240 and item[1] > 240 and item[2] > 240:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)

    img.putdata(new_data)
    img.save(output_path, "PNG")
    print(f"✅ Tayyor! Shaffof logo quyidagi manzilga saqlandi: {output_path}")
except FileNotFoundError:
    print("❌ Xatolik: 'logo.png' fayli topilmadi. Avval rasmni loyiha papkasiga tashlang.")
except Exception as e:
    print(f"❌ Xatolik yuz berdi: {e}")
