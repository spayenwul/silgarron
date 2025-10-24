"""
World Map Export Tool - Sprint 3.5, Phase 3

Exports generated world map to JSON format for use in game/visualization.
"""

import sys
import json
from pathlib import Path
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.world_generator import WorldGenerator


def export_world_map(seed: str, output_format: str = "metadata", output_dir: str = "output"):
    """
    Generate and export world map to JSON.

    Args:
        seed: World generation seed
        output_format: Export format:
            - "metadata": Only metadata (tiny file)
            - "sample": Sample of 1000 sectors (small file)
            - "full": All 65,536 sectors (large file, ~50MB)
        output_dir: Output directory

    Outputs:
        - world_map_{seed}_metadata.json - Metadata only
        - world_map_{seed}_sample.json - Sample sectors
        - world_map_{seed}_full.json - Complete map
    """
    print(f"=== World Map Export ===")
    print(f"Seed: {seed}")
    print(f"Format: {output_format}")
    print()

    # Generate world
    start_time = time.time()
    gen = WorldGenerator(seed=seed)
    result = gen.generate()
    generation_time = time.time() - start_time

    world_map = result['world_map']

    print(f"\nGeneration completed in {generation_time:.1f}s")
    print(f"World Map: {world_map}")
    print()

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Export based on format
    if output_format == "metadata":
        export_metadata(world_map, seed, output_path)

    elif output_format == "sample":
        export_sample(world_map, seed, output_path, sample_size=1000)

    elif output_format == "full":
        export_full(world_map, seed, output_path)

    else:
        print(f"[ERROR] Unknown format: {output_format}")
        print("Valid formats: metadata, sample, full")


def export_metadata(world_map, seed: str, output_path: Path):
    """Export metadata only (tiny file)."""
    filepath = output_path / f"world_map_{seed}_metadata.json"

    stats = world_map.get_statistics()

    data = {
        'seed': world_map.seed,
        'width': world_map.width,
        'height': world_map.height,
        'total_sectors': len(world_map.sectors),
        'statistics': {
            'average_elevation': round(stats['average_elevation'], 3),
            'average_temperature': round(stats['average_temperature'], 3),
            'lymph_channels': stats['lymph_channels'],
            'caverns': stats['caverns'],
            'tissue_distribution': {
                tissue_id: round(pct, 2)
                for tissue_id, pct in stats['tissue_distribution'].items()
            }
        }
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    file_size = filepath.stat().st_size / 1024
    print(f"[OK] Metadata exported to {filepath} ({file_size:.1f} KB)")


def export_sample(world_map, seed: str, output_path: Path, sample_size: int = 1000):
    """Export sample of sectors (small file)."""
    filepath = output_path / f"world_map_{seed}_sample.json"

    stats = world_map.get_statistics()

    # Sample sectors (evenly distributed)
    step = max(1, len(world_map.sectors) // sample_size)
    sampled_sectors = []

    for i, sector in enumerate(world_map.sectors.values()):
        if i % step == 0:
            sampled_sectors.append(sector.to_dict())
            if len(sampled_sectors) >= sample_size:
                break

    data = {
        'seed': world_map.seed,
        'width': world_map.width,
        'height': world_map.height,
        'total_sectors': len(world_map.sectors),
        'sampled_count': len(sampled_sectors),
        'statistics': {
            'average_elevation': round(stats['average_elevation'], 3),
            'average_temperature': round(stats['average_temperature'], 3),
            'lymph_channels': stats['lymph_channels'],
            'caverns': stats['caverns']
        },
        'sectors': sampled_sectors
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    file_size = filepath.stat().st_size / 1024
    print(f"[OK] Sample exported to {filepath} ({file_size:.1f} KB, {len(sampled_sectors)} sectors)")


def export_full(world_map, seed: str, output_path: Path):
    """Export all sectors (large file, ~50MB)."""
    filepath = output_path / f"world_map_{seed}_full.json"

    print(f"[WARNING] Exporting {len(world_map.sectors)} sectors...")
    print(f"[WARNING] This will create a large file (~50MB)...")

    start_time = time.time()

    stats = world_map.get_statistics()

    # Export all sectors
    all_sectors = [sector.to_dict() for sector in world_map.sectors.values()]

    data = {
        'seed': world_map.seed,
        'width': world_map.width,
        'height': world_map.height,
        'total_sectors': len(world_map.sectors),
        'statistics': {
            'average_elevation': round(stats['average_elevation'], 3),
            'average_temperature': round(stats['average_temperature'], 3),
            'lymph_channels': stats['lymph_channels'],
            'caverns': stats['caverns'],
            'tissue_distribution': {
                tissue_id: round(pct, 2)
                for tissue_id, pct in stats['tissue_distribution'].items()
            }
        },
        'sectors': all_sectors
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    export_time = time.time() - start_time
    file_size = filepath.stat().st_size / 1024 / 1024
    print(f"[OK] Full map exported to {filepath} ({file_size:.1f} MB, {export_time:.1f}s)")


if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: python export_world_map.py <seed> [format]")
        print()
        print("Arguments:")
        print("  seed    - World generation seed (e.g., 'silgarron_alpha')")
        print("  format  - Export format: metadata|sample|full (default: metadata)")
        print()
        print("Examples:")
        print("  python export_world_map.py silgarron_alpha")
        print("  python export_world_map.py silgarron_alpha sample")
        print("  python export_world_map.py silgarron_alpha full")
        sys.exit(1)

    seed = sys.argv[1]
    output_format = sys.argv[2] if len(sys.argv) > 2 else "metadata"

    export_world_map(seed, output_format)
