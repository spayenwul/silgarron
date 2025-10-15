import yaml
from pathlib import Path
from services.tag_registry_service import TagRegistry

DATA_DIR = Path(__file__).parent / "data"
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
        print("[!] КРИТИЧЕСКАЯ ОШИБКА: Реестр тегов пуст или не загружен. Валидация невозможна.")
        return

    print(f"[OK] Реестр тегов загружен. Всего легальных тегов: {len(tag_registry._all_tags)}")
    
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
                    print(f"  [!] ОШИБКА в континенте '{continent_id}': "
                          f"Нелегальный ID типа региона '{region_type_id}'. Его нет в реестре тегов.")
    except Exception as e:
        print(f"  [!] Не удалось прочитать или обработать файл: {e}")

    # 3. Валидация правил совместимости
    print("\n--- Проверка глобальных правил совместимости ---")
    try:
        with open(TAG_REGISTRY_FILE, 'r', encoding='utf-8') as f:
            tags_data = yaml.safe_load(f)

        compatibility_rules = tags_data.get("global_compatibility_rules", {})

        # Проверяем synergies
        synergies = compatibility_rules.get("synergies", [])
        for idx, synergy in enumerate(synergies):
            tags = synergy.get("tags", [])
            if not tags or len(tags) < 2:
                print(f"  [!] ОШИБКА в synergy #{idx}: Недостаточно тегов (нужно минимум 2)")
                continue

            for tag in tags:
                if not tag_registry.validate_tag(tag):
                    print(f"  [!] ОШИБКА в synergy #{idx}: Нелегальный тег '{tag}'")

            if "bonus" not in synergy:
                print(f"  [!] ОШИБКА в synergy #{idx}: Отсутствует поле 'bonus'")
            elif not isinstance(synergy["bonus"], (int, float)) or synergy["bonus"] <= 0:
                print(f"  [!] ОШИБКА в synergy #{idx}: bonus должен быть положительным числом")

        print(f"  [OK] Проверено синергий: {len(synergies)}")

        # Проверяем conflicts
        conflicts = compatibility_rules.get("conflicts", [])
        for idx, conflict in enumerate(conflicts):
            tags = conflict.get("tags", [])
            if not tags or len(tags) < 2:
                print(f"  [!] ОШИБКА в conflict #{idx}: Недостаточно тегов (нужно минимум 2)")
                continue

            for tag in tags:
                if not tag_registry.validate_tag(tag):
                    print(f"  [!] ОШИБКА в conflict #{idx}: Нелегальный тег '{tag}'")

            if "penalty" not in conflict:
                print(f"  [!] ОШИБКА в conflict #{idx}: Отсутствует поле 'penalty'")
            elif not isinstance(conflict["penalty"], (int, float)) or conflict["penalty"] < 0 or conflict["penalty"] > 1:
                print(f"  [!] ОШИБКА в conflict #{idx}: penalty должен быть в диапазоне [0.0, 1.0]")

        print(f"  [OK] Проверено конфликтов: {len(conflicts)}")

    except Exception as e:
        print(f"  [!] Не удалось проверить правила совместимости: {e}")

    # 4. Валидация forbidden_combinations
    print("\n--- Проверка forbidden_combinations ---")
    try:
        validation_rules = tags_data.get("validation_rules", {})
        forbidden = validation_rules.get("forbidden_combinations", [])

        for idx, combo in enumerate(forbidden):
            if not isinstance(combo, list) or len(combo) < 2:
                print(f"  [!] ОШИБКА в forbidden combination #{idx}: Должен быть список из минимум 2 тегов")
                continue

            for tag in combo:
                if not tag_registry.validate_tag(tag):
                    print(f"  [!] ОШИБКА в forbidden combination #{idx}: Нелегальный тег '{tag}'")

        print(f"  [OK] Проверено запрещённых комбинаций: {len(forbidden)}")

    except Exception as e:
        print(f"  [!] Не удалось проверить forbidden_combinations: {e}")

    # 5. Валидация location_compatibility.yaml
    print("\n--- Проверка location_compatibility.yaml ---")
    try:
        loc_compat_file = DATA_DIR / "location_compatibility.yaml"
        with open(loc_compat_file, 'r', encoding='utf-8') as f:
            loc_compat = yaml.safe_load(f)

        location_types = loc_compat.get("location_types", {})
        for loc_type, rules in location_types.items():
            # Проверяем can_border
            for border_type in rules.get("can_border", []):
                if border_type not in location_types:
                    print(f"  [!] ПРЕДУПРЕЖДЕНИЕ в '{loc_type}': can_border содержит неизвестный тип '{border_type}'")

            # Проверяем cannot_border
            for border_type in rules.get("cannot_border", []):
                if border_type not in location_types:
                    print(f"  [!] ПРЕДУПРЕЖДЕНИЕ в '{loc_type}': cannot_border содержит неизвестный тип '{border_type}'")

        print(f"  [OK] Проверено типов локаций: {len(location_types)}")

    except Exception as e:
        print(f"  [!] Не удалось проверить location_compatibility.yaml: {e}")

    print("\n--- Валидация завершена ---")

if __name__ == "__main__":
    run_validation()