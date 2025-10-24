"""
Global Sector - Model for 256×256 world map hex cells

Each sector represents one hex on the global anatomical map.
Contains physiological data and tissue type information.

Sprint 3.5, Phase 3: Data Models
"""

from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import json


@dataclass
class GlobalSector:
    """
    Represents a single hex cell on the global 256×256 map.

    Coordinates:
        - offset_x, offset_y: Array indices [0-255]
        - axial_q, axial_r: Axial hex coordinates

    Physiological Data:
        - elevation: Height [0.0-1.0]
        - ridge_mask: Bone ridge intensity [0.0-1.0]
        - lymph_intensity: Lymph flow [0.0-1.0]
        - temperature: Metabolic temperature [0.0-1.0]
        - bioactive_saturation: Respiratory activity [0.0-1.0]

    Tissue Information:
        - tissue_id: Tissue type identifier
        - tissue_name: Human-readable tissue name
        - tissue_color: Hex color code
        - tissue_tags: List of feature tags

    Usage:
        >>> sector = GlobalSector(
        ...     offset_x=128, offset_y=128,
        ...     elevation=0.5, temperature=0.6,
        ...     tissue_id='pulsating_dermis'
        ... )
        >>> sector.to_dict()
    """

    # === Coordinates ===
    offset_x: int  # Array column [0-255]
    offset_y: int  # Array row [0-255]
    axial_q: int = 0  # Axial q coordinate (will be calculated)
    axial_r: int = 0  # Axial r coordinate (will be calculated)

    # === Physiological Parameters ===
    elevation: float = 0.5
    ridge_mask: float = 0.0
    rib_mask: float = 0.0
    lymph_intensity: float = 0.0
    bioactive_saturation: float = 0.0
    temperature: float = 0.5

    # === Tissue Information ===
    tissue_id: str = "unknown"
    tissue_name: str = "Unknown Tissue"
    tissue_color: str = "#808080"
    tissue_tags: Tuple[str, ...] = ()

    # === Flags ===
    is_lymph_channel: bool = False
    is_lymph_source: bool = False
    is_cavern: bool = False

    def __post_init__(self):
        """Calculate axial coordinates from offset coordinates."""
        self.axial_q, self.axial_r = offset_to_axial(self.offset_x, self.offset_y)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert sector to dictionary for JSON export.

        Returns:
            Dict with all sector data
        """
        return {
            'coordinates': {
                'offset': {'x': self.offset_x, 'y': self.offset_y},
                'axial': {'q': self.axial_q, 'r': self.axial_r}
            },
            'physiology': {
                'elevation': round(float(self.elevation), 3),
                'ridge_mask': round(float(self.ridge_mask), 3),
                'rib_mask': round(float(self.rib_mask), 3),
                'lymph_intensity': round(float(self.lymph_intensity), 3),
                'bioactive_saturation': round(float(self.bioactive_saturation), 3),
                'temperature': round(float(self.temperature), 3)
            },
            'tissue': {
                'id': self.tissue_id,
                'name': self.tissue_name,
                'color': self.tissue_color,
                'tags': list(self.tissue_tags)
            },
            'flags': {
                'is_lymph_channel': self.is_lymph_channel,
                'is_lymph_source': self.is_lymph_source,
                'is_cavern': self.is_cavern
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GlobalSector':
        """
        Create sector from dictionary.

        Args:
            data: Dict from to_dict() or JSON

        Returns:
            GlobalSector instance
        """
        coords = data['coordinates']
        phys = data['physiology']
        tissue = data['tissue']
        flags = data['flags']

        return cls(
            offset_x=coords['offset']['x'],
            offset_y=coords['offset']['y'],
            elevation=phys['elevation'],
            ridge_mask=phys['ridge_mask'],
            rib_mask=phys['rib_mask'],
            lymph_intensity=phys['lymph_intensity'],
            bioactive_saturation=phys['bioactive_saturation'],
            temperature=phys['temperature'],
            tissue_id=tissue['id'],
            tissue_name=tissue['name'],
            tissue_color=tissue['color'],
            tissue_tags=tuple(tissue['tags']),
            is_lymph_channel=flags['is_lymph_channel'],
            is_lymph_source=flags['is_lymph_source'],
            is_cavern=flags['is_cavern']
        )

    def get_biome_candidates(self) -> list[str]:
        """
        Get list of potential biomes for this sector.

        Uses tissue type and tags to suggest biomes.

        Returns:
            List of biome names (from generation_rules.yaml)
        """
        # This mapping comes from tissue_rules.yaml integration section
        tissue_to_biomes = {
            'scleritus_bone': ['bone_needles', 'ruined_spires'],
            'chitinous_expanse': ['litho-lichen_slopes', 'broken_lands'],
            'lymph_channels': ['lymph_valley', 'springheads'],
            'pulsating_dermis': ['pulsating_plains'],
            'membranous_plains': ['rolling_hills'],
            'fibrous_thicket': ['blood_clot_thicket'],
            'biolume_forest': ['biolume_forest', 'luminous_fungi_caves'],
            'spore_savanna': ['spore_savanna', 'megatherium_pastures'],
            'lowland_tissue': ['silt_flats', 'foothills'],
            'primordial_fluid': ['primordial_ocean'],
            'inert_zone': ['barren_wastes', 'dead_tissue'],
            'alveolar_cavern': ['alveolar_caverns'],
            'lymph_springhead': ['springheads']
        }

        return tissue_to_biomes.get(self.tissue_id, ['generic_tissue'])

    def __repr__(self) -> str:
        return (
            f"GlobalSector(offset=({self.offset_x}, {self.offset_y}), "
            f"axial=({self.axial_q}, {self.axial_r}), "
            f"tissue={self.tissue_id}, "
            f"elevation={self.elevation:.2f}, "
            f"temperature={self.temperature:.2f})"
        )


# =============================================================================
# Hex Coordinate Conversion Functions
# =============================================================================

def offset_to_axial(offset_x: int, offset_y: int) -> Tuple[int, int]:
    """
    Convert offset coordinates (array indices) to axial hex coordinates.

    Uses "odd-q" vertical layout (pointy-top hexes, odd columns shifted down).

    Args:
        offset_x: Column index [0-255]
        offset_y: Row index [0-255]

    Returns:
        Tuple of (q, r) axial coordinates

    References:
        https://www.redblobgames.com/grids/hexagons/#coordinates-offset
    """
    q = offset_x
    r = offset_y - (offset_x - (offset_x & 1)) // 2
    return (q, r)


def axial_to_offset(q: int, r: int) -> Tuple[int, int]:
    """
    Convert axial hex coordinates to offset coordinates (array indices).

    Uses "odd-q" vertical layout (pointy-top hexes, odd columns shifted down).

    Args:
        q: Axial q coordinate
        r: Axial r coordinate

    Returns:
        Tuple of (offset_x, offset_y)

    References:
        https://www.redblobgames.com/grids/hexagons/#coordinates-offset
    """
    offset_x = q
    offset_y = r + (q - (q & 1)) // 2
    return (offset_x, offset_y)


def axial_distance(q1: int, r1: int, q2: int, r2: int) -> int:
    """
    Calculate distance between two hex cells in axial coordinates.

    Uses cube coordinate distance formula.

    Args:
        q1, r1: First hex coordinates
        q2, r2: Second hex coordinates

    Returns:
        Distance in hexes

    References:
        https://www.redblobgames.com/grids/hexagons/#distances
    """
    # Convert to cube coordinates
    s1 = -q1 - r1
    s2 = -q2 - r2

    # Manhattan distance in cube space / 2
    return (abs(q1 - q2) + abs(r1 - r2) + abs(s1 - s2)) // 2


def get_axial_neighbors(q: int, r: int) -> list[Tuple[int, int]]:
    """
    Get the 6 neighbors of a hex in axial coordinates.

    Args:
        q, r: Hex coordinates

    Returns:
        List of 6 (q, r) tuples for neighbors

    References:
        https://www.redblobgames.com/grids/hexagons/#neighbors
    """
    # Axial direction vectors (pointy-top)
    directions = [
        (1, 0),   # East
        (1, -1),  # Northeast
        (0, -1),  # Northwest
        (-1, 0),  # West
        (-1, 1),  # Southwest
        (0, 1)    # Southeast
    ]

    return [(q + dq, r + dr) for dq, dr in directions]


# =============================================================================
# World Map Container
# =============================================================================

class WorldMap:
    """
    Container for the complete 256×256 global map.

    Stores all GlobalSector objects and provides access methods.

    Usage:
        >>> world_map = WorldMap(seed="silgarron_alpha")
        >>> sector = world_map.get_sector(128, 128)
        >>> neighbors = world_map.get_neighbors(128, 128)
        >>> world_map.export_json("output/world_map.json")
    """

    def __init__(self, seed: str, width: int = 256, height: int = 256):
        """
        Initialize world map container.

        Args:
            seed: World generation seed
            width: Map width in hexes
            height: Map height in hexes
        """
        self.seed = seed
        self.width = width
        self.height = height
        self.sectors: Dict[Tuple[int, int], GlobalSector] = {}

    def add_sector(self, sector: GlobalSector) -> None:
        """Add sector to map."""
        key = (sector.offset_x, sector.offset_y)
        self.sectors[key] = sector

    def get_sector(self, offset_x: int, offset_y: int) -> Optional[GlobalSector]:
        """Get sector by offset coordinates."""
        return self.sectors.get((offset_x, offset_y))

    def get_sector_axial(self, q: int, r: int) -> Optional[GlobalSector]:
        """Get sector by axial coordinates."""
        offset_x, offset_y = axial_to_offset(q, r)
        return self.get_sector(offset_x, offset_y)

    def get_neighbors(self, offset_x: int, offset_y: int) -> list[GlobalSector]:
        """
        Get all neighboring sectors (up to 6).

        Args:
            offset_x, offset_y: Center hex coordinates

        Returns:
            List of neighboring GlobalSector objects
        """
        sector = self.get_sector(offset_x, offset_y)
        if not sector:
            return []

        # Get neighbors in axial space
        neighbor_coords = get_axial_neighbors(sector.axial_q, sector.axial_r)

        # Convert back to offset and fetch sectors
        neighbors = []
        for q, r in neighbor_coords:
            neighbor_sector = self.get_sector_axial(q, r)
            if neighbor_sector:
                neighbors.append(neighbor_sector)

        return neighbors

    def export_json(self, filepath: str, include_all_sectors: bool = False) -> None:
        """
        Export world map to JSON file.

        Args:
            filepath: Output file path
            include_all_sectors: If True, export all 65536 sectors (large file!)
                                If False, export metadata only

        Output format:
            {
                "seed": "silgarron_alpha",
                "width": 256,
                "height": 256,
                "sector_count": 65536,
                "sectors": [...] (optional)
            }
        """
        data = {
            'seed': self.seed,
            'width': self.width,
            'height': self.height,
            'sector_count': len(self.sectors)
        }

        if include_all_sectors:
            data['sectors'] = [
                sector.to_dict()
                for sector in self.sectors.values()
            ]

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        file_size = len(json.dumps(data)) / 1024 / 1024
        print(f"[WorldMap] Exported to {filepath} ({file_size:.1f} MB)")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Calculate map statistics.

        Returns:
            Dict with various statistics
        """
        if not self.sectors:
            return {}

        tissue_counts = {}
        elevation_sum = 0
        temperature_sum = 0
        lymph_channel_count = 0
        cavern_count = 0

        for sector in self.sectors.values():
            # Tissue distribution
            tissue_id = sector.tissue_id
            tissue_counts[tissue_id] = tissue_counts.get(tissue_id, 0) + 1

            # Average parameters
            elevation_sum += sector.elevation
            temperature_sum += sector.temperature

            # Special features
            if sector.is_lymph_channel:
                lymph_channel_count += 1
            if sector.is_cavern:
                cavern_count += 1

        total = len(self.sectors)

        return {
            'total_sectors': total,
            'tissue_distribution': {
                tissue_id: count / total * 100
                for tissue_id, count in tissue_counts.items()
            },
            'average_elevation': elevation_sum / total,
            'average_temperature': temperature_sum / total,
            'lymph_channels': lymph_channel_count,
            'caverns': cavern_count
        }

    def __repr__(self) -> str:
        return f"WorldMap(seed='{self.seed}', size={self.width}x{self.height}, sectors={len(self.sectors)})"


if __name__ == "__main__":
    # Simple test
    print("=== GlobalSector Test ===\n")

    # Test coordinate conversion
    print("1. Coordinate Conversion:")
    offset_x, offset_y = 128, 128
    q, r = offset_to_axial(offset_x, offset_y)
    back_x, back_y = axial_to_offset(q, r)
    print(f"  Offset ({offset_x}, {offset_y}) -> Axial ({q}, {r}) -> Offset ({back_x}, {back_y})")
    assert (back_x, back_y) == (offset_x, offset_y), "Roundtrip conversion failed!"

    # Test distance
    print("\n2. Distance Calculation:")
    q1, r1 = 0, 0
    q2, r2 = 3, 3
    distance = axial_distance(q1, r1, q2, r2)
    print(f"  Distance from ({q1}, {r1}) to ({q2}, {r2}): {distance} hexes")

    # Test neighbors
    print("\n3. Neighbors:")
    neighbors = get_axial_neighbors(0, 0)
    print(f"  Neighbors of (0, 0): {neighbors}")

    # Test GlobalSector
    print("\n4. GlobalSector Creation:")
    sector = GlobalSector(
        offset_x=128,
        offset_y=128,
        elevation=0.7,
        temperature=0.6,
        tissue_id='pulsating_dermis',
        tissue_name='Pulsating Dermis',
        tissue_color='#E8B4B8',
        tissue_tags=('surface:dynamic', 'ecology:moderate')
    )
    print(f"  {sector}")
    print(f"  Biome candidates: {sector.get_biome_candidates()}")

    # Test export
    print("\n5. JSON Export:")
    sector_dict = sector.to_dict()
    print(f"  Exported keys: {list(sector_dict.keys())}")

    # Test WorldMap
    print("\n6. WorldMap Container:")
    world_map = WorldMap(seed="test_seed")
    world_map.add_sector(sector)
    retrieved = world_map.get_sector(128, 128)
    print(f"  {world_map}")
    print(f"  Retrieved sector: {retrieved}")

    print("\n[OK] All tests passed!")
