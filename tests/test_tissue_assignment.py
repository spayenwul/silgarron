"""
Unit tests for tissue assignment system (Task 2.1-2.2)

Tests:
- YAML loading and parsing
- Priority-based tissue matching
- Criteria evaluation (elevation, temperature, lymph, etc.)
- Special rules (caverns, lymph sources)
- Full map assignment
- Integration with WorldGenerator
"""

import pytest
import numpy as np
from pathlib import Path
from core.tissue_assignment import TissueAssignmentEngine
from core.world_generator import WorldGenerator


class TestYAMLLoading:
    """Tests for YAML loading and parsing"""

    def test_load_tissue_rules(self):
        """Engine loads tissue_rules.yaml successfully"""
        engine = TissueAssignmentEngine(rules_path="data/tissue_rules.yaml")

        # Check rules loaded
        assert engine.rules is not None
        assert 'tissues' in engine.rules

    def test_parse_tissues(self):
        """Tissues parsed and sorted by priority"""
        engine = TissueAssignmentEngine()

        # Check tissues list
        assert len(engine.tissues) > 0

        # Check sorted by priority (highest first)
        for i in range(len(engine.tissues) - 1):
            assert engine.tissues[i]['priority'] >= engine.tissues[i+1]['priority']

    def test_tissue_structure(self):
        """Each tissue has required fields"""
        engine = TissueAssignmentEngine()

        for tissue in engine.tissues:
            assert 'id' in tissue
            assert 'name' in tissue
            assert 'priority' in tissue
            assert 'criteria' in tissue
            assert 'color' in tissue
            assert 'tags' in tissue


class TestCriteriaMatching:
    """Tests for criteria matching logic"""

    def test_exact_match(self):
        """Criteria with exact values match correctly"""
        engine = TissueAssignmentEngine()

        # Create simple criteria
        criteria = {'elevation': [0.5, 0.7]}

        # Should match
        assert engine._matches_criteria(criteria, elevation=0.6)
        assert engine._matches_criteria(criteria, elevation=0.5)  # Min edge
        assert engine._matches_criteria(criteria, elevation=0.7)  # Max edge

        # Should not match
        assert not engine._matches_criteria(criteria, elevation=0.4)
        assert not engine._matches_criteria(criteria, elevation=0.8)

    def test_multiple_criteria(self):
        """All criteria must match (AND logic)"""
        engine = TissueAssignmentEngine()

        criteria = {
            'elevation': [0.5, 0.7],
            'temperature': [0.6, 0.9]
        }

        # Both match
        assert engine._matches_criteria(criteria, elevation=0.6, temperature=0.7)

        # Only one matches
        assert not engine._matches_criteria(criteria, elevation=0.6, temperature=0.5)
        assert not engine._matches_criteria(criteria, elevation=0.4, temperature=0.7)

        # Neither matches
        assert not engine._matches_criteria(criteria, elevation=0.4, temperature=0.5)

    def test_missing_parameter(self):
        """Missing required parameter fails match"""
        engine = TissueAssignmentEngine()

        criteria = {'elevation': [0.5, 0.7]}

        # Missing parameter
        assert not engine._matches_criteria(criteria, temperature=0.6)

    def test_empty_criteria(self):
        """Empty criteria always matches (fallback)"""
        engine = TissueAssignmentEngine()

        criteria = {}

        # Should match anything
        assert engine._matches_criteria(criteria, elevation=0.5)
        assert engine._matches_criteria(criteria)


class TestTissueAssignment:
    """Tests for single-hex tissue assignment"""

    def test_high_elevation_cold_ridge(self):
        """High elevation + cold + ridge -> Bone tissue"""
        engine = TissueAssignmentEngine()

        result = engine.assign_tissue_type(
            elevation=0.85,
            ridge_mask=0.9,
            lymph_intensity=0.0,
            bioactive_saturation=0.1,
            temperature=0.2
        )

        # Should be scleritus_bone (high priority, matches criteria)
        assert result['id'] == 'scleritus_bone'
        assert 'resource:bone_chitin' in result['tags']

    def test_low_elevation_warm(self):
        """Low elevation + warm -> Lowland tissue or similar"""
        engine = TissueAssignmentEngine()

        result = engine.assign_tissue_type(
            elevation=0.25,
            ridge_mask=0.0,
            lymph_intensity=0.1,
            bioactive_saturation=0.2,
            temperature=0.6
        )

        # Should be lowland_tissue or similar
        assert result['id'] in ['lowland_tissue', 'moderate_tissue', 'primordial_fluid']

    def test_high_bioactive_warm(self):
        """High bioactive + warm -> Pulsating dermis"""
        engine = TissueAssignmentEngine()

        result = engine.assign_tissue_type(
            elevation=0.5,
            ridge_mask=0.1,
            lymph_intensity=0.2,
            bioactive_saturation=0.8,
            temperature=0.7
        )

        # Should be pulsating_dermis (high bioactive + warm)
        assert result['id'] == 'pulsating_dermis'
        assert 'breathing:active' in result['tags']

    def test_lymph_channel_flag(self):
        """is_lymph_channel flag -> Lymph channels"""
        engine = TissueAssignmentEngine()

        result = engine.assign_tissue_type(
            elevation=0.4,
            ridge_mask=0.0,
            lymph_intensity=0.9,
            bioactive_saturation=0.3,
            temperature=0.6,
            is_lymph_channel=True
        )

        # Should be lymph_channels
        assert result['id'] == 'lymph_channels'
        assert 'resource:pure_lymph' in result['tags']

    def test_cavern_override(self):
        """is_cavern flag -> Alveolar cavern (highest priority)"""
        engine = TissueAssignmentEngine()

        result = engine.assign_tissue_type(
            elevation=0.5,
            ridge_mask=0.0,
            lymph_intensity=0.0,
            bioactive_saturation=0.5,
            temperature=0.5,
            is_cavern=True
        )

        # Should be alveolar_cavern (special rule)
        assert result['id'] == 'alveolar_cavern'
        assert 'breathing:source' in result['tags']

    def test_lymph_source_override(self):
        """is_lymph_source flag -> Lymph springhead"""
        engine = TissueAssignmentEngine()

        result = engine.assign_tissue_type(
            elevation=0.3,
            ridge_mask=0.0,
            lymph_intensity=0.0,
            bioactive_saturation=0.2,
            temperature=0.5,
            is_lymph_source=True
        )

        # Should be lymph_springhead
        assert result['id'] == 'lymph_springhead'
        assert 'location:sacred' in result['tags']

    def test_fallback_tissue(self):
        """Unknown parameters -> moderate_tissue (fallback)"""
        engine = TissueAssignmentEngine()

        # Values that don't match any specific tissue
        result = engine.assign_tissue_type(
            elevation=0.5,
            ridge_mask=0.3,
            lymph_intensity=0.1,
            bioactive_saturation=0.3,
            temperature=0.5
        )

        # Should get some tissue (fallback if nothing matches)
        assert result['id'] is not None
        assert result['name'] is not None


class TestMapAssignment:
    """Tests for full map assignment"""

    def test_assign_tissue_map_shape(self):
        """Tissue map has correct shape and type"""
        engine = TissueAssignmentEngine()

        # Create dummy data
        elevation = np.full((100, 100), 0.5, dtype=np.float32)
        ridge_mask = np.zeros((100, 100), dtype=np.float32)
        lymph_intensity = np.zeros((100, 100), dtype=np.float32)
        lymph_channels = np.zeros((100, 100), dtype=np.float32)
        bioactive_saturation = np.zeros((100, 100), dtype=np.float32)
        temperature = np.full((100, 100), 0.5, dtype=np.float32)

        tissue_map, tissue_info = engine.assign_tissue_map(
            elevation=elevation,
            ridge_mask=ridge_mask,
            lymph_intensity=lymph_intensity,
            lymph_channels=lymph_channels,
            bioactive_saturation=bioactive_saturation,
            temperature=temperature
        )

        # Check shape and type
        assert tissue_map.shape == (100, 100)
        assert tissue_map.dtype == np.int32
        assert isinstance(tissue_info, dict)

    def test_tissue_info_structure(self):
        """Tissue info dict has correct structure"""
        engine = TissueAssignmentEngine()

        # Create dummy data
        elevation = np.full((50, 50), 0.5, dtype=np.float32)
        ridge_mask = np.zeros((50, 50), dtype=np.float32)
        lymph_intensity = np.zeros((50, 50), dtype=np.float32)
        lymph_channels = np.zeros((50, 50), dtype=np.float32)
        bioactive_saturation = np.zeros((50, 50), dtype=np.float32)
        temperature = np.full((50, 50), 0.5, dtype=np.float32)

        tissue_map, tissue_info = engine.assign_tissue_map(
            elevation=elevation,
            ridge_mask=ridge_mask,
            lymph_intensity=lymph_intensity,
            lymph_channels=lymph_channels,
            bioactive_saturation=bioactive_saturation,
            temperature=temperature
        )

        # Check tissue_info entries
        for tissue_int, info in tissue_info.items():
            assert isinstance(tissue_int, int)
            assert 'id' in info
            assert 'name' in info
            assert 'color' in info
            assert 'tags' in info

    def test_cavern_positions_assigned(self):
        """Cavern positions get alveolar_cavern tissue"""
        engine = TissueAssignmentEngine()

        # Create dummy data
        size = 50
        elevation = np.full((size, size), 0.5, dtype=np.float32)
        ridge_mask = np.zeros((size, size), dtype=np.float32)
        lymph_intensity = np.zeros((size, size), dtype=np.float32)
        lymph_channels = np.zeros((size, size), dtype=np.float32)
        bioactive_saturation = np.zeros((size, size), dtype=np.float32)
        temperature = np.full((size, size), 0.5, dtype=np.float32)

        # Add caverns
        cavern_positions = [(10, 10), (30, 30)]

        tissue_map, tissue_info = engine.assign_tissue_map(
            elevation=elevation,
            ridge_mask=ridge_mask,
            lymph_intensity=lymph_intensity,
            lymph_channels=lymph_channels,
            bioactive_saturation=bioactive_saturation,
            temperature=temperature,
            cavern_positions=cavern_positions
        )

        # Check cavern positions have special tissue
        cavern_tissue_ids = []
        for tissue_int, info in tissue_info.items():
            if info['id'] == 'alveolar_cavern':
                cavern_tissue_ids.append(tissue_int)

        assert len(cavern_tissue_ids) > 0

        # Check positions
        for y, x in cavern_positions:
            assert tissue_map[y, x] in cavern_tissue_ids

    def test_lymph_sources_assigned(self):
        """Lymph sources get lymph_springhead tissue"""
        engine = TissueAssignmentEngine()

        # Create dummy data
        size = 50
        elevation = np.full((size, size), 0.5, dtype=np.float32)
        ridge_mask = np.zeros((size, size), dtype=np.float32)
        lymph_intensity = np.zeros((size, size), dtype=np.float32)
        lymph_channels = np.zeros((size, size), dtype=np.float32)
        bioactive_saturation = np.zeros((size, size), dtype=np.float32)
        temperature = np.full((size, size), 0.5, dtype=np.float32)

        # Add lymph sources
        lymph_sources = [(15, 15), (35, 35)]

        tissue_map, tissue_info = engine.assign_tissue_map(
            elevation=elevation,
            ridge_mask=ridge_mask,
            lymph_intensity=lymph_intensity,
            lymph_channels=lymph_channels,
            bioactive_saturation=bioactive_saturation,
            temperature=temperature,
            lymph_sources=lymph_sources
        )

        # Check lymph source positions have special tissue
        source_tissue_ids = []
        for tissue_int, info in tissue_info.items():
            if info['id'] == 'lymph_springhead':
                source_tissue_ids.append(tissue_int)

        assert len(source_tissue_ids) > 0

        # Check positions
        for y, x in lymph_sources:
            assert tissue_map[y, x] in source_tissue_ids


class TestIntegration:
    """Integration tests with WorldGenerator"""

    def test_world_generator_integration(self):
        """WorldGenerator successfully generates tissues"""
        gen = WorldGenerator(seed="test_tissue_integration")

        result = gen.generate()

        # Check result structure
        assert 'tissues' in result
        assert 'tissue_map' in result['tissues']
        assert 'tissue_info' in result['tissues']

        tissue_map = result['tissues']['tissue_map']
        tissue_info = result['tissues']['tissue_info']

        # Check shape
        assert tissue_map.shape == (256, 256)

        # Check tissue types
        assert len(tissue_info) > 0

    def test_tissue_diversity(self):
        """Generated world has multiple tissue types"""
        gen = WorldGenerator(seed="test_tissue_diversity")

        result = gen.generate()
        tissue_info = result['tissues']['tissue_info']

        # Should have at least 5 different tissue types
        assert len(tissue_info) >= 5

    def test_tissue_coverage(self):
        """All cells assigned a tissue type"""
        gen = WorldGenerator(seed="test_tissue_coverage")

        result = gen.generate()
        tissue_map = result['tissues']['tissue_map']

        # No zero values (all assigned)
        assert np.all(tissue_map > 0)

    def test_deterministic_tissue_assignment(self):
        """Same seed produces same tissue map"""
        gen1 = WorldGenerator(seed="deterministic_tissue")
        gen2 = WorldGenerator(seed="deterministic_tissue")

        result1 = gen1.generate()
        result2 = gen2.generate()

        tissue_map1 = result1['tissues']['tissue_map']
        tissue_map2 = result2['tissues']['tissue_map']

        # Maps should be identical
        assert np.array_equal(tissue_map1, tissue_map2)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
