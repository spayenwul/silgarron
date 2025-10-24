"""
Poisson Disk Sampling - Uniform point distribution algorithm

Implements Bridson's algorithm for generating uniformly distributed points
with minimum distance constraint.

Used for placing alveolar caverns (respiratory sources) in Silgarron.

See docs/sprint_3.5_implementation/04_POISSON_DISK_SAMPLING.md for details.
"""

import numpy as np
from typing import List, Tuple, Optional


def place_alveolar_caverns(
    width: int,
    height: int,
    elevation: np.ndarray,
    min_distance: float = 30.0,
    elevation_range: Tuple[float, float] = (0.2, 0.7),
    max_caverns: int = 100,
    k_attempts: int = 30,
    rng: np.random.Generator = None
) -> List[Tuple[int, int]]:
    """
    Places alveolar caverns (exhalation sources) via Poisson Disk Sampling.

    Criteria:
    - Uniformly distributed (Poisson)
    - Minimum distance min_distance between caverns
    - Only in certain elevation range (not on peaks, not in lowlands)

    Uses Bridson's Algorithm with spatial grid optimization for O(1) distance checks.

    Args:
        width, height: Map dimensions
        elevation: np.ndarray (height, width) - elevation map
        min_distance: Minimum distance between caverns (pixels)
        elevation_range: (min, max) elevation for cavern placement
        max_caverns: Maximum number of caverns to place
        k_attempts: Number of attempts per active point
        rng: Random generator for determinism

    Returns:
        List[(y, x)] - coordinates of caverns

    Biological interpretation:
        - Caverns = "alveoli" in respiratory system
        - Not too close together (min_distance)
        - In soft tissue elevation range (not bones, not lowlands)
        - Uniformly distributed across the organism
    """
    if rng is None:
        rng = np.random.default_rng()

    min_elev, max_elev = elevation_range
    caverns = []

    # Spatial grid for fast neighbor lookup (O(1) instead of O(n))
    cell_size = min_distance / np.sqrt(2)
    grid_width = int(np.ceil(width / cell_size))
    grid_height = int(np.ceil(height / cell_size))
    grid = {}  # (grid_y, grid_x) -> (y, x) point

    # Active list (points to try generating candidates around)
    active_list = []

    # Helper: Convert point to grid coordinates
    def point_to_grid(y: float, x: float) -> Tuple[int, int]:
        return (int(y / cell_size), int(x / cell_size))

    # Helper: Check if candidate is valid
    def is_valid_candidate(y: float, x: float) -> bool:
        # Bounds check
        if not (0 <= x < width and 0 <= y < height):
            return False

        # Elevation check
        elev = elevation[int(y), int(x)]
        if not (min_elev <= elev <= max_elev):
            return False

        # Distance check (using spatial grid)
        grid_y, grid_x = point_to_grid(y, x)

        # Check 5x5 neighborhood in grid (to be safe with diagonals)
        for dy in [-2, -1, 0, 1, 2]:
            for dx in [-2, -1, 0, 1, 2]:
                neighbor_cell = (grid_y + dy, grid_x + dx)

                if neighbor_cell in grid:
                    ny, nx = grid[neighbor_cell]
                    distance = np.sqrt((y - ny)**2 + (x - nx)**2)

                    if distance < min_distance:
                        return False  # Too close!

        return True

    # Step 1: Find first valid point
    attempts = 0
    while attempts < 1000:
        x = rng.uniform(0, width)
        y = rng.uniform(0, height)

        if is_valid_candidate(y, x):
            first_point = (y, x)
            active_list.append(first_point)
            grid[point_to_grid(y, x)] = first_point
            caverns.append((int(y), int(x)))
            break

        attempts += 1

    if len(caverns) == 0:
        # No valid starting point found
        return []

    # Step 2: Generate candidates around active points
    while active_list and len(caverns) < max_caverns:
        # Pick random point from active list
        point_idx = rng.integers(0, len(active_list))
        point_y, point_x = active_list[point_idx]

        found = False
        for _ in range(k_attempts):
            # Generate candidate in annulus [min_distance, 2*min_distance]
            angle = rng.uniform(0, 2 * np.pi)
            radius = rng.uniform(min_distance, 2 * min_distance)

            candidate_x = point_x + radius * np.cos(angle)
            candidate_y = point_y + radius * np.sin(angle)

            # Check validity
            if is_valid_candidate(candidate_y, candidate_x):
                # Accept candidate
                candidate = (candidate_y, candidate_x)
                active_list.append(candidate)
                grid[point_to_grid(candidate_y, candidate_x)] = candidate
                caverns.append((int(candidate_y), int(candidate_x)))
                found = True
                break

        # If no candidate found, remove point from active list
        if not found:
            active_list.pop(point_idx)

    return caverns


def visualize_poisson_points(
    points: List[Tuple[int, int]],
    width: int,
    height: int,
    min_distance: float
) -> np.ndarray:
    """
    Creates a visualization image of Poisson points with radius circles.

    Args:
        points: List of (y, x) coordinates
        width, height: Image dimensions
        min_distance: Minimum distance (for radius visualization)

    Returns:
        np.ndarray (height, width) - visualization image [0, 1]
    """
    image = np.zeros((height, width), dtype=np.float32)

    # Draw points
    for y, x in points:
        if 0 <= y < height and 0 <= x < width:
            image[y, x] = 1.0

    # Draw circles around each point (radius = min_distance)
    Y, X = np.meshgrid(np.arange(height), np.arange(width), indexing='ij')

    for y, x in points:
        distances = np.sqrt((Y - y)**2 + (X - x)**2)
        circle_mask = np.abs(distances - min_distance) < 1.5
        image[circle_mask] = 0.5

    return image


if __name__ == "__main__":
    # Simple test
    print("=== Poisson Disk Sampling Test ===")

    # Create simple elevation map (flat with some variation)
    rng = np.random.default_rng(42)
    test_elevation = rng.uniform(0.3, 0.6, (256, 256))

    print("Test elevation shape:", test_elevation.shape)
    print("Test elevation range:", test_elevation.min(), "-", test_elevation.max())

    # Place caverns
    caverns = place_alveolar_caverns(
        width=256,
        height=256,
        elevation=test_elevation,
        min_distance=30.0,
        elevation_range=(0.2, 0.7),
        max_caverns=100,
        rng=rng
    )

    print("\nCaverns placed:", len(caverns))

    # Verify minimum distance constraint
    min_observed_distance = float('inf')
    for i, (y1, x1) in enumerate(caverns):
        for y2, x2 in caverns[i+1:]:
            distance = np.sqrt((y1 - y2)**2 + (x1 - x2)**2)
            min_observed_distance = min(min_observed_distance, distance)

    print("Minimum distance observed:", min_observed_distance)
    print("Expected minimum distance: 30.0")

    if min_observed_distance >= 30.0:
        print("\n[OK] Minimum distance constraint satisfied!")
    else:
        print("\n[ERROR] Minimum distance constraint violated!")

    # Verify elevation constraint
    elevations = [test_elevation[int(y), int(x)] for y, x in caverns]
    min_elev_observed = min(elevations)
    max_elev_observed = max(elevations)

    print("\nElevation range of caverns:", min_elev_observed, "-", max_elev_observed)
    print("Expected range: [0.2, 0.7]")

    if 0.2 <= min_elev_observed and max_elev_observed <= 0.7:
        print("\n[OK] Elevation constraint satisfied!")
    else:
        print("\n[ERROR] Elevation constraint violated!")

    print("\n[OK] Basic test passed!")
