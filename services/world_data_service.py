import yaml
from pathlib import Path
from typing import Dict, List, Any

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_TABLES_DIR = DATA_DIR / "data_tables"

class WorldDataService:
    def __init__(self):
        print("⚙️ Загрузка всех данных мира...")
        self._world_continents = self._load_yaml(DATA_DIR / "world_anatomy.yaml").get("world_continents", {})

        # Загружаем все таблицы
        anatomy = self._load_yaml(DATA_TABLES_DIR / "anatomy.yaml")
        # ... можно добавить загрузку economy, history и т.д. по необходимости

        # Преобразуем списки в словари для быстрого доступа по ID
        self._region_types = {item['id']: item for item in anatomy.get("REGION_TYPES", [])}
        self._biomes = {item['id']: item for item in anatomy.get("BIOMES", [])}
        self._landmarks = {item['id']: item for item in anatomy.get("LANDMARKS", [])}
        print("✅ Данные об анатомии мира успешно загружены.")

    def _load_yaml(self, filepath: Path) -> Dict:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"🔴 ОШИБКА: Не удалось загрузить YAML файл {filepath}: {e}")
            return {}

    def get_continent_data(self, continent_id: str) -> Dict[str, Any] | None:
        return self._world_continents.get(continent_id)

    def get_region_type_by_id(self, region_type_id: str) -> Dict[str, Any] | None:
        return self._region_types.get(region_type_id)

    # В будущем здесь появятся другие геттеры, например:
    # def get_compatible_biomes_for_region(self, region_id: str) -> List[Dict]:
    #     ...