"""
Визуализатор для Sprint 3.6 - Phase 2: Генерация континента

Демонстрирует:
- Perlin Noise heightmap
- Spine path (если включен spine-based generation)
- Continent mask (суша vs океан)
- Геометрия континента (центр, ось, хребет)

Usage:
    # Стандартная генерация (без shape mask)
    python scripts/visualize_continent.py --seed silgarron_alpha_01

    # Со spine-based generation
    python scripts/visualize_continent.py --seed silgarron_alpha_01 --spine

    # Сравнение нескольких seeds
    python scripts/visualize_continent.py --compare seed_A seed_B seed_C

    # Сравнение spine vs no-spine
    python scripts/visualize_continent.py --seed my_seed --compare-modes
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import sys
from pathlib import Path
import argparse

# Добавляем корень проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.world_generator_v2 import WorldGeneratorV2


def visualize_continent(seed: str, enable_spine: bool = False, save_path: str = None):
    """
    Визуализирует генерацию континента с Perlin Noise

    Args:
        seed: Строка-seed для генерации
        enable_spine: Включить spine-based generation
        save_path: Путь для сохранения (None = автоматически)
    """
    print("\n" + "="*70)
    print(f"[CONTINENT] Генерация континента: seed='{seed}'")
    if enable_spine:
        print("[MODE] Spine-Based Generation (anatomy -> geography)")
    else:
        print("[MODE] Standard Generation (pure Perlin Noise)")
    print("="*70)

    # Генерируем континент
    gen = WorldGeneratorV2()

    # Настраиваем режим
    if enable_spine:
        gen.config['continent']['shape_mask']['enabled'] = True
        gen.config['continent']['shape_mask']['type'] = 'spine'
    else:
        gen.config['continent']['shape_mask']['enabled'] = False

    continent = gen._generate_continent(seed)

    # Статистика
    land_count = continent.mask.sum()
    ocean_count = (~continent.mask).sum()
    total = 512 * 512
    land_pct = land_count / total * 100
    ocean_pct = ocean_count / total * 100

    has_spine = continent.spine_path is not None

    print(f"\n[INFO] Статистика континента:")
    print(f"   Суша: {land_count:,} пикселей ({land_pct:.1f}%)")
    print(f"   Океан: {ocean_count:,} пикселей ({ocean_pct:.1f}%)")
    print(f"   Центр масс: {continent.center}")
    print(f"   Главная ось: {continent.major_axis}")
    if has_spine:
        print(f"   Spine path: {continent.spine_path.shape[0]} точек")

    # Длина оси
    (x1, y1), (x2, y2) = continent.major_axis
    axis_length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    print(f"   Длина главной оси: {axis_length:.1f} пикселей")

    # Подсчет островов
    from scipy import ndimage
    labeled, num_islands = ndimage.label(continent.mask)
    print(f"   Количество связных компонент: {num_islands}")

    # Проверяем океан на краях
    edge_pixels = np.concatenate([
        continent.mask[0, :],
        continent.mask[-1, :],
        continent.mask[:, 0],
        continent.mask[:, -1]
    ])
    ocean_edge_pct = (1 - edge_pixels.sum() / len(edge_pixels)) * 100
    print(f"   Океан на краях карты: {ocean_edge_pct:.1f}%")

    # Создаем визуализацию
    print("\n[INFO] Создание визуализации...")
    fig, axes = plt.subplots(2, 2, figsize=(16, 14))

    # 1. Heightmap (raw Perlin Noise)
    im1 = axes[0, 0].imshow(continent.heightmap, cmap='terrain', origin='lower')
    axes[0, 0].set_title('1. Perlin Noise Heightmap', fontsize=14, fontweight='bold')
    axes[0, 0].axis('off')
    plt.colorbar(im1, ax=axes[0, 0], label='Elevation [0, 1]', fraction=0.046)

    # Показываем sea_level
    config = gen.config_manager
    sea_level_used = gen.config['continent']['shape_mask'].get('sea_level_override', config.get_sea_level()) \
                     if enable_spine else config.get_sea_level()

    axes[0, 0].text(
        10, 490,
        f'Sea Level: {sea_level_used}\n' +
        f'Params:\n' +
        f'  scale={config.get_perlin_params()["scale"]}\n' +
        f'  octaves={config.get_perlin_params()["octaves"]}',
        fontsize=10,
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
        verticalalignment='top'
    )

    # Если есть spine, рисуем его
    if has_spine:
        axes[0, 0].plot(continent.spine_path[:, 0], continent.spine_path[:, 1],
                       'r-', linewidth=2, alpha=0.5, label='Spine')
        axes[0, 0].legend(loc='upper right', fontsize=10)

    # 2. Continent Mask (суша vs океан)
    axes[0, 1].imshow(continent.mask, cmap='gray', origin='lower')
    axes[0, 1].set_title('2. Continent Mask (Land vs Ocean)', fontsize=14, fontweight='bold')
    axes[0, 1].axis('off')

    # Если есть spine, рисуем его
    if has_spine:
        axes[0, 1].plot(continent.spine_path[:, 0], continent.spine_path[:, 1],
                       'r-', linewidth=3, alpha=0.8, label='Spine')
        axes[0, 1].scatter(continent.spine_path[0, 0], continent.spine_path[0, 1],
                          c='red', s=150, marker='o', label='North', zorder=10)
        axes[0, 1].scatter(continent.spine_path[-1, 0], continent.spine_path[-1, 1],
                          c='red', s=150, marker='s', label='South', zorder=10)
        axes[0, 1].legend(loc='upper right', fontsize=10)

    axes[0, 1].text(
        10, 490,
        f'Land: {land_pct:.1f}%\n' +
        f'Ocean: {ocean_pct:.1f}%\n' +
        f'Islands: {num_islands}\n' +
        f'Ocean at edges: {ocean_edge_pct:.1f}%',
        fontsize=10,
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
        verticalalignment='top'
    )

    # 3. Heightmap с маской (только суша)
    masked_heightmap = np.where(continent.mask, continent.heightmap, np.nan)
    im3 = axes[1, 0].imshow(masked_heightmap, cmap='terrain', origin='lower')
    axes[1, 0].set_title('3. Land Elevation (Heightmap + Mask)', fontsize=14, fontweight='bold')
    axes[1, 0].axis('off')
    plt.colorbar(im3, ax=axes[1, 0], label='Land Elevation', fraction=0.046)

    # Если есть spine, рисуем его
    if has_spine:
        axes[1, 0].plot(continent.spine_path[:, 0], continent.spine_path[:, 1],
                       'r-', linewidth=2, alpha=0.7)

    # 4. Геометрия континента
    axes[1, 1].imshow(continent.mask, cmap='gray', origin='lower', alpha=0.7)

    # Рисуем spine path если есть
    if has_spine:
        axes[1, 1].plot(continent.spine_path[:, 0], continent.spine_path[:, 1],
                       'r-', linewidth=4, label='Spine Path', zorder=11, alpha=0.9)
        axes[1, 1].scatter(continent.spine_path[0, 0], continent.spine_path[0, 1],
                          c='red', s=200, marker='o', label='North', zorder=12,
                          edgecolors='white', linewidths=2)
        axes[1, 1].scatter(continent.spine_path[-1, 0], continent.spine_path[-1, 1],
                          c='red', s=200, marker='s', label='South', zorder=12,
                          edgecolors='white', linewidths=2)

    # Рисуем центр масс
    cx, cy = continent.center
    axes[1, 1].scatter(cx, cy, c='yellow', s=200, marker='X', label='Center of Mass',
                      zorder=10, edgecolors='black', linewidths=2)

    # Рисуем главную ось (если нет spine, или для сравнения)
    axes[1, 1].plot([x1, x2], [y1, y2], 'b--', linewidth=2, label='Major Axis (PCA)',
                   zorder=9, alpha=0.7)
    axes[1, 1].scatter([x1, x2], [y1, y2], c='blue', s=100, marker='o', zorder=10)

    # Подпись к оси
    mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
    axes[1, 1].text(
        mid_x, mid_y + 20,
        f'Axis Length: {axis_length:.0f}px',
        fontsize=10,
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
        horizontalalignment='center'
    )

    axes[1, 1].set_title('4. Continent Geometry', fontsize=14, fontweight='bold')
    axes[1, 1].legend(loc='upper right', fontsize=9)
    axes[1, 1].axis('off')
    axes[1, 1].set_xlim(0, 512)
    axes[1, 1].set_ylim(0, 512)

    # Общий заголовок
    mode_str = "Spine-Based (Anatomy → Geography)" if has_spine else "Standard (Pure Perlin Noise)"
    plt.suptitle(
        f'Sprint 3.6 Phase 2: Continent Generation\n' +
        f'Seed: "{seed}" | Mode: {mode_str}',
        fontsize=16,
        fontweight='bold'
    )
    plt.tight_layout()

    # Сохранение
    if save_path is None:
        output_dir = project_root / 'output'
        output_dir.mkdir(exist_ok=True)
        suffix = "_spine" if has_spine else ""
        save_path = output_dir / f'continent_{seed.replace(" ", "_")}{suffix}.png'

    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"\n[OK] Визуализация сохранена: {save_path}")
    print(f"[INFO] Размер файла: {save_path.stat().st_size / 1024:.1f} KB")

    # Показываем
    plt.show()


def compare_seeds(seeds: list, enable_spine: bool = False):
    """
    Сравнивает континенты для разных seed-ов

    Args:
        seeds: Список строк-seeds
        enable_spine: Включить spine-based generation
    """
    print("\n" + "="*70)
    print(f"[COMPARE] Сравнение континентов для {len(seeds)} seed-ов")
    if enable_spine:
        print("[MODE] Spine-Based Generation")
    else:
        print("[MODE] Standard Generation")
    print("="*70)

    gen = WorldGeneratorV2()

    # Настраиваем режим
    if enable_spine:
        gen.config['continent']['shape_mask']['enabled'] = True
        gen.config['continent']['shape_mask']['type'] = 'spine'
    else:
        gen.config['continent']['shape_mask']['enabled'] = False

    fig, axes = plt.subplots(2, len(seeds), figsize=(6 * len(seeds), 12))

    for i, seed in enumerate(seeds):
        print(f"\n[INFO] Генерация континента: seed='{seed}'")
        continent = gen._generate_continent(seed)

        land_pct = continent.mask.sum() / (512 * 512) * 100
        has_spine = continent.spine_path is not None

        # Верхний ряд: heightmap
        if len(seeds) > 1:
            ax_top = axes[0, i]
            ax_bot = axes[1, i]
        else:
            ax_top = axes[0]
            ax_bot = axes[1]

        ax_top.imshow(continent.heightmap, cmap='terrain', origin='lower')

        # Рисуем spine если есть
        if has_spine:
            ax_top.plot(continent.spine_path[:, 0], continent.spine_path[:, 1],
                       'r-', linewidth=2, alpha=0.5)

        ax_top.set_title(f'Seed: "{seed}"', fontsize=12, fontweight='bold')
        ax_top.axis('off')

        # Нижний ряд: маска с геометрией
        ax_bot.imshow(continent.mask, cmap='gray', origin='lower', alpha=0.7)

        # Рисуем spine если есть
        if has_spine:
            ax_bot.plot(continent.spine_path[:, 0], continent.spine_path[:, 1],
                       'r-', linewidth=3, alpha=0.8)
            ax_bot.scatter(continent.spine_path[0, 0], continent.spine_path[0, 1],
                          c='red', s=100, marker='o', zorder=10)
            ax_bot.scatter(continent.spine_path[-1, 0], continent.spine_path[-1, 1],
                          c='red', s=100, marker='s', zorder=10)

        cx, cy = continent.center
        ax_bot.scatter(cx, cy, c='yellow', s=100, marker='X', zorder=10,
                      edgecolors='black', linewidths=1.5)

        (x1, y1), (x2, y2) = continent.major_axis
        ax_bot.plot([x1, x2], [y1, y2], 'b--', linewidth=2, zorder=9, alpha=0.7)

        ax_bot.set_title(f'Land: {land_pct:.1f}%', fontsize=10)
        ax_bot.axis('off')

    mode_str = "Spine-Based" if enable_spine else "Standard"
    plt.suptitle(
        f'Continent Comparison: Different Seeds ({mode_str} Mode)',
        fontsize=16,
        fontweight='bold'
    )
    plt.tight_layout()

    # Сохранение
    output_dir = project_root / 'output'
    output_dir.mkdir(exist_ok=True)
    suffix = "_spine" if enable_spine else ""
    save_path = output_dir / f'continent_comparison{suffix}.png'

    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"\n[OK] Сравнение сохранено: {save_path}")
    print(f"[INFO] Размер файла: {save_path.stat().st_size / 1024:.1f} KB")

    plt.show()


def compare_modes(seed: str):
    """
    Сравнивает стандартную генерацию со spine-based

    Args:
        seed: Строка-seed для генерации
    """
    print("\n" + "="*70)
    print(f"[COMPARE MODES] Сравнение режимов генерации")
    print(f"[SEED] {seed}")
    print("="*70)

    gen = WorldGeneratorV2()

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # Режим 1: Стандартный (без shape mask)
    print("\n[1/2] Стандартная генерация...")
    gen.config['continent']['shape_mask']['enabled'] = False
    continent_standard = gen._generate_continent(seed)

    land_pct_standard = continent_standard.mask.sum() / (512 * 512) * 100

    # Режим 2: Spine-based
    print("[2/2] Spine-based генерация...")
    gen.config['continent']['shape_mask']['enabled'] = True
    gen.config['continent']['shape_mask']['type'] = 'spine'
    continent_spine = gen._generate_continent(seed)

    land_pct_spine = continent_spine.mask.sum() / (512 * 512) * 100

    # Верхний ряд: Heightmaps
    axes[0, 0].imshow(continent_standard.heightmap, cmap='terrain', origin='lower')
    axes[0, 0].set_title('Standard: Heightmap\n(Pure Perlin Noise)', fontsize=12, fontweight='bold')
    axes[0, 0].axis('off')

    axes[0, 1].imshow(continent_spine.heightmap, cmap='terrain', origin='lower')
    if continent_spine.spine_path is not None:
        axes[0, 1].plot(continent_spine.spine_path[:, 0], continent_spine.spine_path[:, 1],
                       'r-', linewidth=2, alpha=0.5)
    axes[0, 1].set_title('Spine-Based: Heightmap\n(Noise × Spine Influence)', fontsize=12, fontweight='bold')
    axes[0, 1].axis('off')

    # Нижний ряд: Masks с геометрией
    axes[1, 0].imshow(continent_standard.mask, cmap='gray', origin='lower', alpha=0.7)
    cx1, cy1 = continent_standard.center
    (x1, y1), (x2, y2) = continent_standard.major_axis
    axes[1, 0].scatter(cx1, cy1, c='yellow', s=150, marker='X', zorder=10,
                      edgecolors='black', linewidths=2)
    axes[1, 0].plot([x1, x2], [y1, y2], 'b-', linewidth=3, zorder=9)
    axes[1, 0].set_title(f'Standard: Continent\nLand: {land_pct_standard:.1f}%', fontsize=12, fontweight='bold')
    axes[1, 0].axis('off')

    axes[1, 1].imshow(continent_spine.mask, cmap='gray', origin='lower', alpha=0.7)
    if continent_spine.spine_path is not None:
        axes[1, 1].plot(continent_spine.spine_path[:, 0], continent_spine.spine_path[:, 1],
                       'r-', linewidth=4, alpha=0.9, label='Spine')
        axes[1, 1].scatter(continent_spine.spine_path[0, 0], continent_spine.spine_path[0, 1],
                          c='red', s=150, marker='o', zorder=12, edgecolors='white', linewidths=2)
        axes[1, 1].scatter(continent_spine.spine_path[-1, 0], continent_spine.spine_path[-1, 1],
                          c='red', s=150, marker='s', zorder=12, edgecolors='white', linewidths=2)
    cx2, cy2 = continent_spine.center
    axes[1, 1].scatter(cx2, cy2, c='yellow', s=150, marker='X', zorder=10,
                      edgecolors='black', linewidths=2, label='Center')
    axes[1, 1].legend(loc='upper right', fontsize=10)
    axes[1, 1].set_title(f'Spine-Based: Continent\nLand: {land_pct_spine:.1f}%', fontsize=12, fontweight='bold')
    axes[1, 1].axis('off')

    plt.suptitle(
        f'Mode Comparison: Standard vs Spine-Based\n' +
        f'Seed: "{seed}" | Left: Geography only | Right: Anatomy → Geography',
        fontsize=16,
        fontweight='bold'
    )
    plt.tight_layout()

    # Сохранение
    output_dir = project_root / 'output'
    output_dir.mkdir(exist_ok=True)
    save_path = output_dir / f'continent_mode_comparison_{seed.replace(" ", "_")}.png'

    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"\n[OK] Сравнение режимов сохранено: {save_path}")
    print(f"[INFO] Размер файла: {save_path.stat().st_size / 1024:.1f} KB")

    plt.show()


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(
        description='Visualize continent generation with Perlin Noise'
    )
    parser.add_argument(
        '--seed',
        type=str,
        default='silgarron_alpha_01',
        help='Seed string for generation'
    )
    parser.add_argument(
        '--spine',
        action='store_true',
        help='Enable spine-based generation (anatomy -> geography)'
    )
    parser.add_argument(
        '--compare',
        nargs='+',
        help='Compare multiple seeds (space-separated)'
    )
    parser.add_argument(
        '--compare-modes',
        action='store_true',
        help='Compare standard vs spine-based generation for same seed'
    )

    args = parser.parse_args()

    if args.compare_modes:
        compare_modes(args.seed)
    elif args.compare:
        compare_seeds(args.compare, enable_spine=args.spine)
    else:
        visualize_continent(args.seed, enable_spine=args.spine)


if __name__ == '__main__':
    main()
