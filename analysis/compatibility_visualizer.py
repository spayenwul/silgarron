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
LOCATION_COMPAT_FILE = DATA_DIR / "generation_rules.yaml"


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
    """Выводит статистику из generation_rules.yaml"""
    print("\n" + "=" * 80)
    print("СТАТИСТИКА ИЗ GENERATION_RULES")
    print("=" * 80)

    gen_rules = load_location_compatibility()

    # Показываем race_terrain_affinity
    race_affinity = gen_rules.get("global_modifiers", {}).get("race_terrain_affinity", {})

    if race_affinity:
        # Убираем description из списка
        races = [k for k in race_affinity.keys() if k != "description"]
        print("\nРАСОВЫЕ ПРЕДПОЧТЕНИЯ МЕСТНОСТИ:")
        print(f"Найдено рас: {len(races)}")
        for race_name in races[:5]:  # Показываем первые 5
            print(f"  - {race_name}")
        if len(races) > 5:
            print(f"  ... и ещё {len(races) - 5}")

    # Показываем border rules
    border_rules = gen_rules.get("biome_border_rules", {})
    smooth = border_rules.get("smooth_transitions", [])
    sharp = border_rules.get("sharp_transitions", [])
    buffers = border_rules.get("mandatory_buffers", [])

    print(f"\nПРАВИЛА ГРАНИЦ БИОМОВ:")
    print(f"  Плавные переходы: {len(smooth)}")
    print(f"  Резкие границы: {len(sharp)}")
    print(f"  Обязательные буферы: {len(buffers)}")

    # Показываем region presets
    presets = gen_rules.get("region_presets", {})
    if presets:
        # Убираем description из списка
        preset_items = [(k, v) for k, v in presets.items() if k != "description" and isinstance(v, dict)]
        print(f"\nПРЕСЕТЫ РЕГИОНОВ: {len(preset_items)}")
        for preset_id, preset_data in preset_items[:3]:
            name = preset_data.get("name", preset_id)
            region_type = preset_data.get("region_type", "unknown")
            print(f"  - {name} ({region_type})")


def analyze_race_affinity(race_name: str):
    """Детальный анализ предпочтений расы"""
    print("\n" + "=" * 80)
    print(f"АНАЛИЗ РАСЫ: {race_name}")
    print("=" * 80)

    gen_rules = load_location_compatibility()
    race_affinity = gen_rules.get("global_modifiers", {}).get("race_terrain_affinity", {})

    if race_name not in race_affinity:
        print(f"Раса '{race_name}' не найдена в generation_rules.yaml")
        available = list(race_affinity.keys())[:10]
        print(f"\nДоступные расы: {', '.join(available)}")
        if len(race_affinity) > 10:
            print(f"... и ещё {len(race_affinity) - 10}")
        return

    preferences = race_affinity[race_name]

    print(f"\nПРЕДПОЧТЕНИЯ МЕСТНОСТИ:")

    # Сортируем по значению модификатора
    sorted_prefs = sorted(preferences.items(), key=lambda x: x[1], reverse=True)

    print(f"\n{'Тег':<40} {'Модификатор':<15}")
    print("-" * 55)

    for tag, modifier in sorted_prefs:
        if modifier >= 2.0:
            status = "Очень любит"
        elif modifier >= 1.5:
            status = "Предпочитает"
        elif modifier >= 1.0:
            status = "Нейтрально"
        elif modifier >= 0.5:
            status = "Избегает"
        else:
            status = "Непригодно"

        print(f"{tag:<40} {modifier:<8.1f} ({status})")

    print(f"\nВсего предпочтений: {len(preferences)}")


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

    # Анализируем несколько ключевых рас
    analyze_race_affinity("kith")
    analyze_race_affinity("fen-kin")


if __name__ == "__main__":
    main()
