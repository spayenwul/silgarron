import yaml
from pathlib import Path
from services.tag_registry_service import TagRegistry

DATA_DIR = Path(__file__).parent / "generators"
TAG_REGISTRY_FILE = DATA_DIR / "tags_registry.yaml"
WORLD_ANATOMY_FILE = DATA_DIR / "world_anatomy.yaml"
# RACE_DATA_FILE = DATA_DIR / "races.yaml" 

def run_validation():
    """
    Главная функция для проверки всех игровых данных на корректность.
    Запускается вручную для проверки целостности мира.
    """
    print("--- Запуск валидации игровых данных ---")
    
    # 1. Инициализируем реестр тегов. Он - наш источник правды.
    tag_registry = TagRegistry(filepath=TAG_REGISTRY_FILE)
    if not tag_registry._all_tags:
        print("🔴 КРИТИЧЕСКАЯ ОШИБКА: Реестр тегов пуст или не загружен. Валидация невозможна.")
        return

    print(f"✅ Реестр тегов загружен. Всего легальных тегов: {len(tag_registry._all_tags)}")
    
    # 2. Валидация world_anatomy.yaml
    print("\n--- Проверка world_anatomy.yaml ---")
    try:
        with open(WORLD_ANATOMY_FILE, 'r', encoding='utf-8') as f:
            world_data = yaml.safe_load(f)
        
        # Проверяем, что все 'allowed_region_type_ids' ссылаются на существующие теги
        # (предполагая, что типы регионов тоже являются тегами в реестре)
        for continent_id, continent_data in world_data.get("world_continents", {}).items():
            for region_type_id in continent_data.get("allowed_region_type_ids", []):
                if not tag_registry.validate_tag(region_type_id):
                    print(f"  🔴 ОШИБКА в континенте '{continent_id}': "
                          f"Нелегальный ID типа региона '{region_type_id}'. Его нет в реестре тегов.")
    except Exception as e:
        print(f"  🔴 Не удалось прочитать или обработать файл: {e}")

    # 3. Валидация файла с расами (пример)
    # print("\n--- Проверка races.yaml ---")
    # try:
    #     # ... код для загрузки файла с расами ...
    #     for race_id, race_data in all_races.items():
    #         # Проверяем основные теги расы
    #         for tag in race_data.get("tags", []):
    #             if not tag_registry.validate_tag(tag):
    #                 print(f"  🔴 ОШИБКА в расе '{race_id}': Нелегальный тег '{tag}'.")
    #         # Проверяем теги в правилах совместимости
    #         for tag in race_data.get("compatibility", {}).get("tags", {}).keys():
    #             if not tag_registry.validate_tag(tag):
    #                 print(f"  🔴 ОШИБКА в расе '{race_id}' (compatibility): Нелегальный тег '{tag}'.")
    
    # except Exception as e:
    #     print(f"  🔴 Не удалось прочитать или обработать файл: {e}")

    print("\n--- Валидация завершена ---")

if __name__ == "__main__":
    run_validation()