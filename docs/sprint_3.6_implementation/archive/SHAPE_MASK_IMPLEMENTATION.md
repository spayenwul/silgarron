# Shape Mask Implementation - Sprint 3.6 Extension

## Summary

Implemented **Shape Mask** functionality for creating centered continents with guaranteed ocean at map edges, following the recipe provided for multiplicative noise composition.

---

## What Was Implemented

### 1. Core Implementation

**File:** `core/world_generator_v2.py` (+60 lines)

#### New Method: `_create_shape_mask()`

```python
def _create_shape_mask(self, width, height, mask_type="ellipse",
                      radius_x=0.35, radius_y=0.45) -> np.ndarray:
    """
    Creates elliptical or radial gradient mask
    Returns: 2D array [0, 1] where center=1.0, edges=0.0
    """
```

**Features:**
- Elliptical gradient (adjustable radius_x, radius_y)
- Radial gradient (circular)
- Smooth transition from center (1.0) to edges (0.0)
- Based on normalized distance formula

#### Updated Method: `_generate_continent()`

**Changes:**
1. Generates Perlin Noise (as before)
2. **NEW:** Creates shape mask if enabled
3. **NEW:** Multiplies `heightmap = heightmap * shape_mask`
4. **NEW:** Uses `sea_level_override` when shape mask enabled
5. Applies threshold and smoothing (as before)

**Algorithm:**
```
Perlin Noise → × Shape Mask → Threshold → Smoothing → Continent
```

---

### 2. Configuration

**File:** `config/world_generation_v2.yaml` (+6 lines)

```yaml
continent:
  sea_level: 0.36  # Used WITHOUT shape mask

  shape_mask:
    enabled: false  # Enable to center continents
    type: "ellipse"  # "ellipse" | "radial"
    radius_x: 0.35  # X radius (0-1, fraction of map width)
    radius_y: 0.45  # Y radius (0-1, fraction of map height)
    sea_level_override: 0.20  # Used WITH shape mask
```

**Why `enabled: false` by default?**
- Backward compatibility (all existing tests pass)
- Opt-in feature
- Doesn't change existing behavior

**Why `sea_level_override: 0.20` (lower than 0.36)?**
- Multiplication by shape mask reduces heightmap values
- Lower threshold compensates for this reduction
- Maintains ~50-70% land coverage

---

### 3. Visualization Tools

**File:** `scripts/visualize_shape_mask.py` (new, 298 lines)

#### Main Visualization (6 panels)

```bash
python scripts/visualize_shape_mask.py --seed my_continent
```

**Panels:**
1. Base Perlin Noise (without mask)
2. Shape Mask (gradient: center=1, edges=0)
3. Combined (Noise × Mask)
4. Continent WITHOUT shape mask
5. Continent WITH shape mask
6. Comparison overlay (Red=without, Green=with, Yellow=both)

**Output:** `output/shape_mask_effect_my_continent.png` (~3.2 MB)

#### Type Comparison

```bash
python scripts/visualize_shape_mask.py --compare-types
```

**Shows:**
- 3 ellipse variants (different radii)
- 3 radial variants (different radii)

**Output:** `output/shape_mask_types_comparison.png`

---

### 4. Documentation

**File:** `docs/sprint_3.6_implementation/SHAPE_MASK_GUIDE.md` (new, 450+ lines)

**Contents:**
- Mathematical formula (ellipse distance)
- Configuration guide
- Parameter tuning recipes
- Usage examples (Python API + YAML)
- FAQ and troubleshooting
- Recipes for different world types:
  - "Isolated Continent" (island in ocean)
  - "Large Continent" (default)
  - "Super-Continent" (fills map)
  - "Round World" (symmetric)

---

## Technical Details

### Algorithm

```python
# Step 1: Generate Perlin Noise
base_noise = generate_perlin_map(scale=150, octaves=2, ...)  # [0, 1]

# Step 2: Create Shape Mask
y, x = np.ogrid[:512, :512]
distance = sqrt(((x-cx)^2 / rx^2) + ((y-cy)^2 / ry^2))
shape_mask = clip(1.0 - distance, 0, 1)  # [0, 1]

# Step 3: Multiply
final_heightmap = base_noise * shape_mask  # [0, 1]

# Step 4: Threshold
sea_level = 0.20  # Lower than standard 0.36
continent_mask = (final_heightmap > sea_level)

# Step 5: Smoothing (as before)
continent_mask = binary_opening(continent_mask, ...)
```

### Key Formulas

**Ellipse Distance:**
```python
distance = sqrt(((x - center_x)^2 / radius_x^2) +
                ((y - center_y)^2 / radius_y^2))
```

**Radial Distance:**
```python
distance = sqrt((x - center_x)^2 + (y - center_y)^2) / radius
```

**Gradient:**
```python
shape_mask = 1.0 - distance  # Inverted: center=1, edges=0
shape_mask = clip(shape_mask, 0, 1)
```

---

## Test Results

### All Existing Tests Pass

```bash
python -m pytest tests/models/ tests/core/ -v
# Result: 37/37 passed ✅
```

**Why tests still pass:**
- Shape mask disabled by default (`enabled: false`)
- Backward compatible
- No changes to default behavior

### Manual Testing

```python
# Test 1: Shape mask creates centered continents
gen = WorldGeneratorV2()
gen.config['continent']['shape_mask']['enabled'] = True

continent = gen._generate_continent('test_centered')

# Result: 100% ocean at edges ✅
edge_ocean = check_edges(continent.mask)
# → 100.0%

# Test 2: Without shape mask (default behavior)
gen.config['continent']['shape_mask']['enabled'] = False

continent = gen._generate_continent('test_normal')

# Result: ~76.7% land (as before) ✅
land_pct = continent.mask.sum() / (512*512) * 100
# → 76.7%
```

---

## Usage Examples

### Enable Shape Mask via YAML

```yaml
# config/world_generation_v2.yaml
continent:
  shape_mask:
    enabled: true  # Change this line
```

### Enable Shape Mask via Python

```python
from core.world_generator_v2 import WorldGeneratorV2

gen = WorldGeneratorV2()
gen.config['continent']['shape_mask']['enabled'] = True

continent = gen._generate_continent('silgarron_world_01')
```

### Adjust Parameters

```python
# Larger continent
gen.config['continent']['shape_mask']['radius_x'] = 0.40
gen.config['continent']['shape_mask']['radius_y'] = 0.50

# More land
gen.config['continent']['shape_mask']['sea_level_override'] = 0.15

# Round shape instead of ellipse
gen.config['continent']['shape_mask']['type'] = 'radial'
```

---

## Visualizations Created

### 1. Shape Mask Effect Demonstration

**File:** `output/shape_mask_effect_centered_continent_demo.png` (3.2 MB)

**Shows:**
- Base Perlin Noise
- Elliptical gradient mask
- Combined result
- Continent without mask (random position)
- Continent with mask (centered, ocean at edges)
- Overlay comparison

### 2. Shape Mask Types Comparison

**File:** `output/shape_mask_types_comparison.png`

**Shows:**
- 3 ellipse configurations
- 3 radial configurations
- Different radius values
- Land percentage for each

---

## Benefits

1. **Guaranteed Ocean at Edges**
   - 100% ocean coverage on map boundaries
   - No continent cut-off by map edges

2. **Centered Continents**
   - Predictable continent position
   - Better for organ placement (Phase 3)
   - Easier to design balanced worlds

3. **Organic Shapes**
   - Still uses Perlin Noise for natural forms
   - Maintains coastline complexity
   - Unique for each seed

4. **Flexible**
   - Adjustable radius (compact to large)
   - Two types (ellipse, radial)
   - Easy to enable/disable

5. **Backward Compatible**
   - Disabled by default
   - All existing tests pass
   - Opt-in feature

---

## Files Changed

### Modified

| File | Lines Added | Lines Changed | Purpose |
|------|-------------|---------------|---------|
| `core/world_generator_v2.py` | +60 | ~30 | Implement shape mask |
| `config/world_generation_v2.yaml` | +6 | - | Add configuration |

### Created

| File | Lines | Purpose |
|------|-------|---------|
| `scripts/visualize_shape_mask.py` | 298 | Visualization tool |
| `docs/sprint_3.6_implementation/SHAPE_MASK_GUIDE.md` | 450+ | User guide |
| `docs/sprint_3.6_implementation/SHAPE_MASK_IMPLEMENTATION.md` | ~250 | This file |

### Outputs Generated

| File | Size | Description |
|------|------|-------------|
| `output/shape_mask_effect_centered_continent_demo.png` | 3.2 MB | Effect demonstration |
| `output/shape_mask_types_comparison.png` | - | Types comparison |

---

## Next Steps

**Current Status:** Shape Mask Implementation Complete ✅

**Ready for:**
- Phase 3: Organ Placement (organs can now be placed on centered continents)
- User testing with different configurations
- Integration with world generation pipeline

**Future Enhancements (Optional):**
- Custom center position (not always map center)
- Multiple masks (archipelago generation)
- Gradient strength parameter (sharper/softer transitions)
- Rotation parameter (angled ellipses)

---

## Implementation Timeline

**Date:** 2025-10-25

**Tasks Completed:**
1. ✅ Add shape mask configuration to YAML
2. ✅ Implement `_create_shape_mask()` method
3. ✅ Modify `_generate_continent()` for mask multiplication
4. ✅ Test with shape mask enabled/disabled
5. ✅ Verify all 37 existing tests pass
6. ✅ Create visualization showing effect
7. ✅ Write comprehensive documentation

**Total Time:** ~1 hour

**Test Status:** 37/37 passing ✅

---

## References

**Recipe Source:** User-provided algorithm for centered continents

**Key Concept:** Multiplicative composition
```
final_result = base_noise × shape_mask
```

**ADR Compliance:**
- ADR-016: Compositional generation (noise + mask)
- ADR-019: Global Skeletons 512×512
- ADR-020: WorldGeneratorV2 architecture

---

**Status:** Complete ✅
**Tests:** 37/37 passing
**Documentation:** Complete
**Visualizations:** Generated
