"""
Тест обновлённого FalClient
"""
import asyncio
import os
import sys

# Добавляем корень проекта в путь
sys.path.insert(0, os.path.dirname(__file__))

# API ключ
FAL_API_KEY = "666580cb-bf91-48ea-952b-9c31126cb76d:ca3d5943c73ec5f411ec0774dd638461"


async def test_generate():
    """Тест генерации через FalClient"""
    print("=" * 50)
    print("Тест: FalClient.generate_image()")
    print("=" * 50)
    
    from services.nano_banano.api.fal_client import FalClient
    
    client = FalClient(FAL_API_KEY)
    
    result = await client.generate_image(
        endpoint="fal-ai/nano-banana",
        prompt="A beautiful sunset over mountains, digital art",
        aspect_ratio="16:9",
        output_format="png",
    )
    
    if result.success:
        print(f"✅ Успех!")
        print(f"   URL: {result.image_url}")
        print(f"   Время: {result.generation_time:.2f} сек")
    else:
        print(f"❌ Ошибка: {result.error}")
    
    return result


async def test_generate_pro():
    """Тест Pro версии"""
    print("\n" + "=" * 50)
    print("Тест: FalClient.generate_image() Pro")
    print("=" * 50)
    
    from services.nano_banano.api.fal_client import FalClient
    
    client = FalClient(FAL_API_KEY)
    
    result = await client.generate_image(
        endpoint="fal-ai/nano-banana-pro",
        prompt="A futuristic city at night, neon lights, cyberpunk style",
        aspect_ratio="16:9",
        output_format="png",
        resolution="1K",
    )
    
    if result.success:
        print(f"✅ Успех!")
        print(f"   URL: {result.image_url}")
        print(f"   Время: {result.generation_time:.2f} сек")
    else:
        print(f"❌ Ошибка: {result.error}")
    
    return result


async def main():
    print("\n🍌 Тестирование FalClient\n")
    
    # Тест 1: Базовая генерация
    result1 = await test_generate()
    
    # Тест 2: Pro версия
    result2 = await test_generate_pro()
    
    # Итоги
    print("\n" + "=" * 50)
    print("ИТОГИ")
    print("=" * 50)
    print(f"Nano Banana: {'✅' if result1.success else '❌'}")
    print(f"Nano Banana Pro: {'✅' if result2.success else '❌'}")
    
    if result1.success:
        print(f"\n🖼 Изображение 1: {result1.image_url}")
    if result2.success:
        print(f"🖼 Изображение 2: {result2.image_url}")


if __name__ == "__main__":
    asyncio.run(main())
