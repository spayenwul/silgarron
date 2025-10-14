import sys
from pathlib import Path

# Добавляем корневую папку проекта в sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from services.world_data_service import WorldDataService
from services.compatibility_service import CompatibilityService
from collections import defaultdict

def validate_compatibility_rules(
    comp_service: CompatibilityService,
    world_data: WorldDataService
) -> list[str]:
    print("🚀 Запуск УГЛУБЛЕННОЙ валидации правил генерации мира...")
    issues = []
    
    all_races = world_data.get_all_races()
    all_biomes = world_data.get_all_biomes()

    if not all_races or not all_biomes:
        issues.append("🔴 КРИТИЧЕСКАЯ ПРОБЛЕМА: Не найдены расы или биомы!")
        return issues

    # --- УЛУЧШЕНИЕ: Создаем словари для хранения списков совместимости ---
    race_to_biomes = defaultdict(list)
    biome_to_races = defaultdict(list)

    # --- Единый проход для сбора всех данных ---
    for race_data in all_races:
        race_id = race_data['id']
        for biome_data in all_biomes:
            biome_id = biome_data['id']
            score = comp_service.calculate_race_biome_score(race_data, biome_data)
            if score.is_compatible:
                race_to_biomes[race_id].append(biome_id)
                biome_to_races[biome_id].append(race_id)

    # --- Проверка и вывод жизнеспособности рас ---
    print("\n--- Проверка жизнеспособности рас ---")
    for race_id in sorted(race_to_biomes.keys()):
        compatible_biomes = race_to_biomes[race_id]
        compatible_count = len(compatible_biomes)
        
        print(f"\n  - Раса '{race_id}': найдено {compatible_count} подходящих биомов.")
        # Выводим список биомов для наглядности
        print(f"    └─ Совместимые биомы: {', '.join(sorted(compatible_biomes))}")

        if compatible_count == 0:
            issues.append(f"🔴 КРИТИЧЕСКАЯ ПРОБЛЕМА: Раса '{race_id}' не имеет СОВМЕСТИМЫХ биомов!")
        elif compatible_count < 3:
            issues.append(f"🟡 ПРЕДУПРЕЖДЕНИЕ: У расы '{race_id}' очень мало ({compatible_count}) совместимых биомов.")

    # --- Проверка и вывод заселяемости биомов ---
    print("\n\n--- Проверка заселяемости биомов ---")
    # Сортируем биомы для последовательного вывода
    for biome_id in sorted([b['id'] for b in all_biomes]):
        compatible_races = biome_to_races[biome_id]
        compatible_count = len(compatible_races)

        print(f"\n  - Биом '{biome_id}': могут заселить {compatible_count} рас.")
        # Выводим список рас для наглядности
        if compatible_races:
            print(f"    └─ Совместимые расы: {', '.join(sorted(compatible_races))}")
        else:
            print(f"    └─ 🔴 Нет совместимых рас!")


        if compatible_count == 0:
            issues.append(f"🟡 ПРЕДУПРЕЖДЕНИЕ: Биом '{biome_id}' не может быть заселен ни одной из известных рас.")
            
    return issues

if __name__ == "__main__":
    try:
        wds = WorldDataService()
        rules = wds.get_generation_rules()
        cs = CompatibilityService(rules)
        
        validation_issues = validate_compatibility_rules(cs, wds)
        
        print("\n\n========================================")
        print("✅ Валидация завершена.")
        if validation_issues:
            print("\nНайдены следующие проблемы:")
            for i, issue in enumerate(validation_issues, 1):
                print(f"  {i}. {issue}")
        else:
            print("\n🎉 Проблем не найдено. Правила выглядят сбалансированными!")
        print("========================================")
    except Exception as e:
        print(f"\n❌ Произошла ошибка во время валидации: {e}")
        import traceback
        traceback.print_exc()