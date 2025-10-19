import sys
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from services.world_data_service import WorldDataService
from services.compatibility_service import CompatibilityService

def generate_compatibility_matrix(
    comp_service: CompatibilityService,
    world_data: WorldDataService
) -> dict[str, dict[str, float]]:
    """Генерирует матрицу совместимости для визуализации."""
    matrix = {}
    
    all_races = world_data.get_all_races()
    all_biomes = world_data.get_all_biomes()

    if not all_races:
        print("⚠️ Предупреждение: Расы не найдены. График будет пустым.")
        return {}

    race_ids = [r['id'] for r in all_races]
    
    for race_id in race_ids:
        matrix[race_id] = {}
        for biome_data in all_biomes:
            biome_id = biome_data['id']
            race_data = next((r for r in all_races if r['id'] == race_id), None)
            if race_data:
                score = comp_service.calculate_race_biome_score(race_data, biome_data)
                matrix[race_id][biome_id] = score.raw_score
            
    return matrix

def visualize_compatibility_matrix(matrix: dict[str, dict[str, float]], title: str = "Race-Biome Compatibility"):
    """Создает отсортированную heatmap для выявления паттернов."""
    if not matrix:
        print("❌ Невозможно создать график: нет данных для визуализации.")
        return
        
    try:
        df = pd.DataFrame(matrix).T
        
        # --- СОРТИРОВКА ДАННЫХ ДЛЯ КЛАСТЕРИЗАЦИИ ---
        
        # 1. Считаем средний балл для каждой расы и сортируем их
        race_order = df.mean(axis=1).sort_values().index
        
        # 2. Считаем средний балл для каждого биома и сортируем их
        biome_order = df.mean(axis=0).sort_values().index
        
        # 3. Применяем новый порядок к нашему DataFrame
        df_sorted = df.loc[race_order, biome_order]
        
        # --- КОНЕЦ СОРТИРОВКИ ---

        plt.figure(figsize=(24, 14)) 
        annot_kws = {"size": 8}

        # Используем df_sorted вместо df для отрисовки
        sns.heatmap(df_sorted, 
                    annot=True, 
                    annot_kws=annot_kws,
                    fmt='.2f',          
                    cmap='RdYlGn', 
                    center=1.0, 
                    vmin=-1,
                    vmax=3.0,
                    linewidths=.5,
                    cbar_kws={'label': 'Compatibility Score'})

        plt.title(title + " (Sorted by Compatibility)", fontsize=20) # Добавим в заголовок, что данные отсортированы
        plt.xlabel('Biomes (Sorted by Average Hospitality)', fontsize=14)
        plt.ylabel('Races (Sorted by Average Adaptability)', fontsize=14)
        plt.xticks(rotation=45, ha='right', fontsize=10)
        plt.yticks(rotation=0, fontsize=10)
        plt.tight_layout(pad=2.0)
        print("🖼️  Генерация отсортированной визуализации... Пожалуйста, закройте окно с графиком, чтобы продолжить.")
        plt.show()
        
    except ImportError:
        print("❌ ОШИБКА: Для визуализации установите необходимые библиотеки:")
        print("   pip install matplotlib seaborn pandas")
    except Exception as e:
        print(f"❌ Произошла ошибка при создании графика: {e}")

if __name__ == "__main__":
    print("🚀 Запуск визуализатора совместимости мира...")
    
    # 1. Определяем корень проекта, как и в Jupyter, но более надежным способом
    # Path(__file__) - это путь к текущему файлу скрипта
    project_root = Path(__file__).resolve().parent.parent
    
    # 2. Передаем этот путь в сервис при его создании
    wds = WorldDataService(project_root) 
    
    # Дальше все как обычно
    rules = wds.get_generation_rules()
    cs = CompatibilityService(rules)

    comp_matrix = generate_compatibility_matrix(cs, wds)
    visualize_compatibility_matrix(comp_matrix)
    print("✅ Визуализация завершена.")