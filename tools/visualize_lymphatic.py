"""
Визуализация лимфатической системы (Task 1.3)

Создаёт PNG изображения для визуальной валидации D8 Flow Accumulation.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib.pyplot as plt
import numpy as np
from core.world_generator import WorldGenerator


def visualize_lymphatic_system(seed: str = "test_world", output_dir: str = "output"):
    """Создаёт визуализацию лимфатической системы."""
    print(f"=== Visualizing Lymphatic System ===")
    print(f"Seed: {seed}")

    os.makedirs(output_dir, exist_ok=True)

    # Генерируем
    gen = WorldGenerator(seed=seed)
    skeletal = gen._generate_skeletal_structure()
    lymphatic = gen._generate_lymphatic_system(skeletal)

    elevation = skeletal['elevation']
    ridge_mask = skeletal['ridge_mask']
    flow_accum = lymphatic['flow_accumulation']
    lymph_channels = lymphatic['lymph_channels']
    lymph_intensity = lymphatic['lymph_intensity']
    sources = lymphatic['source_points']

    # 2x2 layout
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    fig.suptitle(f'Lymphatic System - Seed: "{seed}"', fontsize=16, fontweight='bold')

    # 1. Elevation + Ridge + Sources
    ax1 = axes[0, 0]
    im1 = ax1.imshow(elevation, cmap='terrain', origin='lower', vmin=0, vmax=1)
    ax1.contour(ridge_mask, levels=[0.5], colors='red', linewidths=2, alpha=0.7)
    if sources:
        sy, sx = zip(*sources)
        ax1.scatter(sx, sy, c='red', s=100, marker='*', edgecolors='white', linewidths=2, label='Lymph Sources')
    ax1.set_title('1. Elevation + Ridge + Sources', fontweight='bold')
    ax1.legend()
    plt.colorbar(im1, ax=ax1, label='Elevation')

    # 2. Flow Accumulation (log scale)
    ax2 = axes[0, 1]
    log_accum = np.log1p(flow_accum)  # log(1+x) для лучшей визуализации
    im2 = ax2.imshow(log_accum, cmap='Blues', origin='lower')
    ax2.set_title('2. Flow Accumulation (log scale)', fontweight='bold')
    plt.colorbar(im2, ax=ax2, label='log(1+accumulation)')

    # 3. Lymph Channels
    ax3 = axes[1, 0]
    # Показываем elevation + золотые каналы сверху
    ax3.imshow(elevation, cmap='gray', origin='lower', alpha=0.5)
    im3 = ax3.imshow(lymph_channels, cmap='autumn', origin='lower', alpha=0.8, vmin=0, vmax=1)
    ax3.set_title('3. Lymph Channels (top 10% accumulation)', fontweight='bold')
    plt.colorbar(im3, ax=ax3, label='Channel (0=no, 1=yes)')

    # 4. Lymph Intensity
    ax4 = axes[1, 1]
    im4 = ax4.imshow(lymph_intensity, cmap='YlOrRd', origin='lower', vmin=0, vmax=1)
    if sources:
        sy, sx = zip(*sources)
        ax4.scatter(sx, sy, c='cyan', s=100, marker='*', edgecolors='black', linewidths=2)
    ax4.set_title('4. Lymph Intensity (normalized)', fontweight='bold')
    plt.colorbar(im4, ax=ax4, label='Intensity [0-1]')

    plt.tight_layout()

    output_path = os.path.join(output_dir, f"lymphatic_system_{seed}.png")
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n[OK] Visualization saved to: {output_path}")
    plt.close()

    # Статистика
    print(f"\n=== Statistics ===")
    print(f"Sources found: {len(sources)}")
    print(f"Flow accumulation: [{flow_accum.min():.1f}, {flow_accum.max():.1f}], mean: {flow_accum.mean():.1f}")
    print(f"Lymph channels: {np.sum(lymph_channels)} cells ({np.sum(lymph_channels)/lymph_channels.size*100:.1f}%)")
    print(f"Lymph intensity: [{lymph_intensity.min():.3f}, {lymph_intensity.max():.3f}]")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Visualize lymphatic system (Task 1.3)")
    parser.add_argument("--seed", type=str, default="silgarron_lymph", help="World seed")
    parser.add_argument("--output", type=str, default="output", help="Output directory")
    args = parser.parse_args()
    visualize_lymphatic_system(seed=args.seed, output_dir=args.output)
