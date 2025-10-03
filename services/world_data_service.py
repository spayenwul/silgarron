# services/world_data_service.py
from pathlib import Path
import yaml
import random
from typing import Dict, List, Optional

class WorldDataService:
    """
    Единственный источник правды о данных мира.
    Адаптирован для работы с anatomy.yaml и вашим уникальным лором.
    """
    
    def __init__(self):
        self.data_path = Path("data")
        
        # --- Загружаем все YAML-файлы по ПРАВИЛЬНЫМ путям ---
        self._world_continents = self._load_yaml("world_anatomy.yaml")
        self._location_compatibility = self._load_yaml("location_compatibility.yaml")
        self._anatomy = self._load_yaml("data_tables/anatomy.yaml")
        self._location_templates = self._load_yaml("data_tables/location_templates.yaml")
        
        # --- Индексируем данные для быстрого доступа ---
        self._region_types = {item['id']: item for item in self._anatomy.get("REGION_TYPES", [])}
        self._biomes = {item['id']: item for item in self._anatomy.get("BIOMES", [])}
        self._additional_location_types = self._location_compatibility.get("location_types", {})

    def _load_yaml(self, relative_path: str) -> dict:
        filepath = self.data_path / relative_path
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            print(f"⚠️ Файл не найден: {filepath}. Это может быть нормально, если файл опционален.")
            return {}
        except Exception as e:
            print(f"❌ Ошибка загрузки {filepath}: {e}")
            return {}
    
    # === Методы для Континентов и Регионов ===
    
    def get_continent_data(self, continent_id: str) -> dict:
        return self._world_continents.get("world_continents", {}).get(continent_id, {})

    def get_region_types_for_continent(self, continent_id: str) -> List[dict]:
        continent = self.get_continent_data(continent_id)
        allowed_ids = continent.get("allowed_region_type_ids", [])
        return [self._region_types.get(rid) for rid in allowed_ids if rid in self._region_types]

    # === Умные методы для работы с локациями (биомами) ===

    # <<< --- ВОТ НЕДОСТАЮЩИЙ МЕТОД --- >>>
    def get_location_type_data(self, location_type_id: str) -> dict:
        """
        Умный геттер. Ищет данные сначала в БИОМАХ из anatomy.yaml,
        а если не находит, то в ДОПОЛНИТЕЛЬНЫХ типах из compatibility.yaml.
        """
        if location_type_id in self._biomes:
            return self._biomes[location_type_id]
        if location_type_id in self._additional_location_types:
            return self._additional_location_types[location_type_id]
        return {}
    # <<< --- КОНЕЦ МЕТОДА --- >>>

    def get_location_types_for_region(self, region_type_id: str) -> List[str]:
        """Возвращает список ID биомов/локаций, допустимых в данном регионе."""
        rules = self._location_compatibility.get("biome_rules", {})
        allowed_types = rules.get(region_type_id, {}).get("allowed_types")

        if allowed_types:
            return allowed_types
        
        print(f"⚠️ Для региона '{region_type_id}' не найдены правила в biome_rules. "
              f"Используется фолбэк: все биомы с parent_region_id.")
        
        fallback_types = [
            biome_id for biome_id, biome_data in self._biomes.items()
            if region_type_id in biome_data.get("parent_region_ids", [])
        ]
        
        if "kith_settlement" not in fallback_types:
            fallback_types.append("kith_settlement")
        return fallback_types
    
    def get_location_weight(self, location_type_id: str) -> int:
        """Вес (вероятность появления) берем из compatibility.yaml."""
        data = self._additional_location_types.get(location_type_id, {})
        return data.get("spawn_weight", 1)

    def are_locations_compatible(self, type1_id: str, type2_id: str) -> bool:
        """Проверяет, могут ли два типа локаций граничить друг с другом."""
        rules1 = self._additional_location_types.get(type1_id, {})
        if type2_id in rules1.get("cannot_border", []):
            return False
        
        rules2 = self._additional_location_types.get(type2_id, {})
        if type1_id in rules2.get("cannot_border", []):
            return False
            
        return True
        
    def generate_location_name(self, location_type_id: str) -> str:
        """Генерирует название, предпочитая шаблон, но с фолбэком на имя из anatomy.yaml."""
        templates = self._location_templates.get("templates", {})
        template = templates.get(f"{location_type_id}_template")

        if template and (patterns := template.get("name_patterns")):
            pattern = random.choice(patterns)
            result = pattern
            
            # Перебираем ключи (adjectives, nouns) и их значения из шаблона
            for key, values in template.items():
                if isinstance(values, list) and values:
                    # Создаем плейсхолдер в том же виде, как в YAML (например, {Noun}, {Adjective})
                    # Больше не используем .capitalize()
                    placeholder = f"{{{key.rstrip('s').capitalize()}}}" # nouns -> Noun
                    
                    # Проверяем, есть ли такой плейсхолдер в нашем паттерне
                    if placeholder in result:
                        # Заменяем его на случайное значение
                        result = result.replace(placeholder, random.choice(values))
            return result

        else:
            location_data = self.get_location_type_data(location_type_id)
            return location_data.get("name", f"Неизвестная локация: {location_type_id}")
            