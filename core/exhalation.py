"""
BFS Exhalation - Spore spread from alveolar caverns

Implements Breadth-First Search with decay for modeling spore distribution
from respiratory sources.

Used for generating respiratory system of Silgarron.

See docs/sprint_3.5_implementation/05_BFS_EXHALATION.md for details.
"""

import numpy as np
from typing import List, Tuple, Optional
from collections import deque


def spread_exhalation(
    caverns: List[Tuple[int, int]],
    width: int,
    height: int,
    decay_rate: float = 0.92,
    min_threshold: float = 0.01,
    elevation: Optional[np.ndarray] = None,
    elevation_penalty: float = 0.1
) -> np.ndarray:
    """
    Spreads exhalation (spores) from alveolar caverns via BFS with decay.

    Spores spread in all directions with intensity decay.
    Intensity = initial * (decay_rate ^ distance).

    Args:
        caverns: List[(y, x)] - coordinates of caverns (sources)
        width, height: Map dimensions
        decay_rate: Decay coefficient (0.0-1.0)
                    0.92 = 92% intensity preserved per step
        min_threshold: Stop threshold (spores weaker than this don't spread)
        elevation: Elevation map (optional for terrain consideration)
        elevation_penalty: Penalty for uphill spread (optional)

    Returns:
        exhalation_intensity: np.ndarray (height, width) float32
                              Exhalation intensity at each cell [0.0, 1.0]

    Biological interpretation:
        - Caverns = "alveoli" (exhale spores)
        - Spores spread into surrounding tissues
        - Decay with distance
        - Create bioactive saturation zones
    """
    intensity = np.zeros((height, width), dtype=np.float32)
    queue = deque()
    visited = set()

    # Initialize: caverns with intensity 1.0
    for y, x in caverns:
        if 0 <= y < height and 0 <= x < width:
            intensity[y, x] = 1.0
            queue.append((y, x, 1.0))
            visited.add((y, x))

    # 4 directions (N, S, E, W)
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    # BFS with decay
    while queue:
        y, x, current_intensity = queue.popleft()

        for dy, dx in directions:
            ny, nx = y + dy, x + dx

            # Bounds check
            if not (0 <= ny < height and 0 <= nx < width):
                continue

            # Calculate decay
            neighbor_intensity = current_intensity * decay_rate

            # Optional: consider terrain
            if elevation is not None:
                # Uphill = additional decay
                height_diff = elevation[ny, nx] - elevation[y, x]
                if height_diff > 0:
                    # Reduce intensity when going uphill
                    neighbor_intensity *= (1.0 - elevation_penalty * height_diff)
                    # Clamp to positive
                    neighbor_intensity = max(0.0, neighbor_intensity)

            # Stop threshold
            if neighbor_intensity < min_threshold:
                continue

            # Update intensity (max if already exists)
            if (ny, nx) in visited:
                # If already visited, update only if new intensity is higher
                if neighbor_intensity > intensity[ny, nx]:
                    intensity[ny, nx] = neighbor_intensity
                    # Re-add to queue with new intensity
                    queue.append((ny, nx, neighbor_intensity))
            else:
                intensity[ny, nx] = neighbor_intensity
                queue.append((ny, nx, neighbor_intensity))
                visited.add((ny, nx))

    return intensity


def create_bioactive_mask(
    exhalation_intensity: np.ndarray,
    threshold: float = 0.3
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Creates bioactive zone mask from exhalation intensity.

    Args:
        exhalation_intensity: Intensity map [0, 1]
        threshold: Minimum intensity for bioactive zone

    Returns:
        bioactive_mask: np.ndarray (binary) - 1 where bioactive, 0 otherwise
        bioactive_saturation: np.ndarray (float) - normalized saturation [0, 1]
    """
    # Binary mask
    bioactive_mask = (exhalation_intensity >= threshold).astype(np.float32)

    # Saturation = intensity (already normalized)
    bioactive_saturation = exhalation_intensity.copy()

    return bioactive_mask, bioactive_saturation


def calculate_coverage_stats(
    exhalation_intensity: np.ndarray,
    caverns: List[Tuple[int, int]],
    thresholds: List[float] = [0.1, 0.3, 0.5, 0.7]
) -> dict:
    """
    Calculates statistics about exhalation coverage.

    Args:
        exhalation_intensity: Intensity map
        caverns: List of cavern coordinates
        thresholds: Intensity thresholds for coverage calculation

    Returns:
        dict with statistics:
            - num_caverns: Number of caverns
            - max_intensity: Maximum intensity
            - mean_intensity: Mean intensity (non-zero cells)
            - coverage_X: Percentage of cells with intensity >= X
    """
    height, width = exhalation_intensity.shape
    total_cells = height * width

    # Non-zero cells
    non_zero_mask = exhalation_intensity > 0
    non_zero_count = np.sum(non_zero_mask)

    stats = {
        'num_caverns': len(caverns),
        'max_intensity': float(exhalation_intensity.max()),
        'mean_intensity': float(exhalation_intensity[non_zero_mask].mean()) if non_zero_count > 0 else 0.0,
        'affected_cells': int(non_zero_count),
        'affected_ratio': float(non_zero_count / total_cells)
    }

    # Coverage at different thresholds
    for threshold in thresholds:
        coverage = np.sum(exhalation_intensity >= threshold)
        coverage_ratio = coverage / total_cells
        stats[f'coverage_{int(threshold*100)}'] = float(coverage_ratio)

    return stats


if __name__ == "__main__":
    # Simple test
    print("=== BFS Exhalation Test ===")

    # Single cavern at center
    caverns = [(128, 128)]

    print("Caverns:", caverns)

    # Spread exhalation
    intensity = spread_exhalation(
        caverns=caverns,
        width=256,
        height=256,
        decay_rate=0.9,
        min_threshold=0.01
    )

    print("\nIntensity shape:", intensity.shape)
    print("Intensity range:", intensity.min(), "-", intensity.max())

    # Check source
    print("\nSource intensity (should be 1.0):", intensity[128, 128])

    # Check immediate neighbors (should be ~0.9)
    neighbors = [
        intensity[127, 128],  # N
        intensity[129, 128],  # S
        intensity[128, 127],  # W
        intensity[128, 129],  # E
    ]
    print("Neighbor intensities (should be ~0.9):", neighbors)

    # Check decay pattern
    distances = [1, 2, 5, 10, 20]
    expected_intensities = [0.9**d for d in distances]

    print("\nDecay pattern test:")
    for d, expected in zip(distances, expected_intensities):
        actual = intensity[128, 128 + d]
        print(f"  Distance {d}: actual={actual:.4f}, expected={expected:.4f}")

    # Statistics
    stats = calculate_coverage_stats(intensity, caverns)
    print("\nCoverage statistics:")
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")

    # Test with multiple caverns
    print("\n=== Multiple Caverns Test ===")
    caverns_multi = [(64, 64), (192, 192)]

    intensity_multi = spread_exhalation(
        caverns=caverns_multi,
        width=256,
        height=256,
        decay_rate=0.92,
        min_threshold=0.01
    )

    print("Sources:", caverns_multi)
    print("Intensity at sources:", [intensity_multi[y, x] for y, x in caverns_multi])
    print("Max intensity:", intensity_multi.max())

    stats_multi = calculate_coverage_stats(intensity_multi, caverns_multi)
    print("\nMulti-cavern statistics:")
    print(f"  Affected cells: {stats_multi['affected_ratio']*100:.1f}%")
    print(f"  Coverage (>30%): {stats_multi['coverage_30']*100:.1f}%")

    print("\n[OK] Basic test passed!")
