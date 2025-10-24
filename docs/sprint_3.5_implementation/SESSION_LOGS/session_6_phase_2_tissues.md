# Session 6: Phase 2 - Tissue Assignment System

**Дата:** 24 октября 2025
**Задачи:** Task 2.1, Task 2.2 (Tissue Type Assignment)
**Статус:** ✅ ЗАВЕРШЕНО

---

## Цель Phase 2

Создать систему назначения типов тканей (биомов) на основе физиологических параметров, полученных в Phase 1.

**Входные данные:**
- Elevation (скелет)
- Ridge mask (кость)
- Lymph intensity (циркуляция)
- Bioactive saturation (дыхание)
- Temperature (метаболизм)

**Выходные данные:**
- Tissue map (карта типов тканей 256×256)
- Tissue info (метаданные по каждому типу)

---

## Task 2.1: Create `tissue_rules.yaml`

### Цель

Создать YAML-файл с правилами назначения тканей, который:
- Определяет 12 базовых типов тканей
- Использует систему приоритетов (100 = highest)
- Задаёт criteria для каждой ткани
- Интегрируется с существующими системами

### Реализация

**Файл:** `data/tissue_rules.yaml` (600+ строк)

#### Структура файла

```yaml
tissues:
  primordial_fluid:        # Приоритет 100
    name: "Первичная жидкость"
    priority: 100
    criteria:
      elevation: [0.0, 0.15]
      temperature: [0.3, 0.8]
    color: "#1A0F2E"
    tags:
      - surface:fluid
      - terrain:aquatic
    related_biomes:
      - primordial_ocean
```

#### 12 типов тканей

| Tissue ID | Priority | Description | Coverage (typical) |
|-----------|----------|-------------|-------------------|
| `primordial_fluid` | 100 | Протоплазменная жидкость (океан) | ~3% |
| `scleritus_bone` | 95 | Склеритовая кость (хребет) | ~3% |
| `lymph_channels` | 90 | Лимфатические каналы | ~5% |
| `chitinous_expanse` | 85 | Хитиновые покровы | ~15% |
| `biolume_forest` | 82 | Биолюминесцентный лес | ~4% |
| `pulsating_dermis` | 80 | Пульсирующая дерма (breathing) | ~15% |
| `fibrous_thicket` | 75 | Волокнистые заросли (мышцы) | ~3% |
| `membranous_plains` | 70 | Мембранные равнины | ~10% |
| `spore_savanna` | 65 | Споровая саванна | ~2% |
| `lowland_tissue` | 60 | Низменные ткани | ~20% |
| `inert_zone` | 50 | Инертная зона (холодная) | ~2% |
| `moderate_tissue` | 10 | Fallback (по умолчанию) | ~40% |

#### Special Rules

```yaml
special_rules:
  alveolar_cavern_override:
    condition: is_cavern
    tissue_type: alveolar_cavern
    priority: 98
    tags: [breathing:source]

  lymph_source_override:
    condition: is_lymph_source
    tissue_type: lymph_springhead
    priority: 92
    tags: [location:sacred]
```

#### Color Palette

Анатомическая цветовая схема:
- **Bone tones:** `#E8E8E8` (светлая кость), `#D3D3D3` (серая)
- **Tissue tones:** `#E8B4B8` (розовая дерма), `#D4A59A` (бледная кожа)
- **Muscle tones:** `#8B1A1A` (тёмно-красная мышца)
- **Lymph tones:** `#FFD700` (золотая лимфа), `#00CED1` (голубой исток)
- **Vegetation:** `#3CB371` (зелёный биолюм), `#DAA520` (жёлтая саванна)
- **Chitin:** `#2F4F4F` (тёмно-серый хитин)
- **Fluid:** `#1A0F2E` (фиолетовая жидкость)

### Интеграция с существующими системами

YAML совместим с:
- `data/world_anatomy.yaml` - континенты и регионы
- `data/generation_rules.yaml` - правила генерации биомов
- `data_tables/anatomy.yaml` - детальные биомы

**Mapping:** Tissue types → Region types → Biomes

```yaml
integration:
  tissue_to_region_mapping:
    scleritus_bone:
      - spine_ridge
    lymph_channels:
      - lymph_valley
    pulsating_dermis:
      - dermal_plateau
```

---

## Task 2.2: Implement Rule-Based Assignment

### Цель

Создать движок для загрузки YAML и применения правил назначения тканей.

### Реализация

**Файл:** `core/tissue_assignment.py` (352 строки)

#### Class: `TissueAssignmentEngine`

```python
class TissueAssignmentEngine:
    """
    Engine for assigning tissue types based on rules.

    Loads tissue_rules.yaml and applies priority-based matching.
    """

    def __init__(self, rules_path: str = "data/tissue_rules.yaml"):
        self.rules_path = rules_path
        self.rules = self._load_rules()
        self.tissues = self._parse_tissues()
```

#### Алгоритм назначения

**Priority-based matching:**

1. **Special rules first** (highest priority)
   - Check `is_cavern` → Alveolar Cavern
   - Check `is_lymph_source` → Lymph Springhead
   - Check `is_lymph_channel` → Lymph Channels

2. **Iterate tissues by priority** (high → low)
   - For each tissue, check criteria
   - ALL criteria must match (AND logic)
   - First match → assign tissue

3. **Fallback**
   - If no match → `moderate_tissue` (priority 10)

**Псевдокод:**

```python
def assign_tissue_type(elevation, temperature, ...):
    if is_cavern:
        return alveolar_cavern

    if is_lymph_source:
        return lymph_springhead

    for tissue in sorted_tissues:  # By priority
        if matches_criteria(tissue.criteria, params):
            return tissue

    return moderate_tissue  # Fallback
```

#### Criteria Matching

```python
def _matches_criteria(self, criteria, **params):
    """
    Check if parameters match tissue criteria.

    Args:
        criteria: Dict of criteria (e.g., elevation: [0.5, 0.7])
        **params: Parameter values to check

    Returns:
        True if ALL criteria match (AND logic)
    """
    if not criteria:
        return True  # Empty criteria = fallback

    for param_name, param_range in criteria.items():
        param_value = params.get(param_name)

        if param_value is None:
            return False  # Missing parameter

        # Check range [min, max]
        if isinstance(param_range, list):
            min_val, max_val = param_range
            if not (min_val <= param_value <= max_val):
                return False

    return True  # All matched
```

#### Map Assignment

```python
def assign_tissue_map(
    self, elevation, ridge_mask, lymph_intensity,
    lymph_channels, bioactive_saturation, temperature,
    cavern_positions=None, lymph_sources=None
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Assign tissue types for entire map.

    Returns:
        - tissue_map: np.ndarray (height, width) of tissue IDs (integers)
        - tissue_info: Dict mapping tissue_id_int → tissue info
    """
    # Create masks for special positions
    cavern_mask = create_mask(cavern_positions)
    source_mask = create_mask(lymph_sources)

    # Assign tissues for each hex
    for y in range(height):
        for x in range(width):
            tissue_result = self.assign_tissue_type(
                elevation[y, x],
                ridge_mask[y, x],
                ...
                is_cavern=cavern_mask[y, x],
                is_lymph_source=source_mask[y, x]
            )

            tissue_map[y, x] = tissue_id_to_int[tissue_result['id']]

    return tissue_map, tissue_info
```

---

## Integration with WorldGenerator

**Файл:** `core/world_generator.py`

### Changes Made

1. **Added import:**
```python
from core.tissue_assignment import TissueAssignmentEngine
```

2. **Implemented `_assign_tissue_types()` method:**
```python
def _assign_tissue_types(
    self, skeletal_data, lymphatic_data,
    respiratory_data, metabolic_data
) -> Dict[str, Any]:
    """Назначает типы тканей для каждого гекса."""

    engine = TissueAssignmentEngine(rules_path="data/tissue_rules.yaml")

    tissue_map, tissue_info = engine.assign_tissue_map(
        elevation=skeletal_data['elevation'],
        ridge_mask=skeletal_data['ridge_mask'],
        lymph_intensity=lymphatic_data['lymph_intensity'],
        lymph_channels=lymphatic_data['lymph_channels'],
        bioactive_saturation=respiratory_data['bioactive_saturation'],
        temperature=metabolic_data['temperature'],
        cavern_positions=respiratory_data['caverns'],
        lymph_sources=lymphatic_data['source_points']
    )

    return {
        'tissue_map': tissue_map,
        'tissue_info': tissue_info
    }
```

3. **Updated `generate()` method:**
```python
def generate(self):
    skeletal_data = self._generate_skeletal_structure()
    lymphatic_data = self._generate_lymphatic_system(skeletal_data)
    respiratory_data = self._generate_respiratory_system(skeletal_data)
    metabolic_data = self._generate_metabolic_activity(...)

    tissue_data = self._assign_tissue_types(
        skeletal_data, lymphatic_data,
        respiratory_data, metabolic_data
    )

    return {
        'seed': self.seed_string,
        'skeletal': skeletal_data,
        'lymphatic': lymphatic_data,
        'respiratory': respiratory_data,
        'metabolic': metabolic_data,
        'tissues': tissue_data,  # NEW!
        'generator_version': '0.1.0-sprint3.5'
    }
```

---

## Visualization

**Файл:** `tools/visualize_tissues.py` (159 строк)

### 4-Panel Visualization

#### Panel 1: Complete Tissue Map
- Color-coded tissue types
- Legend with all 11 tissue types
- 256×256 resolution

#### Panel 2: Tissue Distribution (Pie Chart)
- Percentage breakdown by tissue type
- Color-matched with tissue colors

#### Panel 3: Special Tissues Only
- Highlights:
  - **Red**: Alveolar Caverns (52 cells)
  - **Cyan**: Lymph Springheads (6 cells)
  - **Gold**: Lymph Channels (3353 cells)

#### Panel 4: Tissue Statistics
- Total cells: 65,536
- Unique tissues: 11
- Coverage table (sorted by count)

### Usage

```bash
python tools/visualize_tissues.py silgarron_tissues
```

**Output:** `output/tissue_map_silgarron_tissues.png`

---

## Results (Seed: "silgarron_tissues")

### Tissue Coverage

| Tissue Name | Cells | Coverage |
|-------------|-------|----------|
| Умеренная ткань (Moderate) | 26,595 | **40.6%** |
| Низменные ткани (Lowland) | 12,727 | **19.4%** |
| Хитиновая поверхность | 9,970 | **15.2%** |
| Мембранные равнины | 6,811 | **10.4%** |
| Лимфатические каналы | 3,352 | **5.1%** |
| Пульсирующая дерма | 2,207 | **3.4%** |
| Споровая саванна | 2,285 | **3.5%** |
| Инертная зона | 1,274 | **1.9%** |
| Склеритовая кость | 257 | **0.4%** |
| Alveolar Cavern | 52 | **0.1%** |
| Lymph Springhead | 6 | **0.0%** |

### Statistics

- **Total cells:** 65,536
- **Unique tissues:** 11
- **Special tissues:** 58 (52 caverns + 6 sources)
- **Lymph channels:** 3,352 cells (5.1%)

### Biological Interpretation

1. **Умеренная ткань (40.6%)** - fallback для областей без специфических характеристик
2. **Низменные ткани (19.4%)** - мягкие, тёплые ткани в низинах
3. **Хитиновая поверхность (15.2%)** - холодные, твёрдые покровы на возвышенностях
4. **Мембранные равнины (10.4%)** - эластичная кожа, участвующая в Дыхании
5. **Лимфатические каналы (5.1%)** - золотые артерии циркуляции

---

## Testing

**Файл:** `tests/test_tissue_assignment.py` (269 строк)

### Test Coverage

**22 теста, 100% pass rate**

#### Test Classes

1. **TestYAMLLoading** (3 теста)
   - `test_load_tissue_rules` - загрузка YAML
   - `test_parse_tissues` - парсинг и сортировка
   - `test_tissue_structure` - структура тканей

2. **TestCriteriaMatching** (4 теста)
   - `test_exact_match` - проверка диапазонов
   - `test_multiple_criteria` - AND логика
   - `test_missing_parameter` - отсутствующие параметры
   - `test_empty_criteria` - fallback без критериев

3. **TestTissueAssignment** (7 тестов)
   - `test_high_elevation_cold_ridge` - кость
   - `test_low_elevation_warm` - низменная ткань
   - `test_high_bioactive_warm` - пульсирующая дерма
   - `test_lymph_channel_flag` - лимфа
   - `test_cavern_override` - каверны
   - `test_lymph_source_override` - истоки
   - `test_fallback_tissue` - fallback

4. **TestMapAssignment** (4 теста)
   - `test_assign_tissue_map_shape` - форма и тип
   - `test_tissue_info_structure` - структура info
   - `test_cavern_positions_assigned` - назначение каверн
   - `test_lymph_sources_assigned` - назначение истоков

5. **TestIntegration** (4 теста)
   - `test_world_generator_integration` - интеграция с генератором
   - `test_tissue_diversity` - разнообразие тканей
   - `test_tissue_coverage` - полное покрытие
   - `test_deterministic_tissue_assignment` - детерминизм

### Test Results

```
============================= 22 passed in 30.22s =============================
```

**Key validations:**
- ✅ Priority-based matching works correctly
- ✅ Special rules (caverns, sources) override correctly
- ✅ All cells assigned (no gaps)
- ✅ Deterministic generation (same seed → same tissues)
- ✅ Integration with WorldGenerator successful

---

## Technical Details

### Performance

- **Map assignment:** O(n × m), где n = cells, m = tissue types
- **256×256 map:** ~65,000 iterations
- **Time:** ~5 seconds (включая все системы)

### Memory

- **Tissue map:** 256×256 × 4 bytes (int32) = 256 KB
- **Tissue info:** ~11 entries × ~200 bytes = ~2 KB
- **Total:** <1 MB для tissue system

### Data Flow

```
WorldGenerator.generate()
  ↓
skeletal_data (elevation, ridge_mask)
  ↓
lymphatic_data (lymph_intensity, channels, sources)
  ↓
respiratory_data (caverns, bioactive_saturation)
  ↓
metabolic_data (temperature)
  ↓
TissueAssignmentEngine.assign_tissue_map()
  ↓
tissue_map (256×256 int32)
tissue_info (dict)
```

---

## Files Created/Modified

### Created Files

1. `data/tissue_rules.yaml` (600+ строк)
   - 12 tissue type definitions
   - Special rules
   - Color palette
   - Integration mappings

2. `core/tissue_assignment.py` (352 строки)
   - `TissueAssignmentEngine` class
   - Priority-based matching
   - Map assignment

3. `tools/visualize_tissues.py` (159 строк)
   - 4-panel visualization
   - Statistics display

4. `tests/test_tissue_assignment.py` (269 строк)
   - 22 comprehensive tests
   - 100% pass rate

### Modified Files

1. `core/world_generator.py`
   - Added `TissueAssignmentEngine` import
   - Implemented `_assign_tissue_types()` method
   - Updated `generate()` return structure

---

## Lessons Learned

### 1. Priority System Works Well

Система приоритетов позволяет:
- Ясный порядок проверки
- Простое добавление новых тканей
- Предсказуемое поведение

### 2. YAML Configuration is Flexible

Вынос правил в YAML даёт:
- Лёгкая настройка без изменения кода
- Возможность A/B тестирования правил
- Простое добавление новых регионов

### 3. Special Rules Need Highest Priority

Каверны и истоки должны переопределять все остальные правила, поэтому проверяются первыми.

### 4. Fallback is Essential

`moderate_tissue` с пустыми criteria гарантирует, что каждый гекс получит ткань.

---

## Next Steps (Phase 3)

Phase 2 завершена. Следующие задачи:

1. **Phase 3:** Data Models
   - Create `GlobalSector` class
   - Implement hex coordinate conversion
   - Create sector storage system

2. **Phase 4:** Visualization
   - Create comprehensive world map
   - Multi-layer visualization
   - Export to image/JSON

3. **Phase 5:** Configuration & Testing
   - Create `generation_config.yaml`
   - Integration tests
   - Performance benchmarks

---

## Summary

✅ **Task 2.1:** Created `tissue_rules.yaml` with 12 tissue types
✅ **Task 2.2:** Implemented `TissueAssignmentEngine` with priority-based matching
✅ **Integration:** Connected to `WorldGenerator`
✅ **Visualization:** Created 4-panel tissue map
✅ **Testing:** 22/22 tests passed (100%)

**Phase 2 COMPLETE!** 🎉

---

**Generated:** 24 октября 2025
**Version:** Sprint 3.5, Phase 2
**Status:** ✅ ЗАВЕРШЕНО
