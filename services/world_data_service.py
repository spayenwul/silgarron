from pathlib import Path
import yaml
import random
from typing import Dict, List, Optional, Any

class WorldDataService:
    def __init__(self, project_root_path: Path):
        self.data_path = project_root_path / "data"
        self._world_continents = self._load_yaml("world_anatomy.yaml")
        self._anatomy = self._load_yaml("data_tables/anatomy.yaml")
        self._location_templates = self._load_yaml("data_tables/location_templates.yaml")
        self._generation_rules = self._load_yaml("generation_rules.yaml")
        self._inhabitants = self._load_yaml("data_tables/inhabitants.yaml")
        
        self._region_types = {item['id']: item for item in self._anatomy.get("REGION_TYPES", [])}
        self._races = {item['id']: item for item in self._inhabitants.get("RACES", [])}
        
        # --- ГЛАВНОЕ ИСПРАВЛЕНИЕ: Обогащаем данные биомов при загрузке ---
        self._biomes = {}
        for biome_def in self._anatomy.get("BIOMES", []):
            # Создаем единый список 'tags' из pillar_tags и defining_tags
            biome_def['tags'] = self._extract_tags_from_definition(biome_def)
            self._biomes[biome_def['id']] = biome_def

    def _load_yaml(self, relative_path: str) -> dict:
        # ... (код _load_yaml без изменений)
        filepath = self.data_path / relative_path
        try:
            with open(filepath, 'r', encoding='utf-8') as f: return yaml.safe_load(f) or {}
        except FileNotFoundError:
            print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: Файл не найден: {filepath}.")
            raise
        except Exception as e:
            print(f"❌ Ошибка загрузки {filepath}: {e}")
            return {}

    def _extract_tags_from_definition(self, definition: Dict[str, Any]) -> List[str]:
        """
        НОВЫЙ МЕТОД: Собирает теги из pillar_tags и defining_tags в единый список.
        """
        tags = set()
        # Извлекаем значения из словаря pillar_tags
        for tag_value in definition.get('pillar_tags', {}).values():
            tags.add(tag_value)
        # Добавляем все элементы из списка defining_tags
        tags.update(definition.get('defining_tags', []))
        return list(tags)

    def get_all_races(self) -> List[Dict]:
        return list(self._races.values())

    def get_all_biomes(self) -> List[Dict]:
        """Теперь этот метод возвращает УЖЕ обогащенные данные с ключом 'tags'."""
        return list(self._biomes.values())
        
    def get_biome_data(self, biome_id: str) -> Optional[Dict]:
        return self._biomes.get(biome_id)
    
    # ... (остальные методы сервиса без изменений) ...
    def get_generation_rules(self) -> Dict: return self._generation_rules
    def get_continent_data(self, continent_id: str) -> dict: return self._world_continents.get("world_continents", {}).get(continent_id, {})
    def get_region_types_for_continent(self, continent_id: str) -> List[dict]:
        continent = self.get_continent_data(continent_id)
        allowed_ids = continent.get("allowed_region_type_ids", [])
        return [self._region_types.get(rid) for rid in allowed_ids if rid in self._region_types]
    def get_all_biome_data_for_region(self, region_type_id: str) -> List[Dict]:
        region_preset_key = self._find_preset_key_for_region(region_type_id)
        if not region_preset_key: return self.get_all_biomes()
        region_preset = self._generation_rules.get('region_presets', {}).get(region_preset_key, {})
        allowed_biomes = []
        for biome_id, weight in region_preset.get('biome_distribution', {}).items():
            biome_data = self.get_biome_data(biome_id)
            if biome_data:
                 biome_data_copy = biome_data.copy()
                 biome_data_copy['spawn_weight'] = weight
                 allowed_biomes.append(biome_data_copy)
        return allowed_biomes
    def _find_preset_key_for_region(self, region_type_id: str) -> Optional[str]:
        for key, preset in self._generation_rules.get('region_presets', {}).items():
            if preset.get('region_type') == region_type_id: return key
        return None
    def generate_location_name(self, location_type_id: str) -> str:
        templates = self._location_templates.get("templates", {})
        template = templates.get(f"{location_type_id}_template")
        if template and (patterns := template.get("name_patterns")):
            pattern = random.choice(patterns)
            result = pattern
            for key, values in template.items():
                if isinstance(values, list) and values:
                    placeholder = f"{{{key.rstrip('s').capitalize()}}}"
                    if placeholder in result: result = result.replace(placeholder, random.choice(values))
            return result
        else:
            location_data = self.get_biome_data(location_type_id)
            return location_data.get("name", f"Неизвестная локация: {location_type_id}")