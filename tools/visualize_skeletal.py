"""
Визуализация скелетной структуры (Task 1.2)

Создаёт PNG изображения для визуальной валидации:
1. Base elevation (Perlin Noise)
2. Ridge mask (хребет)
3. Rib mask (рёбра)
4. Final elevation (комбинированный)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib.pyplot as plt
import numpy as np
from core.world_generator import WorldGenerator


def visualize_skeletal_structure(seed: str = "test_world", output_dir: str = "output"):
    """
    Создаёт визуализацию скелетной структуры.

    Args:
        seed: Seed для генерации
        output_dir: Папка для сохранения изображений
    """
    print(f"=== Visualizing Skeletal Structure ===")
    print(f"Seed: {seed}")

    # Создаём папку для output
    os.makedirs(output_dir, exist_ok=True)

    # Генерируем мир
    gen = WorldGenerator(seed=seed)
    result = gen._generate_skeletal_structure()

    base_elevation = gen._generate_base_elevation()
    ridge_mask = result['ridge_mask']
    rib_mask = result['rib_mask']
    final_elevation = result['elevation']

    # Создаём фигуру с 4 subplots
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    fig.suptitle(f'Skeletal Structure - Seed: "{seed}"', fontsize=16, fontweight='bold')

    # 1. Base Elevation (Perlin Noise)
    ax1 = axes[0, 0]
    im1 = ax1.imshow(base_elevation, cmap='terrain', origin='lower', vmin=0, vmax=1)
    ax1.set_title('1. Base Elevation (Perlin Noise)', fontweight='bold')
    ax1.set_xlabel('X')
    ax1.set_ylabel('Y')
    plt.colorbar(im1, ax=ax1, label='Height [0-1]')
    ax1.grid(True, alpha=0.3)

    # 2. Ridge Mask (вертикальный хребет)
    ax2 = axes[0, 1]
    im2 = ax2.imshow(ridge_mask, cmap='hot', origin='lower', vmin=0, vmax=1)
    ax2.set_title('2. Ridge Mask (Хребет)', fontweight='bold')
    ax2.set_xlabel('X')
    ax2.set_ylabel('Y')
    plt.colorbar(im2, ax=ax2, label='Ridge Intensity [0-1]')
    ax2.grid(True, alpha=0.3)
    # Отмечаем центральную ось
    center_x = gen.width // 2
    ax2.axvline(x=center_x, color='cyan', linestyle='--', linewidth=2, label='Center')
    ax2.legend()

    # 3. Rib Mask (боковые рёбра)
    ax3 = axes[1, 0]
    im3 = ax3.imshow(rib_mask, cmap='Blues', origin='lower', vmin=0, vmax=0.3)
    ax3.set_title('3. Rib Mask (Рёбра)', fontweight='bold')
    ax3.set_xlabel('X')
    ax3.set_ylabel('Y')
    plt.colorbar(im3, ax=ax3, label='Rib Intensity [0-0.3]')
    ax3.grid(True, alpha=0.3)

    # 4. Final Elevation (комбинированный)
    ax4 = axes[1, 1]
    im4 = ax4.imshow(final_elevation, cmap='gist_earth', origin='lower', vmin=0, vmax=1)
    ax4.set_title('4. Final Elevation (60% Base + 30% Ridge + 10% Ribs)', fontweight='bold')
    ax4.set_xlabel('X')
    ax4.set_ylabel('Y')
    plt.colorbar(im4, ax=ax4, label='Elevation [0-1]')
    ax4.grid(True, alpha=0.3)

    # Визуализируем изгиб хребта (snake path)
    # Извлекаем линию максимума ridge mask для каждой Y координаты
    ridge_path_x = []
    ridge_path_y = []
    for y in range(0, gen.height, 4):  # Каждые 4 пикселя для производительности
        ridge_slice = ridge_mask[y, :]
        max_idx = np.argmax(ridge_slice)
        ridge_path_x.append(max_idx)
        ridge_path_y.append(y)

    ax4.plot(ridge_path_x, ridge_path_y, color='cyan', linestyle='-', linewidth=2,
             label='Spine Path (with wiggle)', alpha=0.8)
    ax4.legend()

    plt.tight_layout()

    # Сохраняем
    output_path = os.path.join(output_dir, f"skeletal_structure_{seed}.png")
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n[OK] Visualization saved to: {output_path}")

    plt.close()

    # Дополнительно: Профиль хребта (cross-section)
    fig2, ax = plt.subplots(1, 1, figsize=(12, 6))

    # Берём срез по середине карты (y = height // 2)
    mid_y = gen.height // 2
    x_coords = np.arange(gen.width)

    ax.plot(x_coords, base_elevation[mid_y, :], label='Base Elevation', alpha=0.7, linewidth=2)
    ax.plot(x_coords, ridge_mask[mid_y, :], label='Ridge Mask', alpha=0.7, linewidth=2)
    ax.plot(x_coords, rib_mask[mid_y, :], label='Rib Mask', alpha=0.7, linewidth=2)
    ax.plot(x_coords, final_elevation[mid_y, :], label='Final Elevation', linewidth=3, color='black')

    ax.set_title(f'Cross-Section Profile (Y = {mid_y}) - Seed: "{seed}"', fontweight='bold')
    ax.set_xlabel('X Coordinate')
    ax.set_ylabel('Elevation / Intensity')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.axvline(x=center_x, color='red', linestyle='--', alpha=0.5, label='Ridge Center')

    profile_path = os.path.join(output_dir, f"skeletal_profile_{seed}.png")
    plt.savefig(profile_path, dpi=150, bbox_inches='tight')
    print(f"[OK] Profile saved to: {profile_path}")

    plt.close()

    # Статистика
    print(f"\n=== Statistics ===")
    print(f"Base Elevation:   [{base_elevation.min():.3f}, {base_elevation.max():.3f}], mean: {base_elevation.mean():.3f}, std: {base_elevation.std():.3f}")
    print(f"Ridge Mask:       [{ridge_mask.min():.3f}, {ridge_mask.max():.3f}], mean: {ridge_mask.mean():.3f}")
    print(f"Rib Mask:         [{rib_mask.min():.3f}, {rib_mask.max():.3f}], mean: {rib_mask.mean():.3f}")
    print(f"Final Elevation:  [{final_elevation.min():.3f}, {final_elevation.max():.3f}], mean: {final_elevation.mean():.3f}, std: {final_elevation.std():.3f}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Visualize skeletal structure (Task 1.2)")
    parser.add_argument("--seed", type=str, default="silgarron_alpha", help="World seed")
    parser.add_argument("--output", type=str, default="output", help="Output directory")

    args = parser.parse_args()

    visualize_skeletal_structure(seed=args.seed, output_dir=args.output)
