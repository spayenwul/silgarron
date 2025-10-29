"""
Автоматический тюнинг параметров генерации континента

Создает grid search визуализацию для разных комбинаций параметров:
- scale (частота Perlin Noise)
- sea_level (порог океана)
- octaves (количество слоев детализации)

Usage:
    python scripts/tune_continent_parameters.py --param scale
    python scripts/tune_continent_parameters.py --param sea_level
    python scripts/tune_continent_parameters.py --param octaves
    python scripts/tune_continent_parameters.py --full-grid
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import sys
from pathlib import Path
import argparse
from scipy import ndimage

# Добавляем корень проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.world_generator_v2 import WorldGeneratorV2


def tune_scale(seed: str = "tune_test"):
    """Эксперимент с параметром scale (частота шума)"""
    print("\n" + "="*70)
    print("[TUNING] Параметр: scale (частота Perlin Noise)")
    print("="*70)

    # Диапазон значений scale
    scales = [50, 100, 150, 200, 250, 300]

    gen = WorldGeneratorV2()

    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    axes = axes.flatten()

    for i, scale in enumerate(scales):
        print(f"\n[INFO] Генерация с scale={scale}")

        # Временно меняем конфигурацию
        gen.config['continent']['perlin_noise']['scale'] = scale
        continent = gen._generate_continent(seed)

        # Статистика
        land_pct = continent.mask.sum() / (512 * 512) * 100
        labeled, num_islands = ndimage.label(continent.mask)

        # Визуализация
        axes[i].imshow(continent.mask, cmap='gray', origin='lower')
        axes[i].set_title(
            f'scale={scale}\nLand: {land_pct:.1f}%, Islands: {num_islands}',
            fontsize=12,
            fontweight='bold'
        )
        axes[i].axis('off')

        print(f"   Land: {land_pct:.1f}%, Islands: {num_islands}")

    plt.suptitle(
        'Tuning: scale parameter (Perlin Noise frequency)\n' +
        'Lower scale = high frequency (noisy) | Higher scale = low frequency (smooth)',
        fontsize=14,
        fontweight='bold'
    )
    plt.tight_layout()

    # Сохранение
    output_dir = project_root / 'output'
    output_dir.mkdir(exist_ok=True)
    save_path = output_dir / 'tuning_scale.png'

    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"\n[OK] Сохранено: {save_path}")

    plt.show()


def tune_sea_level(seed: str = "tune_test"):
    """Эксперимент с параметром sea_level (порог океана)"""
    print("\n" + "="*70)
    print("[TUNING] Параметр: sea_level (порог океана)")
    print("="*70)

    # Диапазон значений sea_level
    sea_levels = [0.25, 0.30, 0.35, 0.40, 0.45, 0.50]

    gen = WorldGeneratorV2()

    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    axes = axes.flatten()

    for i, sea_level in enumerate(sea_levels):
        print(f"\n[INFO] Генерация с sea_level={sea_level}")

        # Временно меняем конфигурацию
        gen.config['continent']['sea_level'] = sea_level
        continent = gen._generate_continent(seed)

        # Статистика
        land_pct = continent.mask.sum() / (512 * 512) * 100
        ocean_pct = 100 - land_pct

        # Визуализация
        axes[i].imshow(continent.mask, cmap='gray', origin='lower')
        axes[i].set_title(
            f'sea_level={sea_level}\nLand: {land_pct:.1f}%, Ocean: {ocean_pct:.1f}%',
            fontsize=12,
            fontweight='bold'
        )
        axes[i].axis('off')

        print(f"   Land: {land_pct:.1f}%, Ocean: {ocean_pct:.1f}%")

    plt.suptitle(
        'Tuning: sea_level parameter (ocean threshold)\n' +
        'Lower sea_level = more land | Higher sea_level = more ocean',
        fontsize=14,
        fontweight='bold'
    )
    plt.tight_layout()

    # Сохранение
    output_dir = project_root / 'output'
    output_dir.mkdir(exist_ok=True)
    save_path = output_dir / 'tuning_sea_level.png'

    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"\n[OK] Сохранено: {save_path}")

    plt.show()


def tune_octaves(seed: str = "tune_test"):
    """Эксперимент с параметром octaves (слои детализации)"""
    print("\n" + "="*70)
    print("[TUNING] Параметр: octaves (количество слоев детализации)")
    print("="*70)

    # Диапазон значений octaves
    octaves_list = [1, 2, 3, 4]

    gen = WorldGeneratorV2()

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    axes = axes.flatten()

    for i, octaves in enumerate(octaves_list):
        print(f"\n[INFO] Генерация с octaves={octaves}")

        # Временно меняем конфигурацию
        gen.config['continent']['perlin_noise']['octaves'] = octaves
        continent = gen._generate_continent(seed)

        # Статистика
        land_pct = continent.mask.sum() / (512 * 512) * 100

        # Визуализация heightmap (чтобы видеть детали)
        masked_heightmap = np.where(continent.mask, continent.heightmap, np.nan)
        im = axes[i].imshow(masked_heightmap, cmap='terrain', origin='lower')
        axes[i].set_title(
            f'octaves={octaves}\nLand: {land_pct:.1f}%',
            fontsize=12,
            fontweight='bold'
        )
        axes[i].axis('off')
        plt.colorbar(im, ax=axes[i], fraction=0.046)

        print(f"   Land: {land_pct:.1f}%")

    plt.suptitle(
        'Tuning: octaves parameter (detail layers)\n' +
        'More octaves = more detail (hills, valleys)',
        fontsize=14,
        fontweight='bold'
    )
    plt.tight_layout()

    # Сохранение
    output_dir = project_root / 'output'
    output_dir.mkdir(exist_ok=True)
    save_path = output_dir / 'tuning_octaves.png'

    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"\n[OK] Сохранено: {save_path}")

    plt.show()


def full_grid_search():
    """Полный grid search для оптимальных параметров"""
    print("\n" + "="*70)
    print("[TUNING] Full Grid Search (scale x sea_level)")
    print("="*70)

    seed = "grid_test"

    # Диапазоны
    scales = [100, 150, 200]
    sea_levels = [0.30, 0.35, 0.40, 0.45]

    gen = WorldGeneratorV2()

    fig, axes = plt.subplots(len(scales), len(sea_levels), figsize=(20, 15))

    best_score = -1
    best_params = None

    for row, scale in enumerate(scales):
        for col, sea_level in enumerate(sea_levels):
            print(f"\n[INFO] scale={scale}, sea_level={sea_level}")

            # Устанавливаем параметры
            gen.config['continent']['perlin_noise']['scale'] = scale
            gen.config['continent']['sea_level'] = sea_level

            continent = gen._generate_continent(seed)

            # Статистика
            land_pct = continent.mask.sum() / (512 * 512) * 100
            labeled, num_islands = ndimage.label(continent.mask)

            # Метрика качества:
            # - Предпочитаем 60-70% суши
            # - Минимум островов (1-2 компонента)
            land_score = 100 - abs(land_pct - 65) * 2
            island_penalty = num_islands * 10

            score = land_score - island_penalty

            if score > best_score:
                best_score = score
                best_params = {
                    'scale': scale,
                    'sea_level': sea_level,
                    'land_pct': land_pct,
                    'islands': num_islands,
                    'score': score
                }

            # Визуализация
            axes[row, col].imshow(continent.mask, cmap='gray', origin='lower')
            axes[row, col].set_title(
                f's={scale}, sl={sea_level}\n' +
                f'Land={land_pct:.0f}%, I={num_islands}\n' +
                f'Score={score:.0f}',
                fontsize=9
            )
            axes[row, col].axis('off')

            print(f"   Land: {land_pct:.1f}%, Islands: {num_islands}, Score: {score:.0f}")

    plt.suptitle(
        'Full Grid Search: scale x sea_level\n' +
        f'Best: scale={best_params["scale"]}, sea_level={best_params["sea_level"]} ' +
        f'(Land={best_params["land_pct"]:.1f}%, Islands={best_params["islands"]})',
        fontsize=14,
        fontweight='bold'
    )
    plt.tight_layout()

    # Сохранение
    output_dir = project_root / 'output'
    output_dir.mkdir(exist_ok=True)
    save_path = output_dir / 'tuning_grid_search.png'

    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"\n[OK] Сохранено: {save_path}")

    print("\n" + "="*70)
    print("[RESULT] Лучшие параметры:")
    print("="*70)
    for key, value in best_params.items():
        print(f"   {key}: {value}")

    plt.show()

    return best_params


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(
        description='Tune continent generation parameters'
    )
    parser.add_argument(
        '--param',
        type=str,
        choices=['scale', 'sea_level', 'octaves'],
        help='Parameter to tune'
    )
    parser.add_argument(
        '--full-grid',
        action='store_true',
        help='Run full grid search'
    )

    args = parser.parse_args()

    if args.full_grid:
        full_grid_search()
    elif args.param == 'scale':
        tune_scale()
    elif args.param == 'sea_level':
        tune_sea_level()
    elif args.param == 'octaves':
        tune_octaves()
    else:
        print("\n[INFO] Запускаю все тюнинги по умолчанию...")
        print("\n1. Scale tuning:")
        tune_scale()
        print("\n2. Sea level tuning:")
        tune_sea_level()
        print("\n3. Octaves tuning:")
        tune_octaves()


if __name__ == '__main__':
    main()
