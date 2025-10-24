"""
Tissue Map Visualization - Sprint 3.5, Task 2.2

Creates visual representation of tissue types with color-coded map.
"""

import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.world_generator import WorldGenerator


def visualize_tissue_map(seed: str, output_path: str = None):
    """
    Generate and visualize tissue map.

    Args:
        seed: World seed
        output_path: Optional output path for PNG
    """
    print(f"=== Tissue Map Visualization ===")
    print(f"Seed: {seed}")

    # Generate world
    gen = WorldGenerator(seed=seed)
    result = gen.generate()

    # Extract data
    tissue_map = result['tissues']['tissue_map']
    tissue_info = result['tissues']['tissue_info']

    # Create figure
    fig = plt.figure(figsize=(18, 14))
    fig.suptitle(f"Tissue Map - Seed: {seed}", fontsize=16, fontweight='bold')

    # === Panel 1: Full Tissue Map ===
    ax1 = plt.subplot(2, 2, 1)

    # Create colormap from tissue colors
    tissue_ids = sorted(tissue_info.keys())
    colors = []
    labels = []

    for tissue_id in tissue_ids:
        info = tissue_info[tissue_id]
        colors.append(info['color'])
        labels.append(info['name'])

    cmap = ListedColormap(colors)

    # Remap tissue_map to 0-based indices for colormap
    display_map = np.zeros_like(tissue_map)
    for idx, tissue_id in enumerate(tissue_ids):
        display_map[tissue_map == tissue_id] = idx

    im1 = ax1.imshow(display_map, cmap=cmap, interpolation='nearest', vmin=0, vmax=len(tissue_ids)-1)
    ax1.set_title("Complete Tissue Map", fontsize=12, fontweight='bold')
    ax1.set_xlabel("X (hex)")
    ax1.set_ylabel("Y (hex)")

    # Create legend
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=colors[i], label=labels[i]) for i in range(len(tissue_ids))]
    ax1.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.02, 1), fontsize=8)

    # === Panel 2: Tissue Distribution (Pie Chart) ===
    ax2 = plt.subplot(2, 2, 2)

    # Calculate tissue percentages
    tissue_counts = []
    tissue_labels = []
    tissue_colors = []

    for tissue_id in tissue_ids:
        count = np.sum(tissue_map == tissue_id)
        if count > 0:
            tissue_counts.append(count)
            tissue_labels.append(f"{tissue_info[tissue_id]['name']}\n({count} cells)")
            tissue_colors.append(tissue_info[tissue_id]['color'])

    ax2.pie(tissue_counts, labels=tissue_labels, colors=tissue_colors, autopct='%1.1f%%', startangle=90)
    ax2.set_title("Tissue Distribution", fontsize=12, fontweight='bold')

    # === Panel 3: Special Tissues Only ===
    ax3 = plt.subplot(2, 2, 3)

    # Highlight special tissues (caverns, lymph sources, lymph channels)
    special_mask = np.zeros((256, 256, 3))  # RGB

    for tissue_id in tissue_ids:
        info = tissue_info[tissue_id]
        mask = tissue_map == tissue_id

        # Check for special tags
        if 'breathing:source' in info['tags']:
            # Alveolar caverns - red
            special_mask[mask] = [1.0, 0.0, 0.0]
        elif 'location:sacred' in info['tags']:
            # Lymph springheads - cyan
            special_mask[mask] = [0.0, 1.0, 1.0]
        elif 'resource:pure_lymph' in info['tags'] and info['id'] == 'lymph_channels':
            # Lymph channels - gold
            special_mask[mask] = [1.0, 0.84, 0.0]

    ax3.imshow(special_mask, interpolation='nearest')
    ax3.set_title("Special Tissues (Caverns, Lymph)", fontsize=12, fontweight='bold')
    ax3.set_xlabel("X (hex)")
    ax3.set_ylabel("Y (hex)")

    # Add legend
    from matplotlib.patches import Patch
    special_legend = [
        Patch(facecolor='red', label='Alveolar Caverns'),
        Patch(facecolor='cyan', label='Lymph Springheads'),
        Patch(facecolor='gold', label='Lymph Channels')
    ]
    ax3.legend(handles=special_legend, loc='upper right', fontsize=8)

    # === Panel 4: Tissue Statistics ===
    ax4 = plt.subplot(2, 2, 4)
    ax4.axis('off')

    # Create statistics text
    stats_text = "=== Tissue Statistics ===\n\n"
    stats_text += f"Total Cells: {tissue_map.size:,}\n"
    stats_text += f"Unique Tissues: {len(tissue_info)}\n\n"

    stats_text += "Tissue Coverage:\n"
    stats_text += "-" * 40 + "\n"

    # Sort by coverage
    tissue_coverage = []
    for tissue_id in tissue_ids:
        count = np.sum(tissue_map == tissue_id)
        if count > 0:
            pct = count / tissue_map.size * 100
            tissue_coverage.append((tissue_info[tissue_id]['name'], count, pct))

    tissue_coverage.sort(key=lambda x: x[1], reverse=True)

    for name, count, pct in tissue_coverage:
        stats_text += f"{name:30s}: {count:5d} ({pct:5.1f}%)\n"

    ax4.text(0.05, 0.95, stats_text, transform=ax4.transAxes,
             fontsize=9, verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

    plt.tight_layout()

    # Save or show
    if output_path:
        output_file = Path(f"output/tissue_map_{output_path}.png")
        output_file.parent.mkdir(exist_ok=True)
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"\n[OK] Saved to {output_file}")
    else:
        plt.show()


if __name__ == "__main__":
    # Get seed from command line or use default
    seed = sys.argv[1] if len(sys.argv) > 1 else "silgarron_alpha"

    visualize_tissue_map(seed, output_path=seed)
