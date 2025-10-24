"""
Visualize Respiratory System - Visualization tool for alveolar caverns and exhalation

Creates a 2x2 panel visualization showing:
1. Elevation + Ridge (base structure)
2. Alveolar Caverns (placement pattern)
3. Exhalation Influence (BFS spread with decay)
4. Bioactive Saturation (zones of high activity)

Usage:
    python tools/visualize_respiratory.py [seed]

Example:
    python tools/visualize_respiratory.py silgarron_respiratory
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.world_generator import WorldGenerator


def visualize_respiratory_system(seed: str = "silgarron_respiratory"):
    """
    Generate and visualize respiratory system.

    Args:
        seed: World generation seed
    """
    print(f"Generating world with seed: '{seed}'...")
    gen = WorldGenerator(seed=seed)

    # Generate world
    skeletal = gen._generate_skeletal_structure()
    respiratory = gen._generate_respiratory_system(skeletal)

    elevation = skeletal['elevation']
    ridge_mask = skeletal['ridge_mask']
    caverns = respiratory['caverns']
    exhalation_influence = respiratory['exhalation_influence']
    bioactive_saturation = respiratory['bioactive_saturation']

    print(f"World generated successfully!")
    print(f"  Caverns: {len(caverns)}")
    print(f"  Exhalation max: {exhalation_influence.max():.3f}")
    print(f"  Bioactive cells: {np.sum(bioactive_saturation > 0)} ({np.sum(bioactive_saturation > 0) / bioactive_saturation.size * 100:.1f}%)")

    # Create visualization
    fig, axes = plt.subplots(2, 2, figsize=(14, 14))
    fig.suptitle(f'Respiratory System - Seed: "{seed}"', fontsize=16, fontweight='bold')

    # Panel 1: Elevation + Ridge
    ax1 = axes[0, 0]
    im1 = ax1.imshow(elevation, cmap='terrain', interpolation='nearest')

    # Overlay ridge as contour
    ridge_contour = ridge_mask > 0.5
    ax1.contour(ridge_contour, colors='red', linewidths=1.5, alpha=0.7)

    ax1.set_title('1. Elevation + Ridge (base structure)', fontsize=12, fontweight='bold')
    ax1.set_xlabel('X (hex)')
    ax1.set_ylabel('Y (hex)')
    plt.colorbar(im1, ax=ax1, label='Elevation')

    # Panel 2: Alveolar Caverns (placement pattern)
    ax2 = axes[0, 1]

    # Show elevation as background
    ax2.imshow(elevation, cmap='gray', alpha=0.3, interpolation='nearest')

    # Create cavern visualization
    cavern_map = np.zeros_like(elevation)
    for y, x in caverns:
        # Mark cavern and surrounding area
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                ny, nx = y + dy, x + dx
                if 0 <= ny < elevation.shape[0] and 0 <= nx < elevation.shape[1]:
                    distance = np.sqrt(dy**2 + dx**2)
                    if distance <= 2:
                        cavern_map[ny, nx] = max(cavern_map[ny, nx], 1.0 - distance / 3.0)

    im2 = ax2.imshow(cavern_map, cmap='Reds', interpolation='nearest', alpha=0.8)

    # Mark centers
    if caverns:
        cavern_y, cavern_x = zip(*caverns)
        ax2.scatter(cavern_x, cavern_y, c='darkred', s=30, marker='o', edgecolors='yellow', linewidths=1.5, label=f'{len(caverns)} caverns')

    ax2.set_title(f'2. Alveolar Caverns ({len(caverns)} placed via Poisson)', fontsize=12, fontweight='bold')
    ax2.set_xlabel('X (hex)')
    ax2.set_ylabel('Y (hex)')
    ax2.legend(loc='upper right')
    plt.colorbar(im2, ax=ax2, label='Cavern intensity')

    # Panel 3: Exhalation Influence (BFS spread)
    ax3 = axes[1, 0]

    # Custom colormap: black → red → yellow
    colors_exh = ['black', 'darkred', 'red', 'orange', 'yellow']
    cmap_exh = LinearSegmentedColormap.from_list('exhalation', colors_exh)

    im3 = ax3.imshow(exhalation_influence, cmap=cmap_exh, interpolation='nearest')

    ax3.set_title('3. Exhalation Influence (BFS with decay=0.92)', fontsize=12, fontweight='bold')
    ax3.set_xlabel('X (hex)')
    ax3.set_ylabel('Y (hex)')
    plt.colorbar(im3, ax=ax3, label='Spore intensity [0, 1]')

    # Panel 4: Bioactive Saturation
    ax4 = axes[1, 1]

    # Custom colormap: black → purple → magenta
    colors_bio = ['black', 'darkblue', 'blue', 'purple', 'magenta']
    cmap_bio = LinearSegmentedColormap.from_list('bioactive', colors_bio)

    im4 = ax4.imshow(bioactive_saturation, cmap=cmap_bio, interpolation='nearest')

    bioactive_count = np.sum(bioactive_saturation > 0.3)
    bioactive_ratio = bioactive_count / bioactive_saturation.size

    ax4.set_title(f'4. Bioactive Saturation ({bioactive_ratio*100:.1f}% >30%)', fontsize=12, fontweight='bold')
    ax4.set_xlabel('X (hex)')
    ax4.set_ylabel('Y (hex)')
    plt.colorbar(im4, ax=ax4, label='Saturation [0, 1]')

    # Save figure
    output_path = f'output/respiratory_system_{seed}.png'
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\nVisualization saved to: {output_path}")

    # Show statistics
    print("\n=== Statistics ===")
    print(f"Caverns placed: {len(caverns)}")
    print(f"Min distance between caverns: {_calculate_min_distance(caverns):.1f} pixels")
    print(f"Exhalation coverage (>1%): {np.sum(exhalation_influence > 0.01) / exhalation_influence.size * 100:.1f}%")
    print(f"Exhalation coverage (>30%): {np.sum(exhalation_influence > 0.3) / exhalation_influence.size * 100:.1f}%")
    print(f"Bioactive saturation (>30%): {bioactive_ratio * 100:.1f}%")

    plt.show()


def _calculate_min_distance(caverns):
    """Calculate minimum distance between caverns"""
    if len(caverns) < 2:
        return float('inf')

    min_dist = float('inf')
    for i, (y1, x1) in enumerate(caverns):
        for y2, x2 in caverns[i+1:]:
            dist = np.sqrt((y1 - y2)**2 + (x1 - x2)**2)
            min_dist = min(min_dist, dist)

    return min_dist


if __name__ == "__main__":
    seed = sys.argv[1] if len(sys.argv) > 1 else "silgarron_respiratory"
    visualize_respiratory_system(seed)
