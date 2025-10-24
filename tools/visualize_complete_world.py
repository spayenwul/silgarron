"""
Complete World Visualization - Sprint 3.5, Phase 4

Creates comprehensive multi-layer visualization of generated world.
Shows all physiological systems and tissue types together.
"""

import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, LinearSegmentedColormap
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.world_generator import WorldGenerator


def create_complete_world_visualization(seed: str, output_path: str = None):
    """
    Generate and visualize complete world with all layers.

    Args:
        seed: World generation seed
        output_path: Optional output path for PNG

    Creates:
        - 3x3 grid showing all systems
        - High-resolution output (4K+)
        - Color-coded tissue map
    """
    print(f"=== Complete World Visualization ===")
    print(f"Seed: {seed}")
    print()

    # Generate world
    gen = WorldGenerator(seed=seed)
    result = gen.generate()

    # Extract all data
    skeletal = result['skeletal']
    lymphatic = result['lymphatic']
    respiratory = result['respiratory']
    metabolic = result['metabolic']
    tissues = result['tissues']
    world_map = result['world_map']

    # Create figure (3x3 grid, high-res)
    fig = plt.figure(figsize=(24, 24))
    fig.suptitle(f"Complete World Map - Seed: {seed}", fontsize=24, fontweight='bold', y=0.995)

    # === Panel 1: Elevation + Ridge ===
    ax1 = plt.subplot(3, 3, 1)
    elevation_display = skeletal['elevation'].copy()
    ridge_mask = skeletal['ridge_mask']

    # Overlay ridge in red
    elevation_rgb = plt.cm.terrain(elevation_display)
    elevation_rgb[ridge_mask > 0.7, 0] = 1.0  # Red channel
    elevation_rgb[ridge_mask > 0.7, 1] *= 0.3  # Darken green
    elevation_rgb[ridge_mask > 0.7, 2] *= 0.3  # Darken blue

    ax1.imshow(elevation_rgb, interpolation='bilinear')
    ax1.set_title("1. Skeletal Structure\n(Elevation + Ridge)", fontsize=12, fontweight='bold')
    ax1.axis('off')

    # === Panel 2: Lymphatic System ===
    ax2 = plt.subplot(3, 3, 2)
    lymph_intensity = lymphatic['lymph_intensity']
    lymph_channels = lymphatic['lymph_channels']

    # Create lymph visualization
    lymph_display = lymph_intensity.copy()
    lymph_display[lymph_channels > 0] = 1.0  # Highlight channels

    im2 = ax2.imshow(lymph_display, cmap='YlOrRd', interpolation='bilinear', vmin=0, vmax=1)
    ax2.set_title("2. Lymphatic System\n(Channels + Flow)", fontsize=12, fontweight='bold')
    ax2.axis('off')
    plt.colorbar(im2, ax=ax2, fraction=0.046, pad=0.04)

    # === Panel 3: Respiratory System ===
    ax3 = plt.subplot(3, 3, 3)
    bioactive = respiratory['bioactive_saturation']
    caverns = respiratory['caverns']

    # Mark caverns
    bioactive_display = bioactive.copy()
    for y, x in caverns:
        if 0 <= y < 256 and 0 <= x < 256:
            # Draw cavern as small circle
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < 256 and 0 <= nx < 256:
                        if dy*dy + dx*dx <= 4:
                            bioactive_display[ny, nx] = 1.0

    im3 = ax3.imshow(bioactive_display, cmap='Purples', interpolation='bilinear', vmin=0, vmax=1)
    ax3.set_title("3. Respiratory System\n(Bioactive + Caverns)", fontsize=12, fontweight='bold')
    ax3.axis('off')
    plt.colorbar(im3, ax=ax3, fraction=0.046, pad=0.04)

    # === Panel 4: Metabolic Temperature ===
    ax4 = plt.subplot(3, 3, 4)
    temperature = metabolic['temperature']

    # Custom colormap: blue -> green -> yellow -> red
    colors = ['#0000FF', '#00FFFF', '#00FF00', '#FFFF00', '#FF8800', '#FF0000']
    n_bins = 256
    cmap_temp = LinearSegmentedColormap.from_list('temperature', colors, N=n_bins)

    im4 = ax4.imshow(temperature, cmap=cmap_temp, interpolation='bilinear', vmin=0, vmax=1)
    ax4.set_title("4. Metabolic Temperature\n(Cold = Blue, Hot = Red)", fontsize=12, fontweight='bold')
    ax4.axis('off')
    plt.colorbar(im4, ax=ax4, fraction=0.046, pad=0.04)

    # === Panel 5: Tissue Map (Color-coded) ===
    ax5 = plt.subplot(3, 3, 5)

    tissue_map = tissues['tissue_map']
    tissue_info = tissues['tissue_info']

    # Create colormap from tissue colors
    tissue_ids = sorted(tissue_info.keys())
    colors = [tissue_info[tid]['color'] for tid in tissue_ids]
    cmap_tissue = ListedColormap(colors)

    # Remap to 0-based indices
    display_map = np.zeros_like(tissue_map)
    for idx, tid in enumerate(tissue_ids):
        display_map[tissue_map == tid] = idx

    im5 = ax5.imshow(display_map, cmap=cmap_tissue, interpolation='nearest', vmin=0, vmax=len(tissue_ids)-1)
    ax5.set_title("5. Tissue Types\n(Color-coded Biomes)", fontsize=12, fontweight='bold')
    ax5.axis('off')

    # Legend for tissues (compact)
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=colors[i], label=tissue_info[tissue_ids[i]]['name'][:20])
        for i in range(min(12, len(tissue_ids)))
    ]
    ax5.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.02, 1), fontsize=8, framealpha=0.9)

    # === Panel 6: Ridge Mask (Pure) ===
    ax6 = plt.subplot(3, 3, 6)
    im6 = ax6.imshow(ridge_mask, cmap='Greys', interpolation='bilinear', vmin=0, vmax=1)
    ax6.set_title("6. Ridge Mask\n(Bone Intensity)", fontsize=12, fontweight='bold')
    ax6.axis('off')
    plt.colorbar(im6, ax=ax6, fraction=0.046, pad=0.04)

    # === Panel 7: Combined Physiological ===
    ax7 = plt.subplot(3, 3, 7)

    # Create RGB composite: R=temperature, G=lymph, B=bioactive
    combined = np.zeros((256, 256, 3))
    combined[:, :, 0] = temperature  # Red = temperature
    combined[:, :, 1] = lymph_intensity  # Green = lymph
    combined[:, :, 2] = bioactive  # Blue = bioactive

    ax7.imshow(combined, interpolation='bilinear')
    ax7.set_title("7. Physiological RGB\n(R=Temp, G=Lymph, B=Bioactive)", fontsize=12, fontweight='bold')
    ax7.axis('off')

    # === Panel 8: Special Features ===
    ax8 = plt.subplot(3, 3, 8)

    # Highlight special features
    special_map = np.zeros((256, 256, 3))

    # Lymph channels - gold
    special_map[lymph_channels > 0, 0] = 1.0  # R
    special_map[lymph_channels > 0, 1] = 0.84  # G
    special_map[lymph_channels > 0, 2] = 0.0   # B

    # Caverns - red
    for y, x in caverns:
        if 0 <= y < 256 and 0 <= x < 256:
            for dy in range(-3, 4):
                for dx in range(-3, 4):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < 256 and 0 <= nx < 256:
                        if dy*dy + dx*dx <= 9:
                            special_map[ny, nx] = [1.0, 0.0, 0.0]  # Red

    # Lymph sources - cyan
    for y, x in lymphatic['source_points']:
        if 0 <= y < 256 and 0 <= x < 256:
            for dy in range(-4, 5):
                for dx in range(-4, 5):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < 256 and 0 <= nx < 256:
                        if dy*dy + dx*dx <= 16:
                            special_map[ny, nx] = [0.0, 1.0, 1.0]  # Cyan

    ax8.imshow(special_map, interpolation='nearest')
    ax8.set_title("8. Special Features\n(Cyan=Sources, Gold=Channels, Red=Caverns)", fontsize=12, fontweight='bold')
    ax8.axis('off')

    # === Panel 9: Statistics ===
    ax9 = plt.subplot(3, 3, 9)
    ax9.axis('off')

    # Compile statistics
    stats = world_map.get_statistics()

    stats_text = "=== World Statistics ===\n\n"
    stats_text += f"Seed: {seed}\n"
    stats_text += f"Size: {result['width']}x{result['height']}\n"
    stats_text += f"Total Hexes: {stats['total_sectors']:,}\n\n"

    stats_text += "--- Physiology ---\n"
    stats_text += f"Avg Elevation: {stats['average_elevation']:.3f}\n"
    stats_text += f"Avg Temperature: {stats['average_temperature']:.3f}\n"
    stats_text += f"Lymph Channels: {stats['lymph_channels']} ({stats['lymph_channels']/stats['total_sectors']*100:.1f}%)\n"
    stats_text += f"Caverns: {stats['caverns']}\n"
    stats_text += f"Lymph Sources: {len(lymphatic['source_points'])}\n\n"

    stats_text += "--- Tissue Distribution ---\n"
    tissue_dist = sorted(stats['tissue_distribution'].items(), key=lambda x: x[1], reverse=True)

    # Create reverse mapping: tissue_id_string -> tissue_int -> tissue_info
    tissue_id_to_info = {}
    for tissue_int, info in tissue_info.items():
        tissue_id_to_info[info['id']] = info

    for tissue_id_string, pct in tissue_dist[:8]:
        if tissue_id_string in tissue_id_to_info:
            tissue_name = tissue_id_to_info[tissue_id_string]['name']
            stats_text += f"{tissue_name[:20]:20s}: {pct:5.1f}%\n"

    stats_text += f"\nVersion: {result['generator_version']}"

    ax9.text(0.05, 0.95, stats_text, transform=ax9.transAxes,
             fontsize=10, verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()

    # Save or show
    if output_path:
        output_file = Path(f"output/complete_world_{output_path}.png")
        output_file.parent.mkdir(exist_ok=True)
        plt.savefig(output_file, dpi=200, bbox_inches='tight')
        print(f"\n[OK] Saved to {output_file}")

        # Also save high-res version
        output_file_hires = Path(f"output/complete_world_{output_path}_4k.png")
        plt.savefig(output_file_hires, dpi=300, bbox_inches='tight')
        print(f"[OK] High-res saved to {output_file_hires}")
    else:
        plt.show()


if __name__ == "__main__":
    # Get seed from command line or use default
    seed = sys.argv[1] if len(sys.argv) > 1 else "silgarron_complete"

    create_complete_world_visualization(seed, output_path=seed)
