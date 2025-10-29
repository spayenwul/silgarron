# WP1: Foundation - Usage Guide

Quick guide for using the World Generator v3.0 (WP1 - Foundation)

---

## Quick Start

### 1. Generate Visualizations

#### Single World Generation

```bash
python scripts/visualize_wp1_foundation.py --seed your_seed_name
```

**Output:** 4 PNG images in `output/<seed>/` directory:
- `wp1_foundation_bw.png` - Black/white continent mask
- `wp1_spine_overlay.png` - Spine path + geometry
- `wp1_organs_placement.png` - Organs on terrain
- `wp1_full_composite.png` - Complete 2×2 grid (main artifact)

**Options:**
```bash
--seed SEED              World seed (default: silgarron_world_001)
--config PATH            Config file (default: config/world_generation_v3.yaml)
--output-dir DIR         Output directory (default: output)
```

**Examples:**
```bash
# Generate with custom seed
python scripts/visualize_wp1_foundation.py --seed my_world_123

# Custom output directory
python scripts/visualize_wp1_foundation.py --seed test --output-dir results/
```

---

#### Batch Generation (NEW!)

Generate multiple worlds with different seeds in one command:

```bash
# Generate 10 worlds with numbered seeds
python scripts/visualize_wp1_foundation.py --batch 10

# Generate 5 worlds with random UUID seeds
python scripts/visualize_wp1_foundation.py --batch 5 --random-seeds

# Custom seed prefix
python scripts/visualize_wp1_foundation.py --batch 20 --seed-prefix "world"

# Custom output directory
python scripts/visualize_wp1_foundation.py --batch 10 --output-dir gallery/
```

**Batch Options:**
```bash
--batch N                Number of worlds to generate
--seed-prefix PREFIX     Prefix for numbered seeds (default: batch)
--random-seeds           Use random UUID seeds instead of numbered
--output-dir DIR         Base output directory
```

**Output Structure:**
```
output/
├── batch_001/
│   ├── wp1_foundation_bw.png
│   ├── wp1_spine_overlay.png
│   ├── wp1_organs_placement.png
│   └── wp1_full_composite.png
├── batch_002/
│   └── ...
└── batch_003/
    └── ...
```

**Batch Statistics:**
After completion, you'll get statistics for all generated worlds:
```
Statistics:
  Average land: 59.7%
  Min land: 55.9%
  Max land: 65.1%
  Avg time per world: 2.55s
```

---

### 2. Validate Schema

```bash
python scripts/validate_wp1_schema.py --seed your_seed_name
```

**Output:** Console validation report

**Options:**
```bash
--seed SEED              World seed (default: validation_test)
--config PATH            Config file
--verbose                Detailed output
```

**Example:**
```bash
python scripts/validate_wp1_schema.py --seed my_world_123 --verbose
```

---

### 3. Run Tests

```bash
# Run all WP1 tests
pytest tests/core/test_wp1_foundation.py -v

# Run specific test
pytest tests/core/test_wp1_foundation.py::test_continent_connectivity -v

# With coverage
pytest tests/core/test_wp1_foundation.py --cov=core.world_generator_v3
```

---

## Programmatic Usage

### Basic Generation

```python
from core.world_generator_v3 import WorldGeneratorV3
import yaml

# Load config
with open('config/world_generation_v3.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Create generator
generator = WorldGeneratorV3(config)

# Generate world
world = generator.generate_wp1("my_seed")

# Access data
print(f"Continent area: {world.continent.mask.sum()} pixels")
print(f"Center: {world.continent.center}")
print(f"Organs: {len(world.organs)}")
```

### Access World Data

```python
# Continent data
mask = world.continent.mask           # (512, 512) bool
heightmap = world.continent.heightmap # (512, 512) float32
center = world.continent.center       # (cx, cy)
major_axis = world.continent.major_axis  # ((x1, y1), (x2, y2))
spine_path = world.continent.spine_path  # (N, 2) array

# Organs
for organ_id, organ in world.organs.items():
    print(f"{organ_id}: {organ.type} at {organ.position}")

# World metadata
print(f"Seed: {world.seed}")
print(f"Phase: {world.world_phase}")
print(f"Age: {world.age}")
```

---

## Configuration

Edit `config/world_generation_v3.yaml` to customize:

### Spine Generation
```yaml
spine_generation:
  path:
    num_points: 100      # Number of spine points
    curvature: 0.3       # Curvature [0-1]
  smoothing:
    factor: 100.0        # Smoothing strength
  influence:
    max_distance: 200.0  # Influence radius (px)
```

### Continent Generation
```yaml
continent_generation:
  perlin_noise:
    scale: 150.0         # Noise frequency
    octaves: 2
    persistence: 0.6
  sea_level: 0.35        # Land/ocean threshold
  sea_level_spine_mode: 0.20  # When spine enabled
```

### Organs
```yaml
organs:
  metabolic_organ:
    radius: 30           # Organ size
    temperature: 0.95
  digestive:
    radius: 25
  # ... etc
```

---

## Understanding the Output

### Continent Statistics

**Land Percentage:**
- **55-65%:** Typical (good balance)
- **65-75%:** Large continent (less ocean)
- **< 55%:** Small continent (adjust sea_level)
- **> 80%:** Very large (may need adjustment)

**Center of Mass:**
- Should be near (256, 256) for centered continents
- May vary with spine curvature

### Organ Placement

1. **Metabolic Core** (red, radius 30)
   - Always at center of mass
   - Hottest organ (temp=0.95)

2. **Stomach** (orange, radius 25)
   - Southern lowland
   - Y > center Y
   - Elevation < 0.5

3. **Ganglions** (blue, radius 15)
   - ganglion_0: 35% along major axis
   - ganglion_1: 65% along major axis

4. **Lymph Node** (green, radius 10)
   - Near ganglion_0
   - On elevated ground (elevation > 0.5)

---

## Troubleshooting

### "Module not found: core"
**Fixed!** Scripts now include path resolution.

### Continent too small/large
Adjust `sea_level` in config:
- Increase → less land
- Decrease → more land

### Multiple islands instead of one continent
**Fixed!** Generator now keeps only largest component.

### Organs placement fails
Check continent size - needs minimum 55% land for reliable placement.

### Unicode errors (emojis in console)
**Fixed!** All emojis replaced with ASCII.

---

## Performance Tips

- **Fast generation:** ~0.5 sec per world
- **Parallel generation:** Create multiple generators for different threads
- **Caching:** Save generated worlds with `pickle` for reuse

```python
import pickle

# Save
with open('my_world.pkl', 'wb') as f:
    pickle.dump(world, f)

# Load
with open('my_world.pkl', 'rb') as f:
    world = pickle.load(f)
```

---

## Examples

### Generate Gallery of 50 Worlds

```bash
# Generate 50 worlds for a gallery (takes ~2 minutes)
python scripts/visualize_wp1_foundation.py --batch 50 --seed-prefix gallery --output-dir gallery/

# Or with random seeds for more variety
python scripts/visualize_wp1_foundation.py --batch 50 --random-seeds --output-dir gallery/
```

### Generate Test Datasets

```bash
# Generate 100 worlds for testing/analysis
python scripts/visualize_wp1_foundation.py --batch 100 --seed-prefix dataset --output-dir datasets/wp1_v3_test/

# After generation, you can analyze the results
ls -d datasets/wp1_v3_test/*/ | wc -l  # Count generated worlds
```

### Programmatic Batch Generation

```python
from core.world_generator_v3 import WorldGeneratorV3
import yaml
from pathlib import Path

# Load config
with open('config/world_generation_v3.yaml', 'r') as f:
    config = yaml.safe_load(f)

generator = WorldGeneratorV3(config)

# Generate multiple worlds and collect stats
stats_list = []
for i in range(10):
    seed = f"test_{i:03d}"
    world = generator.generate_wp1(seed)

    stats = {
        'seed': seed,
        'land_pct': world.continent.mask.mean() * 100,
        'organs': len(world.organs),
        'center': world.continent.center
    }
    stats_list.append(stats)
    print(f"{seed}: {stats['land_pct']:.1f}% land")

# Analyze results
avg_land = sum(s['land_pct'] for s in stats_list) / len(stats_list)
print(f"\nAverage land percentage: {avg_land:.1f}%")
```

### Compare Different Seeds

```bash
# Generate worlds with similar prefixes to compare
python scripts/visualize_wp1_foundation.py --batch 5 --seed-prefix silgarron_alpha
python scripts/visualize_wp1_foundation.py --batch 5 --seed-prefix silgarron_beta

# Results will be in:
# output/silgarron_alpha_001/, output/silgarron_alpha_002/, ...
# output/silgarron_beta_001/, output/silgarron_beta_002/, ...
```

---

## Next: WP2 (Anatomy & Relief)

After WP1, you can proceed to WP2 which adds:
- **Skeleton:** Vertebrae, ribs (L-Systems), phalanges
- **Vessels:** Blood/lymph networks with bone avoidance

**Status:** WP2 implementation ready to begin

---

## Support

- **Tests:** `pytest tests/core/test_wp1_foundation.py -v`
- **Documentation:** See `docs/sprint_3.6_implementation/`
- **Issues:** Check WP1_COMPLETION_REPORT.md for known issues

**WP1 is production-ready!** 🎉
