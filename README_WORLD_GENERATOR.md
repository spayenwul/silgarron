# Silgarron World Generator - Quick Start

> **Anatomical Procedural World Generation for Silgarron RPG**
>
> Generate 256x256 hex-based worlds with physiological systems: skeletal structure, lymphatic circulation, respiratory caverns, and metabolic temperature.

## Quick Start (3 Steps)

### 1. Generate Your First World

```python
from core.world_generator import WorldGenerator

# Generate world
gen = WorldGenerator(seed="my_first_world")
result = gen.generate()

# Access world map
world_map = result['world_map']
print(f"Generated {world_map.get_statistics()['total_sectors']:,} sectors")
```

### 2. Query Sector Data

```python
# Get specific hex cell
sector = world_map.get_sector(128, 128)  # Center of map

print(f"Tissue: {sector.tissue_name}")
print(f"Elevation: {sector.elevation:.2f}")
print(f"Temperature: {sector.temperature:.2f}")
print(f"Coordinates: ({sector.axial_q}, {sector.axial_r})")

# Get neighbors
neighbors = world_map.get_neighbors(128, 128)
print(f"Found {len(neighbors)} neighbors")
```

### 3. Visualize & Export

```bash
# Create comprehensive 9-panel visualization
python tools/visualize_complete_world.py my_first_world

# Export to JSON (3 formats)
python tools/export_world_map.py my_first_world metadata  # ~0.6 KB
python tools/export_world_map.py my_first_world sample    # ~800 KB (1000 sectors)
python tools/export_world_map.py my_first_world full      # ~50 MB (all 65,536 sectors)
```

**Output:** `output/complete_world_my_first_world.png` (200 DPI) + `_4k.png` (300 DPI)

---

## What Gets Generated?

### 5 Physiological Systems

1. **Skeletal Structure** - Ridge-biased Perlin noise (elevation, bone ridge, ribs)
2. **Lymphatic System** - D8 flow accumulation (channels, circulation, sources)
3. **Respiratory System** - Alveolar caverns with spore exhalation (BFS spread)
4. **Metabolic Activity** - Temperature synthesis from all systems
5. **Tissue Assignment** - 12 tissue types (rule-based priority matching)

### 12 Tissue Types

- `primordial_fluid` - Deep fluid pools
- `scleritus_bone` - Rigid skeletal structures
- `chitinous_expanse` - Hard shell-like terrain
- `lymph_channels` - Active circulation pathways
- `pulsating_dermis` - Warm, bioactive membrane
- `membranous_plains` - Flexible flat terrain
- `fibrous_thicket` - Dense connective tissue
- `biolume_forest` - Luminescent growth zones
- `spore_savanna` - Respiratory grasslands
- `lowland_tissue` - Soft valley regions
- `inert_zone` - Cold, inactive areas
- `moderate_tissue` - Balanced fallback tissue

---

## Key Features

- **Deterministic** - Same seed = same world (SHA-256 hashing)
- **Hex-based** - 256x256 grid with axial coordinate support
- **Data-rich** - 65,536 GlobalSector objects with full physiology
- **Configurable** - YAML-based parameter tuning
- **Tested** - 77 unit tests, 100% pass rate
- **Visualized** - Multi-layer PNG exports (standard + 4K)

---

## Project Structure

```
neuro_rpg/
├── core/                          # Generation algorithms
│   ├── world_generator.py         # Main generator
│   ├── perlin_noise.py            # Terrain generation
│   ├── flow_accumulation.py       # Lymphatic system (D8)
│   ├── poisson_sampling.py        # Cavern placement
│   ├── exhalation.py              # Spore spread (BFS)
│   └── tissue_assignment.py       # Rule-based biomes
├── models/
│   └── global_sector.py           # GlobalSector & WorldMap classes
├── data/
│   ├── tissue_rules.yaml          # 12 tissue definitions
│   └── generation_config.yaml     # Parameter tuning (future)
├── tools/                         # Visualization & export
│   ├── visualize_complete_world.py   # 9-panel comprehensive map
│   ├── visualize_skeletal.py         # Skeletal system only
│   ├── visualize_lymphatic.py        # Lymphatic system only
│   ├── visualize_respiratory.py      # Respiratory system only
│   ├── visualize_metabolic.py        # Temperature only
│   ├── visualize_tissues.py          # Tissue map only
│   └── export_world_map.py           # JSON export
├── tests/                         # 77 unit tests
│   ├── test_skeletal.py           # 14 tests
│   ├── test_lymphatic.py          # 13 tests
│   ├── test_respiratory.py        # 18 tests
│   ├── test_metabolic.py          # 10 tests
│   └── test_tissue_assignment.py  # 22 tests
└── output/                        # Generated maps & exports
```

---

## Detailed Documentation

For comprehensive documentation, see:

- **[USAGE_GUIDE.md](docs/sprint_3.5_implementation/USAGE_GUIDE.md)** - Complete API reference, examples, troubleshooting
- **[PROGRESS_REPORT.md](docs/sprint_3.5_implementation/PROGRESS_REPORT.md)** - Implementation timeline and statistics
- **[generation_config.yaml](data/generation_config.yaml)** - Parameter documentation and presets
- **[ADR-013 to ADR-015](docs/sprint_3.5_implementation/)** - Architecture decision records

---

## Common Use Cases

### Use Case 1: Generate Multiple Worlds

```python
from core.world_generator import WorldGenerator

seeds = ["alpha", "beta", "gamma"]

for seed in seeds:
    gen = WorldGenerator(seed=seed)
    result = gen.generate()
    world_map = result['world_map']

    # Export
    world_map.export_json(f"output/{seed}_world.json", include_all_sectors=False)
    print(f"[OK] Generated world: {seed}")
```

### Use Case 2: Find All Caverns

```python
gen = WorldGenerator(seed="cavern_search")
result = gen.generate()
world_map = result['world_map']

caverns = []
for sector in world_map.sectors.values():
    if sector.is_cavern:
        caverns.append((sector.offset_x, sector.offset_y, sector.tissue_name))

print(f"Found {len(caverns)} caverns")
for x, y, tissue in caverns[:5]:
    print(f"  Cavern at ({x}, {y}) - {tissue}")
```

### Use Case 3: Analyze Tissue Distribution

```python
gen = WorldGenerator(seed="tissue_analysis")
result = gen.generate()
stats = result['world_map'].get_statistics()

print("=== Tissue Distribution ===")
for tissue_id, percentage in sorted(stats['tissue_distribution'].items(),
                                    key=lambda x: x[1], reverse=True):
    print(f"{tissue_id:25s}: {percentage:5.1f}%")
```

### Use Case 4: Custom Parameter Tuning (Future)

```python
# NOTE: Full YAML loading not yet implemented (Task 5.1)
# For now, parameters are hardcoded in WorldGenerator

# Future syntax:
gen = WorldGenerator(
    seed="custom_world",
    config_path="data/my_custom_config.yaml"  # Custom parameters
)
result = gen.generate()
```

---

## Testing

Run all 77 unit tests:

```bash
# All tests
pytest tests/ -v

# Specific systems
pytest tests/test_skeletal.py -v
pytest tests/test_lymphatic.py -v
pytest tests/test_respiratory.py -v
pytest tests/test_metabolic.py -v
pytest tests/test_tissue_assignment.py -v
```

**Expected:** 77 tests, 100% pass rate, ~44 seconds

---

## Configuration

### Current Status

Parameters are currently hardcoded in `core/world_generator.py`. A comprehensive `generation_config.yaml` has been created for future integration (Task 5.1).

### Available Presets (Future)

Once YAML loading is implemented, you'll be able to use presets:

- **default** - Balanced world (current)
- **mountainous** - More mountains, higher ridges
- **plains** - Flat terrain, wide channels
- **oceanic** - More fluid, less land
- **volcanic** - High temperature, many caverns

See `data/generation_config.yaml` for full parameter documentation.

---

## Coordinate Systems

The generator uses **dual coordinate systems**:

### 1. Offset Coordinates (Array Access)

```python
elevation = result['skeletal']['elevation']
value = elevation[y, x]  # Row, column (0-255)
```

### 2. Axial Coordinates (Hex Math)

```python
sector = world_map.get_sector(x, y)  # Returns GlobalSector
q, r = sector.axial_q, sector.axial_r

# Distance between hexes
from models.global_sector import axial_distance
dist = axial_distance(q1, r1, q2, r2)

# Get 6 neighbors
neighbors = world_map.get_neighbors(x, y)
```

**Layout:** "odd-q" vertical (pointy-top hexes)

**Reference:** https://www.redblobgames.com/grids/hexagons/

---

## Troubleshooting

### Issue: Import errors

```bash
# Make sure you're in the project root
cd E:\neuro_rpg

# Run Python from root
python tools/visualize_complete_world.py my_seed
```

### Issue: NumPy warnings

```python
# Add to top of script
import warnings
warnings.filterwarnings('ignore', category=RuntimeWarning)
```

### Issue: Visualization too slow

```python
# Use standard resolution instead of 4K
# Edit visualize_complete_world.py line 245:
plt.savefig(output_file, dpi=150, bbox_inches='tight')  # Lower DPI
```

### Issue: JSON export too large

```bash
# Use sample instead of full
python tools/export_world_map.py my_seed sample  # 1000 sectors instead of 65,536
```

---

## Performance

### Generation Time

- **World generation:** ~5-10 seconds (256x256, all systems)
- **Visualization:** ~15-30 seconds (9-panel, 200 DPI)
- **JSON export (full):** ~10-15 seconds (~50 MB)

### Memory Usage

- **World generation:** ~200 MB (float32 arrays)
- **WorldMap storage:** ~100 MB (65,536 objects)
- **Visualization:** ~300 MB (matplotlib figure)

**Total:** ~600 MB for full pipeline

---

## Sprint 3.5 Status

**Progress: 80% COMPLETE**

- ✅ Phase 1: World Generation Systems (Tasks 1.1-1.5)
- ✅ Phase 2: Tissue Assignment (Tasks 2.1-2.2)
- ✅ Phase 3: Data Models & Export (Task 3.1)
- ✅ Phase 4: Comprehensive Visualization (Task 4.1)
- 🔄 Phase 5: Configuration & Testing (Tasks 5.1-5.3) - IN PROGRESS

**Core functionality complete!** Phase 5 is optional polish.

---

## License

Part of the Silgarron RPG project. See project root for license information.

---

## Questions?

See **[USAGE_GUIDE.md](docs/sprint_3.5_implementation/USAGE_GUIDE.md)** for comprehensive documentation, API reference, and troubleshooting.

**Generated:** Sprint 3.5 - October 2025
