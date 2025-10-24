"""
Integration Tests - Sprint 3.5, Phase 5

Tests full pipeline from generation to export to visualization.
Validates all phases working together correctly.
"""

import sys
import pytest
import numpy as np
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.world_generator import WorldGenerator
from models.global_sector import GlobalSector, WorldMap, offset_to_axial, axial_to_offset


class TestFullPipeline:
    """Test complete world generation pipeline."""

    def test_basic_generation(self):
        """Test basic world generation completes successfully."""
        gen = WorldGenerator(seed="integration_test_basic")
        result = gen.generate()

        # Check all expected keys present
        assert 'skeletal' in result
        assert 'lymphatic' in result
        assert 'respiratory' in result
        assert 'metabolic' in result
        assert 'tissues' in result
        assert 'world_map' in result
        assert 'generator_version' in result

    def test_deterministic_generation(self):
        """Test same seed produces identical worlds."""
        seed = "integration_test_deterministic"

        # Generate world twice
        gen1 = WorldGenerator(seed=seed)
        result1 = gen1.generate()

        gen2 = WorldGenerator(seed=seed)
        result2 = gen2.generate()

        # Compare elevations
        elev1 = result1['skeletal']['elevation']
        elev2 = result2['skeletal']['elevation']
        assert np.allclose(elev1, elev2, rtol=1e-9)

        # Compare tissue maps
        tissue1 = result1['tissues']['tissue_map']
        tissue2 = result2['tissues']['tissue_map']
        assert np.array_equal(tissue1, tissue2)

        # Compare world map statistics
        stats1 = result1['world_map'].get_statistics()
        stats2 = result2['world_map'].get_statistics()
        assert stats1['total_sectors'] == stats2['total_sectors']
        assert stats1['average_elevation'] == stats2['average_elevation']

    def test_all_systems_coherent(self):
        """Test all physiological systems work together coherently."""
        gen = WorldGenerator(seed="integration_test_coherent")
        result = gen.generate()

        skeletal = result['skeletal']
        lymphatic = result['lymphatic']
        respiratory = result['respiratory']
        metabolic = result['metabolic']
        tissues = result['tissues']

        # Check array shapes match
        shape = (256, 256)
        assert skeletal['elevation'].shape == shape
        assert lymphatic['lymph_intensity'].shape == shape
        assert respiratory['bioactive_saturation'].shape == shape
        assert metabolic['temperature'].shape == shape
        assert tissues['tissue_map'].shape == shape

        # Check value ranges
        assert 0.0 <= skeletal['elevation'].min() <= 1.0
        assert 0.0 <= skeletal['elevation'].max() <= 1.0
        assert 0.0 <= metabolic['temperature'].min() <= 1.0
        assert 0.0 <= metabolic['temperature'].max() <= 1.0

        # Check lymph channels exist
        assert lymphatic['lymph_channels'].sum() > 0

        # Check caverns exist
        assert len(respiratory['caverns']) > 0

        # Check tissues assigned
        unique_tissues = np.unique(tissues['tissue_map'])
        assert len(unique_tissues) > 1  # At least 2 tissue types

    def test_world_map_integration(self):
        """Test WorldMap correctly integrates all data."""
        gen = WorldGenerator(seed="integration_test_worldmap")
        result = gen.generate()

        world_map = result['world_map']

        # Check basic properties
        assert world_map.seed == "integration_test_worldmap"
        assert world_map.width == 256
        assert world_map.height == 256
        assert len(world_map.sectors) == 256 * 256

        # Check random sectors have correct data
        sector = world_map.get_sector(128, 128)
        assert sector is not None
        assert isinstance(sector, GlobalSector)
        assert 0.0 <= sector.elevation <= 1.0
        assert 0.0 <= sector.temperature <= 1.0
        assert sector.tissue_id != "unknown"
        assert sector.tissue_name != "Unknown Tissue"

        # Check coordinates are correct
        assert sector.offset_x == 128
        assert sector.offset_y == 128
        q, r = offset_to_axial(128, 128)
        assert sector.axial_q == q
        assert sector.axial_r == r

    def test_neighbor_system(self):
        """Test hex neighbor system works correctly."""
        gen = WorldGenerator(seed="integration_test_neighbors")
        result = gen.generate()
        world_map = result['world_map']

        # Test center hex
        neighbors = world_map.get_neighbors(128, 128)
        assert len(neighbors) == 6  # Should have 6 neighbors

        # Test corner hex (has fewer neighbors)
        neighbors_corner = world_map.get_neighbors(0, 0)
        assert len(neighbors_corner) < 6  # Edge hex has fewer neighbors

        # Test edge hex
        neighbors_edge = world_map.get_neighbors(0, 128)
        assert len(neighbors_edge) < 6

    def test_statistics_calculation(self):
        """Test statistics are calculated correctly."""
        gen = WorldGenerator(seed="integration_test_stats")
        result = gen.generate()
        world_map = result['world_map']

        stats = world_map.get_statistics()

        # Check required keys
        assert 'total_sectors' in stats
        assert 'average_elevation' in stats
        assert 'average_temperature' in stats
        assert 'lymph_channels' in stats
        assert 'caverns' in stats
        assert 'tissue_distribution' in stats

        # Check values are reasonable
        assert stats['total_sectors'] == 65536
        assert 0.0 <= stats['average_elevation'] <= 1.0
        assert 0.0 <= stats['average_temperature'] <= 1.0
        assert stats['lymph_channels'] >= 0
        assert stats['caverns'] >= 0

        # Check tissue distribution sums to ~100%
        total_pct = sum(stats['tissue_distribution'].values())
        assert 99.0 <= total_pct <= 101.0  # Allow small rounding error

    def test_special_features_flagged(self):
        """Test special features (caverns, sources, channels) are flagged correctly."""
        gen = WorldGenerator(seed="integration_test_features")
        result = gen.generate()
        world_map = result['world_map']

        # Count special features
        cavern_count = 0
        source_count = 0
        channel_count = 0

        for sector in world_map.sectors.values():
            if sector.is_cavern:
                cavern_count += 1
            if sector.is_lymph_source:
                source_count += 1
            if sector.is_lymph_channel:
                channel_count += 1

        # Check counts are reasonable
        assert cavern_count > 0, "No caverns found"
        assert source_count > 0, "No lymph sources found"
        assert channel_count > 0, "No lymph channels found"

        # Check against respiratory data
        respiratory = result['respiratory']
        assert cavern_count == len(respiratory['caverns'])

        # Check against lymphatic data
        lymphatic = result['lymphatic']
        assert source_count == len(lymphatic['source_points'])


class TestJSONExport:
    """Test JSON export functionality."""

    def test_metadata_export(self):
        """Test metadata-only export."""
        gen = WorldGenerator(seed="integration_test_metadata")
        result = gen.generate()
        world_map = result['world_map']

        # Export to temp file
        output_path = Path("output/test_metadata.json")
        output_path.parent.mkdir(exist_ok=True)
        world_map.export_json(str(output_path), include_all_sectors=False)

        # Check file exists and is small
        assert output_path.exists()
        file_size = output_path.stat().st_size
        assert file_size < 10000  # Should be < 10 KB

        # Cleanup
        output_path.unlink()

    def test_sample_export(self):
        """Test sample sector export (metadata only)."""
        gen = WorldGenerator(seed="integration_test_sample")
        result = gen.generate()
        world_map = result['world_map']

        # Export to temp file (metadata only)
        output_path = Path("output/test_sample.json")
        world_map.export_json(str(output_path), include_all_sectors=False)

        # Check file exists
        assert output_path.exists()
        file_size = output_path.stat().st_size
        assert file_size < 20000  # Metadata should be < 20KB

        # Cleanup
        output_path.unlink()

    def test_full_export(self):
        """Test full sector export (slow)."""
        gen = WorldGenerator(seed="integration_test_full")
        result = gen.generate()
        world_map = result['world_map']

        # Export to temp file
        output_path = Path("output/test_full.json")
        world_map.export_json(str(output_path), include_all_sectors=True)

        # Check file exists and is large
        assert output_path.exists()
        file_size = output_path.stat().st_size
        assert file_size > 10_000_000  # Should be > 10 MB

        # Cleanup
        output_path.unlink()


class TestCoordinateConversion:
    """Test hex coordinate conversion."""

    def test_offset_to_axial_conversion(self):
        """Test offset -> axial conversion."""
        # Test various positions
        test_cases = [
            (0, 0),
            (128, 128),
            (255, 255),
            (100, 50),
            (50, 100),
        ]

        for offset_x, offset_y in test_cases:
            q, r = offset_to_axial(offset_x, offset_y)
            # Convert back
            back_x, back_y = axial_to_offset(q, r)
            assert back_x == offset_x
            assert back_y == offset_y

    def test_axial_to_offset_conversion(self):
        """Test axial -> offset conversion."""
        # Test various axial coordinates
        test_cases = [
            (0, 0),
            (10, 10),
            (-10, -10),
            (50, -30),
            (-30, 50),
        ]

        for q, r in test_cases:
            offset_x, offset_y = axial_to_offset(q, r)
            # Convert back
            back_q, back_r = offset_to_axial(offset_x, offset_y)
            assert back_q == q
            assert back_r == r

    def test_sectors_have_correct_coordinates(self):
        """Test all sectors have correct coordinate conversion."""
        gen = WorldGenerator(seed="integration_test_coords")
        result = gen.generate()
        world_map = result['world_map']

        # Test random sample
        import random
        random.seed(42)
        sample = random.sample(list(world_map.sectors.values()), 100)

        for sector in sample:
            # Check offset -> axial conversion
            q, r = offset_to_axial(sector.offset_x, sector.offset_y)
            assert sector.axial_q == q
            assert sector.axial_r == r

            # Check reverse conversion
            back_x, back_y = axial_to_offset(sector.axial_q, sector.axial_r)
            assert back_x == sector.offset_x
            assert back_y == sector.offset_y


class TestTissueIntegration:
    """Test tissue assignment integrates correctly with physiology."""

    def test_fluid_is_low_elevation(self):
        """Test primordial fluid appears at low elevations."""
        gen = WorldGenerator(seed="integration_test_fluid")
        result = gen.generate()
        world_map = result['world_map']

        # Find all fluid sectors
        fluid_elevations = []
        for sector in world_map.sectors.values():
            if sector.tissue_id == "primordial_fluid":
                fluid_elevations.append(sector.elevation)

        if fluid_elevations:  # If any fluid exists
            avg_fluid_elevation = np.mean(fluid_elevations)
            # Fluid should be low elevation (< 0.2 per tissue_rules.yaml)
            assert avg_fluid_elevation < 0.25

    def test_bone_is_high_elevation(self):
        """Test bone appears at high elevations."""
        gen = WorldGenerator(seed="integration_test_bone")
        result = gen.generate()
        world_map = result['world_map']

        # Find all bone sectors
        bone_elevations = []
        for sector in world_map.sectors.values():
            if sector.tissue_id == "scleritus_bone":
                bone_elevations.append(sector.elevation)

        if bone_elevations:  # If any bone exists
            avg_bone_elevation = np.mean(bone_elevations)
            # Bone should be high elevation (> 0.7 per tissue_rules.yaml)
            assert avg_bone_elevation > 0.6

    def test_caverns_have_correct_tissue(self):
        """Test all caverns are assigned respiratory tissues."""
        gen = WorldGenerator(seed="integration_test_cavern_tissue")
        result = gen.generate()
        world_map = result['world_map']

        # Count cavern sectors
        cavern_count = 0
        for sector in world_map.sectors.values():
            if sector.is_cavern:
                cavern_count += 1
                # Cavern tissue should be alveolar_cavern (singular)
                assert sector.tissue_id == "alveolar_cavern"

        assert cavern_count > 0

    def test_lymph_channels_flagged(self):
        """Test lymph channels are flagged and have correct tissue."""
        gen = WorldGenerator(seed="integration_test_lymph_tissue")
        result = gen.generate()
        world_map = result['world_map']

        # Count channel sectors
        channel_count = 0
        for sector in world_map.sectors.values():
            if sector.is_lymph_channel:
                channel_count += 1
                # Should have lymph_channels tissue
                assert sector.tissue_id == "lymph_channels"

        assert channel_count > 0


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_seed(self):
        """Test generation with empty seed."""
        gen = WorldGenerator(seed="")
        result = gen.generate()

        # Should still work
        assert result is not None
        assert result['world_map'].seed == ""

    def test_unicode_seed(self):
        """Test generation with unicode seed."""
        gen = WorldGenerator(seed="силгаррон_тест")
        result = gen.generate()

        # Should work
        assert result is not None
        assert result['world_map'].seed == "силгаррон_тест"

    def test_very_long_seed(self):
        """Test generation with very long seed."""
        long_seed = "a" * 1000
        gen = WorldGenerator(seed=long_seed)
        result = gen.generate()

        # Should work (SHA-256 handles any length)
        assert result is not None

    def test_get_nonexistent_sector(self):
        """Test querying non-existent sector."""
        gen = WorldGenerator(seed="integration_test_nonexistent")
        result = gen.generate()
        world_map = result['world_map']

        # Out of bounds
        sector = world_map.get_sector(999, 999)
        assert sector is None

        sector = world_map.get_sector(-1, -1)
        assert sector is None


class TestPerformance:
    """Test performance characteristics (optional)."""

    def test_generation_completes_quickly(self):
        """Test world generation completes in reasonable time."""
        import time

        start = time.time()
        gen = WorldGenerator(seed="integration_test_performance")
        result = gen.generate()
        elapsed = time.time() - start

        # Should complete in < 30 seconds
        assert elapsed < 30.0, f"Generation took {elapsed:.1f}s (expected < 30s)"

    def test_statistics_calculation_fast(self):
        """Test statistics calculation is fast."""
        import time

        gen = WorldGenerator(seed="integration_test_stats_perf")
        result = gen.generate()
        world_map = result['world_map']

        start = time.time()
        stats = world_map.get_statistics()
        elapsed = time.time() - start

        # Should complete in < 5 seconds
        assert elapsed < 5.0, f"Statistics took {elapsed:.1f}s (expected < 5s)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
