"""
Visualization script for WP1: Foundation

Generates 4 output images:
1. wp1_foundation_bw.png - Black/white continent mask
2. wp1_spine_overlay.png - Spine path + center + major axis
3. wp1_organs_placement.png - Organs on continent (colored)
4. wp1_full_composite.png - Complete visualization (final artifact)

Usage:
    python scripts/visualize_wp1_foundation.py --seed my_seed
    python scripts/visualize_wp1_foundation.py --seed my_seed --output-dir custom_dir
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import argparse
import yaml
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap

from core.world_generator_v3 import WorldGeneratorV3
from core.models.world import World


def load_config(config_path: str = "config/world_generation_v3.yaml") -> dict:
    """Load configuration"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def visualize_continent_bw(world: World, output_path: Path):
    """
    Generate black/white continent mask visualization

    Args:
        world: Generated world
        output_path: Output file path
    """
    fig, ax = plt.subplots(figsize=(10, 10), dpi=100)

    # Display continent mask (black=ocean, white=land)
    ax.imshow(world.continent.mask, cmap='gray', interpolation='nearest')

    ax.set_title('WP1: Continent Mask (512×512)', fontsize=16, fontweight='bold')
    ax.axis('off')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[OK] Saved: {output_path}")


def visualize_spine_overlay(world: World, output_path: Path):
    """
    Generate spine + geometry visualization
    (ОБНОВЛЕНО для отображения контрольных точек Безье)
    """
    fig, ax = plt.subplots(figsize=(10, 10), dpi=100)

    ax.imshow(world.continent.mask, cmap='gray', alpha=0.7, interpolation='nearest')

    # (НОВОЕ) Отрисовка контрольных точек и соединяющих их линий
    if world.continent.control_points is not None:
        cp = world.continent.control_points
        # Соединяющие линии (серый пунктир)
        ax.plot(cp[:, 0], cp[:, 1], 'o--', color='gray', linewidth=1.5,
                markersize=8, markerfacecolor='white', label='Bézier Control Points')

    if world.continent.spine_path is not None:
        spine = world.continent.spine_path
        ax.plot(spine[:, 0], spine[:, 1], 'r-', linewidth=3, label='Spine Path (Bézier Curve)', alpha=0.9)

    cx, cy = world.continent.center
    ax.plot(cx, cy, 'y+', markersize=20, markeredgewidth=3, label='Center of Mass')

    (x1, y1), (x2, y2) = world.continent.major_axis
    ax.plot([x1, x2], [y1, y2], 'b-', linewidth=2, label='Major Axis (PCA)', alpha=0.8)

    ax.set_title('WP1: Spine & Geometry', fontsize=16, fontweight='bold')
    ax.legend(loc='upper right', fontsize=12) # Увеличим шрифт легенды
    ax.axis('off')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[OK] Saved: {output_path}")


def visualize_organs_placement(world: World, config: dict, output_path: Path):
    """
    Generate organ placement visualization

    Args:
        world: Generated world
        config: Configuration with organ colors
        output_path: Output file path
    """
    fig, ax = plt.subplots(figsize=(10, 10), dpi=100)

    # Background: heightmap
    cmap_terrain = LinearSegmentedColormap.from_list('terrain', [
        '#1a472a', '#2d5a3d', '#4a7c59', '#8fbc8f', '#c2d6a4', '#e5dcc5', '#f5e6d3'
    ])
    ax.imshow(world.continent.heightmap, cmap=cmap_terrain, interpolation='bilinear')

    # Organ colors from config
    organ_colors_config = config.get('visualization', {}).get('organ_colors', {})

    # Default colors if not in config
    default_colors = {
        'metabolic_organ': '#FF4444',
        'digestive': '#FF8844',
        'neural_cluster': '#4488FF',
        'immune_node': '#44FF88'
    }

    # Plot organs
    legend_handles = []
    for organ_id, organ in world.organs.items():
        x, y = organ.position
        color = organ_colors_config.get(organ.type, default_colors.get(organ.type, '#FFFFFF'))

        # Draw organ as circle
        circle = plt.Circle((x, y), organ.radius, color=color, alpha=0.8, linewidth=2, edgecolor='white')
        ax.add_patch(circle)

        # Label
        ax.text(x, y, organ_id.split('_')[-1].upper()[:3],
                ha='center', va='center', fontsize=8, fontweight='bold', color='white')

        # Legend entry (one per type)
        if organ.type not in [h.get_label() for h in legend_handles]:
            legend_handles.append(
                mpatches.Patch(color=color, label=organ.type.replace('_', ' ').title())
            )

    ax.set_title('WP1: Organ Placement', fontsize=16, fontweight='bold')
    ax.legend(handles=legend_handles, loc='upper right', fontsize=10)
    ax.axis('off')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[OK] Saved: {output_path}")


def visualize_full_composite(world: World, config: dict, output_path: Path):
    """
    Generate complete WP1 visualization (final artifact)
    (ОБНОВЛЕНО для отображения контрольных точек Безье)

    Args:
        world: Generated world
        config: Configuration
        output_path: Output file path
    """
    fig, axes = plt.subplots(2, 2, figsize=(16, 16), dpi=100)

    # ===== Subplot 1: Continent Mask =====
    ax1 = axes[0, 0]
    ax1.imshow(world.continent.mask, cmap='gray', interpolation='nearest')
    ax1.set_title('1. Continent Mask', fontsize=14, fontweight='bold')
    ax1.axis('off')

    # ===== Subplot 2: Heightmap =====
    ax2 = axes[0, 1]
    cmap_height = 'terrain'
    im2 = ax2.imshow(world.continent.heightmap, cmap=cmap_height, interpolation='bilinear')
    ax2.set_title('2. Heightmap (Elevation)', fontsize=14, fontweight='bold')
    ax2.axis('off')
    plt.colorbar(im2, ax=ax2, fraction=0.046, pad=0.04)

    # ===== Subplot 3: Spine & Geometry =====
    ax3 = axes[1, 0]
    ax3.imshow(world.continent.mask, cmap='gray', alpha=0.7, interpolation='nearest')

    # Spine path
    
    # Отрисовка контрольных точек
    if world.continent.control_points is not None:
        cp = world.continent.control_points
        ax3.plot(cp[:, 0], cp[:, 1], 'o--', color='gray', linewidth=1, markersize=5)

    if world.continent.spine_path is not None:
        spine = world.continent.spine_path
        ax3.plot(spine[:, 0], spine[:, 1], 'r-', linewidth=2, alpha=0.9)

    # Center
    cx, cy = world.continent.center
    ax3.plot(cx, cy, 'y+', markersize=15, markeredgewidth=2)

    # Major axis
    (x1, y1), (x2, y2) = world.continent.major_axis
    ax3.plot([x1, x2], [y1, y2], 'b-', linewidth=2, alpha=0.8)
    ax3.plot([x1, x2], [y1, y2], 'bo', markersize=6)

    ax3.set_title('3. Spine & Geometry', fontsize=14, fontweight='bold')
    ax3.axis('off')

    # ===== Subplot 4: Complete View with Organs =====
    ax4 = axes[1, 1]
    cmap_terrain = LinearSegmentedColormap.from_list('terrain', [
        '#1a472a', '#2d5a3d', '#4a7c59', '#8fbc8f', '#c2d6a4', '#e5dcc5', '#f5e6d3'
    ])
    ax4.imshow(world.continent.heightmap, cmap=cmap_terrain, interpolation='bilinear', alpha=0.9)

    # Spine
    if world.continent.spine_path is not None:
        ax4.plot(spine[:, 0], spine[:, 1], 'r-', linewidth=1, alpha=0.5)

    # Organs
    organ_colors_config = config.get('visualization', {}).get('organ_colors', {})
    default_colors = {
        'metabolic_organ': '#FF4444',
        'digestive': '#FF8844',
        'neural_cluster': '#4488FF',
        'immune_node': '#44FF88'
    }

    for organ_id, organ in world.organs.items():
        x, y = organ.position
        color = organ_colors_config.get(organ.type, default_colors.get(organ.type, '#FFFFFF'))

        circle = plt.Circle((x, y), organ.radius, color=color, alpha=0.9,
                           linewidth=2, edgecolor='white')
        ax4.add_patch(circle)

        # Abbreviated label
        label = organ_id.split('_')[-1][:3].upper()
        ax4.text(x, y, label, ha='center', va='center',
                fontsize=7, fontweight='bold', color='white')

    ax4.set_title('4. Complete WP1 (Foundation)', fontsize=14, fontweight='bold')
    ax4.axis('off')

    # Main title
    fig.suptitle(f'WP1: World Foundation - Seed: {world.seed}',
                fontsize=18, fontweight='bold', y=0.98)

    plt.tight_layout(rect=[0, 0, 1, 0.97])
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[OK] Saved: {output_path}")


def generate_single_world(seed: str, config: dict, output_dir: Path, verbose: bool = True) -> dict:
    """
    Generate and visualize a single world

    Args:
        seed: World seed
        config: Configuration dict
        output_dir: Output directory for images
        verbose: Print detailed output

    Returns:
        dict with world statistics
    """
    # Generate world
    if verbose:
        print(f"Generating world (seed: {seed})...")

    generator = WorldGeneratorV3(config)
    world = generator.generate_wp1(seed)

    # Statistics
    stats = {
        'seed': seed,
        'land_area': world.continent.mask.sum(),
        'land_percentage': world.continent.mask.mean() * 100,
        'center': world.continent.center,
        'organs': len(world.organs),
        'spine_points': len(world.continent.spine_path) if world.continent.spine_path is not None else 0
    }

    if verbose:
        print(f"[OK] World generated:")
        print(f"  - Continent area: {stats['land_area']} pixels ({stats['land_percentage']:.1f}%)")
        print(f"  - Center: {stats['center']}")
        print(f"  - Organs: {stats['organs']}")
        print(f"  - Spine points: {stats['spine_points']}")
        print()

    # Generate visualizations
    if verbose:
        print("Generating visualizations...")

    # Create seed-specific subdirectory
    seed_dir = output_dir / seed
    seed_dir.mkdir(exist_ok=True, parents=True)

    # 1. Black/white mask
    visualize_continent_bw(world, seed_dir / 'wp1_foundation_bw.png')

    # 2. Spine overlay
    visualize_spine_overlay(world, seed_dir / 'wp1_spine_overlay.png')

    # 3. Organs placement
    visualize_organs_placement(world, config, seed_dir / 'wp1_organs_placement.png')

    # 4. Full composite (final artifact)
    visualize_full_composite(world, config, seed_dir / 'wp1_full_composite.png')

    return stats


def batch_generate(count: int, config: dict, output_dir: Path, seed_prefix: str = 'batch',
                   random_seeds: bool = False) -> list:
    """
    Generate multiple worlds with different seeds

    Args:
        count: Number of worlds to generate
        config: Configuration dict
        output_dir: Base output directory
        seed_prefix: Prefix for generated seeds (if not random)
        random_seeds: Use random UUID seeds instead of numbered

    Returns:
        List of statistics dicts for all worlds
    """
    import time
    import uuid

    print(f"\n{'='*60}")
    print(f"BATCH GENERATION: {count} worlds")
    print(f"{'='*60}\n")

    all_stats = []
    start_time = time.time()

    for i in range(1, count + 1):
        # Generate seed
        if random_seeds:
            seed = str(uuid.uuid4())[:8]
        else:
            seed = f"{seed_prefix}_{i:03d}"

        print(f"[{i}/{count}] Seed: {seed}")
        print("-" * 60)

        try:
            stats = generate_single_world(seed, config, output_dir, verbose=False)
            all_stats.append(stats)

            print(f"  Land: {stats['land_percentage']:.1f}%, Center: {stats['center']}, Organs: {stats['organs']}")
            print(f"  Output: {output_dir / seed}")
            print()

        except Exception as e:
            print(f"  [ERROR] Failed: {e}")
            print()
            continue

    # Summary
    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"BATCH COMPLETE: {len(all_stats)}/{count} worlds generated in {elapsed:.1f}s")
    print(f"{'='*60}")

    if all_stats:
        avg_land = sum(s['land_percentage'] for s in all_stats) / len(all_stats)
        min_land = min(s['land_percentage'] for s in all_stats)
        max_land = max(s['land_percentage'] for s in all_stats)

        print(f"\nStatistics:")
        print(f"  Average land: {avg_land:.1f}%")
        print(f"  Min land: {min_land:.1f}%")
        print(f"  Max land: {max_land:.1f}%")
        print(f"  Avg time per world: {elapsed/len(all_stats):.2f}s")
        print()

    return all_stats


def main():
    parser = argparse.ArgumentParser(
        description='Visualize WP1: Foundation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single world
  python scripts/visualize_wp1_foundation.py --seed my_world

  # Batch generate 10 worlds
  python scripts/visualize_wp1_foundation.py --batch 10

  # Batch with random seeds
  python scripts/visualize_wp1_foundation.py --batch 5 --random-seeds

  # Custom seed prefix
  python scripts/visualize_wp1_foundation.py --batch 3 --seed-prefix "test"
        """
    )

    # Single world mode
    parser.add_argument('--seed', type=str, default=None,
                       help='World seed for single generation')
    parser.add_argument('--config', type=str, default='config/world_generation_v3.yaml',
                       help='Config file path')
    parser.add_argument('--output-dir', type=str, default='output',
                       help='Output directory (default: output)')

    # Batch mode
    parser.add_argument('--batch', type=int, default=None,
                       help='Generate multiple worlds (specify count)')
    parser.add_argument('--seed-prefix', type=str, default='batch',
                       help='Prefix for batch seeds (default: batch)')
    parser.add_argument('--random-seeds', action='store_true',
                       help='Use random UUID seeds instead of numbered')

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    # Load config
    config = load_config(args.config)

    # Batch mode
    if args.batch is not None:
        if args.batch < 1:
            print("[ERROR] Batch count must be >= 1")
            return

        batch_generate(
            count=args.batch,
            config=config,
            output_dir=output_dir,
            seed_prefix=args.seed_prefix,
            random_seeds=args.random_seeds
        )
        return

    # Single world mode
    seed = args.seed if args.seed else 'silgarron_world_001'

    print(f"\n{'='*60}")
    print(f"WP1 Visualization - World Foundation")
    print(f"{'='*60}")
    print(f"Seed: {seed}")
    print(f"Config: {args.config}")
    print(f"Output: {output_dir}")
    print(f"{'='*60}\n")

    generate_single_world(seed, config, output_dir, verbose=True)

    print(f"\n{'='*60}")
    print("[OK] WP1 Visualization Complete!")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
