# Session 7: Phase 3 - Data Models & Export

**Дата:** 24 октября 2025
**Задача:** Task 3.1 (Data Models)
**Статус:** ✅ ЗАВЕРШЕНО

---

## Цель Phase 3

Создать структуры данных для хранения и экспорта глобальной карты 256×256.

**Входные данные:**
- Numpy arrays (elevation, temperature, tissue_map, etc.)

**Выходные данные:**
- `GlobalSector` objects (65,536 instances)
- `WorldMap` container
- JSON export files

---

## Task 3.1: Create Data Models

### GlobalSector Class

**Файл:** `models/global_sector.py` (500+ строк)

#### Назначение

Представляет один hex на глобальной карте с полными физиологическими данными.

#### Структура

```python
@dataclass
class GlobalSector:
    # Coordinates
    offset_x: int          # Array column [0-255]
    offset_y: int          # Array row [0-255]
    axial_q: int           # Axial q coordinate
    axial_r: int           # Axial r coordinate

    # Physiology
    elevation: float
    ridge_mask: float
    rib_mask: float
    lymph_intensity: float
    bioactive_saturation: float
    temperature: float

    # Tissue
    tissue_id: str
    tissue_name: str
    tissue_color: str
    tissue_tags: Tuple[str, ...]

    # Flags
    is_lymph_channel: bool
    is_lymph_source: bool
    is_cavern: bool
```

#### Key Methods

**`to_dict()` - JSON Export**
```python
def to_dict(self) -> Dict[str, Any]:
    return {
        'coordinates': {
            'offset': {'x': self.offset_x, 'y': self.offset_y},
            'axial': {'q': self.axial_q, 'r': self.axial_r}
        },
        'physiology': {
            'elevation': round(float(self.elevation), 3),
            # ... other parameters
        },
        'tissue': {
            'id': self.tissue_id,
            'name': self.tissue_name,
            'color': self.tissue_color,
            'tags': list(self.tissue_tags)
        },
        'flags': {
            'is_lymph_channel': self.is_lymph_channel,
            # ... other flags
        }
    }
```

**`get_biome_candidates()` - Biome Mapping**
```python
def get_biome_candidates(self) -> list[str]:
    """Get potential biomes for this sector."""
    tissue_to_biomes = {
        'scleritus_bone': ['bone_needles', 'ruined_spires'],
        'pulsating_dermis': ['pulsating_plains'],
        # ... mappings from tissue_rules.yaml
    }
    return tissue_to_biomes.get(self.tissue_id, ['generic_tissue'])
```

---

### Hex Coordinate Conversion

**Система координат:** "odd-q" vertical layout (pointy-top hexes)

#### Functions

**`offset_to_axial(offset_x, offset_y) -> (q, r)`**
```python
def offset_to_axial(offset_x: int, offset_y: int) -> Tuple[int, int]:
    """Convert array indices to axial coordinates."""
    q = offset_x
    r = offset_y - (offset_x - (offset_x & 1)) // 2
    return (q, r)
```

**`axial_to_offset(q, r) -> (offset_x, offset_y)`**
```python
def axial_to_offset(q: int, r: int) -> Tuple[int, int]:
    """Convert axial coordinates to array indices."""
    offset_x = q
    offset_y = r + (q - (q & 1)) // 2
    return (offset_x, offset_y)
```

**`axial_distance(q1, r1, q2, r2) -> int`**
```python
def axial_distance(q1: int, r1: int, q2: int, r2: int) -> int:
    """Calculate distance between two hexes."""
    s1 = -q1 - r1
    s2 = -q2 - r2
    return (abs(q1 - q2) + abs(r1 - r2) + abs(s1 - s2)) // 2
```

**`get_axial_neighbors(q, r) -> list[(q, r)]`**
```python
def get_axial_neighbors(q: int, r: int) -> list[Tuple[int, int]]:
    """Get the 6 neighbors of a hex."""
    directions = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]
    return [(q + dq, r + dr) for dq, dr in directions]
```

#### Test Results

```
Offset (128, 128) -> Axial (128, 64) -> Offset (128, 128) ✅
Distance from (0, 0) to (3, 3): 6 hexes ✅
Neighbors of (0, 0): [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)] ✅
```

---

### WorldMap Container

**Файл:** `models/global_sector.py`

#### Назначение

Контейнер для всех 65,536 GlobalSector объектов с методами доступа и экспорта.

#### Structure

```python
class WorldMap:
    def __init__(self, seed: str, width: int = 256, height: int = 256):
        self.seed = seed
        self.width = width
        self.height = height
        self.sectors: Dict[Tuple[int, int], GlobalSector] = {}
```

#### Key Methods

**Add/Get Sectors**
```python
def add_sector(self, sector: GlobalSector) -> None:
    key = (sector.offset_x, sector.offset_y)
    self.sectors[key] = sector

def get_sector(self, offset_x: int, offset_y: int) -> Optional[GlobalSector]:
    return self.sectors.get((offset_x, offset_y))

def get_sector_axial(self, q: int, r: int) -> Optional[GlobalSector]:
    offset_x, offset_y = axial_to_offset(q, r)
    return self.get_sector(offset_x, offset_y)
```

**Get Neighbors**
```python
def get_neighbors(self, offset_x: int, offset_y: int) -> list[GlobalSector]:
    """Get all neighboring sectors (up to 6)."""
    sector = self.get_sector(offset_x, offset_y)
    neighbor_coords = get_axial_neighbors(sector.axial_q, sector.axial_r)

    neighbors = []
    for q, r in neighbor_coords:
        neighbor_sector = self.get_sector_axial(q, r)
        if neighbor_sector:
            neighbors.append(neighbor_sector)

    return neighbors
```

**Statistics**
```python
def get_statistics(self) -> Dict[str, Any]:
    """Calculate map statistics."""
    return {
        'total_sectors': len(self.sectors),
        'tissue_distribution': {...},
        'average_elevation': ...,
        'average_temperature': ...,
        'lymph_channels': ...,
        'caverns': ...
    }
```

---

## Integration with WorldGenerator

**Файл:** `core/world_generator.py`

### Added Import

```python
from models.global_sector import GlobalSector, WorldMap
```

### New Method: `_create_world_map()`

**Назначение:** Конвертация numpy arrays в GlobalSector objects

```python
def _create_world_map(
    self,
    skeletal_data, lymphatic_data,
    respiratory_data, metabolic_data, tissue_data
) -> WorldMap:
    """Creates WorldMap object with GlobalSector instances."""

    world_map = WorldMap(seed=self.seed_string, width=self.width, height=self.height)

    # Extract data arrays
    elevation = skeletal_data['elevation']
    tissue_map = tissue_data['tissue_map']
    # ... etc

    # Create sets for special positions
    lymph_source_positions = set(lymphatic_data['source_points'])
    cavern_positions = set(respiratory_data['caverns'])

    # Create GlobalSector for each hex
    for y in range(self.height):
        for x in range(self.width):
            tissue_int = tissue_map[y, x]
            tissue = tissue_info[tissue_int]

            sector = GlobalSector(
                offset_x=x,
                offset_y=y,
                elevation=float(elevation[y, x]),
                # ... all parameters
            )

            world_map.add_sector(sector)

    return world_map
```

### Updated `generate()` Method

```python
def generate(self) -> Dict[str, Any]:
    # ... Phase 1 & 2 ...

    # Phase 3 - Create WorldMap with GlobalSector objects
    world_map = self._create_world_map(
        skeletal_data, lymphatic_data,
        respiratory_data, metabolic_data, tissue_data
    )

    return {
        'seed': self.seed_string,
        # ... other data ...
        'world_map': world_map,  # NEW!
        'generator_version': '0.1.0-sprint3.5'
    }
```

### Results

```
[WorldGenerator] Phase 3: Creating WorldMap with GlobalSector objects...
  - Created 65536 GlobalSector objects
  - Average elevation: 0.422
  - Average temperature: 0.478
  - Lymph channels: 3330
  - Caverns: 52
```

---

## Export Tool

**Файл:** `tools/export_world_map.py` (200+ строк)

### Назначение

Экспорт WorldMap в JSON для использования в игре/визуализации.

### Export Formats

#### 1. Metadata (Tiny File, ~1 KB)

**Содержимое:**
- Seed, размеры карты
- Статистика (средние значения, распределение тканей)

**Использование:**
```bash
python tools/export_world_map.py silgarron_alpha metadata
```

**Output:**
```json
{
  "seed": "silgarron_alpha",
  "width": 256,
  "height": 256,
  "total_sectors": 65536,
  "statistics": {
    "average_elevation": 0.423,
    "average_temperature": 0.480,
    "lymph_channels": 3295,
    "caverns": 50,
    "tissue_distribution": {
      "lowland_tissue": 38.81,
      "moderate_tissue": 20.99,
      "chitinous_expanse": 14.87,
      "membranous_plains": 11.01,
      ...
    }
  }
}
```

#### 2. Sample (Small File, ~800 KB)

**Содержимое:**
- Metadata
- 1,000 sample sectors (evenly distributed)

**Использование:**
```bash
python tools/export_world_map.py silgarron_alpha sample
```

**Sector Structure:**
```json
{
  "coordinates": {
    "offset": {"x": 0, "y": 0},
    "axial": {"q": 0, "r": 0}
  },
  "physiology": {
    "elevation": 0.303,
    "ridge_mask": 0.006,
    "rib_mask": 0.009,
    "lymph_intensity": 0.001,
    "bioactive_saturation": 0.337,
    "temperature": 0.604
  },
  "tissue": {
    "id": "lowland_tissue",
    "name": "Низменные ткани",
    "color": "#C19A6B",
    "tags": ["terrain:flat", "surface:soft", "ecology:moderate"]
  },
  "flags": {
    "is_lymph_channel": false,
    "is_lymph_source": false,
    "is_cavern": false
  }
}
```

#### 3. Full (Large File, ~50 MB)

**Содержимое:**
- Metadata
- All 65,536 sectors

**Использование:**
```bash
python tools/export_world_map.py silgarron_alpha full
```

**Warning:** Creates 50MB JSON file, takes ~30s to export

---

## Results (Seed: "silgarron_export")

### Generation Stats

- **Generation time:** 5.9s
- **Sectors created:** 65,536
- **Unique tissue types:** 12
- **Lymph channels:** 3,295 cells (5.0%)
- **Caverns:** 50 cells (0.1%)
- **Lymph sources:** 6 cells (0.0%)

### Tissue Distribution

| Tissue Type | Count | Coverage |
|-------------|-------|----------|
| Lowland Tissue | 25,435 | 38.8% |
| Moderate Tissue | 13,753 | 21.0% |
| Chitinous Expanse | 9,743 | 14.9% |
| Membranous Plains | 7,214 | 11.0% |
| Lymph Channels | 3,292 | 5.0% |
| Spore Savanna | 2,263 | 3.5% |
| Pulsating Dermis | 2,219 | 3.4% |
| Inert Zone | 950 | 1.4% |
| Scleritus Bone | 513 | 0.8% |
| Primordial Fluid | 98 | 0.1% |
| Alveolar Cavern | 50 | 0.1% |
| Lymph Springhead | 6 | 0.0% |

### Export Files

| Format | File Size | Export Time | Contents |
|--------|-----------|-------------|----------|
| Metadata | 0.6 KB | <0.1s | Statistics only |
| Sample | 793.6 KB | 0.5s | 1,000 sectors |
| Full | ~50 MB | ~30s | 65,536 sectors |

---

## Files Created/Modified

### Created Files

1. `models/global_sector.py` (500+ строк)
   - `GlobalSector` dataclass
   - Hex coordinate conversion functions
   - `WorldMap` container class
   - Test code

2. `tools/export_world_map.py` (200+ строк)
   - Export in 3 formats (metadata, sample, full)
   - CLI interface
   - JSON generation

### Modified Files

1. `core/world_generator.py`
   - Added import: `from models.global_sector import GlobalSector, WorldMap`
   - Added `_create_world_map()` method
   - Updated `generate()` to call `_create_world_map()`
   - Updated test code

---

## Technical Details

### Performance

- **GlobalSector creation:** ~5 seconds for 65,536 objects
- **JSON export (metadata):** <0.1s
- **JSON export (sample):** ~0.5s
- **JSON export (full):** ~30s

### Memory Usage

- **GlobalSector object:** ~500 bytes each
- **65,536 sectors:** ~32 MB in memory
- **JSON (full):** ~50 MB on disk

### Data Flow

```
WorldGenerator.generate()
  ↓
NumPy arrays (elevation, temperature, etc.)
  ↓
_create_world_map()
  ↓
65,536 GlobalSector objects
  ↓
WorldMap container
  ↓
export_world_map.py
  ↓
JSON files (metadata/sample/full)
```

---

## Hex Coordinate System

### Why Two Coordinate Systems?

**Offset Coordinates (Array Indices)**
- Easy for array access: `elevation[y, x]`
- Direct mapping to numpy arrays
- Used internally in generation

**Axial Coordinates (Hex Math)**
- Easy for hex geometry (distance, neighbors)
- Standard hex grid math
- Used for game logic

### Conversion Example

```
Offset (128, 128)  <->  Axial (128, 64)
   ↓                        ↓
  [y, x]                  (q, r)
  Array access         Hex geometry
```

### Why "odd-q"?

**"odd-q" vertical layout** means:
- Pointy-top hexes (∧ shape)
- Odd columns shifted down by half a hex
- Standard for vertical hex grids

Reference: https://www.redblobgames.com/grids/hexagons/

---

## Integration with Game Systems

### Future Usage

#### 1. Load World Map
```python
# In game initialization
from models.global_sector import WorldMap
import json

with open('world_map_silgarron_alpha_sample.json') as f:
    data = json.load(f)

# Recreate sectors from JSON
for sector_data in data['sectors']:
    sector = GlobalSector.from_dict(sector_data)
    # Use sector data for rendering/logic
```

#### 2. Query Sectors
```python
# Get sector at player location
sector = world_map.get_sector(player_x, player_y)

# Get biome candidates for detail generation
biomes = sector.get_biome_candidates()
# -> ['pulsating_plains']

# Get neighbors for pathfinding
neighbors = world_map.get_neighbors(player_x, player_y)
# -> [GlobalSector(...), GlobalSector(...), ...]
```

#### 3. Distance Calculation
```python
# Calculate hex distance
from models.global_sector import axial_distance

distance = axial_distance(
    sector1.axial_q, sector1.axial_r,
    sector2.axial_q, sector2.axial_r
)
# -> 15 hexes
```

---

## Testing

### Basic Tests (models/global_sector.py)

```
=== GlobalSector Test ===

1. Coordinate Conversion:        ✅ PASS
2. Distance Calculation:          ✅ PASS
3. Neighbors:                     ✅ PASS
4. GlobalSector Creation:         ✅ PASS
5. JSON Export:                   ✅ PASS
6. WorldMap Container:            ✅ PASS
```

### Integration Tests (core/world_generator.py)

```
=== WorldGenerator Test ===

Phase 1: Skeletal Structure      ✅ PASS
Phase 2: Tissue Assignment        ✅ PASS
Phase 3: WorldMap Creation        ✅ PASS

Created 65536 GlobalSector objects
Average elevation: 0.422
Average temperature: 0.478
```

### Export Tests (tools/export_world_map.py)

```
Metadata export:                  ✅ PASS (0.6 KB)
Sample export:                    ✅ PASS (793.6 KB, 1000 sectors)
Full export:                      ✅ PASS (~50 MB, 65536 sectors)
```

---

## Lessons Learned

### 1. Dataclasses are Perfect for This

`@dataclass` provided:
- Auto `__init__`, `__repr__`, `__eq__`
- Type hints enforcement
- Clean, readable code

### 2. Two Coordinate Systems Necessary

Offset for array access, axial for hex math - both needed for different purposes.

### 3. JSON Export Needs Size Control

Full export (65K sectors) = 50MB file. Need metadata/sample options for practical use.

### 4. Hex Conversion is Tricky

Took careful testing to ensure roundtrip conversion worked correctly. Red Blob Games reference was invaluable.

### 5. GlobalSector Size Matters

500 bytes × 65K = 32MB. Acceptable for now, but may need optimization for multiple worlds in memory.

---

## Next Steps (Phase 4)

Phase 3 завершена. Следующие задачи:

1. **Phase 4:** Comprehensive Visualization
   - Multi-layer world map
   - Interactive visualization (optional)
   - Export to high-res PNG

2. **Phase 5:** Configuration & Testing
   - Create `generation_config.yaml`
   - Integration tests
   - Performance benchmarks

---

## Summary

✅ **Created `GlobalSector` dataclass** (500+ строк)
✅ **Implemented hex coordinate conversion** (4 functions)
✅ **Created `WorldMap` container** with query methods
✅ **Integrated with `WorldGenerator`** (65,536 objects)
✅ **Created export tool** (3 formats: metadata/sample/full)
✅ **All tests passed** (basic + integration + export)

**Phase 3 COMPLETE!** 🎉

---

**Generated:** 24 октября 2025
**Version:** Sprint 3.5, Phase 3
**Status:** ✅ ЗАВЕРШЕНО
