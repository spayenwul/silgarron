# Batch Generation Feature - WP1 Visualization

**Added:** 29 октября 2025
**Version:** WP1 v1.1

---

## Overview

Added batch generation capability to WP1 visualization script, allowing generation of multiple worlds with different seeds in a single command.

## Features

### 1. Numbered Seed Generation

Generate multiple worlds with sequential numbered seeds:

```bash
python scripts/visualize_wp1_foundation.py --batch 10
```

**Output:** `batch_001`, `batch_002`, ..., `batch_010`

### 2. Random UUID Seeds

Generate worlds with random unique identifiers:

```bash
python scripts/visualize_wp1_foundation.py --batch 5 --random-seeds
```

**Output:** `d2b28ce2`, `e2f0fa59`, ... (8-character UUIDs)

### 3. Custom Seed Prefix

Customize the prefix for numbered seeds:

```bash
python scripts/visualize_wp1_foundation.py --batch 20 --seed-prefix "world"
```

**Output:** `world_001`, `world_002`, ..., `world_020`

### 4. Statistics Summary

After batch completion, displays aggregate statistics:
- Average land percentage
- Min/max land percentage
- Average generation time per world
- Success rate (generated/requested)

## Implementation Details

### Functions Added

#### `generate_single_world(seed, config, output_dir, verbose)`
- Generates and visualizes one world
- Returns statistics dict
- Creates seed-specific subdirectory
- Optionally verbose output

#### `batch_generate(count, config, output_dir, seed_prefix, random_seeds)`
- Orchestrates batch generation
- Handles errors gracefully
- Displays progress
- Returns list of statistics

### Directory Structure

```
output/
├── batch_001/
│   ├── wp1_foundation_bw.png
│   ├── wp1_spine_overlay.png
│   ├── wp1_organs_placement.png
│   └── wp1_full_composite.png
├── batch_002/
│   └── ... (same files)
└── batch_003/
    └── ... (same files)
```

Each seed gets its own subdirectory to prevent file collisions.

## Performance

Based on testing with 3 worlds:

- **Average time per world:** 2.55 seconds
- **Total time (3 worlds):** 7.6 seconds
- **Overhead:** ~0.1 seconds per world (progress printing)

**Scaling estimates:**
- 10 worlds: ~26 seconds
- 50 worlds: ~130 seconds (~2 minutes)
- 100 worlds: ~260 seconds (~4.5 minutes)

## Use Cases

### 1. Gallery Generation
Create a visual gallery of diverse worlds:
```bash
python scripts/visualize_wp1_foundation.py --batch 50 --random-seeds --output-dir gallery/
```

### 2. Testing & Validation
Generate test dataset for algorithm validation:
```bash
python scripts/visualize_wp1_foundation.py --batch 100 --seed-prefix test --output-dir datasets/
```

### 3. Parameter Exploration
Generate multiple worlds to understand parameter effects on generation.

### 4. Comparison Studies
Compare different configurations or algorithm versions:
```bash
python scripts/visualize_wp1_foundation.py --batch 10 --seed-prefix v3_baseline
# (modify config)
python scripts/visualize_wp1_foundation.py --batch 10 --seed-prefix v3_tuned
```

## Example Output

```
============================================================
BATCH GENERATION: 3 worlds
============================================================

[1/3] Seed: test_001
------------------------------------------------------------
  Land: 60.9%, Center: (257, 251), Organs: 5
  Output: output\test_001

[2/3] Seed: test_002
------------------------------------------------------------
  Land: 58.4%, Center: (254, 256), Organs: 5
  Output: output\test_002

[3/3] Seed: test_003
------------------------------------------------------------
  Land: 59.7%, Center: (256, 249), Organs: 5
  Output: output\test_003


============================================================
BATCH COMPLETE: 3/3 worlds generated in 7.6s
============================================================

Statistics:
  Average land: 59.7%
  Min land: 58.4%
  Max land: 60.9%
  Avg time per world: 2.55s
```

## Error Handling

- **Invalid batch count:** Error message if `--batch < 1`
- **Generation failures:** Caught and logged, batch continues
- **Directory creation:** Automatic with `parents=True`
- **Config errors:** Propagated with clear error messages

## Backward Compatibility

✅ **Fully backward compatible**

Single world generation unchanged:
```bash
python scripts/visualize_wp1_foundation.py --seed my_seed
```

Old behavior maintained when `--batch` is not specified.

## Testing

Tested scenarios:
- ✅ Small batch (3 worlds)
- ✅ Random seeds (2 worlds)
- ✅ Custom prefix
- ✅ Custom output directory
- ✅ Help display
- ✅ Single world mode (backward compatibility)

## Future Enhancements

Potential improvements:
- [ ] Progress bar (using `tqdm`)
- [ ] Parallel generation (multiprocessing)
- [ ] Export statistics to CSV/JSON
- [ ] Resume interrupted batch
- [ ] Filter by land percentage range
- [ ] Generate comparison grid image

## Documentation

Updated:
- ✅ `WP1_USAGE_GUIDE.md` - Added batch generation section
- ✅ `--help` output - Includes examples
- ✅ `BATCH_GENERATION_FEATURE.md` - This document

## Credits

**Implemented by:** Claude Code (Anthropic)
**Date:** 29 октября 2025
**Sprint:** 3.6 (WP1 - Foundation)

---

**Status:** ✅ Production Ready
