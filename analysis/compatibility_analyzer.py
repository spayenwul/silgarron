"""
Углубленный анализ системы совместимости биомов и рас.

Инструменты:
1. Гистограмма распределения очков совместимости
2. Box Plot для анализа расовых предпочтений (специалисты vs универсалы)
3. Статистика синергий и конфликтов
"""

import sys
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from typing import Dict, List, Tuple

# Добавляем корень проекта в путь
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.compatibility_service import CompatibilityService
from services.world_data_service import WorldDataService


class CompatibilityAnalyzer:
    """Анализатор системы совместимости"""

    def __init__(self, wds: WorldDataService, cs: CompatibilityService):
        """Инициализация с передачей готовых сервисов."""
        self.world_data = wds
        self.compat_service = cs
        # Загружаем tags_registry и generation_rules напрямую
        import yaml
        tags_registry_path = PROJECT_ROOT / "data" / "tags_registry.yaml"
        with open(tags_registry_path, 'r', encoding='utf-8') as f:
            tags_registry = yaml.safe_load(f)

        generation_rules_path = PROJECT_ROOT / "data" / "generation_rules.yaml"
        with open(generation_rules_path, 'r', encoding='utf-8') as f:
            generation_rules = yaml.safe_load(f)

        self.compat_service = CompatibilityService(
            tags_registry=tags_registry,
            generation_rules=generation_rules
        )

    def collect_all_biome_compatibility_scores(self) -> List[float]:
        """Собирает все очки совместимости между всеми биомами."""
        scores = []
        all_biomes_data = self.world_data.get_all_biomes()

        print(f"Собираю совместимость для {len(all_biomes_data)} типов биомов...")

        # Проходим по всем уникальным парам биомов
        for i, biome1_data in enumerate(all_biomes_data):
            biome1_tags = set(biome1_data.get("tags", []))

            for biome2_data in all_biomes_data[i+1:]: # i+1 чтобы избежать дублей и сравнения с собой
                biome2_tags = set(biome2_data.get("tags", []))

                # --- ИСПРАВЛЕНИЕ ЗДЕСЬ ---
                # Приводим имена аргументов в соответствие с объявлением в CompatibilityService
                score_obj = self.compat_service.calculate_biome_compatibility(
                    candidate_biome_tags=biome1_tags,
                    neighbor_biomes_tags=[biome2_tags] # Передаем как список из одного соседа
                )
                # --- КОНЕЦ ИСПРАВЛЕНИЯ ---
                
                # ВАЖНО: Мы получаем объект CompatibilityScore, а не просто словарь
                scores.append(score_obj.raw_score)

        return scores

    def plot_compatibility_distribution(self, save_path: str = None):
        """
        Строит гистограмму распределения очков совместимости.

        Интерпретация:
        - Если все scores около 1.0 → правила слишком слабые
        - Несколько пиков → хорошо, есть контраст между совместимыми/несовместимыми

        Args:
            save_path: Путь для сохранения графика (опционально)
        """
        scores = self.collect_all_biome_compatibility_scores()

        plt.figure(figsize=(12, 6))

        # Гистограмма с KDE (kernel density estimate)
        sns.histplot(scores, bins=30, kde=True, color='steelblue', edgecolor='black')

        # Добавляем вертикальные линии для ориентиров
        plt.axvline(x=0.0, color='red', linestyle='--', label='Forbidden (0.0)', linewidth=2)
        plt.axvline(x=1.0, color='orange', linestyle='--', label='Neutral (1.0)', linewidth=2)

        # Статистика
        mean_score = np.mean(scores)
        median_score = np.median(scores)
        std_score = np.std(scores)

        plt.axvline(x=mean_score, color='green', linestyle='-',
                   label=f'Mean ({mean_score:.2f})', linewidth=2)

        plt.title('Distribution of Biome Compatibility Scores', fontsize=16, fontweight='bold')
        plt.xlabel('Compatibility Score', fontsize=12)
        plt.ylabel('Frequency', fontsize=12)
        plt.legend(fontsize=10)
        plt.grid(True, alpha=0.3)

        # Текстовая статистика
        stats_text = f'Stats:\nMean: {mean_score:.2f}\nMedian: {median_score:.2f}\nStd: {std_score:.2f}\nSamples: {len(scores)}'
        plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes,
                fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"График сохранён: {save_path}")

        plt.show()

        # Вывод интерпретации
        self._interpret_distribution(scores, mean_score, std_score)

    def _interpret_distribution(self, scores: List[float], mean: float, std: float):
        """Автоматическая интерпретация распределения"""
        print("\n" + "="*60)
        print("ИНТЕРПРЕТАЦИЯ РАСПРЕДЕЛЕНИЯ")
        print("="*60)

        if std < 0.3:
            print("[!] ПРОБЛЕМА: Очень низкая вариативность (std < 0.3)")
            print("    Правила синергий/конфликтов слишком слабые.")
            print("    Рекомендация: Увеличить bonus/penalty в tags_registry.yaml")
        elif std < 0.5:
            print("[~] ПРЕДУПРЕЖДЕНИЕ: Низкая вариативность (std < 0.5)")
            print("    Контраст между биомами недостаточен.")
        else:
            print("[OK] Хорошая вариативность (std >= 0.5)")
            print("    Система создаёт осмысленные различия между биомами.")

        if 0.8 < mean < 1.2:
            print("\n[~] Средний score близок к нейтральному (1.0)")
            print("    Большинство биомов умеренно совместимы.")
        elif mean < 0.8:
            print("\n[!] Низкий средний score")
            print("    Возможно, слишком много конфликтов.")
        else:
            print("\n[OK] Высокий средний score")
            print("    Биомы имеют тенденцию к совместимости.")

        # Проверка на запрещённые комбинации
        forbidden_count = sum(1 for s in scores if s == 0.0)
        if forbidden_count > 0:
            forbidden_percent = (forbidden_count / len(scores)) * 100
            print(f"\n[INFO] Запрещённые комбинации: {forbidden_count} ({forbidden_percent:.1f}%)")

    def analyze_race_specialization(self, save_path: str = None):
        """
        Анализ специализации рас через Box Plot.

        Интерпретация:
        - Короткий box → раса-универсал (одинаково приспособлена везде)
        - Длинный box с выбросами → раса-специалист (идеальна для 1-2 биомов)

        Args:
            save_path: Путь для сохранения графика
        """
        race_scores = self._collect_race_biome_scores()

        if not race_scores:
            print("Нет данных о расах для анализа")
            return

        # Подготовка данных для box plot
        data_for_plot = []
        race_names = []

        for race_name, scores in race_scores.items():
            data_for_plot.append(scores)
            race_names.append(race_name)

        plt.figure(figsize=(14, 8))

        # Box plot
        bp = plt.boxplot(data_for_plot, labels=race_names, patch_artist=True)

        # Раскрашиваем boxes
        colors = plt.cm.Set3(np.linspace(0, 1, len(race_names)))
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)

        plt.title('Race Specialization Analysis (Box Plot)', fontsize=16, fontweight='bold')
        plt.xlabel('Race', fontsize=12)
        plt.ylabel('Biome Compatibility Score', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.grid(True, alpha=0.3, axis='y')

        # Добавляем горизонтальную линию нейтральной совместимости
        plt.axhline(y=1.0, color='red', linestyle='--', alpha=0.5, label='Neutral (1.0)')
        plt.legend()

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"График сохранён: {save_path}")

        plt.show()

        # Интерпретация
        self._interpret_race_specialization(race_scores)

    def _collect_race_biome_scores(self) -> Dict[str, List[float]]:
        """Собирает scores для каждой расы по всем биомам"""
        all_races_data = self.world_data.get_all_races()
        all_biomes_data = self.world_data.get_all_biomes()

        race_scores = {}

        for race_data in all_races_data:
            race_name = race_data.get("id", "unknown_race")
            scores = []

            for biome_data in all_biomes_data:
                # --- ИСПРАВЛЕНИЕ ЗДЕСЬ ---
                # Передаем полные словари, как того требует метод
                score_obj = self.compat_service.calculate_race_biome_score(
                    race_data=race_data,
                    biome_data=biome_data
                )
                # --- КОНЕЦ ИСПРАВЛЕНИЯ ---

                scores.append(score_obj.raw_score)

            race_scores[race_name] = scores

        return race_scores

    def _interpret_race_specialization(self, race_scores: Dict[str, List[float]]):
        """Интерпретирует результаты специализации рас"""
        print("\n" + "="*60)
        print("АНАЛИЗ СПЕЦИАЛИЗАЦИИ РАС")
        print("="*60)

        for race_name, scores in race_scores.items():
            std = np.std(scores)
            mean = np.mean(scores)
            max_score = np.max(scores)
            min_score = np.min(scores)

            if std < 0.3:
                specialization = "Универсал"
                comment = "Одинаково приспособлена к большинству биомов"
            elif std < 0.6:
                specialization = "Умеренный специалист"
                comment = "Есть предпочтения, но адаптивна"
            else:
                specialization = "Строгий специалист"
                comment = "Критически зависит от определённых биомов"

            print(f"\n{race_name}:")
            print(f"  Тип: {specialization}")
            print(f"  {comment}")
            print(f"  Mean: {mean:.2f}, Std: {std:.2f}")
            print(f"  Range: [{min_score:.2f}, {max_score:.2f}]")

    # Вспомогательные методы

    def _get_all_biome_types(self) -> List[str]:
        """Получает список всех типов биомов из data_tables/anatomy.yaml"""
        import yaml
        anatomy_path = PROJECT_ROOT / "data" / "data_tables" / "anatomy.yaml"
        with open(anatomy_path, 'r', encoding='utf-8') as f:
            anatomy = yaml.safe_load(f)

        biome_types = []
        for region_type_data in anatomy.get("region_types", {}).values():
            biome_types.extend(region_type_data.get("biome_types", []))

        return list(set(biome_types))  # Уникальные

    def _get_biome_tags(self, biome_type: str) -> List[str]:
        """Получает теги для биома"""
        import yaml
        anatomy_path = PROJECT_ROOT / "data" / "data_tables" / "anatomy.yaml"
        with open(anatomy_path, 'r', encoding='utf-8') as f:
            anatomy = yaml.safe_load(f)

        for biome_data in anatomy.get("biome_types", {}).values():
            if biome_data.get("type_id") == biome_type:
                return biome_data.get("tags", [])

        return []

    def _get_biome_config(self, biome_type: str) -> Dict:
        """Получает конфигурацию биома"""
        import yaml
        anatomy_path = PROJECT_ROOT / "data" / "data_tables" / "anatomy.yaml"
        with open(anatomy_path, 'r', encoding='utf-8') as f:
            anatomy = yaml.safe_load(f)

        for biome_data in anatomy.get("biome_types", {}).values():
            if biome_data.get("type_id") == biome_type:
                return biome_data

        return {}

    def _get_race_data(self) -> Dict:
        """Получает данные о расах из inhabitants.yaml"""
        import yaml
        inhabitants_path = PROJECT_ROOT / "data" / "data_tables" / "inhabitants.yaml"
        with open(inhabitants_path, 'r', encoding='utf-8') as f:
            inhabitants = yaml.safe_load(f)
        return inhabitants.get("races", {})


def main():
    """Главная функция для запуска анализов"""
    print("Запуск анализатора совместимости...")

    analyzer = CompatibilityAnalyzer()

    # 1. Анализ распределения совместимости
    print("\n1. Анализ распределения очков совместимости...")
    analyzer.plot_compatibility_distribution(
        save_path="analysis/compatibility_distribution.png"
    )

    # 2. Анализ специализации рас
    print("\n2. Анализ специализации рас...")
    analyzer.analyze_race_specialization(
        save_path="analysis/race_specialization.png"
    )


if __name__ == "__main__":
    main()
