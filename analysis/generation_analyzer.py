"""
Анализ результатов процедурной генерации мира.

Этот модуль будет использоваться после реализации SpatialLocationGenerator
для оценки качества и паттернов генерации.

Инструменты:
1. Частотный анализ появления биомов (Bar Chart)
2. Матрица смежности биомов (Adjacency Matrix Heatmap)
3. Сетевой граф мира (NetworkX Visualization)
"""

import sys
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import networkx as nx
from typing import Dict, List, Tuple, Optional
from collections import defaultdict, Counter

# Добавляем корень проекта в путь
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class GenerationAnalyzer:
    """
    Анализатор результатов генерации мира.

    ВНИМАНИЕ: Для работы требуется реализованный SpatialLocationGenerator!
    """

    def __init__(self, generator=None):
        """
        Args:
            generator: Экземпляр SpatialLocationGenerator (опционально)
        """
        self.generator = generator
        self.generation_results = []  # Хранилище результатов для анализа

    def run_frequency_analysis(
        self,
        n_iterations: int = 1000,
        region_type: str = "dermal_plateau",
        save_path: str = None
    ):
        """
        Запускает генерацию N раз и анализирует частоту появления биомов.

        Вопрос: "Случайность работает так, как ожидается?"

        Args:
            n_iterations: Количество прогонов генерации
            region_type: Тип региона для генерации
            save_path: Путь для сохранения графика
        """
        if not self.generator:
            print("[!] ОШИБКА: SpatialLocationGenerator не инициализирован")
            print("    Создайте mock-данные или реализуйте генератор")
            self._demo_frequency_analysis(save_path=save_path)
            return

        print(f"Запуск {n_iterations} итераций генерации...")

        biome_counts = Counter()

        for i in range(n_iterations):
            if i % 100 == 0:
                print(f"  Прогресс: {i}/{n_iterations}")

            # TODO: Заменить на реальный вызов после реализации генератора
            # region = self.generator.generate_starting_region(region_type)
            # for location in region.locations:
            #     biome_counts[location.biome_type] += 1

        self._plot_frequency_chart(biome_counts, n_iterations, save_path)

    def _demo_frequency_analysis(self, save_path=None):
        """Демо-режим с mock данными для иллюстрации"""
        print("\nДЕМО-РЕЖИМ: Используются mock-данные\n")

        # Mock данные (как будто сгенерировали 1000 регионов)
        mock_biome_counts = {
            "pulsating_plains": 450,
            "spore_savanna": 250,
            "megatherium_pastures": 200,
            "geyser_fields": 80,
            "crystal_scar": 20
        }

        self._plot_frequency_chart(mock_biome_counts, 1000,
                                   save_path=save_path)

    def _plot_frequency_chart(
        self,
        biome_counts: Dict[str, int],
        total_iterations: int,
        save_path: str = None
    ):
        """Строит столбчатую диаграмму частот"""
        if not biome_counts:
            print("Нет данных для анализа")
            return

        # Сортируем по частоте (от большего к меньшему)
        sorted_biomes = sorted(biome_counts.items(), key=lambda x: x[1], reverse=True)
        biome_names = [b[0] for b in sorted_biomes]
        counts = [b[1] for b in sorted_biomes]
        percentages = [(c / total_iterations) * 100 for c in counts]

        plt.figure(figsize=(14, 8))

        # Столбчатая диаграмма
        bars = plt.bar(range(len(biome_names)), percentages, color='steelblue', edgecolor='black')

        # Раскрашиваем столбики по градиенту
        colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(biome_names)))
        for bar, color in zip(bars, colors):
            bar.set_color(color)

        plt.xlabel('Biome Type', fontsize=12)
        plt.ylabel('Frequency (%)', fontsize=12)
        plt.title(f'Biome Frequency Distribution (N={total_iterations})',
                 fontsize=16, fontweight='bold')
        plt.xticks(range(len(biome_names)), biome_names, rotation=45, ha='right')
        plt.grid(True, alpha=0.3, axis='y')

        # Добавляем значения на столбики
        for i, (count, pct) in enumerate(zip(counts, percentages)):
            plt.text(i, pct + 1, f'{pct:.1f}%\n({count})',
                    ha='center', va='bottom', fontsize=9)

        plt.tight_layout()

        if save_path:
            save_path_obj = Path(save_path)
            # Создаем родительскую директорию ('analysis/results/'), если ее нет
            save_path_obj.parent.mkdir(parents=True, exist_ok=True)            
            plt.savefig(save_path_obj, dpi=300, bbox_inches='tight')
            print(f"График сохранён: {save_path_obj}")

        plt.show()

        # Интерпретация
        self._interpret_frequency(biome_counts, percentages)

    def _interpret_frequency(self, biome_counts: Dict, percentages: List[float]):
        """Интерпретирует результаты частотного анализа"""
        print("\n" + "="*60)
        print("ИНТЕРПРЕТАЦИЯ ЧАСТОТНОГО АНАЛИЗА")
        print("="*60)

        max_pct = max(percentages)
        min_pct = min(percentages)

        if max_pct > 60:
            print(f"[!] ПРОБЛЕМА: Один биом доминирует ({max_pct:.1f}%)")
            print("    Возможно, его spawn_weight слишком высок")
        elif min_pct < 1:
            print(f"[~] ПРЕДУПРЕЖДЕНИЕ: Редкие биомы почти не появляются ({min_pct:.1f}%)")
            print("    Проверьте spawn_weight и правила совместимости")
        else:
            print("[OK] Распределение биомов выглядит сбалансированным")

        # Коэффициент вариации
        cv = np.std(percentages) / np.mean(percentages)
        print(f"\nКоэффициент вариации: {cv:.2f}")
        if cv > 1.0:
            print("  -> Высокая неравномерность (может быть задуманным)")
        else:
            print("  -> Умеренная неравномерность")

    def analyze_adjacency_matrix(
        self,
        world_graph: Dict,
        save_path: str = None
    ):
        """
        Анализирует паттерны соседства биомов.

        Вопрос: "Какие биомы часто граничат друг с другом?"

        Args:
            world_graph: Граф мира (dict с location_id -> location_data)
            save_path: Путь для сохранения матрицы
        """
        if not world_graph:
            print("[!] ОШИБКА: Пустой граф мира")
            self._demo_adjacency_matrix(save_path=save_path)
            return

        # Строим матрицу смежности
        adjacency_matrix = self._build_adjacency_matrix(world_graph)

        self._plot_adjacency_heatmap(adjacency_matrix, save_path)

    def _demo_adjacency_matrix(self, save_path):
        """Демо-режим с mock данными"""
        print("\nДЕМО-РЕЖИМ: Используются mock-данные\n")

        # Mock матрица смежности
        biomes = ["plains", "savanna", "pastures", "geyser", "scar"]
        matrix = np.array([
            [0, 45, 30, 10, 5],   # plains
            [45, 0, 25, 15, 8],   # savanna
            [30, 25, 0, 12, 3],   # pastures
            [10, 15, 12, 0, 20],  # geyser
            [5, 8, 3, 20, 0]      # scar
        ])

        self._plot_adjacency_heatmap(
            {"biomes": biomes, "matrix": matrix},
            save_path=save_path
        )

    def _build_adjacency_matrix(self, world_graph: Dict) -> Dict:
        """Строит матрицу смежности из графа мира"""
        # TODO: Реализовать после создания SpatialLocationGenerator
        pass

    def _plot_adjacency_heatmap(self, adjacency_data: Dict, save_path: str = None):
        """Строит тепловую карту матрицы смежности"""
        biomes = adjacency_data["biomes"]
        matrix = adjacency_data["matrix"]

        plt.figure(figsize=(12, 10))

        # Heatmap
        sns.heatmap(
            matrix,
            annot=True,
            fmt='d',
            cmap='YlOrRd',
            xticklabels=biomes,
            yticklabels=biomes,
            cbar_kws={'label': 'Number of Adjacencies'},
            linewidths=0.5
        )

        plt.title('Biome Adjacency Matrix', fontsize=16, fontweight='bold')
        plt.xlabel('Adjacent Biome', fontsize=12)
        plt.ylabel('Source Biome', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)

        plt.tight_layout()

        if save_path:
            save_path_obj = Path(save_path)
            save_path_obj.parent.mkdir(parents=True, exist_ok=True)

            plt.savefig(save_path_obj, dpi=300, bbox_inches='tight')
            print(f"Матрица сохранена: {save_path_obj}")

        plt.show()

        print("\n[INFO] Матрица смежности показывает, как часто биомы граничат.")
        print("       Высокие значения -> частое соседство")
        print("       Низкие значения -> редкое или запрещённое соседство")

    def visualize_world_graph(
        self,
        world_graph: Dict,
        layout: str = "spring",
        save_path: str = None
    ):
        """
        Визуализирует граф мира через NetworkX.

        Самый мощный инструмент! Показывает:
        - Изолированные зоны
        - Центральные хабы
        - Кластеры биомов

        Args:
            world_graph: Граф мира
            layout: Тип layout ("spring", "circular", "kamada_kawai")
            save_path: Путь для сохранения графа
        """
        if not world_graph:
            print("[!] ОШИБКА: Пустой граф мира")
            self._demo_network_graph(save_path=save_path)
            return

        # TODO: Реализовать после SpatialLocationGenerator
        pass

    def _demo_network_graph(self, save_path):
        """Демо-режим с mock данными"""
        print("\nДЕМО-РЕЖИМ: Создаю mock граф мира\n")

        # Создаём демо-граф
        G = nx.Graph()

        # Mock локации
        locations = {
            1: "plains", 2: "plains", 3: "savanna", 4: "savanna",
            5: "pastures", 6: "geyser", 7: "geyser", 8: "scar"
        }

        # Добавляем узлы с цветами
        biome_colors = {
            "plains": "#90EE90",
            "savanna": "#FFD700",
            "pastures": "#87CEEB",
            "geyser": "#FF6347",
            "scar": "#8B008B"
        }

        for loc_id, biome in locations.items():
            G.add_node(loc_id, biome=biome, color=biome_colors[biome])

        # Добавляем рёбра (соседства)
        edges = [(1,2), (2,3), (3,4), (4,5), (5,6), (6,7), (7,8), (1,3), (2,4), (5,7)]
        G.add_edges_from(edges)

        # Визуализация
        plt.figure(figsize=(14, 10))

        pos = nx.spring_layout(G, k=2, iterations=50, seed=42)

        node_colors = [G.nodes[node]["color"] for node in G.nodes()]

        nx.draw(
            G,
            pos,
            node_color=node_colors,
            node_size=800,
            with_labels=True,
            font_size=10,
            font_weight='bold',
            edge_color='gray',
            width=2,
            alpha=0.9
        )

        # Легенда
        from matplotlib.patches import Patch
        legend_elements = [Patch(facecolor=color, label=biome)
                          for biome, color in biome_colors.items()]
        plt.legend(handles=legend_elements, loc='upper right', fontsize=10)

        plt.title('World Graph Visualization (DEMO)', fontsize=16, fontweight='bold')
        plt.axis('off')
        plt.tight_layout()

        plt.savefig(save_path, dpi=300, bbox_inches='tight') 
        print(f"Граф сохранён: {save_path}")

        plt.show()

        # Статистика графа
        print("\n" + "="*60)
        print("СТАТИСТИКА ГРАФА")
        print("="*60)
        print(f"Узлов (локаций): {G.number_of_nodes()}")
        print(f"Рёбер (соседств): {G.number_of_edges()}")
        print(f"Средняя степень: {np.mean([d for n, d in G.degree()]):.2f}")
        print(f"Диаметр графа: {nx.diameter(G)}")
        print(f"Компоненты связности: {nx.number_connected_components(G)}")


def main():
    """Главная функция для демо-режима"""
    print("="*60)
    print("АНАЛИЗАТОР ГЕНЕРАЦИИ МИРА (DEMO MODE)")
    print("="*60)
    print("\nВНИМАНИЕ: Используются mock-данные")
    print("После реализации SpatialLocationGenerator замените на реальные данные\n")

    analyzer = GenerationAnalyzer()

    # 1. Частотный анализ
    print("1. Частотный анализ биомов...")
    analyzer.run_frequency_analysis()

    # 2. Матрица смежности
    print("\n2. Матрица смежности...")
    analyzer.analyze_adjacency_matrix(world_graph=None)

    # 3. Сетевой граф
    print("\n3. Визуализация графа мира...")
    analyzer.visualize_world_graph(world_graph=None)

    print("\n" + "="*60)
    print("АНАЛИЗ ЗАВЕРШЁН")
    print("="*60)
    print("\nВсе графики сохранены в директории analysis/")


if __name__ == "__main__":
    main()
