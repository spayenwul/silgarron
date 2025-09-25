import random
from typing import Dict, Any

# Пока что у нас нет данных о локациях, поэтому генератор будет очень простым.
# Он просто выберет биом, который подходит для сгенерированного региона.
# Это ЗАГЛУШКА, которую мы разовьём в Фазе II Roadmap.

def generate_location_passport(
    region_passport: Dict[str, Any],
    tag_registry: object, # Пока не используется, но оставляем для совместимости
    world_data_service: object # Пока не используется
) -> Dict[str, Any]:
    print(f"--- Генерация локации-заглушки в регионе '{region_passport['name']}' ---")

    # В будущем здесь будет сложная логика выбора из location_blueprints
    # А пока просто создаем локацию, которая наследует имя и теги региона
    location_name = f"Неизведанная часть '{region_passport['name']}'"

    location_passport = {
        "name": location_name,
        "description": "Это место еще предстоит исследовать и описать...",
        "tags": region_passport.get("tags", []) + ["неизведанное"]
    }
    
    print(f"  -> Паспорт локации-заглушки создан. Теги: {location_passport['tags']}")
    return location_passport