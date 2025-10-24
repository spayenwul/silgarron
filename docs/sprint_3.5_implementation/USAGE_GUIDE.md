# Silgarron World Generator - Usage Guide

**Version:** 1.0.0 (Sprint 3.5)
**Last Updated:** 24 октября 2025

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [World Generation](#world-generation)
3. [Data Export](#data-export)
4. [Visualization](#visualization)
5. [Data Models](#data-models)
6. [Configuration](#configuration)
7. [Troubleshooting](#troubleshooting)
8. [API Reference](#api-reference)

---

## Quick Start

### Installation

Убедитесь, что установлены все зависимости:

```bash
pip install numpy matplotlib pyyaml
```

### Generate Your First World

```python
from core.world_generator import WorldGenerator

# Создать генератор с seed
gen = WorldGenerator(seed="my_first_world")

# Сгенерировать мир (занимает ~6 секунд)
result = gen.generate()

# Получить WorldMap
world_map = result['world_map']
print(world_map)  # WorldMap(seed='my_first_world', size=256x256, sectors=65536)
```

---

## World Generation

### Basic Generation

```python
from core.world_generator import WorldGenerator

# Инициализация
gen = WorldGenerator(seed="silgarron_alpha", width=256, height=256)

# Генерация
result = gen.generate()
```

### Understanding the Result

`result` это dict с ключами:

```python
{
    'seed': 'silgarron_alpha',        # Seed мира
    'seed_int': 1234567890,            # Числовой seed (для RNG)
    'width': 256,                      # Ширина карты
    'height': 256,                     # Высота карты
    'skeletal': {...},                 # Скелетная структура (numpy arrays)
    'lymphatic': {...},                # Лимфатическая система
    'respiratory': {...},              # Дыхательная система
    'metabolic': {...},                # Метаболизм
    'tissues': {...},                  # Типы тканей
    'world_map': WorldMap(...),        # GlobalSector objects
    'generator_version': '0.1.0-sprint3.5'
}
```

### Accessing Generated Data

#### Skeletal Data

```python
skeletal = result['skeletal']

elevation = skeletal['elevation']      # np.ndarray (256, 256) - высота [0, 1]
ridge_mask = skeletal['ridge_mask']    # np.ndarray (256, 256) - хребет [0, 1]
rib_mask = skeletal['rib_mask']        # np.ndarray (256, 256) - рёбра [0, 1]
```

#### Lymphatic Data

```python
lymphatic = result['lymphatic']

lymph_intensity = lymphatic['lymph_intensity']        # np.ndarray - поток [0, 1]
lymph_channels = lymphatic['lymph_channels']          # np.ndarray - маска каналов
source_points = lymphatic['source_points']            # List[(y, x)] - истоки
flow_accumulation = lymphatic['flow_accumulation']    # np.ndarray - накопление
```

#### Respiratory Data

```python
respiratory = result['respiratory']

caverns = respiratory['caverns']                        # List[(y, x)] - каверны
exhalation_influence = respiratory['exhalation_influence']  # np.ndarray [0, 1]
bioactive_saturation = respiratory['bioactive_saturation']  # np.ndarray [0, 1]
```

#### Metabolic Data

```python
metabolic = result['metabolic']

temperature = metabolic['temperature']  # np.ndarray (256, 256) - температура [0, 1]
```

#### Tissue Data

```python
tissues = result['tissues']

tissue_map = tissues['tissue_map']    # np.ndarray (256, 256) - int IDs
tissue_info = tissues['tissue_info']  # Dict[int, Dict] - метаданные тканей

# Пример tissue_info
# {
#     1: {
#         'id': 'scleritus_bone',
#         'name': 'Склеритовая кость',
#         'color': '#E8E8E8',
#         'tags': ['terrain:elevated', 'resource:bone_chitin']
#     },
#     ...
# }
```

---

## Data Export

### Export to JSON

```python
from tools.export_world_map import export_world_map

# Экспорт metadata только (0.6 KB)
export_world_map("my_world", output_format="metadata")

# Экспорт sample (1000 секторов, ~800 KB)
export_world_map("my_world", output_format="sample")

# Экспорт full map (все 65,536 секторов, ~50 MB)
export_world_map("my_world", output_format="full")
```

**Command Line:**

```bash
python tools/export_world_map.py my_world metadata
python tools/export_world_map.py my_world sample
python tools/export_world_map.py my_world full
```

### JSON Structure

#### Metadata Format

```json
{
  "seed": "my_world",
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
      ...
    }
  }
}
```

#### Full/Sample Sector Format

```json
{
  "coordinates": {
    "offset": {"x": 128, "y": 128},
    "axial": {"q": 128, "r": 64}
  },
  "physiology": {
    "elevation": 0.523,
    "ridge_mask": 0.012,
    "rib_mask": 0.005,
    "lymph_intensity": 0.234,
    "bioactive_saturation": 0.456,
    "temperature": 0.678
  },
  "tissue": {
    "id": "pulsating_dermis",
    "name": "Пульсирующая дерма",
    "color": "#E8B4B8",
    "tags": ["surface:dynamic", "ecology:moderate"]
  },
  "flags": {
    "is_lymph_channel": false,
    "is_lymph_source": false,
    "is_cavern": false
  }
}
```

---

## Visualization

### Complete World Map (9-panel)

```bash
python tools/visualize_complete_world.py my_world
```

**Output:**
- `output/complete_world_my_world.png` (200 DPI, ~10 MB)
- `output/complete_world_my_world_4k.png` (300 DPI, ~20 MB)

**Panels:**
1. Skeletal Structure (elevation + ridge)
2. Lymphatic System (channels + flow)
3. Respiratory System (bioactive + caverns)
4. Metabolic Temperature (heat map)
5. Tissue Types (color-coded)
6. Ridge Mask (bone intensity)
7. Physiological RGB (composite)
8. Special Features (sources, channels, caverns)
9. Statistics (text)

### Individual System Visualizations

```bash
# Skeletal system (4 panels)
python tools/visualize_skeletal.py my_world

# Lymphatic system (6 panels)
python tools/visualize_lymphatic.py my_world

# Respiratory system (4 panels)
python tools/visualize_respiratory.py my_world

# Metabolic system (6 panels)
python tools/visualize_metabolic.py my_world

# Tissue map (4 panels)
python tools/visualize_tissues.py my_world
```

---

## Data Models

### GlobalSector Class

Represents a single hex cell on the global map.

#### Creating a Sector

```python
from models.global_sector import GlobalSector

sector = GlobalSector(
    offset_x=128,
    offset_y=128,
    elevation=0.5,
    temperature=0.6,
    tissue_id='pulsating_dermis',
    tissue_name='Pulsating Dermis',
    tissue_color='#E8B4B8',
    tissue_tags=('surface:dynamic', 'ecology:moderate')
)

print(sector)
# GlobalSector(offset=(128, 128), axial=(128, 64), tissue=pulsating_dermis, ...)
```

#### Accessing Sector Data

```python
# Coordinates
print(sector.offset_x, sector.offset_y)  # Array indices
print(sector.axial_q, sector.axial_r)    # Hex coordinates

# Physiology
print(sector.elevation)
print(sector.temperature)
print(sector.lymph_intensity)

# Tissue
print(sector.tissue_id)
print(sector.tissue_name)
print(sector.tissue_color)
print(sector.tissue_tags)

# Flags
print(sector.is_lymph_channel)
print(sector.is_cavern)
```

#### Export/Import

```python
# Export to dict
data = sector.to_dict()

# Import from dict
sector2 = GlobalSector.from_dict(data)
```

#### Get Biome Candidates

```python
biomes = sector.get_biome_candidates()
# -> ['pulsating_plains'] (for pulsating_dermis)
```

### WorldMap Class

Container for all 65,536 GlobalSector objects.

#### Accessing WorldMap

```python
from core.world_generator import WorldGenerator

gen = WorldGenerator(seed="test")
result = gen.generate()
world_map = result['world_map']

print(world_map)
# WorldMap(seed='test', size=256x256, sectors=65536)
```

#### Querying Sectors

```python
# Get sector by offset coordinates
sector = world_map.get_sector(128, 128)

# Get sector by axial coordinates
sector = world_map.get_sector_axial(q=128, r=64)

# Get neighbors (up to 6)
neighbors = world_map.get_neighbors(128, 128)
for neighbor in neighbors:
    print(neighbor.tissue_id)
```

#### Statistics

```python
stats = world_map.get_statistics()

print(stats['total_sectors'])           # 65536
print(stats['average_elevation'])       # 0.423
print(stats['average_temperature'])     # 0.480
print(stats['lymph_channels'])          # 3295
print(stats['caverns'])                 # 50
print(stats['tissue_distribution'])     # Dict[tissue_id, percentage]
```

#### Export

```python
# Metadata only
world_map.export_json("output/my_world_metadata.json", include_all_sectors=False)

# Full export
world_map.export_json("output/my_world_full.json", include_all_sectors=True)
```

### Hex Coordinate Conversion

```python
from models.global_sector import (
    offset_to_axial,
    axial_to_offset,
    axial_distance,
    get_axial_neighbors
)

# Convert offset to axial
q, r = offset_to_axial(128, 128)  # -> (128, 64)

# Convert axial to offset
x, y = axial_to_offset(128, 64)   # -> (128, 128)

# Calculate distance
dist = axial_distance(0, 0, 10, 10)  # -> 20 hexes

# Get neighbors
neighbors = get_axial_neighbors(128, 64)
# -> [(129, 64), (129, 63), (128, 63), (127, 64), (127, 65), (128, 65)]
```

---

## Configuration

### Using generation_config.yaml

**File location:** `data/generation_config.yaml`

#### Current Status

⚠️ **Note:** Config file создан, но пока не используется WorldGenerator напрямую.

Параметры в config файле служат как:
1. Документация текущих значений
2. Референс для будущей реализации
3. Шаблон для кастомных конфигов

#### How to Use Now

**Option 1:** Modify source code directly

```python
# In core/world_generator.py, modify constants:
RIDGE_CENTER = 0.5
RIDGE_WIDTH = 0.15
```

**Option 2:** Create wrapper function

```python
import yaml
from core.world_generator import WorldGenerator

def create_generator_with_config(seed, config_path):
    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Create generator
    gen = WorldGenerator(seed=seed)

    # Apply config (would need implementation)
    # gen.apply_config(config)

    return gen
```

#### Presets

Config file contains presets for different world types:

- **default** - Balanced world (active)
- **mountainous** - Преобладают горы
- **plains** - Плоские равнины
- **oceanic** - Много жидкости
- **volcanic** - Высокая температура, много каверн

To use a preset (future):
```python
gen = WorldGenerator(seed="test", preset="mountainous")
```

---

## Troubleshooting

### Common Issues

#### 1. ModuleNotFoundError

```
ModuleNotFoundError: No module named 'core'
```

**Solution:**
```bash
# Set PYTHONPATH
export PYTHONPATH=/path/to/neuro_rpg  # Linux/Mac
set PYTHONPATH=E:\neuro_rpg           # Windows
```

Or use absolute imports:
```python
import sys
sys.path.insert(0, '/path/to/neuro_rpg')
```

#### 2. UnicodeEncodeError

```
UnicodeEncodeError: 'charmap' codec can't encode character
```

**Solution:** Windows console issue. Already fixed in code (× replaced with x, etc.)

#### 3. Memory Issues

Generating worlds uses ~500 MB RAM. For multiple worlds:

```python
# Clear data after generation
result = gen.generate()
world_map = result['world_map']

# Clear numpy arrays
del result['skeletal']
del result['lymphatic']
# ... etc
```

#### 4. Slow Generation

First generation takes ~6s due to imports. Subsequent generations ~5s.

**Speed up:**
- Use smaller maps: `WorldGenerator(seed="test", width=128, height=128)`
- Skip WorldMap creation (modify source to return early)

---

## API Reference

### WorldGenerator

```python
class WorldGenerator:
    def __init__(self, seed: str, width: int = 256, height: int = 256)
    def generate(self) -> Dict[str, Any]
```

**Methods:**
- `generate()` - Generate complete world, returns dict

**Parameters:**
- `seed` (str) - World seed, любая строка
- `width` (int) - Map width in hexes (default: 256)
- `height` (int) - Map height in hexes (default: 256)

### GlobalSector

```python
@dataclass
class GlobalSector:
    offset_x: int
    offset_y: int
    elevation: float
    temperature: float
    tissue_id: str
    # ... (see full list in code)

    def to_dict(self) -> Dict[str, Any]
    def get_biome_candidates(self) -> list[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GlobalSector'
```

### WorldMap

```python
class WorldMap:
    def __init__(self, seed: str, width: int = 256, height: int = 256)

    def add_sector(self, sector: GlobalSector) -> None
    def get_sector(self, offset_x: int, offset_y: int) -> Optional[GlobalSector]
    def get_sector_axial(self, q: int, r: int) -> Optional[GlobalSector]
    def get_neighbors(self, offset_x: int, offset_y: int) -> list[GlobalSector]
    def get_statistics(self) -> Dict[str, Any]
    def export_json(self, filepath: str, include_all_sectors: bool = False) -> None
```

### Coordinate Functions

```python
def offset_to_axial(offset_x: int, offset_y: int) -> Tuple[int, int]
def axial_to_offset(q: int, r: int) -> Tuple[int, int]
def axial_distance(q1: int, r1: int, q2: int, r2: int) -> int
def get_axial_neighbors(q: int, r: int) -> list[Tuple[int, int]]
```

---

## Examples

### Example 1: Generate and Export

```python
from core.world_generator import WorldGenerator

# Generate
gen = WorldGenerator(seed="example1")
result = gen.generate()

# Export
world_map = result['world_map']
world_map.export_json("output/example1.json", include_all_sectors=False)

print(f"Generated {len(world_map.sectors)} sectors")
```

### Example 2: Query Specific Location

```python
# Generate world
gen = WorldGenerator(seed="example2")
result = gen.generate()
world_map = result['world_map']

# Query center of map
center_sector = world_map.get_sector(128, 128)

print(f"Center sector tissue: {center_sector.tissue_name}")
print(f"Elevation: {center_sector.elevation:.2f}")
print(f"Temperature: {center_sector.temperature:.2f}")

# Get neighbors
neighbors = world_map.get_neighbors(128, 128)
print(f"Number of neighbors: {len(neighbors)}")
```

### Example 3: Find All Caverns

```python
gen = WorldGenerator(seed="example3")
result = gen.generate()
world_map = result['world_map']

# Find all cavern sectors
caverns = []
for sector in world_map.sectors.values():
    if sector.is_cavern:
        caverns.append(sector)

print(f"Found {len(caverns)} caverns:")
for cavern in caverns:
    print(f"  - Cavern at ({cavern.offset_x}, {cavern.offset_y})")
```

### Example 4: Calculate Statistics

```python
gen = WorldGenerator(seed="example4")
result = gen.generate()
world_map = result['world_map']

stats = world_map.get_statistics()

print("=== World Statistics ===")
print(f"Total sectors: {stats['total_sectors']:,}")
print(f"Average elevation: {stats['average_elevation']:.3f}")
print(f"Average temperature: {stats['average_temperature']:.3f}")
print(f"Lymph channels: {stats['lymph_channels']} ({stats['lymph_channels']/stats['total_sectors']*100:.1f}%)")
print(f"Caverns: {stats['caverns']}")

print("\nTissue Distribution:")
for tissue_id, pct in sorted(stats['tissue_distribution'].items(), key=lambda x: x[1], reverse=True):
    print(f"  {tissue_id:30s}: {pct:5.1f}%")
```

### Example 5: Batch Generation

```python
from core.world_generator import WorldGenerator

seeds = ["world1", "world2", "world3", "world4", "world5"]

for seed in seeds:
    print(f"Generating {seed}...")

    gen = WorldGenerator(seed=seed)
    result = gen.generate()

    # Export metadata
    world_map = result['world_map']
    world_map.export_json(f"output/{seed}_metadata.json", include_all_sectors=False)

    print(f"  - Sectors: {len(world_map.sectors)}")
    print(f"  - Done!\n")
```

---

## Next Steps

1. **Integrate with Game:** Use WorldMap to drive game world
2. **Biome Detail Generation:** Use `get_biome_candidates()` to generate local 32×32 maps
3. **Implement Config Loading:** Add YAML config support to WorldGenerator
4. **Performance Optimization:** Multi-threading for large maps
5. **Interactive Visualization:** Web-based map viewer

---

## Support

- **Documentation:** `docs/sprint_3.5_implementation/`
- **Tests:** `tests/test_*.py`
- **Issues:** Create issue on GitHub

---

**Generated:** 24 октября 2025
**Version:** 1.0.0 (Sprint 3.5)
**Status:** Production Ready ✅
