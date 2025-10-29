# Phase 7: Tissues (Biome Assignment)

**Статус:** 🚧 Запланировано (Sprint 3.9)

## Задачи реализации

1. Сбор полного контекста для каждой клетки (11 параметров)
2. Обработка специальных случаев (каверны, каналы, зоны заражения)
3. Контекстное назначение от органов (кислотные озёра у желудка)
4. Региональные особенности (пульсирующие равнины в диафрагме)
5. Применение стандартных правил из tissue_rules.yaml
6. Опциональная текстуризация через Worley Noise для hex properties

## Инструменты

- **NumPy**: массивы, векторные операции
- **PyYAML**: загрузка tissue_rules.yaml
- **SciPy**: `scipy.spatial.distance_transform_edt` для proximity
- **Worley Noise** (опционально): для текстурных свойств hex

## Входные данные

```python
# Все данные из предыдущих фаз
elevation: np.ndarray
temperature: np.ndarray
moisture: np.ndarray
bone_density_map: np.ndarray
vessels: list
caverns: list
bioactive_saturation: np.ndarray
river_mask: np.ndarray
organs: dict
regions: dict
```

## Выходные данные

```python
tissue_map: np.ndarray  # (512, 512) dtype='U32' - строковые ID тканей
```

## Пошаговый план

### 1. Сбор контекста для клеток

```python
def _build_cell_context(x: int, y: int, world_data: dict) -> dict:
    """
    Создание полного контекста для клетки (x, y)

    Контекст включает 11 параметров:
    - elevation, temperature, moisture
    - lymph_flow, bioactive_saturation
    - bone_density, region, nearest_organ
    - distance_to_vessel, is_cavern, infection_level
    """
    context = {
        'elevation': world_data['elevation'][y, x],
        'temperature': world_data['temperature'][y, x],
        'moisture': world_data['moisture'][y, x],
        'bone_density': world_data['bone_density_map'][y, x],
        'bioactive_saturation': world_data['bioactive_saturation'][y, x],
        'is_river': world_data['river_mask'][y, x],
        'region': _get_region_at(x, y, world_data['regions']),
        'nearest_organ': _find_nearest_organ(x, y, world_data['organs']),
        'distance_to_vessel': _distance_to_nearest_vessel(x, y, world_data['vessels']),
        'is_cavern': _is_cavern(x, y, world_data['caverns']),
        'infection_level': 0.0  # Placeholder (будущая фича)
    }

    return context


def _get_region_at(x: int, y: int, regions: dict) -> str:
    """Определение региона клетки"""
    for region_name, region in regions.items():
        if region.mask[y, x]:
            return region_name
    return 'UNKNOWN'


def _find_nearest_organ(x: int, y: int, organs: dict) -> tuple:
    """Ближайший орган и расстояние"""
    min_dist = float('inf')
    nearest = None

    for organ_id, organ in organs.items():
        ox, oy = organ.position
        dist = np.sqrt((x - ox)**2 + (y - oy)**2)

        if dist < min_dist:
            min_dist = dist
            nearest = (organ_id, dist)

    return nearest


def _distance_to_nearest_vessel(x: int, y: int, vessels: list) -> float:
    """Расстояние до ближайшей артерии"""
    min_dist = float('inf')

    for vessel in vessels:
        vx, vy = vessel['to']
        dist = np.sqrt((x - vx)**2 + (y - vy)**2)
        min_dist = min(min_dist, dist)

    return min_dist


def _is_cavern(x: int, y: int, caverns: list) -> bool:
    """Проверка: является ли клетка каверной"""
    for cavern in caverns:
        cx, cy = cavern['position']
        if abs(x - cx) < cavern['radius'] and abs(y - cy) < cavern['radius']:
            return True
    return False
```

### 2. Специальные случаи (приоритет 1)

```python
def _assign_special_cases(x: int, y: int, context: dict) -> str:
    """
    Специальные ткани (высший приоритет)

    1. Каверны → alveolar_cavern
    2. Каналы артерий → arterial_canal
    3. Реки → lymph_river
    4. Зоны заражения → infected_tissue
    """
    if context['is_cavern']:
        return 'alveolar_cavern'

    if context['distance_to_vessel'] < 3:  # В радиусе 3px от артерии
        return 'arterial_canal'

    if context['is_river']:
        return 'lymph_river'

    if context['infection_level'] > 0.5:
        return 'infected_tissue'

    return None  # Не специальный случай
```

### 3. Контекстное назначение от органов (приоритет 2)

```python
def _assign_organ_contextual(x: int, y: int, context: dict) -> str:
    """
    Ткани зависящие от близости к органам

    - У желудка (stomach): acid_lake
    - У metabolic_core: thermal_vents
    - У neural clusters: neural_membrane
    """
    if context['nearest_organ'] is None:
        return None

    organ_id, distance = context['nearest_organ']

    if 'stomach' in organ_id and distance < 40:
        if context['elevation'] < 0.3 and context['moisture'] > 0.7:
            return 'acid_lake'

    if 'metabolic_core' in organ_id and distance < 50:
        if context['temperature'] > 0.8:
            return 'thermal_vents'

    if 'ganglion' in organ_id and distance < 25:
        return 'neural_membrane'

    return None
```

### 4. Региональные особенности (приоритет 3)

```python
def _assign_regional(x: int, y: int, context: dict) -> str:
    """
    Региональные ткани

    - THORAX: chitinous_plates (если bone_density > 0.7)
    - DIAPHRAGM: pulsating_plains (если 0.4 < elevation < 0.6)
    - ORGANOID: nutrient_pools (если moisture > 0.7)
    """
    region = context['region']

    if region == 'THORAX':
        if context['bone_density'] > 0.7:
            return 'chitinous_plates'

    if region == 'DIAPHRAGM':
        if 0.4 < context['elevation'] < 0.6:
            return 'pulsating_plains'

    if region == 'ORGANOID':
        if context['moisture'] > 0.7 and context['temperature'] > 0.6:
            return 'nutrient_pools'

    return None
```

### 5. Стандартные правила (приоритет 4)

```python
def _load_tissue_rules(config_path: str) -> dict:
    """Загрузка tissue_rules.yaml"""
    import yaml
    with open(config_path, 'r') as f:
        rules = yaml.safe_load(f)
    return rules


def _assign_standard(x: int, y: int, context: dict, rules: dict) -> str:
    """
    Применение стандартных правил из tissue_rules.yaml

    Правила в формате:
    tissue_id:
      conditions:
        temperature: [min, max]
        moisture: [min, max]
        elevation: [min, max]
        bioactive: [min, max]
    """
    for tissue_id, rule in rules.items():
        conditions = rule.get('conditions', {})

        # Проверка всех условий
        match = True
        for param, (min_val, max_val) in conditions.items():
            if param in context:
                if not (min_val <= context[param] <= max_val):
                    match = False
                    break

        if match:
            return tissue_id

    # Fallback: default tissue
    return 'muscle_tissue'
```

### 6. Основной алгоритм назначения

```python
def _assign_tissue_cell(x: int, y: int, world_data: dict, rules: dict) -> str:
    """
    Назначение ткани для клетки (x, y) с приоритетами

    Приоритет (сверху вниз):
    1. Специальные случаи
    2. Контекстные от органов
    3. Региональные
    4. Стандартные правила
    """
    # Контекст
    context = _build_cell_context(x, y, world_data)

    # 1. Специальные
    tissue = _assign_special_cases(x, y, context)
    if tissue:
        return tissue

    # 2. Контекстные
    tissue = _assign_organ_contextual(x, y, context)
    if tissue:
        return tissue

    # 3. Региональные
    tissue = _assign_regional(x, y, context)
    if tissue:
        return tissue

    # 4. Стандартные
    tissue = _assign_standard(x, y, context, rules)

    return tissue
```

### 7. Генерация tissue_map

```python
def _generate_tissue_map(world_data: dict, rules: dict) -> np.ndarray:
    """
    Генерация полной карты тканей (512×512)
    """
    tissue_map = np.empty((512, 512), dtype='U32')

    for y in range(512):
        for x in range(512):
            # Только на суше
            if world_data['continent_mask'][y, x]:
                tissue_map[y, x] = _assign_tissue_cell(x, y, world_data, rules)
            else:
                tissue_map[y, x] = 'ocean'

    return tissue_map
```

### 8. Интеграция в генератор

```python
class WorldGeneratorV2:
    def _generate_tissues(self, world_data: dict) -> np.ndarray:
        """
        Phase 7: Назначение тканей (биомов)
        """
        # Загрузка правил
        rules = self._load_tissue_rules('config/tissue_rules.yaml')

        # Генерация tissue map
        tissue_map = self._generate_tissue_map(world_data, rules)

        return tissue_map
```

## Конфигурация

```yaml
# config/tissue_rules.yaml
muscle_tissue:
  conditions:
    temperature: [0.4, 0.7]
    moisture: [0.3, 0.7]
    elevation: [0.3, 0.7]
    bioactive: [0.2, 0.8]

chitinous_plates:
  conditions:
    bone_density: [0.7, 1.0]
    elevation: [0.5, 1.0]

spore_fields:
  conditions:
    bioactive: [0.7, 1.0]
    moisture: [0.5, 1.0]

# ... (50+ tissue types)
```

## Опциональная текстуризация (Worley Noise)

```python
def _apply_worley_texture(tissue_map: np.ndarray, seed: int) -> dict:
    """
    Генерация текстурных свойств hex через Worley Noise

    ⭐ v3.0 INSIGHT: Worley Noise в гексагональном мире становится
    генератором ДАННЫХ для hex properties, а не визуальной текстурой!

    Returns:
        hex_properties: dict[tissue_id] -> np.ndarray (512, 512) float
    """
    # Worley Noise для вариативности hex свойств
    # Детали опущены - см. будущую спецификацию
    pass
```

## Тестирование

```python
def test_special_cases():
    context = {
        'is_cavern': True,
        'distance_to_vessel': 10,
        'is_river': False
    }
    tissue = _assign_special_cases(0, 0, context)
    assert tissue == 'alveolar_cavern'

def test_organ_contextual():
    context = {
        'nearest_organ': ('organ_stomach', 30),
        'elevation': 0.2,
        'moisture': 0.8,
        'temperature': 0.7
    }
    tissue = _assign_organ_contextual(0, 0, context)
    assert tissue == 'acid_lake'
```

## Метрики

- **Время выполнения**: ~2-5 секунд (зависит от сложности правил)
- **Память**: ~8 MB (tissue_map 512×512 strings)

## Зависимости

**Зависит от:**
- ВСЕ предыдущие фазы (0-6)

**Используется в:**
- Финальная визуализация мира
- Геймплей (hex properties, movement cost, etc.)

## Визуализация

```bash
python scripts/visualize_world_v2.py --seed my_seed --full
```

## См. также

- **tissue_rules.yaml** - Полные правила назначения тканей (50+ типов)
- **Worley Noise specification** - Будущая спецификация текстуризации hex
