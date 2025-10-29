"""
Compare linear vs walker spine generation methods.
Creates a side-by-side comparison visualization.
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import matplotlib.pyplot as plt
import matplotlib.image as mpimg

def create_comparison():
    """Create side-by-side comparison of linear vs walker methods"""

    # Define image paths
    linear_img = project_root / "output" / "comparison_linear" / "wp1_spine_overlay.png"
    walker_img = project_root / "output" / "walker_006" / "wp1_spine_overlay.png"

    # Check if images exist
    if not linear_img.exists():
        print(f"[ERROR] Linear image not found: {linear_img}")
        return
    if not walker_img.exists():
        print(f"[ERROR] Walker image not found: {walker_img}")
        return

    # Load images
    linear = mpimg.imread(str(linear_img))
    walker = mpimg.imread(str(walker_img))

    # Create figure
    fig, axes = plt.subplots(1, 2, figsize=(16, 8))
    fig.suptitle('Spine Generation Methods Comparison', fontsize=16, fontweight='bold')

    # Linear method
    axes[0].imshow(linear)
    axes[0].set_title('LINEAR Method\n(Classic S-curves, always progressing)', fontsize=12)
    axes[0].axis('off')

    # Walker method
    axes[1].imshow(walker)
    axes[1].set_title('WALKER Method\n(Spirals and rings possible)', fontsize=12)
    axes[1].axis('off')

    plt.tight_layout()

    # Save
    output_path = project_root / "output" / "spine_methods_comparison.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"[OK] Comparison saved: {output_path}")

    plt.close()

if __name__ == "__main__":
    print("Creating spine methods comparison...")
    create_comparison()
    print("[OK] Comparison complete!")
