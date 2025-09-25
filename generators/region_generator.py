import random
from typing import Dict, Any
from services.world_data_service import WorldDataService
from services.tag_registry_service import TagRegistry

def generate_region_passport_in_context(
    world_data_service: WorldDataService,
    tag_registry: TagRegistry,
    continent_id: str
) -> Dict[str, Any]:
    print(f"--- Генерация региона в контексте континента '{continent_id}' ---")

    continent_data = world_data_service.get_continent_data(continent_id)
    if not continent_data:
        raise ValueError(f"Континент с ID '{continent_id}' не найден.")

    allowed_region_ids = continent_data.get("allowed_region_type_ids", [])
    if not allowed_region_ids:
        raise ValueError(f"Для континента '{continent_id}' не указаны типы регионов.")

    allowed_regions_data = [world_data_service.get_region_type_by_id(rid) for rid in allowed_region_ids if world_data_service.get_region_type_by_id(rid)]

    if not allowed_regions_data:
        raise ValueError(f"Ни один из разрешенных типов регионов для '{continent_id}' не найден в data_tables.")

    weights = [data.get("weight", 1) for data in allowed_regions_data]
    chosen_region_type = random.choices(population=allowed_regions_data, weights=weights, k=1)[0]

    print(f"  -> Выбран тип региона: {chosen_region_type['name']}")

    region_passport = {
        "id": chosen_region_type['id'],
        "name": chosen_region_type['name'],
        "description": chosen_region_type.get("description", ""),
        "tags": chosen_region_type.get("base_tags", []) # ПРЕДУПРЕЖДЕНИЕ: 'base_tags' нужно добавить в YAML!
    }

    # Валидация тегов (хорошая практика)
    for tag in region_passport["tags"]:
        if not tag_registry.validate_tag(tag):
             print(f"⚠️ ВНИМАНИЕ: Тег '{tag}' из региона '{region_passport['id']}' не зарегистрирован!")


    print(f"  -> Паспорт региона создан. Теги: {region_passport['tags']}")
    return region_passport