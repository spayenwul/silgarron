"""
Tissue Assignment - Rule-based tissue type assignment

Loads tissue_rules.yaml and applies criteria to assign tissue types
based on physiological parameters (elevation, lymph, bioactive, temperature).

See docs/sprint_3.5_implementation (Task 2.2) for details.
"""

import yaml
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path


class TissueAssignmentEngine:
    """
    Engine for assigning tissue types based on rules.

    Loads tissue_rules.yaml and applies priority-based matching.
    """

    def __init__(self, rules_path: str = "data/tissue_rules.yaml"):
        """
        Initialize tissue assignment engine.

        Args:
            rules_path: Path to tissue_rules.yaml
        """
        self.rules_path = rules_path
        self.rules = self._load_rules()
        self.tissues = self._parse_tissues()

    def _load_rules(self) -> Dict[str, Any]:
        """Load tissue rules from YAML file."""
        path = Path(self.rules_path)

        if not path.exists():
            raise FileNotFoundError(f"Tissue rules not found: {self.rules_path}")

        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _parse_tissues(self) -> List[Dict[str, Any]]:
        """
        Parse tissue definitions and sort by priority.

        Returns:
            List of tissue definitions sorted by priority (highest first)
        """
        tissues_dict = self.rules.get('tissues', {})

        tissues = []
        for tissue_id, tissue_data in tissues_dict.items():
            tissue = {
                'id': tissue_id,
                'name': tissue_data.get('name', tissue_id),
                'description': tissue_data.get('description', ''),
                'priority': tissue_data.get('priority', 0),
                'criteria': tissue_data.get('criteria', {}),
                'color': tissue_data.get('color', '#808080'),
                'tags': tissue_data.get('tags', []),
                'related_biomes': tissue_data.get('related_biomes', [])
            }
            tissues.append(tissue)

        # Sort by priority (highest first)
        tissues.sort(key=lambda t: t['priority'], reverse=True)

        return tissues

    def assign_tissue_type(
        self,
        elevation: float,
        ridge_mask: float,
        lymph_intensity: float,
        bioactive_saturation: float,
        temperature: float,
        is_lymph_channel: bool = False,
        is_cavern: bool = False,
        is_lymph_source: bool = False
    ) -> Dict[str, Any]:
        """
        Assign tissue type for a single hex based on physiological parameters.

        Args:
            elevation: Elevation value [0, 1]
            ridge_mask: Ridge mask value [0, 1]
            lymph_intensity: Lymph flow intensity [0, 1]
            bioactive_saturation: Bioactive saturation [0, 1]
            temperature: Metabolic temperature [0, 1]
            is_lymph_channel: Special flag for lymph channels
            is_cavern: Special flag for alveolar caverns
            is_lymph_source: Special flag for lymph sources

        Returns:
            Dict with tissue information:
                - id: Tissue type ID
                - name: Human-readable name
                - color: Hex color code
                - tags: List of tags
        """
        # Check special rules first (highest priority)
        if is_cavern:
            return self._get_special_tissue('alveolar_cavern')

        if is_lymph_source:
            return self._get_special_tissue('lymph_springhead')

        if is_lymph_channel:
            # Find lymph_channels tissue
            for tissue in self.tissues:
                if tissue['id'] == 'lymph_channels':
                    return self._tissue_to_result(tissue)

        # Check regular tissues by priority
        for tissue in self.tissues:
            if self._matches_criteria(
                tissue['criteria'],
                elevation=elevation,
                ridge_mask=ridge_mask,
                lymph_intensity=lymph_intensity,
                bioactive_saturation=bioactive_saturation,
                temperature=temperature,
                is_lymph_channel=is_lymph_channel
            ):
                return self._tissue_to_result(tissue)

        # Fallback (should not happen if moderate_tissue is defined)
        return {
            'id': 'unknown',
            'name': 'Unknown Tissue',
            'color': '#808080',
            'tags': []
        }

    def _get_special_tissue(self, tissue_id: str) -> Dict[str, Any]:
        """Get special tissue from special_rules."""
        special_rules = self.rules.get('special_rules', {})

        # Map tissue_id to rule
        rule_map = {
            'alveolar_cavern': 'alveolar_cavern_override',
            'lymph_springhead': 'lymph_source_override'
        }

        rule_id = rule_map.get(tissue_id)
        if rule_id and rule_id in special_rules:
            rule = special_rules[rule_id]
            return {
                'id': rule.get('tissue_type', tissue_id),
                'name': rule.get('tissue_type', tissue_id).replace('_', ' ').title(),
                'color': rule.get('color', '#808080'),
                'tags': rule.get('tags', [])
            }

        # Fallback
        return {
            'id': tissue_id,
            'name': tissue_id.replace('_', ' ').title(),
            'color': '#808080',
            'tags': []
        }

    def _matches_criteria(
        self,
        criteria: Dict[str, Any],
        **params
    ) -> bool:
        """
        Check if parameters match tissue criteria.

        Args:
            criteria: Dict of criteria from tissue definition
            **params: Parameter values to check

        Returns:
            True if all criteria match
        """
        # If no criteria, it's a fallback (always matches)
        if not criteria:
            return True

        # Check each criterion
        for param_name, param_range in criteria.items():
            # Special handling for is_lymph_channel
            if param_name == 'is_lymph_channel':
                if params.get('is_lymph_channel', False) != param_range:
                    return False
                continue

            # Get parameter value
            param_value = params.get(param_name)
            if param_value is None:
                return False  # Required parameter missing

            # Check range [min, max]
            if isinstance(param_range, list) and len(param_range) == 2:
                min_val, max_val = param_range
                if not (min_val <= param_value <= max_val):
                    return False
            else:
                # Exact match required
                if param_value != param_range:
                    return False

        return True  # All criteria matched

    def _tissue_to_result(self, tissue: Dict[str, Any]) -> Dict[str, Any]:
        """Convert tissue definition to result dict."""
        return {
            'id': tissue['id'],
            'name': tissue['name'],
            'color': tissue['color'],
            'tags': tissue['tags']
        }

    def assign_tissue_map(
        self,
        elevation: np.ndarray,
        ridge_mask: np.ndarray,
        lymph_intensity: np.ndarray,
        lymph_channels: np.ndarray,
        bioactive_saturation: np.ndarray,
        temperature: np.ndarray,
        cavern_positions: List[Tuple[int, int]] = None,
        lymph_sources: List[Tuple[int, int]] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Assign tissue types for entire map.

        Args:
            elevation: Elevation map (height, width)
            ridge_mask: Ridge mask (height, width)
            lymph_intensity: Lymph flow intensity (height, width)
            lymph_channels: Binary mask of lymph channels (height, width)
            bioactive_saturation: Bioactive saturation (height, width)
            temperature: Temperature map (height, width)
            cavern_positions: List of (y, x) cavern positions
            lymph_sources: List of (y, x) lymph source positions

        Returns:
            Tuple of:
                - tissue_map: np.ndarray of tissue IDs (as integers)
                - tissue_info: Dict mapping tissue_id_int → tissue info
        """
        height, width = elevation.shape

        # Create masks for special positions
        cavern_mask = np.zeros((height, width), dtype=bool)
        if cavern_positions:
            for y, x in cavern_positions:
                if 0 <= y < height and 0 <= x < width:
                    cavern_mask[y, x] = True

        source_mask = np.zeros((height, width), dtype=bool)
        if lymph_sources:
            for y, x in lymph_sources:
                if 0 <= y < height and 0 <= x < width:
                    source_mask[y, x] = True

        # Create tissue map (integer IDs)
        tissue_map = np.zeros((height, width), dtype=np.int32)
        tissue_id_to_int = {}  # Map tissue_id → integer
        tissue_info = {}  # Map integer → tissue info
        next_tissue_int = 1

        print(f"[TissueAssignment] Assigning tissues for {height}x{width} map...")

        # Assign tissues for each hex
        for y in range(height):
            for x in range(width):
                tissue_result = self.assign_tissue_type(
                    elevation=float(elevation[y, x]),
                    ridge_mask=float(ridge_mask[y, x]),
                    lymph_intensity=float(lymph_intensity[y, x]),
                    bioactive_saturation=float(bioactive_saturation[y, x]),
                    temperature=float(temperature[y, x]),
                    is_lymph_channel=bool(lymph_channels[y, x]),
                    is_cavern=bool(cavern_mask[y, x]),
                    is_lymph_source=bool(source_mask[y, x])
                )

                tissue_id = tissue_result['id']

                # Assign integer ID
                if tissue_id not in tissue_id_to_int:
                    tissue_id_to_int[tissue_id] = next_tissue_int
                    tissue_info[next_tissue_int] = tissue_result
                    next_tissue_int += 1

                tissue_map[y, x] = tissue_id_to_int[tissue_id]

        # Print statistics
        unique_tissues = len(tissue_info)
        print(f"  - Unique tissue types: {unique_tissues}")

        for tissue_int, tissue_data in tissue_info.items():
            count = np.sum(tissue_map == tissue_int)
            ratio = count / (height * width)
            print(f"  - {tissue_data['name']}: {count} cells ({ratio*100:.1f}%)")

        return tissue_map, tissue_info


if __name__ == "__main__":
    # Simple test
    print("=== TissueAssignmentEngine Test ===")

    engine = TissueAssignmentEngine()

    print(f"\nLoaded {len(engine.tissues)} tissue types:")
    for tissue in engine.tissues:
        print(f"  - {tissue['name']} (priority: {tissue['priority']})")

    # Test single assignment
    print("\nTest case: High elevation, cold, on ridge")
    result = engine.assign_tissue_type(
        elevation=0.8,
        ridge_mask=0.9,
        lymph_intensity=0.0,
        bioactive_saturation=0.1,
        temperature=0.2
    )
    print(f"  -> Assigned: {result['name']} ({result['id']})")
    print(f"  -> Color: {result['color']}")

    print("\nTest case: Low elevation, warm, high bioactive")
    result = engine.assign_tissue_type(
        elevation=0.4,
        ridge_mask=0.1,
        lymph_intensity=0.2,
        bioactive_saturation=0.8,
        temperature=0.7
    )
    print(f"  -> Assigned: {result['name']} ({result['id']})")
    print(f"  -> Color: {result['color']}")

    print("\nTest case: Lymph channel")
    result = engine.assign_tissue_type(
        elevation=0.3,
        ridge_mask=0.0,
        lymph_intensity=0.9,
        bioactive_saturation=0.3,
        temperature=0.6,
        is_lymph_channel=True
    )
    print(f"  -> Assigned: {result['name']} ({result['id']})")
    print(f"  -> Color: {result['color']}")

    print("\n[OK] Basic test passed!")
