"""
Unit tests for metabolic system (Task 1.5)

Tests:
- Temperature calculation formula
- Component contributions (bone, lymph, bioactive)
- Temperature ranges and distribution
- Integration with WorldGenerator
"""

import pytest
import numpy as np
from core.world_generator import WorldGenerator


class TestMetabolicCalculation:
    """Tests for metabolic temperature calculation"""

    def test_base_temperature_moderate(self):
        """Base temperature without modifiers is moderate (0.5)"""
        gen = WorldGenerator(seed="test_base_temp")

        # Create minimal inputs (all zeros/moderate)
        skeletal = {
            'elevation': np.full((256, 256), 0.5, dtype=np.float32),
            'ridge_mask': np.zeros((256, 256), dtype=np.float32),
            'rib_mask': np.zeros((256, 256), dtype=np.float32)
        }

        lymphatic = {
            'lymph_intensity': np.zeros((256, 256), dtype=np.float32),
            'lymph_channels': np.zeros((256, 256), dtype=np.float32),
            'source_points': [],
            'flow_accumulation': np.zeros((256, 256), dtype=np.float32)
        }

        respiratory = {
            'caverns': [],
            'exhalation_influence': np.zeros((256, 256), dtype=np.float32),
            'bioactive_saturation': np.zeros((256, 256), dtype=np.float32)
        }

        metabolic = gen._generate_metabolic_activity(skeletal, lymphatic, respiratory)
        temperature = metabolic['temperature']

        # With no modifiers, temperature should be close to base (0.5)
        assert np.isclose(temperature.mean(), 0.5, atol=0.05), \
            f"Base temperature should be ~0.5, got {temperature.mean():.3f}"

    def test_bone_makes_cold(self):
        """High ridge (bone) decreases temperature"""
        gen = WorldGenerator(seed="test_cold_bone")

        # Create high ridge
        skeletal = {
            'elevation': np.full((256, 256), 0.8, dtype=np.float32),
            'ridge_mask': np.ones((256, 256), dtype=np.float32),  # Full ridge
            'rib_mask': np.zeros((256, 256), dtype=np.float32)
        }

        lymphatic = {
            'lymph_intensity': np.zeros((256, 256), dtype=np.float32),
            'lymph_channels': np.zeros((256, 256), dtype=np.float32),
            'source_points': [],
            'flow_accumulation': np.zeros((256, 256), dtype=np.float32)
        }

        respiratory = {
            'caverns': [],
            'exhalation_influence': np.zeros((256, 256), dtype=np.float32),
            'bioactive_saturation': np.zeros((256, 256), dtype=np.float32)
        }

        metabolic = gen._generate_metabolic_activity(skeletal, lymphatic, respiratory)
        temperature = metabolic['temperature']

        # Ridge should make temperature lower than base (0.5)
        assert temperature.mean() < 0.5, \
            f"Bone should decrease temperature, got {temperature.mean():.3f}"

        # Check that cold zones exist
        cold_ratio = np.sum(temperature < 0.3) / temperature.size
        assert cold_ratio > 0.1, \
            f"Should have cold zones (bone), got {cold_ratio*100:.1f}%"

    def test_lymph_makes_warm(self):
        """High lymph flow increases temperature"""
        gen = WorldGenerator(seed="test_warm_lymph")

        skeletal = {
            'elevation': np.full((256, 256), 0.5, dtype=np.float32),
            'ridge_mask': np.zeros((256, 256), dtype=np.float32),
            'rib_mask': np.zeros((256, 256), dtype=np.float32)
        }

        # High lymph everywhere
        lymphatic = {
            'lymph_intensity': np.ones((256, 256), dtype=np.float32),
            'lymph_channels': np.ones((256, 256), dtype=np.float32),
            'source_points': [],
            'flow_accumulation': np.full((256, 256), 100.0, dtype=np.float32)
        }

        respiratory = {
            'caverns': [],
            'exhalation_influence': np.zeros((256, 256), dtype=np.float32),
            'bioactive_saturation': np.zeros((256, 256), dtype=np.float32)
        }

        metabolic = gen._generate_metabolic_activity(skeletal, lymphatic, respiratory)
        temperature = metabolic['temperature']

        # Lymph should make temperature higher than base (0.5)
        assert temperature.mean() > 0.5, \
            f"Lymph should increase temperature, got {temperature.mean():.3f}"

    def test_bioactive_makes_warm(self):
        """High bioactive saturation increases temperature"""
        gen = WorldGenerator(seed="test_warm_bioactive")

        skeletal = {
            'elevation': np.full((256, 256), 0.5, dtype=np.float32),
            'ridge_mask': np.zeros((256, 256), dtype=np.float32),
            'rib_mask': np.zeros((256, 256), dtype=np.float32)
        }

        lymphatic = {
            'lymph_intensity': np.zeros((256, 256), dtype=np.float32),
            'lymph_channels': np.zeros((256, 256), dtype=np.float32),
            'source_points': [],
            'flow_accumulation': np.zeros((256, 256), dtype=np.float32)
        }

        # High bioactive everywhere
        respiratory = {
            'caverns': [(128, 128)],
            'exhalation_influence': np.ones((256, 256), dtype=np.float32),
            'bioactive_saturation': np.ones((256, 256), dtype=np.float32)
        }

        metabolic = gen._generate_metabolic_activity(skeletal, lymphatic, respiratory)
        temperature = metabolic['temperature']

        # Bioactive should make temperature higher than base (0.5)
        assert temperature.mean() > 0.5, \
            f"Bioactive should increase temperature, got {temperature.mean():.3f}"

    def test_temperature_clamped(self):
        """Temperature is clamped to [0, 1]"""
        gen = WorldGenerator(seed="test_clamp")

        # Extreme values
        skeletal = {
            'elevation': np.full((256, 256), 0.9, dtype=np.float32),
            'ridge_mask': np.ones((256, 256), dtype=np.float32) * 2.0,  # Extreme
            'rib_mask': np.zeros((256, 256), dtype=np.float32)
        }

        lymphatic = {
            'lymph_intensity': np.ones((256, 256), dtype=np.float32) * 5.0,  # Extreme
            'lymph_channels': np.ones((256, 256), dtype=np.float32),
            'source_points': [],
            'flow_accumulation': np.full((256, 256), 1000.0, dtype=np.float32)
        }

        respiratory = {
            'caverns': [],
            'exhalation_influence': np.ones((256, 256), dtype=np.float32) * 3.0,  # Extreme
            'bioactive_saturation': np.ones((256, 256), dtype=np.float32) * 3.0
        }

        metabolic = gen._generate_metabolic_activity(skeletal, lymphatic, respiratory)
        temperature = metabolic['temperature']

        # Check clamping
        assert temperature.min() >= 0.0, f"Temperature should be >= 0, got {temperature.min():.3f}"
        assert temperature.max() <= 1.0, f"Temperature should be <= 1, got {temperature.max():.3f}"

    def test_lowlands_warmer_than_highlands(self):
        """Lowlands (soft tissue) are warmer than highlands (bone)"""
        gen = WorldGenerator(seed="test_elevation_effect")

        # Create gradient: low on left, high on right
        elevation = np.tile(np.linspace(0.2, 0.9, 256), (256, 1))
        ridge_mask = np.where(elevation > 0.7, 1.0, 0.0)

        skeletal = {
            'elevation': elevation.astype(np.float32),
            'ridge_mask': ridge_mask.astype(np.float32),
            'rib_mask': np.zeros((256, 256), dtype=np.float32)
        }

        lymphatic = {
            'lymph_intensity': np.zeros((256, 256), dtype=np.float32),
            'lymph_channels': np.zeros((256, 256), dtype=np.float32),
            'source_points': [],
            'flow_accumulation': np.zeros((256, 256), dtype=np.float32)
        }

        respiratory = {
            'caverns': [],
            'exhalation_influence': np.zeros((256, 256), dtype=np.float32),
            'bioactive_saturation': np.zeros((256, 256), dtype=np.float32)
        }

        metabolic = gen._generate_metabolic_activity(skeletal, lymphatic, respiratory)
        temperature = metabolic['temperature']

        # Left (lowlands) should be warmer than right (highlands)
        left_temp = temperature[:, :64].mean()
        right_temp = temperature[:, 192:].mean()

        assert left_temp > right_temp, \
            f"Lowlands should be warmer than highlands: {left_temp:.3f} vs {right_temp:.3f}"


class TestMetabolicIntegration:
    """Integration tests with WorldGenerator"""

    def test_generate_metabolic_activity(self):
        """WorldGenerator successfully generates metabolic activity"""
        gen = WorldGenerator(seed="test_metabolic_integration")

        skeletal = gen._generate_skeletal_structure()
        lymphatic = gen._generate_lymphatic_system(skeletal)
        respiratory = gen._generate_respiratory_system(skeletal)
        metabolic = gen._generate_metabolic_activity(skeletal, lymphatic, respiratory)

        # Check structure
        assert 'temperature' in metabolic
        temperature = metabolic['temperature']

        # Check type and shape
        assert isinstance(temperature, np.ndarray)
        assert temperature.shape == (256, 256)
        assert temperature.dtype == np.float32

        # Check values
        assert temperature.min() >= 0.0
        assert temperature.max() <= 1.0

    def test_temperature_reasonable_distribution(self):
        """Temperature has reasonable distribution"""
        gen = WorldGenerator(seed="test_distribution")

        skeletal = gen._generate_skeletal_structure()
        lymphatic = gen._generate_lymphatic_system(skeletal)
        respiratory = gen._generate_respiratory_system(skeletal)
        metabolic = gen._generate_metabolic_activity(skeletal, lymphatic, respiratory)

        temperature = metabolic['temperature']

        # Mean should be moderate (around 0.4-0.6)
        mean_temp = temperature.mean()
        assert 0.3 <= mean_temp <= 0.7, \
            f"Mean temperature should be moderate, got {mean_temp:.3f}"

        # Should have some variation (not all same)
        std_temp = temperature.std()
        assert std_temp > 0.05, \
            f"Temperature should vary, got std={std_temp:.3f}"

        # Should have both cold and warm zones
        cold_ratio = np.sum(temperature < 0.4) / temperature.size
        warm_ratio = np.sum(temperature > 0.6) / temperature.size

        assert cold_ratio > 0.1, f"Should have cold zones, got {cold_ratio*100:.1f}%"
        assert warm_ratio > 0.05, f"Should have warm zones, got {warm_ratio*100:.1f}%"

    def test_deterministic_generation(self):
        """Same seed produces same metabolic temperature"""
        gen1 = WorldGenerator(seed="deterministic_metabolic")
        gen2 = WorldGenerator(seed="deterministic_metabolic")

        skeletal1 = gen1._generate_skeletal_structure()
        lymphatic1 = gen1._generate_lymphatic_system(skeletal1)
        respiratory1 = gen1._generate_respiratory_system(skeletal1)
        metabolic1 = gen1._generate_metabolic_activity(skeletal1, lymphatic1, respiratory1)

        skeletal2 = gen2._generate_skeletal_structure()
        lymphatic2 = gen2._generate_lymphatic_system(skeletal2)
        respiratory2 = gen2._generate_respiratory_system(skeletal2)
        metabolic2 = gen2._generate_metabolic_activity(skeletal2, lymphatic2, respiratory2)

        # Check temperature is identical
        assert np.array_equal(metabolic1['temperature'], metabolic2['temperature']), \
            "Temperature should be identical for same seed"

    def test_full_generation_pipeline(self):
        """Full generation pipeline works with metabolic activity"""
        gen = WorldGenerator(seed="test_full_pipeline")

        # This should not raise any errors
        result = gen.generate()

        # Result should be dict (even if empty for now)
        assert isinstance(result, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
