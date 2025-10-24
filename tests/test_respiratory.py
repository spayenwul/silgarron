"""
Unit tests for respiratory system (Task 1.4)

Tests:
- Poisson Disk Sampling (cavern placement)
- BFS Exhalation (spore spread)
- Integration with WorldGenerator
"""

import pytest
import numpy as np
from core.poisson_sampling import place_alveolar_caverns
from core.exhalation import spread_exhalation, create_bioactive_mask, calculate_coverage_stats
from core.world_generator import WorldGenerator


class TestPoissonDiskSampling:
    """Tests for Poisson Disk Sampling algorithm"""

    def test_minimum_distance_constraint(self):
        """All caverns are at least min_distance apart"""
        rng = np.random.default_rng(42)
        elevation = rng.uniform(0.3, 0.6, (256, 256))

        min_distance = 30.0
        caverns = place_alveolar_caverns(
            width=256,
            height=256,
            elevation=elevation,
            min_distance=min_distance,
            elevation_range=(0.2, 0.7),
            rng=rng
        )

        assert len(caverns) > 0, "Should place at least some caverns"

        # Check all pairs
        for i, (y1, x1) in enumerate(caverns):
            for y2, x2 in caverns[i+1:]:
                distance = np.sqrt((y1 - y2)**2 + (x1 - x2)**2)
                assert distance >= min_distance, \
                    f"Caverns at ({y1},{x1}) and ({y2},{x2}) too close: {distance:.1f} < {min_distance}"

    def test_elevation_range_constraint(self):
        """Caverns only placed in specified elevation range"""
        rng = np.random.default_rng(123)
        # Create gradient: 0.0 at left to 1.0 at right
        elevation = np.tile(np.linspace(0.0, 1.0, 256), (256, 1))

        elevation_range = (0.3, 0.7)
        caverns = place_alveolar_caverns(
            width=256,
            height=256,
            elevation=elevation,
            min_distance=30.0,
            elevation_range=elevation_range,
            rng=rng
        )

        assert len(caverns) > 0, "Should find caverns in valid range"

        min_elev, max_elev = elevation_range
        for y, x in caverns:
            elev = elevation[y, x]
            assert min_elev <= elev <= max_elev, \
                f"Cavern at ({y},{x}) outside elevation range: {elev:.3f} not in [{min_elev}, {max_elev}]"

    def test_bounds_constraint(self):
        """All caverns within map bounds"""
        rng = np.random.default_rng(456)
        elevation = rng.uniform(0.3, 0.6, (256, 256))

        caverns = place_alveolar_caverns(
            width=256,
            height=256,
            elevation=elevation,
            min_distance=30.0,
            elevation_range=(0.2, 0.7),
            rng=rng
        )

        for y, x in caverns:
            assert 0 <= y < 256, f"Y coordinate {y} out of bounds"
            assert 0 <= x < 256, f"X coordinate {x} out of bounds"

    def test_deterministic_with_seed(self):
        """Same seed produces same cavern placement"""
        elevation = np.random.default_rng(42).uniform(0.3, 0.6, (256, 256))

        # Generate twice with same seed
        rng1 = np.random.default_rng(999)
        caverns1 = place_alveolar_caverns(
            width=256, height=256, elevation=elevation,
            min_distance=30.0, elevation_range=(0.2, 0.7), rng=rng1
        )

        rng2 = np.random.default_rng(999)
        caverns2 = place_alveolar_caverns(
            width=256, height=256, elevation=elevation,
            min_distance=30.0, elevation_range=(0.2, 0.7), rng=rng2
        )

        assert len(caverns1) == len(caverns2), "Should produce same number of caverns"
        assert caverns1 == caverns2, "Should produce identical caverns"

    def test_max_caverns_limit(self):
        """Respects max_caverns parameter"""
        rng = np.random.default_rng(789)
        elevation = rng.uniform(0.3, 0.6, (256, 256))

        max_caverns = 10
        caverns = place_alveolar_caverns(
            width=256,
            height=256,
            elevation=elevation,
            min_distance=20.0,  # Smaller distance to allow more caverns
            elevation_range=(0.2, 0.7),
            max_caverns=max_caverns,
            rng=rng
        )

        assert len(caverns) <= max_caverns, \
            f"Should not exceed max_caverns: {len(caverns)} > {max_caverns}"


class TestBFSExhalation:
    """Tests for BFS Exhalation algorithm"""

    def test_source_intensity(self):
        """Caverns have intensity 1.0"""
        caverns = [(128, 128), (64, 192)]

        intensity = spread_exhalation(
            caverns=caverns,
            width=256,
            height=256,
            decay_rate=0.9,
            min_threshold=0.01
        )

        for y, x in caverns:
            assert intensity[y, x] == 1.0, \
                f"Cavern at ({y},{x}) should have intensity 1.0, got {intensity[y,x]:.3f}"

    def test_neighbor_decay(self):
        """Immediate neighbors have decay_rate intensity"""
        caverns = [(128, 128)]
        decay_rate = 0.9

        intensity = spread_exhalation(
            caverns=caverns,
            width=256,
            height=256,
            decay_rate=decay_rate,
            min_threshold=0.01
        )

        # Check 4 neighbors (N, S, E, W)
        neighbors = [
            (127, 128),  # N
            (129, 128),  # S
            (128, 127),  # W
            (128, 129),  # E
        ]

        for y, x in neighbors:
            assert np.isclose(intensity[y, x], decay_rate), \
                f"Neighbor at ({y},{x}) should have intensity {decay_rate:.3f}, got {intensity[y,x]:.3f}"

    def test_distance_decay_pattern(self):
        """Intensity decays with distance"""
        caverns = [(128, 128)]
        decay_rate = 0.9

        intensity = spread_exhalation(
            caverns=caverns,
            width=256,
            height=256,
            decay_rate=decay_rate,
            min_threshold=0.001  # Low threshold to see far distances
        )

        # Check exponential decay along a line
        distances = [0, 1, 2, 5, 10]
        for d in distances[1:]:
            actual = intensity[128, 128 + d]
            expected = decay_rate ** d
            assert np.isclose(actual, expected, atol=0.001), \
                f"At distance {d}, expected {expected:.4f}, got {actual:.4f}"

    def test_threshold_stops_spread(self):
        """Spread stops when intensity falls below threshold"""
        caverns = [(128, 128)]
        decay_rate = 0.9
        min_threshold = 0.5  # High threshold

        intensity = spread_exhalation(
            caverns=caverns,
            width=256,
            height=256,
            decay_rate=decay_rate,
            min_threshold=min_threshold
        )

        # Calculate expected radius
        # decay_rate^d < threshold
        # d > log(threshold) / log(decay_rate)
        expected_radius = int(np.log(min_threshold) / np.log(decay_rate))

        # Check that intensity drops to zero beyond expected radius
        far_point = (128, 128 + expected_radius + 5)
        assert intensity[far_point] == 0.0, \
            f"Intensity should be 0 beyond radius, got {intensity[far_point]:.3f}"

    def test_multiple_sources_overlap(self):
        """Multiple caverns create overlapping zones"""
        caverns = [(100, 100), (156, 156)]

        intensity = spread_exhalation(
            caverns=caverns,
            width=256,
            height=256,
            decay_rate=0.92,
            min_threshold=0.01
        )

        # Both sources should have intensity 1.0
        assert intensity[100, 100] == 1.0
        assert intensity[156, 156] == 1.0

        # Check that both zones exist (neighbors should be affected)
        assert intensity[101, 100] > 0.0, "First cavern should spread"
        assert intensity[157, 156] > 0.0, "Second cavern should spread"

        # Check total affected area
        affected_count = np.sum(intensity > 0)
        assert affected_count > 100, \
            "Multiple caverns should affect significant area"

    def test_elevation_penalty(self):
        """Uphill spread has reduced intensity"""
        caverns = [(128, 50)]  # Source on left side

        # Create slope: low on left, high on right
        elevation = np.tile(np.linspace(0.0, 1.0, 256), (256, 1))

        # Without penalty
        intensity_no_penalty = spread_exhalation(
            caverns=caverns,
            width=256,
            height=256,
            decay_rate=0.92,
            min_threshold=0.01,
            elevation=None
        )

        # With penalty
        intensity_with_penalty = spread_exhalation(
            caverns=caverns,
            width=256,
            height=256,
            decay_rate=0.92,
            min_threshold=0.01,
            elevation=elevation,
            elevation_penalty=0.3  # Strong penalty
        )

        # Check points to the right (uphill)
        uphill_point = (128, 70)
        assert intensity_with_penalty[uphill_point] < intensity_no_penalty[uphill_point], \
            "Uphill spread should have lower intensity with penalty"


class TestBioactiveMask:
    """Tests for bioactive zone creation"""

    def test_threshold_filtering(self):
        """Mask correctly filters by threshold"""
        # Create test intensity map
        intensity = np.array([
            [0.0, 0.2, 0.4],
            [0.5, 0.7, 0.9],
            [0.1, 0.3, 0.6]
        ], dtype=np.float32)

        threshold = 0.5
        mask, saturation = create_bioactive_mask(intensity, threshold)

        # Check mask
        expected_mask = (intensity >= threshold).astype(np.float32)
        assert np.array_equal(mask, expected_mask), \
            "Mask should match threshold filtering"

        # Check saturation
        assert np.array_equal(saturation, intensity), \
            "Saturation should be copy of intensity"

    def test_saturation_values(self):
        """Saturation preserves intensity values"""
        intensity = np.random.uniform(0.0, 1.0, (10, 10)).astype(np.float32)

        mask, saturation = create_bioactive_mask(intensity, threshold=0.3)

        assert np.array_equal(saturation, intensity), \
            "Saturation should preserve all intensity values"


class TestRespiratoryIntegration:
    """Integration tests with WorldGenerator"""

    def test_generate_respiratory_system(self):
        """WorldGenerator successfully generates respiratory system"""
        gen = WorldGenerator(seed="test_respiratory")

        skeletal = gen._generate_skeletal_structure()
        respiratory = gen._generate_respiratory_system(skeletal)

        # Check structure
        assert 'caverns' in respiratory
        assert 'exhalation_influence' in respiratory
        assert 'bioactive_saturation' in respiratory

        caverns = respiratory['caverns']
        exhalation = respiratory['exhalation_influence']
        bioactive = respiratory['bioactive_saturation']

        # Check types and shapes
        assert isinstance(caverns, list)
        assert isinstance(exhalation, np.ndarray)
        assert isinstance(bioactive, np.ndarray)

        assert exhalation.shape == (256, 256)
        assert bioactive.shape == (256, 256)

    def test_caverns_placed(self):
        """Caverns are actually placed"""
        gen = WorldGenerator(seed="test_caverns")

        skeletal = gen._generate_skeletal_structure()
        respiratory = gen._generate_respiratory_system(skeletal)

        caverns = respiratory['caverns']
        assert len(caverns) > 0, "Should place at least some caverns"
        assert len(caverns) <= 100, "Should not exceed max_caverns limit"

    def test_exhalation_from_caverns(self):
        """Exhalation spreads from caverns"""
        gen = WorldGenerator(seed="test_exhalation")

        skeletal = gen._generate_skeletal_structure()
        respiratory = gen._generate_respiratory_system(skeletal)

        caverns = respiratory['caverns']
        exhalation = respiratory['exhalation_influence']

        if len(caverns) > 0:
            # Check that caverns have max intensity
            for y, x in caverns:
                assert exhalation[y, x] == 1.0, \
                    f"Cavern at ({y},{x}) should have intensity 1.0"

            # Check that exhalation covers significant area
            affected_ratio = np.sum(exhalation > 0) / exhalation.size
            assert affected_ratio > 0.5, \
                f"Exhalation should cover significant area, got {affected_ratio*100:.1f}%"

    def test_bioactive_saturation_reasonable(self):
        """Bioactive saturation has reasonable coverage"""
        gen = WorldGenerator(seed="test_bioactive")

        skeletal = gen._generate_skeletal_structure()
        respiratory = gen._generate_respiratory_system(skeletal)

        bioactive = respiratory['bioactive_saturation']

        # Check that some cells are bioactive
        bioactive_count = np.sum(bioactive > 0.3)
        bioactive_ratio = bioactive_count / bioactive.size

        # Should be between 10% and 50%
        assert 0.1 <= bioactive_ratio <= 0.5, \
            f"Bioactive saturation should be reasonable, got {bioactive_ratio*100:.1f}%"

    def test_deterministic_generation(self):
        """Same seed produces same respiratory system"""
        gen1 = WorldGenerator(seed="deterministic_test")
        gen2 = WorldGenerator(seed="deterministic_test")

        skeletal1 = gen1._generate_skeletal_structure()
        skeletal2 = gen2._generate_skeletal_structure()

        respiratory1 = gen1._generate_respiratory_system(skeletal1)
        respiratory2 = gen2._generate_respiratory_system(skeletal2)

        # Check caverns
        assert len(respiratory1['caverns']) == len(respiratory2['caverns'])
        assert respiratory1['caverns'] == respiratory2['caverns']

        # Check exhalation
        assert np.array_equal(
            respiratory1['exhalation_influence'],
            respiratory2['exhalation_influence']
        ), "Exhalation should be identical"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
