"""
Утилита для визуализации правил совместимости биомов.

Создаёт графы и таблицы совместимости для отладки и анализа.
"""
import yaml
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict


DATA_DIR = Path(__file__).parent.parent / "data"
TAG_REGISTRY_FILE = DATA_DIR / "tags_registry.yaml"
LOCATION_COMPAT_FILE = DATA_DIR / "location_compatibility.yaml"


def load_tags_registry() -> Dict:
    """Загружает tags_registry.yaml"""
    with open(TAG_REGISTRY_FILE, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_location_compatibility() -> Dict:
    """Загружает location_compatibility.yaml"""
    with open(LOCATION_COMPAT_FILE, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def print_synergies_table():
    """Выводит таблицу всех синергий между тегами"""
    print("\n" + "=" * 80)
    print("ТАБЛИЦА СИНЕРГИЙ")
    print("=" * 80)

    tags_data = load_tags_registry()
    synergies = tags_data.get("global_compatibility_rules", {}).get("synergies", [])

    if not synergies:
        print("Синергии не найдены.")
        return

    print(f"\n{'Теги':<50} {'Бонус':<10} {'Причина'}")
    print("-" * 80)

    for synergy in synergies:
        tags = synergy.get("tags", [])
        bonus = synergy.get("bonus", 0)
        reason = synergy.get("reason", "")

        tags_str = " + ".join(tags)
        print(f"{tags_str:<50} {bonus:<10.1f} {reason}")

    print(f"\nВсего синергий: {len(synergies)}")


def print_conflicts_table():
    """Выводит таблицу всех конфликтов между тегами"""
    print("\n" + "=" * 80)
    print("ТАБЛИЦА КОНФЛИКТОВ")
    print("=" * 80)

    tags_data = load_tags_registry()
    conflicts = tags_data.get("global_compatibility_rules", {}).get("conflicts", [])

    if not conflicts:
        print("Конфликты не найдены.")
        return

    print(f"\n{'Теги':<50} {'Штраф':<10} {'Причина'}")
    print("-" * 80)

    for conflict in conflicts:
        tags = conflict.get("tags", [])
        penalty = conflict.get("penalty", 0)
        reason = conflict.get("reason", "")

        tags_str = " + ".join(tags)
        print(f"{tags_str:<50} {penalty:<10.1f} {reason}")

    print(f"\nВсего конфликтов: {len(conflicts)}")


def print_forbidden_combinations():
    """Выводит все запрещённые комбинации тегов"""
    print("\n" + "=" * 80)
    print("ЗАПРЕЩЁННЫЕ КОМБИНАЦИИ")
    print("=" * 80)

    tags_data = load_tags_registry()
    forbidden = tags_data.get("validation_rules", {}).get("forbidden_combinations", [])

    if not forbidden:
        print("Запрещённые комбинации не найдены.")
        return

    print()
    for idx, combo in enumerate(forbidden, 1):
        print(f"{idx}. {' + '.join(combo)}")

    print(f"\nВсего запрещённых комбинаций: {len(forbidden)}")


def print_biome_compatibility_matrix():
    """Выводит матрицу совместимости биомов (can_border/cannot_border)"""
    print("\n" + "=" * 80)
    print("МАТРИЦА СОВМЕСТИМОСТИ БИОМОВ")
    print("=" * 80)

    loc_compat = load_location_compatibility()
    location_types = loc_compat.get("location_types", {})

    if not location_types:
        print("Типы локаций не найдены.")
        return

    # Собираем статистику
    can_border_count = defaultdict(int)
    cannot_border_count = defaultdict(int)

    for loc_type, rules in location_types.items():
        can_border_count[loc_type] = len(rules.get("can_border", []))
        cannot_border_count[loc_type] = len(rules.get("cannot_border", []))

    # Сортируем по количеству связей
    sorted_types = sorted(
        location_types.keys(),
        key=lambda x: can_border_count[x],
        reverse=True
    )

    print(f"\n{'Тип локации':<30} {'Может граничить':<20} {'Не может граничить':<20}")
    print("-" * 80)

    for loc_type in sorted_types:
        can = can_border_count[loc_type]
        cannot = cannot_border_count[loc_type]
        print(f"{loc_type:<30} {can:<20} {cannot:<20}")

    print(f"\nВсего типов локаций: {len(location_types)}")


def analyze_biome(biome_name: str):
    """Детальный анализ совместимости конкретного биома"""
    print("\n" + "=" * 80)
    print(f"АНАЛИЗ БИОМА: {biome_name}")
    print("=" * 80)

    loc_compat = load_location_compatibility()
    location_types = loc_compat.get("location_types", {})

    if biome_name not in location_types:
        print(f"Биом '{biome_name}' не найден в location_compatibility.yaml")
        return

    rules = location_types[biome_name]

    print(f"\nСвойства биома:")
    print(f"  Spawn Weight: {rules.get('spawn_weight', 'не указан')}")

    can_border = rules.get("can_border", [])
    cannot_border = rules.get("cannot_border", [])

    print(f"\nМОЖЕТ ГРАНИЧИТЬ С ({len(can_border)} типов):")
    for neighbor in sorted(can_border):
        print(f"  - {neighbor}")

    print(f"\nНЕ МОЖЕТ ГРАНИЧИТЬ С ({len(cannot_border)} типов):")
    for neighbor in sorted(cannot_border):
        print(f"  - {neighbor}")

    # Проверяем обратную совместимость
    print(f"\nПРОВЕРКА ОБРАТНОЙ СОВМЕСТИМОСТИ:")
    inconsistencies = []

    for neighbor in can_border:
        if neighbor in location_types:
            neighbor_can_border = location_types[neighbor].get("can_border", [])
            if biome_name not in neighbor_can_border:
                inconsistencies.append((neighbor, "can_border", "отсутствует обратная связь"))

    for neighbor in cannot_border:
        if neighbor in location_types:
            neighbor_cannot_border = location_types[neighbor].get("cannot_border", [])
            if biome_name not in neighbor_cannot_border:
                inconsistencies.append((neighbor, "cannot_border", "отсутствует обратная связь"))

    if inconsistencies:
        print("  ПРЕДУПРЕЖДЕНИЯ:")
        for neighbor, rule_type, reason in inconsistencies:
            print(f"    - {neighbor} ({rule_type}): {reason}")
    else:
        print("  Все связи симметричны")


def main():
    """Главная функция - выводит все таблицы"""
    print("\n" + "=" * 80)
    print("ВИЗУАЛИЗАЦИЯ ПРАВИЛ СОВМЕСТИМОСТИ")
    print("=" * 80)

    print_synergies_table()
    print_conflicts_table()
    print_forbidden_combinations()
    print_biome_compatibility_matrix()

    # Пример детального анализа
    print("\n" + "=" * 80)
    print("ПРИМЕРЫ ДЕТАЛЬНОГО АНАЛИЗА")
    print("=" * 80)

    # Анализируем несколько ключевых биомов
    analyze_biome("kith_settlement")
    analyze_biome("toxic_swamp")


if __name__ == "__main__":
    main()
