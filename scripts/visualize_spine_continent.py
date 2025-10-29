"""
Визуализация генерации континента на основе хребта (spine)

Показывает философию "от анатомии к географии":
1. Процедурный путь хребта (позвоночник)
2. Поле влияния вокруг хребта
3. Комбинация с Perlin Noise
4. Финальный континент
5. Сравнение с ellipse mask

Usage:
    python scripts/visualize_spine_continent.py
    python scripts/visualize_spine_continent.py --seed silgarron_001
    python scripts/visualize_spine_continent.py --compare
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


def visualize_spine_generation(seed: str = "spine_demo"):
    """Визуализация процесса генерации континента на основе хребта"""
    print("="*70)
    print("[VIZ] Spine-Based Continent Generation")
    print("="*70)
    print(f"Seed: {seed}")
    print()

    gen = WorldGeneratorV2()

    # Создаем фигуру с 6 панелями
    fig = plt.figure(figsize=(20, 13))

    # ========== ПАНЕЛЬ 1: Базовый Perlin Noise (без маски) ==========
    print("[1/6] Генерация базового Perlin Noise...")
    gen.config['continent']['shape_mask']['enabled'] = False
    continent_no_mask = gen._generate_continent(seed)

    ax1 = plt.subplot(2, 3, 1)
    im1 = ax1.imshow(continent_no_mask.heightmap, cmap='terrain', origin='lower', vmin=0, vmax=1)
    ax1.set_title(
        '1. Base Perlin Noise\n(Without Shape Mask)',
        fontsize=12,
        fontweight='bold'
    )
    ax1.axis('off')
    plt.colorbar(im1, ax=ax1, fraction=0.046)

    # ========== ПАНЕЛЬ 2: Spine Path + Influence Mask ==========
    print("[2/6] Генерация пути хребта...")
    spine_seed = hash(seed + "spine") % (2**31)
    spine_path = gen._generate_spine_path(
        seed=spine_seed,
        width=512,
        height=512,
        num_points=100,
        curvature=0.3
    )

    print("[3/6] Создание поля влияния хребта...")
    spine_influence = gen._create_spine_influence_mask(
        spine_path=spine_path,
        width=512,
        height=512,
        max_influence=200.0
    )

    ax2 = plt.subplot(2, 3, 2)
    im2 = ax2.imshow(spine_influence, cmap='viridis', origin='lower', vmin=0, vmax=1)

    # Отображаем путь хребта
    ax2.plot(spine_path[:, 0], spine_path[:, 1], 'r-', linewidth=3, label='Spine Path', alpha=0.8)
    ax2.scatter(spine_path[0, 0], spine_path[0, 1], c='white', s=150, marker='o',
                edgecolors='red', linewidths=3, label='North', zorder=10)
    ax2.scatter(spine_path[-1, 0], spine_path[-1, 1], c='white', s=150, marker='s',
                edgecolors='red', linewidths=3, label='South', zorder=10)

    ax2.set_title(
        '2. Spine Path + Influence Field\n(Skeleton defines the form)',
        fontsize=12,
        fontweight='bold'
    )
    ax2.legend(loc='upper right', fontsize=8)
    ax2.axis('off')
    plt.colorbar(im2, ax=ax2, fraction=0.046)

    # ========== ПАНЕЛЬ 3: Комбинация (Noise * Spine Influence) ==========
    print("[4/6] Комбинация шума и поля влияния...")
    combined_heightmap = continent_no_mask.heightmap * spine_influence

    ax3 = plt.subplot(2, 3, 3)
    im3 = ax3.imshow(combined_heightmap, cmap='terrain', origin='lower', vmin=0, vmax=1)

    # Отображаем хребет поверх
    ax3.plot(spine_path[:, 0], spine_path[:, 1], 'r-', linewidth=2, alpha=0.5)

    ax3.set_title(
        '3. Combined (Noise x Spine)\n(Body grows around skeleton)',
        fontsize=12,
        fontweight='bold'
    )
    ax3.axis('off')
    plt.colorbar(im3, ax=ax3, fraction=0.046)

    # ========== ПАНЕЛЬ 4: Континент С хребтом ==========
    print("[5/6] Генерация континента на основе хребта...")
    gen.config['continent']['shape_mask']['enabled'] = True
    gen.config['continent']['shape_mask']['type'] = 'spine'
    gen.config['continent']['shape_mask']['sea_level_override'] = 0.20

    continent_with_spine = gen._generate_continent(seed)

    land_pct_spine = continent_with_spine.mask.sum() / (512 * 512) * 100

    ax4 = plt.subplot(2, 3, 4)
    ax4.imshow(continent_with_spine.mask, cmap='gray', origin='lower')

    # Отображаем хребет
    if continent_with_spine.spine_path is not None:
        ax4.plot(continent_with_spine.spine_path[:, 0],
                continent_with_spine.spine_path[:, 1],
                'r-', linewidth=3, label='Spine', alpha=0.9)
        ax4.scatter(continent_with_spine.spine_path[0, 0],
                   continent_with_spine.spine_path[0, 1],
                   c='red', s=100, marker='o', label='North', zorder=10)
        ax4.scatter(continent_with_spine.spine_path[-1, 0],
                   continent_with_spine.spine_path[-1, 1],
                   c='red', s=100, marker='s', label='South', zorder=10)

    # Отображаем центр и ось
    cx, cy = continent_with_spine.center
    ax4.scatter(cx, cy, c='yellow', s=100, marker='x', linewidths=3, label='Center')

    # Проверяем океан на краях
    edge_pixels = np.concatenate([
        continent_with_spine.mask[0, :],
        continent_with_spine.mask[-1, :],
        continent_with_spine.mask[:, 0],
        continent_with_spine.mask[:, -1]
    ])
    ocean_edge_pct = (1 - edge_pixels.sum() / len(edge_pixels)) * 100

    ax4.set_title(
        f'4. Continent WITH Spine\n' +
        f'Land: {land_pct_spine:.1f}%, Ocean at edges: {ocean_edge_pct:.1f}%',
        fontsize=12,
        fontweight='bold'
    )
    ax4.legend(loc='upper right', fontsize=8)
    ax4.axis('off')

    # ========== ПАНЕЛЬ 5: Континент БЕЗ хребта (ellipse) ==========
    print("[6/6] Сравнение с ellipse mask...")
    gen.config['continent']['shape_mask']['type'] = 'ellipse'

    continent_with_ellipse = gen._generate_continent(seed)

    land_pct_ellipse = continent_with_ellipse.mask.sum() / (512 * 512) * 100

    ax5 = plt.subplot(2, 3, 5)
    ax5.imshow(continent_with_ellipse.mask, cmap='gray', origin='lower')

    # Отображаем центр
    cx2, cy2 = continent_with_ellipse.center
    (x1, y1), (x2, y2) = continent_with_ellipse.major_axis

    ax5.scatter(cx2, cy2, c='red', s=100, marker='x', linewidths=3, label='Center')
    ax5.plot([x1, x2], [y1, y2], 'r-', linewidth=2, label='Major Axis')

    ax5.set_title(
        f'5. Continent WITH Ellipse (old)\n' +
        f'Land: {land_pct_ellipse:.1f}% (geometric, artificial)',
        fontsize=12,
        fontweight='bold'
    )
    ax5.legend(loc='upper right', fontsize=8)
    ax5.axis('off')

    # ========== ПАНЕЛЬ 6: Сравнение (наложение) ==========
    ax6 = plt.subplot(2, 3, 6)

    # Создаем RGB изображение для наложения
    comparison = np.zeros((512, 512, 3))

    # Красный канал - континент с ellipse
    comparison[:, :, 0] = continent_with_ellipse.mask * 0.7

    # Зелёный канал - континент с spine
    comparison[:, :, 1] = continent_with_spine.mask * 0.7

    # Синий канал - пересечение
    comparison[:, :, 2] = (continent_with_ellipse.mask & continent_with_spine.mask) * 0.3

    ax6.imshow(comparison, origin='lower')

    # Отображаем spine поверх
    if continent_with_spine.spine_path is not None:
        ax6.plot(continent_with_spine.spine_path[:, 0],
                continent_with_spine.spine_path[:, 1],
                'w-', linewidth=2, alpha=0.8, label='Spine')

    ax6.set_title(
        '6. Comparison (Overlay)\n' +
        'Red=Ellipse, Green=Spine, Yellow=Both',
        fontsize=12,
        fontweight='bold'
    )
    ax6.legend(loc='upper right', fontsize=8)
    ax6.axis('off')

    # Общий заголовок
    plt.suptitle(
        f'Spine-Based Continent Generation: "From Anatomy to Geography"\n' +
        f'Seed: {seed} | Body grows around skeleton',
        fontsize=16,
        fontweight='bold'
    )

    plt.tight_layout()

    # Сохранение
    output_dir = project_root / 'output'
    output_dir.mkdir(exist_ok=True)
    save_path = output_dir / f'spine_continent_{seed}.png'

    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print()
    print(f"[OK] Сохранено: {save_path}")
    print(f"[INFO] Размер файла: {save_path.stat().st_size / 1024:.1f} KB")

    plt.show()


def compare_multiple_spines():
    """Сравнение нескольких континентов на основе хребта"""
    print("="*70)
    print("[VIZ] Comparing Multiple Spine-Based Continents")
    print("="*70)

    gen = WorldGeneratorV2()
    gen.config['continent']['shape_mask']['enabled'] = True
    gen.config['continent']['shape_mask']['type'] = 'spine'
    gen.config['continent']['shape_mask']['sea_level_override'] = 0.20

    seeds = ["silgarron_alpha", "silgarron_beta", "silgarron_gamma"]

    fig, axes = plt.subplots(2, 3, figsize=(18, 12))

    for i, seed in enumerate(seeds):
        print(f"\n[{i+1}/3] Генерация континента: {seed}...")

        continent = gen._generate_continent(seed)
        land_pct = continent.mask.sum() / (512 * 512) * 100

        # Верхний ряд: Influence mask с хребтом
        ax_top = axes[0, i]
        spine_seed = hash(seed + "spine") % (2**31)
        spine_path = gen._generate_spine_path(spine_seed, 512, 512, 100, 0.3)
        spine_influence = gen._create_spine_influence_mask(spine_path, 512, 512, 200.0)

        ax_top.imshow(spine_influence, cmap='viridis', origin='lower')
        ax_top.plot(spine_path[:, 0], spine_path[:, 1], 'r-', linewidth=2)
        ax_top.set_title(f'{seed} - Spine Influence', fontsize=10, fontweight='bold')
        ax_top.axis('off')

        # Нижний ряд: Континент
        ax_bottom = axes[1, i]
        ax_bottom.imshow(continent.mask, cmap='gray', origin='lower')

        if continent.spine_path is not None:
            ax_bottom.plot(continent.spine_path[:, 0],
                          continent.spine_path[:, 1],
                          'r-', linewidth=2, alpha=0.8)

        ax_bottom.set_title(f'Land: {land_pct:.1f}%', fontsize=10, fontweight='bold')
        ax_bottom.axis('off')

    plt.suptitle(
        'Multiple Spine-Based Continents\n' +
        'Each seed creates unique anatomical form',
        fontsize=14,
        fontweight='bold'
    )
    plt.tight_layout()

    output_dir = project_root / 'output'
    save_path = output_dir / 'spine_continents_comparison.png'
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"\n[OK] Сохранено: {save_path}")

    plt.show()


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(
        description='Visualize spine-based continent generation'
    )
    parser.add_argument(
        '--seed',
        type=str,
        default='spine_demo',
        help='Seed for generation'
    )
    parser.add_argument(
        '--compare',
        action='store_true',
        help='Compare multiple spine-based continents'
    )

    args = parser.parse_args()

    if args.compare:
        compare_multiple_spines()
    else:
        visualize_spine_generation(args.seed)


if __name__ == '__main__':
    main()
