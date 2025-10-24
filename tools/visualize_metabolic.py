"""
Visualize Metabolic System - Visualization tool for metabolic temperature

Creates a comprehensive 2x3 panel visualization showing:
1. Elevation + Ridge (structure)
2. Lymph Intensity (circulation)
3. Bioactive Saturation (respiratory activity)
4. Metabolic Temperature (combined)
5. Cold Zones (<0.3)
6. Hot Zones (>0.7)

Usage:
    python tools/visualize_metabolic.py [seed]

Example:
    python tools/visualize_metabolic.py silgarron_metabolic
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.world_generator import WorldGenerator


def visualize_metabolic_system(seed: str = "silgarron_metabolic"):
    """
    Generate and visualize metabolic system.

    Args:
        seed: World generation seed
    """
    print(f"Generating world with seed: '{seed}'...")
    gen = WorldGenerator(seed=seed)

    # Generate all systems
    skeletal = gen._generate_skeletal_structure()
    lymphatic = gen._generate_lymphatic_system(skeletal)
    respiratory = gen._generate_respiratory_system(skeletal)
    metabolic = gen._generate_metabolic_activity(skeletal, lymphatic, respiratory)

    elevation = skeletal['elevation']
    ridge_mask = skeletal['ridge_mask']
    lymph_intensity = lymphatic['lymph_intensity']
    bioactive_saturation = respiratory['bioactive_saturation']
    temperature = metabolic['temperature']

    print(f"World generated successfully!")
    print(f"  Temperature range: {temperature.min():.3f} - {temperature.max():.3f}")
    print(f"  Mean temperature: {temperature.mean():.3f}")
    print(f"  Cold zones (<0.3): {np.sum(temperature < 0.3) / temperature.size * 100:.1f}%")
    print(f"  Hot zones (>0.7): {np.sum(temperature > 0.7) / temperature.size * 100:.1f}%")

    # Create visualization
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle(f'Metabolic System - Seed: "{seed}"', fontsize=18, fontweight='bold')

    # Panel 1: Elevation + Ridge
    ax1 = axes[0, 0]
    im1 = ax1.imshow(elevation, cmap='terrain', interpolation='nearest')
    ridge_contour = ridge_mask > 0.5
    ax1.contour(ridge_contour, colors='red', linewidths=1.5, alpha=0.7)
    ax1.set_title('1. Elevation + Ridge\n(Skeletal Structure)', fontsize=11, fontweight='bold')
    ax1.set_xlabel('X (hex)')
    ax1.set_ylabel('Y (hex)')
    plt.colorbar(im1, ax=ax1, label='Elevation')

    # Panel 2: Lymph Intensity
    ax2 = axes[0, 1]
    colors_lymph = ['black', 'darkblue', 'blue', 'cyan', 'yellow', 'gold']
    cmap_lymph = LinearSegmentedColormap.from_list('lymph', colors_lymph)
    im2 = ax2.imshow(lymph_intensity, cmap=cmap_lymph, interpolation='nearest')

    lymph_coverage = np.sum(lymph_intensity > 0.1) / lymph_intensity.size
    ax2.set_title(f'2. Lymph Intensity\n(Circulation: {lymph_coverage*100:.1f}% active)',
                  fontsize=11, fontweight='bold')
    ax2.set_xlabel('X (hex)')
    ax2.set_ylabel('Y (hex)')
    plt.colorbar(im2, ax=ax2, label='Lymph Flow [0, 1]')

    # Panel 3: Bioactive Saturation
    ax3 = axes[0, 2]
    colors_bio = ['black', 'darkmagenta', 'magenta', 'violet', 'pink']
    cmap_bio = LinearSegmentedColormap.from_list('bioactive', colors_bio)
    im3 = ax3.imshow(bioactive_saturation, cmap=cmap_bio, interpolation='nearest')

    bio_coverage = np.sum(bioactive_saturation > 0.3) / bioactive_saturation.size
    ax3.set_title(f'3. Bioactive Saturation\n(Respiratory: {bio_coverage*100:.1f}% active)',
                  fontsize=11, fontweight='bold')
    ax3.set_xlabel('X (hex)')
    ax3.set_ylabel('Y (hex)')
    plt.colorbar(im3, ax=ax3, label='Saturation [0, 1]')

    # Panel 4: Metabolic Temperature (main result)
    ax4 = axes[1, 0]
    colors_temp = ['darkblue', 'blue', 'cyan', 'green', 'yellow', 'orange', 'red', 'darkred']
    cmap_temp = LinearSegmentedColormap.from_list('temperature', colors_temp)
    im4 = ax4.imshow(temperature, cmap=cmap_temp, interpolation='nearest', vmin=0, vmax=1)

    ax4.set_title(f'4. Metabolic Temperature\n(Combined: mean={temperature.mean():.3f})',
                  fontsize=11, fontweight='bold')
    ax4.set_xlabel('X (hex)')
    ax4.set_ylabel('Y (hex)')
    cbar4 = plt.colorbar(im4, ax=ax4, label='Temperature [0=Cold, 1=Hot]')
    cbar4.set_ticks([0, 0.25, 0.5, 0.75, 1.0])
    cbar4.set_ticklabels(['0.0\n(Bone)', '0.25', '0.5\n(Moderate)', '0.75', '1.0\n(Active)'])

    # Panel 5: Cold Zones (<0.3)
    ax5 = axes[1, 1]
    cold_mask = temperature < 0.3
    cold_display = np.where(cold_mask, temperature, np.nan)

    ax5.imshow(elevation, cmap='gray', alpha=0.3, interpolation='nearest')
    im5 = ax5.imshow(cold_display, cmap='Blues_r', interpolation='nearest', vmin=0, vmax=0.3)

    cold_count = np.sum(cold_mask)
    cold_ratio = cold_count / temperature.size
    ax5.set_title(f'5. Cold Zones (<0.3)\n({cold_ratio*100:.1f}% of map = bone/dead tissue)',
                  fontsize=11, fontweight='bold')
    ax5.set_xlabel('X (hex)')
    ax5.set_ylabel('Y (hex)')
    plt.colorbar(im5, ax=ax5, label='Cold Temperature')

    # Panel 6: Hot Zones (>0.7)
    ax6 = axes[1, 2]
    hot_mask = temperature > 0.7
    hot_display = np.where(hot_mask, temperature, np.nan)

    ax6.imshow(elevation, cmap='gray', alpha=0.3, interpolation='nearest')
    im6 = ax6.imshow(hot_display, cmap='hot', interpolation='nearest', vmin=0.7, vmax=1.0)

    hot_count = np.sum(hot_mask)
    hot_ratio = hot_count / temperature.size
    ax6.set_title(f'6. Hot Zones (>0.7)\n({hot_ratio*100:.1f}% of map = active metabolism)',
                  fontsize=11, fontweight='bold')
    ax6.set_xlabel('X (hex)')
    ax6.set_ylabel('Y (hex)')
    plt.colorbar(im6, ax=ax6, label='Hot Temperature')

    # Save figure
    output_path = f'output/metabolic_system_{seed}.png'
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\nVisualization saved to: {output_path}")

    # Show component statistics
    print("\n=== Component Contributions ===")

    # Calculate individual components
    bone_mask = ridge_mask > 0.7
    bone_coverage = np.sum(bone_mask) / bone_mask.size
    print(f"Bone (cold ridge): {bone_coverage*100:.1f}% of map")

    lymph_active = np.sum(lymph_intensity > 0.1) / lymph_intensity.size
    print(f"Lymph (warm flow): {lymph_active*100:.1f}% of map")

    bio_active = np.sum(bioactive_saturation > 0.3) / bioactive_saturation.size
    print(f"Bioactive (warm zones): {bio_active*100:.1f}% of map")

    # Temperature distribution
    print("\n=== Temperature Distribution ===")
    bins = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
    labels = ['Very Cold (0.0-0.2)', 'Cold (0.2-0.4)', 'Moderate (0.4-0.6)',
              'Warm (0.6-0.8)', 'Hot (0.8-1.0)']

    for i in range(len(bins)-1):
        count = np.sum((temperature >= bins[i]) & (temperature < bins[i+1]))
        ratio = count / temperature.size
        print(f"  {labels[i]}: {ratio*100:.1f}%")

    plt.show()


if __name__ == "__main__":
    seed = sys.argv[1] if len(sys.argv) > 1 else "silgarron_metabolic"
    visualize_metabolic_system(seed)
