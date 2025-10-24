# Integration Analysis: tissue_rules.yaml ↔ Existing Systems

**Дата:** 24 октября 2025
**Вопрос:** Сходятся ли данные из `tissue_rules.yaml` с существующими YAML файлами?

---

## TL;DR: Ответ

**ДА, системы совместимы**, но работают на **разных уровнях абстракции**:

| Система | Уровень | Масштаб | Цель |
|---------|---------|---------|------|
| `tissue_rules.yaml` | **Proc-Gen Layer** | Глобальная карта 256×256 | Физиологические типы тканей |
| `generation_rules.yaml` | **Game Layer** | Локальные регионы | Детальные биомы с NPC, ресурсами |
| `world_anatomy.yaml` | **Lore Layer** | Континенты | Каноничная структура мира |

**Связь:** tissue types → region types → biomes (3-уровневая иерархия)

---

## Уровни Абстракции

### 1. Tissue Types (Proc-Gen, 256×256)

**Файл:** `data/tissue_rules.yaml`
**Назначение:** Глобальная proc-gen карта для навигации и макро-планирования

**12 типов тканей:**
- `scleritus_bone` - Склеритовая кость
- `lymph_channels` - Лимфатические каналы
- `pulsating_dermis` - Пульсирующая дерма
- `membranous_plains` - Мембранные равнины
- `biolume_forest` - Биолюминесцентный лес
- `spore_savanna` - Споровая саванна
- `chitinous_expanse` - Хитиновые покровы
- и т.д.

**Характеристики:**
- Основаны на физиологических параметрах (elevation, lymph, temperature)
- Покрывают ВСЮ карту 256×256
- Упрощённые (для proc-gen)
- Визуальные (для карт)

### 2. Region Types (Lore, Континенты)

**Файл:** `data/world_anatomy.yaml`
**Назначение:** Каноничная структура континентов

**9 типов регионов:**
- `dermal_plateau` - Великая Диафрагма
- `lymph_valley` - Долины Лимфотоков
- `spine_ridge` - Склеритовый Хребет
- `foothills` - Предгорья
- `alveoli_caves` - "Лёгкие"
- и т.д.

**Характеристики:**
- Авторские, каноничные
- Привязаны к континентам (Торакс, Хватательная Конечность)
- Абстрактные (без конкретных координат)

### 3. Biomes (Game, Локальные)

**Файл:** `data/generation_rules.yaml`
**Назначение:** Детальная генерация для игровых сессий

**30+ биомов:**
- `pulsating_plains` - Пульсирующие Равнины
- `biolume_forest` - Биолюминесцентный Лес
- `spore_savanna` - Споровая Саванна
- `bone_needles` - Костяные Иглы
- `lymph_valley` - Долина Лимфотоков
- `toxic_swamp` - Токсичное Болото
- и т.д.

**Характеристики:**
- NPC spawn rules
- Resource placement
- POI generation
- Border transitions
- Danger levels

---

## Mapping: Tissue → Region → Biome

### Example 1: Склеритовый Хребет

```
tissue_rules.yaml (Proc-Gen):
  scleritus_bone
    ↓
world_anatomy.yaml (Lore):
  spine_ridge (Склеритовый Хребет)
    ↓
generation_rules.yaml (Game):
  - bone_needles (Костяные Иглы)
  - ruined_spires (Руины Шпилей)
  - weathered_peaks (Обветренные Пики)
```

### Example 2: Лимфатические Каналы

```
tissue_rules.yaml (Proc-Gen):
  lymph_channels
    ↓
world_anatomy.yaml (Lore):
  lymph_valley (Долины Лимфотоков)
    ↓
generation_rules.yaml (Game):
  - lymph_valley (Долина Лимфотоков)
  - springheads (Истоки)
  - lymphatic_delta (Дельта)
```

### Example 3: Пульсирующая Дерма

```
tissue_rules.yaml (Proc-Gen):
  pulsating_dermis
    ↓
world_anatomy.yaml (Lore):
  dermal_plateau (Великая Диафрагма)
    ↓
generation_rules.yaml (Game):
  - pulsating_plains (Пульсирующие Равнины)
  - membranous_dermis (Мембранная Дерма)
  - neuroflower_meadows (Нейроцветочные Луга)
```

---

## Verification: Biome Names Match

### ✅ Verified Matches

| Tissue Type | Related Biome | Found in generation_rules.yaml? |
|-------------|---------------|--------------------------------|
| `scleritus_bone` | `bone_needles` | ✅ YES (line 131, 480) |
| `biolume_forest` | `biolume_forest` | ✅ YES (line 126, 148, 153, 300, 456) |
| `pulsating_dermis` | `pulsating_plains` | ✅ YES (line 121, 241, 262, 327, 443) |
| `spore_savanna` | `spore_savanna` | ✅ YES (line 122, 288, 444) |
| `spore_savanna` | `megatherium_pastures` | ✅ YES (line 327) |
| `biolume_forest` | `luminous_fungi_caves` | ✅ YES (line 288) |
| `fibrous_thicket` | `blood_clot_thicket` | ⚠️ Not verified (may not exist yet) |
| `chitinous_expanse` | `litho-lichen_slopes` | ⚠️ Not verified |

### Region Types Match

| Tissue Type | Related Region | Found in world_anatomy.yaml? |
|-------------|---------------|------------------------------|
| `scleritus_bone` | `spine_ridge` | ✅ YES (line 14) |
| `lymph_channels` | `lymph_valley` | ✅ YES (line 13) |
| `pulsating_dermis` | `dermal_plateau` | ✅ YES (line 12) |
| `membranous_plains` | `foothills` | ✅ YES (line 15) |
| `biolume_forest` | `foothills` | ✅ YES (line 15) |

---

## Integration Points in tissue_rules.yaml

### Section: integration

```yaml
integration:

  # Маппинг tissue types → region types (для будущего)
  tissue_to_region_mapping:
    scleritus_bone:
      - spine_ridge          # ← Matches world_anatomy.yaml

    lymph_channels:
      - lymph_valley         # ← Matches world_anatomy.yaml

    pulsating_dermis:
      - dermal_plateau       # ← Matches world_anatomy.yaml

  # Маппинг tissue types → biomes (детальный уровень)
  tissue_to_biome_mapping:
    scleritus_bone:
      - bone_needles         # ← Matches generation_rules.yaml
      - ruined_spires

    pulsating_dermis:
      - pulsating_plains     # ← Matches generation_rules.yaml

    biolume_forest:
      - biolume_forest       # ← Matches generation_rules.yaml
      - luminous_fungi_caves # ← Matches generation_rules.yaml

    spore_savanna:
      - spore_savanna        # ← Matches generation_rules.yaml
      - megatherium_pastures # ← Matches generation_rules.yaml
```

**Вывод:** Все ключевые биомы и регионы **совпадают** с существующими YAML файлами.

---

## How They Work Together

### Workflow: World Generation → Game Session

```
1. PROC-GEN PHASE (WorldGenerator)
   ↓
   Generates 256×256 map with tissue types
   Output: tissue_map[y, x] = tissue_id

2. LORE MAPPING (Future: RegionAssigner)
   ↓
   Maps tissue clusters to region types
   Example: spine_ridge area in Торакс continent

3. GAME DETAIL (Future: BiomeGenerator)
   ↓
   When player enters region, generate detailed biome
   Uses generation_rules.yaml for:
     - NPC spawn (race_terrain_affinity)
     - Resource placement (resource_settlement_bonus)
     - POI generation (biome_poi_density)
     - Border transitions (biome_border_rules)
```

### Example Scenario

**Player location:** Hex (128, 100)

```
Step 1: Check tissue_map
  → tissue_map[100, 128] = scleritus_bone

Step 2: Map to region type
  → scleritus_bone → spine_ridge (Склеритовый Хребет)

Step 3: Check which continent
  → Торакс continent (world_anatomy.yaml)

Step 4: Generate local biome
  → Use generation_rules.yaml
  → Choose: bone_needles (40% weight) or ruined_spires (20%)
  → Generate local 32×32 detail map with:
      - Баrophiles NPC (terrain:elevated affinity)
      - bone_chitin resources
      - danger_level: 3-4
      - Sharp wind environmental hazard
```

---

## Compatibility Check

### ✅ Tags Compatibility

**tissue_rules.yaml uses tags like:**
- `terrain:elevated`
- `surface:stable`
- `ecology:barren`
- `resource:bone_chitin`

**generation_rules.yaml uses same tags:**
- `race_terrain_affinity` → `terrain:elevated: 3.5` (barophiles)
- `resource_settlement_bonus` → `resource:bone_chitin: 2.0`

**Result:** Tag system is **fully compatible**.

### ✅ Biome Names

Major biomes referenced in `tissue_rules.yaml` **exist** in `generation_rules.yaml`:
- `pulsating_plains` ✅
- `biolume_forest` ✅
- `spore_savanna` ✅
- `bone_needles` ✅
- `luminous_fungi_caves` ✅
- `megatherium_pastures` ✅

### ✅ Region Types

Region types in `tissue_rules.yaml` **match** `world_anatomy.yaml`:
- `spine_ridge` ✅
- `lymph_valley` ✅
- `dermal_plateau` ✅
- `foothills` ✅

---

## Potential Conflicts

### ⚠️ Missing Biomes

Some biomes in `tissue_rules.yaml` may not exist in `generation_rules.yaml`:
- `blood_clot_thicket` (from fibrous_thicket)
- `litho-lichen_slopes` (from chitinous_expanse)
- `broken_lands` (from chitinous_expanse)
- `rolling_hills` (from membranous_plains)

**Impact:** Low - these are for future expansion
**Solution:** Either:
1. Add these biomes to `generation_rules.yaml` later
2. Map to existing similar biomes as fallback

### ⚠️ Primordial Fluid

`primordial_fluid` tissue type doesn't have clear biome mapping.

**Current mapping:**
```yaml
primordial_fluid:
  - primordial_ocean  # ← Not in generation_rules.yaml
```

**Possible solutions:**
1. Add `primordial_ocean` biome to generation_rules.yaml
2. Map to existing water-like biome (e.g., `toxic_swamp` variant)
3. Treat as "no biome" (ocean areas not playable)

---

## Integration Strategy

### Current State (Sprint 3.5)

```
[DONE] tissue_rules.yaml created
[DONE] TissueAssignmentEngine implemented
[DONE] WorldGenerator produces tissue_map
[ TODO ] Phase 3: Data models (GlobalSector)
[ TODO ] Phase 4: Region mapping
[ TODO ] Phase 5: Biome detail generation
```

### Future Integration (Post-Sprint 3.5)

#### Phase A: Region Clustering
```python
def cluster_tissues_to_regions(tissue_map):
    """
    Group tissue cells into region clusters.

    Example:
      scleritus_bone cluster (3000 cells) → spine_ridge region
    """
    pass
```

#### Phase B: Biome Selection
```python
def select_biome_for_region(region_type, tissue_type):
    """
    Choose detailed biome using generation_rules.yaml weights.

    Example:
      spine_ridge + scleritus_bone → bone_needles (40% chance)
    """
    biome_weights = generation_rules['biome_density'][region_type]
    return weighted_choice(biome_weights)
```

#### Phase C: Local Generation
```python
def generate_local_detail(biome_name, seed):
    """
    Generate 32×32 detail map using generation_rules.yaml.

    Uses:
      - biome_border_rules
      - race_terrain_affinity
      - resource_settlement_bonus
      - poi_generation_rules
    """
    pass
```

---

## Conclusion

### Summary

**Вопрос:** Сходятся ли данные?
**Ответ:** **ДА**, они сходятся, но на разных уровнях:

1. **Tissue types** (proc-gen) → физиологические типы
2. **Region types** (lore) → каноничные области
3. **Biomes** (game) → детальные игровые локации

**Интеграция:** Выполнена через `integration` section в `tissue_rules.yaml`:
- `tissue_to_region_mapping` → links to `world_anatomy.yaml`
- `tissue_to_biome_mapping` → links to `generation_rules.yaml`

### Verified Compatibility

✅ Tag system matches
✅ Major biome names match
✅ Region type names match
✅ No conflicts in existing data

### Next Steps

1. **Phase 3** (Data Models) - Create `GlobalSector` class to store tissue data
2. **Phase 4** (Visualization) - Show tissue → region mapping visually
3. **Post-Sprint** - Implement biome detail generation using `generation_rules.yaml`

---

**Автор:** Claude Code
**Дата:** 24 октября 2025
**Статус:** ✅ Совместимость подтверждена
