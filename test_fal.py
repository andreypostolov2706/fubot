"""
Тест fal.ai API
"""
import os

# Устанавливаем API ключ
os.environ['FAL_KEY'] = '666580cb-bf91-48ea-952b-9c31126cb76d:ca3d5943c73ec5f411ec0774dd638461'

import fal_client

print("Тестирование fal.ai API...")
print("=" * 50)

try:
    result = fal_client.run(
        "fal-ai/nano-banana",
        arguments={
            "prompt": "A cute cat astronaut floating in space, digital art",
            "num_images": 1,
            "aspect_ratio": "1:1",
            "output_format": "png"
        }
    )
    
    print("✅ Успех!")
    print(f"Результат: {result}")
    
    if "images" in result and result["images"]:
        print(f"\n🖼 URL изображения:")
        print(result["images"][0].get("url", "N/A"))
    
except Exception as e:
    print(f"❌ Ошибка: {e}")
