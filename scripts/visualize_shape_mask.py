"""
Визуализация эффекта маски формы для центрирования континента

Показывает:
1. Базовый Perlin Noise (без маски)
2. Маска формы (эллиптический градиент)
3. Комбинация (Noise * Mask)
4. Финальный континент (после threshold и smoothing)
5. Сравнение: без маски vs с маской

Usage:
    python scripts/visualize_shape_mask.py
    python scripts/visualize_shape_mask.py --seed custom_seed_123
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


def visualize_shape_mask_effect(seed: str = "shape_mask_demo"):
    """Визуализация процесса применения маски формы"""
    print("="*70)
    print("[VIZ] Shape Mask Effect Visualization")
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

    # ========== ПАНЕЛЬ 2: Маска формы (градиент) ==========
    print("[2/6] Создание маски формы...")
    shape_mask = gen._create_shape_mask(
        width=512,
        height=512,
        mask_type='ellipse',
        radius_x=0.35,
        radius_y=0.45
    )

    ax2 = plt.subplot(2, 3, 2)
    im2 = ax2.imshow(shape_mask, cmap='viridis', origin='lower', vmin=0, vmax=1)
    ax2.set_title(
        '2. Shape Mask (Ellipse)\n(Center=1.0, Edges=0.0)',
        fontsize=12,
        fontweight='bold'
    )
    ax2.axis('off')
    plt.colorbar(im2, ax=ax2, fraction=0.046)

    # ========== ПАНЕЛЬ 3: Комбинация (Noise * Mask) ==========
    print("[3/6] Комбинация шума и маски...")
    combined_heightmap = continent_no_mask.heightmap * shape_mask

    ax3 = plt.subplot(2, 3, 3)
    im3 = ax3.imshow(combined_heightmap, cmap='terrain', origin='lower', vmin=0, vmax=1)
    ax3.set_title(
        '3. Combined (Noise * Mask)\n(Constrained to center)',
        fontsize=12,
        fontweight='bold'
    )
    ax3.axis('off')
    plt.colorbar(im3, ax=ax3, fraction=0.046)

    # ========== ПАНЕЛЬ 4: Континент БЕЗ маски ==========
    print("[4/6] Генерация континента без маски...")
    land_pct_no_mask = continent_no_mask.mask.sum() / (512 * 512) * 100

    ax4 = plt.subplot(2, 3, 4)
    ax4.imshow(continent_no_mask.mask, cmap='gray', origin='lower')

    # Отображаем центр и ось
    cx, cy = continent_no_mask.center
    (x1, y1), (x2, y2) = continent_no_mask.major_axis

    ax4.scatter(cx, cy, c='red', s=100, marker='x', linewidths=3, label='Center')
    ax4.plot([x1, x2], [y1, y2], 'r-', linewidth=2, label='Major Axis')

    ax4.set_title(
        f'4. Continent WITHOUT Shape Mask\n' +
        f'Land: {land_pct_no_mask:.1f}%, Center: ({cx}, {cy})',
        fontsize=12,
        fontweight='bold'
    )
    ax4.legend(loc='upper right', fontsize=8)
    ax4.axis('off')

    # ========== ПАНЕЛЬ 5: Континент С маской ==========
    print("[5/6] Генерация континента с маской...")
    gen.config['continent']['shape_mask']['enabled'] = True
    gen.config['continent']['shape_mask']['sea_level_override'] = 0.20
    continent_with_mask = gen._generate_continent(seed)

    land_pct_with_mask = continent_with_mask.mask.sum() / (512 * 512) * 100

    ax5 = plt.subplot(2, 3, 5)
    ax5.imshow(continent_with_mask.mask, cmap='gray', origin='lower')

    # Отображаем центр и ось
    cx2, cy2 = continent_with_mask.center
    (x1_2, y1_2), (x2_2, y2_2) = continent_with_mask.major_axis

    ax5.scatter(cx2, cy2, c='red', s=100, marker='x', linewidths=3, label='Center')
    ax5.plot([x1_2, x2_2], [y1_2, y2_2], 'r-', linewidth=2, label='Major Axis')

    # Проверяем океан на краях
    edge_pixels = np.concatenate([
        continent_with_mask.mask[0, :],
        continent_with_mask.mask[-1, :],
        continent_with_mask.mask[:, 0],
        continent_with_mask.mask[:, -1]
    ])
    ocean_edge_pct = (1 - edge_pixels.sum() / len(edge_pixels)) * 100

    ax5.set_title(
        f'5. Continent WITH Shape Mask\n' +
        f'Land: {land_pct_with_mask:.1f}%, Ocean at edges: {ocean_edge_pct:.1f}%',
        fontsize=12,
        fontweight='bold'
    )
    ax5.legend(loc='upper right', fontsize=8)
    ax5.axis('off')

    # ========== ПАНЕЛЬ 6: Сравнение (наложение) ==========
    print("[6/6] Создание сравнения...")

    ax6 = plt.subplot(2, 3, 6)

    # Создаем RGB изображение для наложения
    comparison = np.zeros((512, 512, 3))

    # Красный канал - континент БЕЗ маски
    comparison[:, :, 0] = continent_no_mask.mask * 0.7

    # Зелёный канал - континент С маской
    comparison[:, :, 1] = continent_with_mask.mask * 0.7

    # Синий канал - пересечение (оба континента)
    comparison[:, :, 2] = (continent_no_mask.mask & continent_with_mask.mask) * 0.3

    ax6.imshow(comparison, origin='lower')
    ax6.set_title(
        '6. Comparison (Overlay)\n' +
        'Red=Without mask, Green=With mask, Yellow=Both',
        fontsize=12,
        fontweight='bold'
    )
    ax6.axis('off')

    # Общий заголовок
    plt.suptitle(
        f'Shape Mask Effect Demonstration\n' +
        f'Seed: {seed} | Type: Ellipse (radius_x=0.35, radius_y=0.45)',
        fontsize=16,
        fontweight='bold'
    )

    plt.tight_layout()

    # Сохранение
    output_dir = project_root / 'output'
    output_dir.mkdir(exist_ok=True)
    save_path = output_dir / f'shape_mask_effect_{seed}.png'

    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print()
    print(f"[OK] Сохранено: {save_path}")
    print(f"[INFO] Размер файла: {save_path.stat().st_size / 1024:.1f} KB")

    plt.show()


def compare_shape_mask_types():
    """Сравнение разных типов масок (ellipse vs radial)"""
    print("="*70)
    print("[VIZ] Comparing Shape Mask Types")
    print("="*70)

    gen = WorldGeneratorV2()
    seed = "mask_types_comparison"

    fig, axes = plt.subplots(2, 3, figsize=(18, 12))

    # Ellipse masks
    for i, (rx, ry) in enumerate([(0.3, 0.4), (0.35, 0.45), (0.4, 0.5)]):
        gen.config['continent']['shape_mask']['enabled'] = True
        gen.config['continent']['shape_mask']['type'] = 'ellipse'
        gen.config['continent']['shape_mask']['radius_x'] = rx
        gen.config['continent']['shape_mask']['radius_y'] = ry
        gen.config['continent']['shape_mask']['sea_level_override'] = 0.20

        continent = gen._generate_continent(f"{seed}_ellipse_{i}")
        land_pct = continent.mask.sum() / (512 * 512) * 100

        axes[0, i].imshow(continent.mask, cmap='gray', origin='lower')
        axes[0, i].set_title(
            f'Ellipse (rx={rx}, ry={ry})\nLand: {land_pct:.1f}%',
            fontsize=10,
            fontweight='bold'
        )
        axes[0, i].axis('off')

    # Radial masks
    for i, radius in enumerate([0.3, 0.35, 0.4]):
        gen.config['continent']['shape_mask']['type'] = 'radial'
        gen.config['continent']['shape_mask']['radius_x'] = radius
        gen.config['continent']['shape_mask']['sea_level_override'] = 0.20

        continent = gen._generate_continent(f"{seed}_radial_{i}")
        land_pct = continent.mask.sum() / (512 * 512) * 100

        axes[1, i].imshow(continent.mask, cmap='gray', origin='lower')
        axes[1, i].set_title(
            f'Radial (r={radius})\nLand: {land_pct:.1f}%',
            fontsize=10,
            fontweight='bold'
        )
        axes[1, i].axis('off')

    plt.suptitle(
        'Shape Mask Types Comparison\nTop: Ellipse | Bottom: Radial',
        fontsize=14,
        fontweight='bold'
    )
    plt.tight_layout()

    output_dir = project_root / 'output'
    save_path = output_dir / 'shape_mask_types_comparison.png'
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"\n[OK] Сохранено: {save_path}")

    plt.show()


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(
        description='Visualize shape mask effect for continent centering'
    )
    parser.add_argument(
        '--seed',
        type=str,
        default='shape_mask_demo',
        help='Seed for generation'
    )
    parser.add_argument(
        '--compare-types',
        action='store_true',
        help='Compare different shape mask types'
    )

    args = parser.parse_args()

    if args.compare_types:
        compare_shape_mask_types()
    else:
        visualize_shape_mask_effect(args.seed)


if __name__ == '__main__':
    main()
