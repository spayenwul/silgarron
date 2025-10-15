## 📊 АНАЛИЗ ВАЛИДНОСТИ ВЫВОДОВ

Изучив кодовую базу, документацию спринтов и текущий CompatibilityService, вот моя оценка:

### ✅ **ВАЛИДНЫЕ ВЫВОДЫ:**

**Шаг 2: Переписать CompatibilityService** - **ПОЛНОСТЬЮ ВАЛИДНО**

- Текущий `CompatibilityService` имеет метод `calculate_race_biome_score`, но **НЕТ** метода `find_best_biome_for_region`
- **Проблема**: В `hex_world_service.py:135` вызывается несуществующий метод:

```python
best_biome_data = self.compatibility.find_best_biome_for_region(
    allowed_biome_candidates,
    placed_neighbors_data
)
```

- Текущая реализация проверяет только `race_data` vs `biome_data`, НО нужна проверка `biome` vs `biome` (соседи)
- **НЕТ** проверки `forbidden_combinations` из `tags_registry.yaml`
- **НЕТ** применения глобальных синергий/конфликтов из `tags_registry.yaml`

**Шаг 3: Создать заглушку SpatialLocationGenerator** - **ЧАСТИЧНО ВАЛИДНО**

- Файл `generators/spatial_location_generator.py` **НЕ СУЩЕСТВУЕТ**
- НО, логика уже **частично реализована** в `HexWorldService.discover_region()` (строки 107-151)
- Метод `get_best_neighbor` **НЕ НУЖЕН** - логика уже встроена в `discover_region`

**Шаг 4: Написать тесты** - **ПОЛНОСТЬЮ ВАЛИДНО**

- **КРИТИЧНО**: Тестов на `CompatibilityService` **НЕ СУЩЕСТВУЕТ**
- Есть только `validators/world_gen_validator.py` (скрипт валидации, не unit-тесты)
- Нужны pytest unit-тесты для TDD

### ❌ **НЕ ВАЛИДНЫЕ/НЕТОЧНЫЕ ВЫВОДЫ:**

1. **"Создать spatial_location_generator.py"** - логика уже в `HexWorldService`
2. **"Интеграция с Noise Maps"** - в коде **НЕТ** noise maps, только простая hex-координатная система

---

## 🎯 ПОДРОБНЫЙ РАСШИРЕННЫЙ ПЛАН СПРИНТА

# SPRINT: Hex Generation Refactoring & Compatibility System

**Цель:** Реализовать полноценную систему совместимости биомов с применением синергий, конфликтов и forbidden combinations для корректной генерации hex-based мира.

**Длительность:** 2 недели (80 часов)  
**Приоритет:** 🔴 **КРИТИЧЕСКИЙ** (блокирует генерацию мира)

---

## 📐 АРХИТЕКТУРНОЕ ОБОСНОВАНИЕ

### Текущая Проблема

```python
# ❌ ПРОБЛЕМА 1: Метод не существует
best_biome = self.compatibility.find_best_biome_for_region(...)  # AttributeError!

# ❌ ПРОБЛЕМА 2: Нет проверки forbidden_combinations
# tags_registry.yaml содержит:
# forbidden_combinations:
#   - ["terrain:aquatic", "terrain:subterranean"]
# Но CompatibilityService это не проверяет!

# ❌ ПРОБЛЕМА 3: Нет применения synergies/conflicts из tags_registry.yaml
# global_compatibility_rules:
#   synergies:
#     - tags: ["surface:stable", "lifestyle:sedentary"]
#       bonus: 2.0
# Не применяется при расчете biome-to-biome!
```

### Новая Архитектура

```
┌─────────────────────────────────────────┐
│     HexWorldService.discover_region()   │
│                                         │
│  1. Получает allowed_biome_candidates   │
│  2. Генерирует hex layout               │
│  3. ДЛЯ КАЖДОГО ГЕКСА:                  │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│   CompatibilityService (REFACTORED)     │
│                                         │
│  calculate_biome_compatibility(         │
│    candidate_biome_tags: Set[str],     │
│    neighbor_biomes_tags: List[Set]     │
│  ) -> CompatibilityScore               │
│                                         │
│  ЛОГИКА:                                │
│  1. ✅ Проверка forbidden_combinations  │
│  2. ✅ Базовый score = 1.0              │
│  3. ✅ Применение synergies (bonus)     │
│  4. ✅ Применение conflicts (penalty)   │
│  5. ✅ Возврат CompatibilityScore       │
└─────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│   find_best_biome_for_region(           │
│     candidates: List[Dict],            │
│     placed_neighbors: List[Dict]       │
│   ) -> Dict                            │
│                                         │
│   АЛГОРИТМ:                             │
│   1. Для каждого candidate:             │
│      - Извлечь tags                     │
│      - Рассчитать scores с каждым       │
│        соседом через                    │
│        calculate_biome_compatibility()  │
│      - Агрегировать (average)           │
│   2. Выбрать candidate с max score      │
│   3. Вернуть biome_data                 │
└─────────────────────────────────────────┘
```

---

## 🔍 ДЕТАЛЬНЫЙ АНАЛИЗ ДАННЫХ

### Существующие Данные (✅ Доступны)

#### 1. **tags_registry.yaml** - Глобальные правила

```yaml
global_compatibility_rules:
  synergies:
    - tags: ["surface:stable", "lifestyle:sedentary"]
      bonus: 2.0  # Умножаем score на 2.0
      
  conflicts:
    - tags: ["surface:unstable", "lifestyle:sedentary"]
      penalty: 0.2  # Умножаем score на 0.2
      
validation_rules:
  forbidden_combinations:
    - ["terrain:aquatic", "terrain:subterranean"]  # is_compatible = False
    - ["manifestation:numb", "manifestation:chaotic"]
    - ["ecology:barren", "ecology:fertile"]
```

**Использование:**

- `synergies` применяются при совпадении тегов → умножение score
- `conflicts` применяются при совпадении тегов → уменьшение score
- `forbidden_combinations` → немедленный возврат `is_compatible: False`

#### 2. **generation_rules.yaml** - Формулы (НЕ ИСПОЛЬЗУЮТСЯ В КОДЕ!)

```yaml
compatibility_formulas:
  biome_spawn_probability:
    formula: |
      probability = base_weight * noise_match * compatibility_with_neighbors
```

**ПРОБЛЕМА:** Формула описана, но **НЕ РЕАЛИЗОВАНА** в коде!

#### 3. **data/biomes/*.yaml** - Теги биомов

```yaml
# Пример: data/biomes/rolling_hills.yaml
id: rolling_hills
base_tags:
  - terrain:elevated
  - surface:stable
  - ecology:moderate
  - lifestyle:sedentary
  - location:inhabited
```

**Использование:** Извлекаем через `world_data.get_biome_data(biome_id)`

### Данные, Которые Нужны в Будущем (🔮 TODO)

1. **Noise Maps для процедурной генерации**
    
    - Сейчас: Hex layout = `random.choice(allowed_biomes)`
    - Будущее: Noise-based distribution (Perlin/Simplex noise)
2. **Biome Transition Rules**
    
    - Резкие переходы (жар → холод) должны иметь penalty
    - Плавные переходы (лес → опушка) должны иметь bonus
3. **Historical Context для POI**
    
    - `era_of_sky_principalities` → больше руин
    - `era_of_old_gods` → больше священных мест

---

## 🛠️ ЗАДАЧИ И РЕАЛИЗАЦИЯ

### **ЗАДАЧА 1: Рефакторинг CompatibilityService** (20 часов)

#### 1.1 Добавить `calculate_biome_compatibility()` (8 часов)

**Сигнатура:**

```python
def calculate_biome_compatibility(
    self,
    candidate_tags: Set[str],
    neighbor_tags: List[Set[str]]
) -> CompatibilityScore:
    """
    Рассчитывает совместимость биома-кандидата с соседними биомами.
    
    Args:
        candidate_tags: Теги биома-кандидата (например, из rolling_hills)
        neighbor_tags: Список тегов уже размещенных соседей
        
    Returns:
        CompatibilityScore с полным breakdown
        
    Пример:
        candidate = {"terrain:elevated", "surface:stable"}
        neighbors = [
            {"terrain:elevated", "ecology:fertile"},  # Сосед 1
            {"surface:stable", "lifestyle:sedentary"} # Сосед 2
        ]
        
        score = service.calculate_biome_compatibility(candidate, neighbors)
        # score.raw_score = 2.0 (synergy bonus применён)
        # score.is_compatible = True
    """
```

**Алгоритм:**

```python
def calculate_biome_compatibility(self, candidate_tags, neighbor_tags):
    breakdown = {}
    blocking_factors = []
    
    # ШАГ 1: Проверка forbidden_combinations
    # Пример: ["terrain:aquatic", "terrain:subterranean"]
    forbidden = self.rules.get('validation_rules', {}).get('forbidden_combinations', [])
    
    for neighbor_tag_set in neighbor_tags:
        for forbidden_pair in forbidden:
            # Если candidate имеет первый тег, а сосед второй → ЗАПРЕЩЕНО
            if forbidden_pair[0] in candidate_tags and forbidden_pair[1] in neighbor_tag_set:
                blocking_factors.append(
                    f"Forbidden: {forbidden_pair[0]} + {forbidden_pair[1]}"
                )
                return self._create_score(0.0, {}, blocking_factors)
            # Проверяем и обратный случай
            if forbidden_pair[1] in candidate_tags and forbidden_pair[0] in neighbor_tag_set:
                blocking_factors.append(
                    f"Forbidden: {forbidden_pair[1]} + {forbidden_pair[0]}"
                )
                return self._create_score(0.0, {}, blocking_factors)
    
    # ШАГ 2: Базовый score
    base_score = 1.0
    breakdown['base_score'] = base_score
    
    # ШАГ 3: Применение synergies (из tags_registry.yaml)
    synergies = self.rules.get('global_compatibility_rules', {}).get('synergies', [])
    synergy_multiplier = 1.0
    
    for neighbor_tag_set in neighbor_tags:
        for synergy_rule in synergies:
            required_tags = set(synergy_rule['tags'])
            # Проверяем, есть ли все требуемые теги между candidate и neighbor
            combined_tags = candidate_tags | neighbor_tag_set
            if required_tags.issubset(combined_tags):
                synergy_multiplier *= synergy_rule['bonus']
                breakdown[f"synergy_{synergy_rule['reason'][:20]}"] = synergy_rule['bonus']
    
    # ШАГ 4: Применение conflicts
    conflicts = self.rules.get('global_compatibility_rules', {}).get('conflicts', [])
    conflict_multiplier = 1.0
    
    for neighbor_tag_set in neighbor_tags:
        for conflict_rule in conflicts:
            required_tags = set(conflict_rule['tags'])
            combined_tags = candidate_tags | neighbor_tag_set
            if required_tags.issubset(combined_tags):
                conflict_multiplier *= conflict_rule['penalty']
                breakdown[f"conflict_{conflict_rule['reason'][:20]}"] = conflict_rule['penalty']
    
    # ШАГ 5: Итоговый расчет
    final_score = base_score * synergy_multiplier * conflict_multiplier
    breakdown['synergy_multiplier'] = synergy_multiplier
    breakdown['conflict_multiplier'] = conflict_multiplier
    
    return self._create_score(final_score, breakdown, blocking_factors)
```

**Тестовые случаи:**

```python
# Тест 1: Synergy применяется
candidate = {"surface:stable", "lifestyle:sedentary"}
neighbor = {"surface:stable"}
# Ожидание: bonus 2.0, score = 2.0

# Тест 2: Conflict применяется
candidate = {"surface:unstable", "lifestyle:sedentary"}
neighbor = {"surface:unstable"}
# Ожидание: penalty 0.2, score = 0.2

# Тест 3: Forbidden combination
candidate = {"terrain:aquatic"}
neighbor = {"terrain:subterranean"}
# Ожидание: is_compatible = False, score = 0.0
```

---

#### 1.2 Добавить `find_best_biome_for_region()` (6 часов)

**Сигнатура:**

```python
def find_best_biome_for_region(
    self,
    allowed_biome_candidates: List[Dict],
    placed_neighbors_data: List[Dict]
) -> Optional[Dict]:
    """
    Выбирает наиболее совместимый биом из кандидатов.
    
    Args:
        allowed_biome_candidates: Список biome_data словарей
            [{'id': 'rolling_hills', 'base_tags': [...], ...}, ...]
        placed_neighbors_data: Список biome_data уже размещенных соседей
            [{'id': 'pulsating_plains', 'base_tags': [...], ...}, ...]
            
    Returns:
        Словарь biome_data с лучшим score, или None если все несовместимы
        
    Пример:
        candidates = [
            {'id': 'rolling_hills', 'base_tags': ['terrain:elevated', ...]},
            {'id': 'geyser_fields', 'base_tags': ['terrain:dynamic', ...]}
        ]
        neighbors = [
            {'id': 'pulsating_plains', 'base_tags': ['surface:stable', ...]}
        ]
        
        best = service.find_best_biome_for_region(candidates, neighbors)
        # Возвращает rolling_hills (synergy с stable)
    """
```

**Алгоритм:**

```python
def find_best_biome_for_region(self, candidates, neighbors):
    if not candidates:
        return None
    
    # Если нет соседей, возвращаем случайного кандидата
    if not neighbors:
        return random.choice(candidates)
    
    # Подготовка: извлекаем теги соседей
    neighbor_tag_sets = []
    for neighbor_data in neighbors:
        neighbor_tags = set(neighbor_data.get('base_tags', []))
        neighbor_tag_sets.append(neighbor_tags)
    
    # Оценка каждого кандидата
    candidate_scores = []
    
    for candidate_data in candidates:
        candidate_tags = set(candidate_data.get('base_tags', []))
        candidate_id = candidate_data['id']
        
        # Рассчитываем совместимость с соседями
        score = self.calculate_biome_compatibility(
            candidate_tags,
            neighbor_tag_sets
        )
        
        # Храним только совместимые кандидаты
        if score.is_compatible:
            candidate_scores.append({
                'biome_data': candidate_data,
                'score': score.raw_score,
                'breakdown': score.breakdown
            })
    
    # Если все несовместимы, возвращаем None
    if not candidate_scores:
        logger.warning("No compatible biomes found!")
        return None
    
    # Сортируем по score (от большего к меньшему)
    candidate_scores.sort(key=lambda x: x['score'], reverse=True)
    
    # Возвращаем лучшего кандидата
    best = candidate_scores[0]
    logger.info(f"Best biome: {best['biome_data']['id']} (score: {best['score']:.2f})")
    
    return best['biome_data']
```

**Тестовые случаи:**

```python
# Тест 1: Выбор лучшего из двух
candidates = [hills_data, geyser_data]
neighbors = [stable_plains_data]
# Ожидание: hills_data (synergy с stable)

# Тест 2: Все несовместимы
candidates = [aquatic_data]
neighbors = [subterranean_data]
# Ожидание: None (forbidden combination)

# Тест 3: Нет соседей
candidates = [hills_data, plains_data]
neighbors = []
# Ожидание: random.choice([hills_data, plains_data])
```

---

#### 1.3 Обновить существующий метод (4 часа)

**Обновление `calculate_race_biome_score()`:**

```python
# БЫЛО: Только race vs biome
def calculate_race_biome_score(self, race_data, biome_data):
    # ... существующий код ...
    pass

# ДОБАВИТЬ: Также использовать global_compatibility_rules
def calculate_race_biome_score(self, race_data, biome_data):
    # ... существующая логика для local rules ...
    
    # НОВОЕ: Применяем synergies/conflicts из tags_registry
    race_tags = set(race_data.get('base_tags', []))
    biome_tags = set(biome_data.get('base_tags', []))
    
    synergies = self.rules.get('global_compatibility_rules', {}).get('synergies', [])
    for synergy_rule in synergies:
        required_tags = set(synergy_rule['tags'])
        combined = race_tags | biome_tags
        if required_tags.issubset(combined):
            base_score *= synergy_rule['bonus']
    
    # ... аналогично для conflicts ...
```

---

#### 1.4 Документация и логирование (2 часа)

```python
# Добавить в docstrings:
"""
CompatibilityService - Математическое ядро генерации мира

АРХИТЕКТУРА:
    1. calculate_biome_compatibility() - биом vs биом
    2. calculate_race_biome_score() - раса vs биом
    3. find_best_biome_for_region() - выбор лучшего биома

ИСТОЧНИКИ ДАННЫХ:
    - tags_registry.yaml:
        * global_compatibility_rules.synergies
        * global_compatibility_rules.conflicts
        * validation_rules.forbidden_combinations
    - generation_rules.yaml:
        * global_modifiers.race_terrain_affinity
    - data/biomes/*.yaml:
        * base_tags для каждого биома

ФОРМУЛЫ:
    biome_compatibility_score = 
        base_score (1.0) 
        * synergy_multipliers 
        * conflict_multipliers
        
    Если forbidden_combination найдена:
        score = 0.0, is_compatible = False
        
ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ:
    # Выбор биома для нового гекса
    best_biome = service.find_best_biome_for_region(
        candidates=[hills, plains, forest],
        neighbors=[existing_plain, existing_hill]
    )
    
    # Прямой расчет совместимости
    score = service.calculate_biome_compatibility(
        candidate_tags={"terrain:elevated", "surface:stable"},
        neighbor_tags=[{"terrain:elevated"}, {"surface:stable"}]
    )
"""

# Логирование:
logger.debug(f"Checking biome {candidate_id} against {len(neighbors)} neighbors")
logger.debug(f"Applied synergy: {synergy_rule['reason']} (bonus: {bonus})")
logger.warning(f"Forbidden combination detected: {pair}")
logger.info(f"Final score: {final_score:.2f}, compatible: {is_compatible}")
```

---

### **ЗАДАЧА 2: Unit-тесты для CompatibilityService** (15 часов)

#### 2.1 Структура тестов

```
tests/
  test_services/
    test_compatibility_service.py  # НОВЫЙ ФАЙЛ
```

#### 2.2 Тесты для `calculate_biome_compatibility()` (7 часов)

```python
# tests/test_services/test_compatibility_service.py

import pytest
from services.compatibility_service import CompatibilityService
from services.world_data_service import WorldDataService

@pytest.fixture
def compatibility_service():
    """Fixture: инициализация CompatibilityService"""
    wds = WorldDataService()
    rules = wds.get_generation_rules()
    return CompatibilityService(rules)

@pytest.fixture
def sample_tags():
    """Fixture: примеры тегов для тестирования"""
    return {
        'stable': {'surface:stable', 'lifestyle:sedentary'},
        'unstable': {'surface:unstable', 'lifestyle:sedentary'},
        'elevated': {'terrain:elevated', 'lifestyle:isolated'},
        'aquatic': {'terrain:aquatic'},
        'subterranean': {'terrain:subterranean'},
        'fertile': {'ecology:fertile', 'resource:pure_lymph'},
    }

# ===== ТЕСТ 1: Forbidden Combination =====
def test_forbidden_combination_returns_incompatible(compatibility_service, sample_tags):
    """
    КРИТИЧЕСКИЙ ТЕСТ: Проверка forbidden_combinations
    
    Ожидание:
        - is_compatible = False
        - raw_score = 0.0
        - blocking_factors содержит причину
    """
    candidate = sample_tags['aquatic']
    neighbors = [sample_tags['subterranean']]
    
    score = compatibility_service.calculate_biome_compatibility(
        candidate,
        neighbors
    )
    
    assert score.is_compatible == False, "Aquatic + Subterranean должны быть несовместимы!"
    assert score.raw_score == 0.0
    assert len(score.blocking_factors) > 0
    assert "Forbidden" in score.blocking_factors[0]

# ===== ТЕСТ 2: Synergy Увеличивает Score =====
def test_synergy_increases_score(compatibility_service, sample_tags):
    """
    Проверка применения synergy bonus
    
    tags_registry.yaml содержит:
        synergies:
          - tags: ["surface:stable", "lifestyle:sedentary"]
            bonus: 2.0
    
    Ожидание:
        - raw_score > 1.0 (базовый score умножен на bonus)
        - breakdown содержит 'synergy_...'
    """
    candidate = sample_tags['stable']
    neighbors = [sample_tags['stable']]
    
    score = compatibility_service.calculate_biome_compatibility(
        candidate,
        neighbors
    )
    
    assert score.is_compatible == True
    assert score.raw_score > 1.0, "Synergy должна увеличить score!"
    assert score.raw_score == pytest.approx(2.0, rel=0.1), "Ожидается bonus 2.0"
    
    # Проверяем breakdown
    assert 'synergy_multiplier' in score.breakdown
    assert score.breakdown['synergy_multiplier'] == pytest.approx(2.0)

# ===== ТЕСТ 3: Conflict Уменьшает Score =====
def test_conflict_decreases_score(compatibility_service, sample_tags):
    """
    Проверка применения conflict penalty
    
    tags_registry.yaml:
        conflicts:
          - tags: ["surface:unstable", "lifestyle:sedentary"]
            penalty: 0.2
    
    Ожидание:
        - raw_score < 1.0 (базовый score умножен на penalty)
        - breakdown содержит 'conflict_...'
    """
    candidate = sample_tags['unstable']
    neighbors = [sample_tags['unstable']]
    
    score = compatibility_service.calculate_biome_compatibility(
        candidate,
        neighbors
    )
    
    assert score.is_compatible == True  # Всё ещё совместимо, но с низким score
    assert score.raw_score < 1.0, "Conflict должен уменьшить score!"
    assert score.raw_score == pytest.approx(0.2, rel=0.1), "Ожидается penalty 0.2"
    
    assert 'conflict_multiplier' in score.breakdown
    assert score.breakdown['conflict_multiplier'] == pytest.approx(0.2)

# ===== ТЕСТ 4: Без Соседей =====
def test_no_neighbors_returns_base_score(compatibility_service, sample_tags):
    """
    Если соседей нет, должен вернуться базовый score = 1.0
    """
    candidate = sample_tags['stable']
    neighbors = []
    
    score = compatibility_service.calculate_biome_compatibility(
        candidate,
        neighbors
    )
    
    assert score.is_compatible == True
    assert score.raw_score == pytest.approx(1.0)

# ===== ТЕСТ 5: Множественные Синергии =====
def test_multiple_synergies_stack(compatibility_service):
    """
    Проверка, что несколько synergies умножаются
    
    Пример:
        candidate = {'surface:stable', 'ecology:fertile'}
        neighbor1 = {'lifestyle:sedentary'}  # synergy 1: stable + sedentary = 2.0
        neighbor2 = {'resource:pure_lymph'}  # synergy 2: fertile + lymph = 1.8
        
    Ожидаемый score = 1.0 * 2.0 * 1.8 = 3.6
    """
    candidate = {'surface:stable', 'ecology:fertile'}
    neighbors = [
        {'lifestyle:sedentary'},      # Synergy 1
        {'resource:pure_lymph'}       # Synergy 2
    ]
    
    score = compatibility_service.calculate_biome_compatibility(
        candidate,
        neighbors
    )
    
    assert score.is_compatible == True
    # 1.0 * 2.0 (stable+sedentary) * 1.8 (fertile+lymph) = 3.6
    assert score.raw_score == pytest.approx(3.6, rel=0.1)

# ===== ТЕСТ 6: Синергия И Конфликт Одновременно =====
def test_synergy_and_conflict_both_apply(compatibility_service):
    """
    Если есть и synergy, и conflict, оба применяются
    
    candidate = {'surface:stable', 'lifestyle:sedentary'}
    neighbor = {'surface:unstable', 'lifestyle:sedentary'}
    
    - Synergy: stable + sedentary = 2.0
    - Conflict: unstable + sedentary = 0.2
    
    Итого: 1.0 * 2.0 * 0.2 = 0.4
    """
    candidate = {'surface:stable', 'lifestyle:sedentary'}
    neighbors = [{'surface:unstable', 'lifestyle:sedentary'}]
    
    score = compatibility_service.calculate_biome_compatibility(
        candidate,
        neighbors
    )
    
    assert score.is_compatible == True
    # 1.0 * 2.0 (synergy) * 0.2 (conflict) = 0.4
    assert score.raw_score == pytest.approx(0.4, rel=0.1)
```

---

#### 2.3 Тесты для `find_best_biome_for_region()` (5 часов)

```python
# ===== ТЕСТ 7: Выбор Лучшего Биома =====
def test_find_best_biome_prefers_synergistic(compatibility_service):
    """
    Из двух кандидатов должен выбраться тот, у которого выше score
    """
    # Подготовка: создаём фейковые biome_data
	    candidate1 = {
        'id': 'rolling_hills',
        'base_tags': ['surface:stable', 'lifestyle:sedentary']  # Synergy с соседом
    }
    candidate2 = {
        'id': 'geyser_fields',
        'base_tags': ['surface:unstable', 'lifestyle:nomadic']  # Нет синергии
    }
    
    neighbor = {
        'id': 'stable_plains',
        'base_tags': ['surface:stable', 'ecology:moderate']
    }
    
    candidates = [candidate1, candidate2]
    neighbors = [neighbor]
    
    best = compatibility_service.find_best_biome_for_region(
        candidates,
        neighbors
    )
    
    assert best is not None
    assert best['id'] == 'rolling_hills', "Должен выбраться биом с synergy!"

# ===== ТЕСТ 8: Все Несовместимы =====
def test_find_best_biome_all_incompatible_returns_none(compatibility_service):
    """
    Если все кандидаты имеют forbidden_combinations с соседями,
    должен вернуться None
    """
    candidate1 = {
        'id': 'underwater_caves',
        'base_tags': ['terrain:aquatic']
    }
    candidate2 = {
        'id': 'deep_ocean',
        'base_tags': ['terrain:aquatic', 'ecology:unique']
    }
    
    neighbor = {
        'id': 'crystal_mines',
        'base_tags': ['terrain:subterranean']
    }
    
    candidates = [candidate1, candidate2]
    neighbors = [neighbor]
    
    best = compatibility_service.find_best_biome_for_region(
        candidates,
        neighbors
    )
    
    assert best is None, "Все кандидаты несовместимы, должен вернуться None!"

# ===== ТЕСТ 9: Нет Соседей =====
def test_find_best_biome_no_neighbors_returns_random(compatibility_service):
    """
    Если соседей нет, должен вернуться один из кандидатов
    """
    candidate1 = {'id': 'hills', 'base_tags': ['terrain:elevated']}
    candidate2 = {'id': 'plains', 'base_tags': ['terrain:flat']}
    
    candidates = [candidate1, candidate2]
    neighbors = []
    
    best = compatibility_service.find_best_biome_for_region(
        candidates,
        neighbors
    )
    
    assert best is not None
    assert best['id'] in ['hills', 'plains']

# ===== ТЕСТ 10: Пустой Список Кандидатов =====
def test_find_best_biome_no_candidates_returns_none(compatibility_service):
    """
    Если кандидатов нет, должен вернуться None
    """
    candidates = []
    neighbors = [{'id': 'plains', 'base_tags': ['terrain:flat']}]
    
    best = compatibility_service.find_best_biome_for_region(
        candidates,
        neighbors
    )
    
    assert best is None

# ===== ТЕСТ 11: Сортировка по Score =====
def test_find_best_biome_sorts_by_score(compatibility_service):
    """
    Должен выбираться кандидат с МАКСИМАЛЬНЫМ score
    
    candidate1: score = 2.0 (synergy)
    candidate2: score = 1.0 (нейтральный)
    candidate3: score = 0.3 (conflict)
    
    Ожидание: candidate1
    """
    candidate1 = {
        'id': 'synergy_biome',
        'base_tags': ['surface:stable', 'lifestyle:sedentary']  # Synergy 2.0
    }
    candidate2 = {
        'id': 'neutral_biome',
        'base_tags': ['ecology:moderate']  # Нет правил
    }
    candidate3 = {
        'id': 'conflict_biome',
        'base_tags': ['surface:unstable', 'lifestyle:sedentary']  # Conflict 0.2
    }
    
    neighbor = {
        'id': 'stable_neighbor',
        'base_tags': ['surface:stable', 'lifestyle:sedentary']
    }
    
    candidates = [candidate3, candidate2, candidate1]  # Специально перемешиваем
    neighbors = [neighbor]
    
    best = compatibility_service.find_best_biome_for_region(
        candidates,
        neighbors
    )
    
    assert best['id'] == 'synergy_biome', "Должен выбраться биом с highest score!"
```

---

#### 2.4 Integration тесты (3 часа)

```python
# ===== ТЕСТ 12: Интеграция с HexWorldService =====
def test_integration_hex_world_uses_compatibility(compatibility_service):
    """
    Проверка, что HexWorldService.discover_region() 
    корректно использует CompatibilityService
    
    ЭТОТ ТЕСТ ПРОВЕРЯЕТ РЕАЛЬНУЮ ГЕНЕРАЦИЮ!
    """
    from services.hex_world_service import HexWorldService
    from services.world_data_service import WorldDataService
    from services.tag_service import TagRegistry
    
    wds = WorldDataService()
    tag_registry = TagRegistry(wds.get_tags_registry())
    
    hex_service = HexWorldService(
        session_id="test_session",
        world_data_service=wds,
        tag_registry=tag_registry,
        compatibility_service=compatibility_service
    )
    
    # Генерируем континент
    center_region_id = hex_service.generate_continent("silgarron", radius=1)
    
    # Открываем регион (генерируем биомы)
    biome_ids = hex_service.discover_region(center_region_id)
    
    assert len(biome_ids) > 0, "Должны сгенерироваться биомы!"
    
    # Проверяем, что биомы НЕ имеют forbidden_combinations
    region = hex_service.regions[center_region_id]
    biome_tag_sets = []
    
    for biome_id in biome_ids:
        biome = hex_service.biomes[biome_id]
        biome_tags = set(biome.tags)
        biome_tag_sets.append(biome_tags)
    
    # Проверяем каждую пару соседних биомов
    forbidden = compatibility_service.rules.get('validation_rules', {}).get('forbidden_combinations', [])
    
    for i, tags1 in enumerate(biome_tag_sets):
        for j, tags2 in enumerate(biome_tag_sets):
            if i == j:
                continue
            
            for forbidden_pair in forbidden:
                # Проверяем, что forbidden_pair НЕ присутствует
                has_forbidden = (
                    forbidden_pair[0] in tags1 and forbidden_pair[1] in tags2
                ) or (
                    forbidden_pair[1] in tags1 and forbidden_pair[0] in tags2
                )
                
                assert not has_forbidden, f"Forbidden combination found: {forbidden_pair}!"
    
    print(f"✅ Сгенерировано {len(biome_ids)} биомов без forbidden combinations")

# ===== ТЕСТ 13: Реальные Данные из YAML =====
def test_real_data_from_yaml(compatibility_service):
    """
    Проверка, что сервис корректно читает данные из tags_registry.yaml
    """
    rules = compatibility_service.rules
    
    # Проверяем наличие ключевых секций
    assert 'global_compatibility_rules' in rules
    assert 'validation_rules' in rules
    
    # Проверяем synergies
    synergies = rules['global_compatibility_rules'].get('synergies', [])
    assert len(synergies) > 0, "В tags_registry.yaml должны быть synergies!"
    
    # Проверяем, что есть synergy для stable + sedentary
    found_synergy = False
    for synergy in synergies:
        if 'surface:stable' in synergy['tags'] and 'lifestyle:sedentary' in synergy['tags']:
            found_synergy = True
            assert synergy['bonus'] == 2.0
            break
    
    assert found_synergy, "Должна быть synergy для stable + sedentary!"
    
    # Проверяем conflicts
    conflicts = rules['global_compatibility_rules'].get('conflicts', [])
    assert len(conflicts) > 0
    
    # Проверяем forbidden_combinations
    forbidden = rules['validation_rules'].get('forbidden_combinations', [])
    assert len(forbidden) > 0
    assert ['terrain:aquatic', 'terrain:subterranean'] in forbidden

# ===== ТЕСТ 14: Кэширование =====
def test_caching_works(compatibility_service):
    """
    Проверка, что повторные вызовы используют кэш
    """
    candidate = {'terrain:elevated', 'surface:stable'}
    neighbors = [{'terrain:elevated'}]
    
    # Первый вызов - должен рассчитать
    score1 = compatibility_service.calculate_biome_compatibility(candidate, neighbors)
    
    # Второй вызов - должен взять из кэша
    score2 = compatibility_service.calculate_biome_compatibility(candidate, neighbors)
    
    # Результаты должны быть идентичны
    assert score1.raw_score == score2.raw_score
    assert score1.is_compatible == score2.is_compatible
    
    # Проверяем, что кэш действительно используется
    # (в реальности нужно мокнуть calculate и проверить call_count)
    assert len(compatibility_service._compatibility_cache) > 0
```

---

### **ЗАДАЧА 3: Обновление HexWorldService** (10 часов)

#### 3.1 Исправление вызова find_best_biome_for_region (3 часа)

**Файл:** `services/hex_world_service.py` строка 135

```python
# БЫЛО (НЕ РАБОТАЕТ):
best_biome_data = self.compatibility.find_best_biome_for_region(
    allowed_biome_candidates,
    placed_neighbors_data
)

# НУЖНО ИЗМЕНИТЬ:
def discover_region(self, region_id: str) -> List[str]:
    """
    Генерация биомов внутри региона с использованием CompatibilityService.
    """
    region = self.regions.get(region_id)
    if not region or region.discovered:
        return region.biome_ids if region else []

    region.discovered = True
    target_biome_count = random.randint(
        self.config.min_biomes_per_region,
        self.config.max_biomes_per_region
    )
    
    # Получаем список всех возможных биомов для этого типа региона
    allowed_biome_candidates = self.world_data.get_all_biome_data_for_region(region.region_type)
    if not allowed_biome_candidates:
        logger.warning(f"No biomes found for region type {region.region_type}")
        return []

    # Генерируем hex layout
    biome_coords = self._generate_local_biome_layout(target_biome_count)
    placed_biomes_map: Dict[HexCoord, Dict] = {}

    # ГЛАВНЫЙ ЦИКЛ: размещаем биомы по одному
    for coord in biome_coords:
        # Находим соседей, которые уже размещены
        neighbor_coords = coord.neighbors()
        placed_neighbors_data = [
            placed_biomes_map[nc] 
            for nc in neighbor_coords 
            if nc in placed_biomes_map
        ]

        # === КРИТИЧЕСКАЯ ЧАСТЬ: используем CompatibilityService ===
        best_biome_data = self.compatibility.find_best_biome_for_region(
            allowed_biome_candidates,
            placed_neighbors_data
        )
        # ==========================================================

        if best_biome_data:
            # Создаём биом
            biome = self._create_biome(region, best_biome_data['id'], coord)
            self.biomes[biome.id] = biome
            region.biome_ids.append(biome.id)
            
            # Запоминаем для следующих соседей
            placed_biomes_map[coord] = best_biome_data
        else:
            # Если не нашли совместимого, логируем и пропускаем
            logger.warning(f"Could not find compatible biome for coord {coord}")

    return region.biome_ids
```

---

#### 3.2 Добавление fallback логики (4 часа)

**Проблема:** Что если `find_best_biome_for_region()` возвращает `None`?

**Решение: Fallback стратегия**

```python
def discover_region(self, region_id: str) -> List[str]:
    # ... существующий код ...
    
    for coord in biome_coords:
        neighbor_coords = coord.neighbors()
        placed_neighbors_data = [
            placed_biomes_map[nc] 
            for nc in neighbor_coords 
            if nc in placed_biomes_map
        ]

        # СТРАТЕГИЯ 1: Пытаемся найти совместимый биом
        best_biome_data = self.compatibility.find_best_biome_for_region(
            allowed_biome_candidates,
            placed_neighbors_data
        )
        
        # СТРАТЕГИЯ 2: Fallback - если не нашли совместимого
        if best_biome_data is None and placed_neighbors_data:
            logger.warning(f"No compatible biome found for {coord}. Trying without compatibility check...")
            
            # Пытаемся найти биом, который хотя бы НЕ имеет forbidden_combinations
            for candidate in allowed_biome_candidates:
                candidate_tags = set(candidate.get('base_tags', []))
                
                # Проверяем только forbidden, игнорируем score
                has_forbidden = False
                for neighbor_data in placed_neighbors_data:
                    neighbor_tags = set(neighbor_data.get('base_tags', []))
                    
                    forbidden = self.compatibility.rules.get('validation_rules', {}).get('forbidden_combinations', [])
                    for forbidden_pair in forbidden:
                        if (forbidden_pair[0] in candidate_tags and forbidden_pair[1] in neighbor_tags) or \
                           (forbidden_pair[1] in candidate_tags and forbidden_pair[0] in neighbor_tags):
                            has_forbidden = True
                            break
                    
                    if has_forbidden:
                        break
                
                if not has_forbidden:
                    best_biome_data = candidate
                    logger.info(f"Fallback: Selected {candidate['id']} (no forbidden combinations)")
                    break
        
        # СТРАТЕГИЯ 3: Last resort - случайный выбор (если даже fallback не помог)
        if best_biome_data is None:
            if allowed_biome_candidates:
                best_biome_data = random.choice(allowed_biome_candidates)
                logger.warning(f"Last resort: Random biome {best_biome_data['id']} selected for {coord}")
            else:
                logger.error(f"No biome candidates available for region type {region.region_type}!")
                continue

        # Создаём биом
        biome = self._create_biome(region, best_biome_data['id'], coord)
        self.biomes[biome.id] = biome
        region.biome_ids.append(biome.id)
        placed_biomes_map[coord] = best_biome_data

    return region.biome_ids
```

---

#### 3.3 Улучшение логирования (2 часа)

```python
def discover_region(self, region_id: str) -> List[str]:
    logger.info(f"=== Discovering region {region_id} ===")
    
    # ... код ...
    
    logger.info(f"Target biome count: {target_biome_count}")
    logger.info(f"Available biome types: {[b['id'] for b in allowed_biome_candidates]}")
    
    for i, coord in enumerate(biome_coords):
        logger.debug(f"Processing biome {i+1}/{len(biome_coords)} at {coord}")
        
        # ... поиск best_biome_data ...
        
        if best_biome_data:
            logger.info(
                f"✅ Placed {best_biome_data['id']} at {coord} "
                f"(neighbors: {len(placed_neighbors_data)})"
            )
        
    logger.info(f"=== Region {region_id} complete: {len(region.biome_ids)} biomes placed ===")
    return region.biome_ids
```

---

#### 3.4 Добавление метрик (1 час)

```python
@dataclass
class BiomePlacementMetrics:
    """Метрики для анализа генерации"""
    total_attempts: int = 0
    successful_placements: int = 0
    fallback_used: int = 0
    random_fallback_used: int = 0
    average_compatibility_score: float = 0.0
    biome_type_distribution: Dict[str, int] = field(default_factory=dict)

class HexWorldService:
    def __init__(self, ...):
        # ... существующий код ...
        self.placement_metrics = BiomePlacementMetrics()
    
    def discover_region(self, region_id: str) -> List[str]:
        # ... код ...
        
        self.placement_metrics.total_attempts += 1
        
        if best_biome_data:
            self.placement_metrics.successful_placements += 1
            biome_type = best_biome_data['id']
            self.placement_metrics.biome_type_distribution[biome_type] = \
                self.placement_metrics.biome_type_distribution.get(biome_type, 0) + 1
        
        # ... после завершения региона ...
        
        logger.info(f"Placement metrics: {self.placement_metrics}")
        return region.biome_ids
```

---

### **ЗАДАЧА 4: Валидация и Визуализация** (12 часов)

#### 4.1 Обновление validators/world_gen_validator.py (4 часа)

```python
def validate_biome_placements(hex_service: HexWorldService) -> List[str]:
    """
    НОВАЯ ФУНКЦИЯ: Проверяет, что сгенерированные биомы не имеют forbidden_combinations
    """
    issues = []
    
    for region_id, region in hex_service.regions.items():
        if not region.discovered:
            continue
        
        logger.info(f"Validating region {region_id}...")
        
        # Получаем все биомы региона
        biomes = [hex_service.biomes[bid] for bid in region.biome_ids]
        
        # Проверяем каждую пару соседних биомов
        for biome in biomes:
            neighbor_coords = biome.hex_coord.neighbors()
            
            for neighbor_coord in neighbor_coords:
                # Ищем соседа с такой координатой
                neighbor_biome = None
                for potential_neighbor_id in region.biome_ids:
                    if hex_service.biomes[potential_neighbor_id].hex_coord == neighbor_coord:
                        neighbor_biome = hex_service.biomes[potential_neighbor_id]
                        break
                
                if neighbor_biome:
                    # Проверяем на forbidden_combinations
                    biome_tags = set(biome.tags)
                    neighbor_tags = set(neighbor_biome.tags)
                    
                    forbidden = hex_service.compatibility.rules.get('validation_rules', {}).get('forbidden_combinations', [])
                    
                    for forbidden_pair in forbidden:
                        has_forbidden = (
                            forbidden_pair[0] in biome_tags and forbidden_pair[1] in neighbor_tags
                        ) or (
                            forbidden_pair[1] in biome_tags and forbidden_pair[0] in neighbor_tags
                        )
                        
                        if has_forbidden:
                            issues.append(
                                f"🔴 FORBIDDEN COMBINATION: {biome.biome_type} ({biome.id}) "
                                f"adjacent to {neighbor_biome.biome_type} ({neighbor_biome.id}) "
                                f"violates rule: {forbidden_pair}"
                            )
    
    return issues


def generate_biome_adjacency_report(hex_service: HexWorldService) -> str:
    """
    НОВАЯ ФУНКЦИЯ: Создаёт отчёт о всех соседствах биомов
    """
    report_lines = ["=== BIOME ADJACENCY REPORT ===\n"]
    
    adjacency_counts = defaultdict(lambda: defaultdict(int))
    
    for region_id, region in hex_service.regions.items():
        if not region.discovered:
            continue
        
        biomes = [hex_service.biomes[bid] for bid in region.biome_ids]
        
        for biome in biomes:
            neighbor_coords = biome.hex_coord.neighbors()
            
            for neighbor_coord in neighbor_coords:
                for potential_neighbor_id in region.biome_ids:
                    neighbor_biome = hex_service.biomes[potential_neighbor_id]
                    if neighbor_biome.hex_coord == neighbor_coord:
                        # Записываем adjacency
                        adjacency_counts[biome.biome_type][neighbor_biome.biome_type] += 1
                        break
    
    # Форматируем отчёт
    for biome_type in sorted(adjacency_counts.keys()):
        report_lines.append(f"\n{biome_type}:")
        neighbors = adjacency_counts[biome_type]
        for neighbor_type in sorted(neighbors.keys()):
            count = neighbors[neighbor_type]
            report_lines.append(f"  → {neighbor_type}: {count} times")
    
    return "\n".join(report_lines)
```

---

#### 4.2 Обновление utils/world_gen_visualizer.py (5 часов)

```python
def visualize_hex_region(hex_service: HexWorldService, region_id: str):
    """
    НОВАЯ ФУНКЦИЯ: Визуализирует биомы региона на hex grid
    """
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.collections import PatchCollection
    
    region = hex_service.regions[region_id]
    biomes = [hex_service.biomes[bid] for bid in region.biome_ids]
    
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Цвета для биомов (можно взять из config или хардкодить)
    biome_colors = {
        'rolling_hills': '#8B7355',
        'pulsating_plains': '#9ACD32',
        'geyser_fields': '#FF6347',
        'biolume_forest': '#00CED1',
        'silt_flats': '#D2B48C',
        'kith_settlement': '#FFD700',
        # ... добавить все биомы ...
    }
    
    # Рисуем каждый биом как гекс
    for biome in biomes:
        hex_coord = biome.hex_coord
        x, y = hex_coord.to_pixel(hex_service.config.hex_size)
        
        # Создаём гексагон
        hex_patch = mpatches.RegularPolygon(
            (x, y),
            numVertices=6,
            radius=hex_service.config.hex_size,
            orientation=0,
            facecolor=biome_colors.get(biome.biome_type, '#CCCCCC'),
            edgecolor='black',
            linewidth=2
        )
        ax.add_patch(hex_patch)
        
        # Подпись
        ax.text(x, y, biome.biome_type[:10], ha='center', va='center', fontsize=8)
    
    ax.set_aspect('equal')
    ax.set_title(f"Region: {region.name} ({region_id})")
    plt.tight_layout()
    plt.show()


def generate_compatibility_heatmap_for_biomes(comp_service: CompatibilityService):
    """
    Создаёт heatmap biome-to-biome совместимости
    """
    # Получаем все типы биомов
    from services.world_data_service import WorldDataService
    wds = WorldDataService()
    all_biomes = wds.get_all_biomes()
    
    biome_ids = [b['id'] for b in all_biomes]
    n = len(biome_ids)
    
    # Создаём матрицу
    matrix = np.zeros((n, n))
    
    for i, biome1 in enumerate(all_biomes):
        tags1 = set(biome1.get('base_tags', []))
        
        for j, biome2 in enumerate(all_biomes):
            if i == j:
                matrix[i][j] = 1.0  # Сам с собой всегда совместим
                continue
            
            tags2 = set(biome2.get('base_tags', []))
            
            score = comp_service.calculate_biome_compatibility(
                tags1,
                [tags2]
            )
            
            matrix[i][j] = score.raw_score if score.is_compatible else 0.0
    
    # Визуализация
    plt.figure(figsize=(16, 14))
    sns.heatmap(
        matrix,
        xticklabels=biome_ids,
        yticklabels=biome_ids,
        annot=True,
        fmt='.2f',
        cmap='RdYlGn',
        center=1.0,
        vmin=0.0,
        vmax=3.0
    )
    plt.title("Biome-to-Biome Compatibility Matrix")
    plt.xlabel("Neighbor Biome")
    plt.ylabel("Candidate Biome")
    plt.tight_layout()
    plt.show()
```

---

#### 4.3 Создание тестового скрипта (3 часа)

```python
# tests/manual/test_hex_generation_manual.py

"""
Ручной тест генерации hex world с визуализацией.
Запускать: python -m tests.manual.test_hex_generation_manual
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from services.world_data_service import WorldDataService
from services.hex_world_service import HexWorldService
from services.compatibility_service import CompatibilityService
from services.tag_service import TagRegistry
from validators.world_gen_validator import validate_biome_placements, generate_biome_adjacency_report
from utils.world_gen_visualizer import visualize_hex_region, generate_compatibility_heatmap_for_biomes

def main():
    print("=== MANUAL HEX GENERATION TEST ===\n")
    
    # Инициализация
    wds = WorldDataService()
    rules = wds.get_generation_rules()
    comp_service = CompatibilityService(rules)
    tag_registry = TagRegistry(wds.get_tags_registry())
    
    hex_service = HexWorldService(
        session_id="manual_test",
        world_data_service=wds,
        tag_registry=tag_registry,
        compatibility_service=comp_service
    )
    
    print("1️⃣ Generating continent...")
    center_region_id = hex_service.generate_continent("silgarron", radius=2)
    print(f"✅ Continent generated. Center region: {center_region_id}")
    print(f"   Total regions: {len(hex_service.regions)}\n")
    
    print("2️⃣ Discovering center region...")
    biome_ids = hex_service.discover_region(center_region_id)
    print(f"✅ Region discovered. Biomes placed: {len(biome_ids)}")
    
    # Выводим метрики
    metrics = hex_service.placement_metrics
    print(f"\n📊 Placement Metrics:")
    print(f"   Total attempts: {metrics.total_attempts}")
    print(f"   Successful: {metrics.successful_placements}")
    print(f"   Fallback used: {metrics.fallback_used}")
    print(f"   Random fallback: {metrics.random_fallback_used}")
    print(f"\n   Biome distribution:")
    for biome_type, count in metrics.biome_type_distribution.items():
        print(f"     - {biome_type}: {count}")
    
    print("\n3️⃣ Validating placements...")
    issues = validate_biome_placements(hex_service)
    
    if issues:
        print(f"❌ Found {len(issues)} issues:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("✅ No forbidden combinations found!")
    
    print("\n4️⃣ Generating adjacency report...")
    report = generate_biome_adjacency_report(hex_service)
    print(report)
    
    print("\n5️⃣ Visualizing...")
    try:
        visualize_hex_region(hex_service, center_region_id)
        generate_compatibility_heatmap_for_biomes(comp_service)
    except Exception as e:
        print(f"⚠️ Visualization failed: {e}")
    
    print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    main()
```

---
```python
    # Подготовка: создаём фейковые biome_data
    candidate1 = {
        'id': 'rolling_hills',
        'base_tags': ['surface:stable', 'lifestyle:sedentary']  # Synergy с соседом
    }
    candidate2 = {
        'id': 'geyser_fields',
        'base_tags': ['surface:unstable', 'lifestyle:nomadic']  # Нет синергии
    }
    
    neighbor = {
        'id': 'stable_plains',
        'base_tags': ['surface:stable', 'ecology:moderate']
    }
    
    candidates = [candidate1, candidate2]
    neighbors = [neighbor]
    
    best = compatibility_service.find_best_biome_for_region(
        candidates,
        neighbors
    )
    
    assert best is not None
    assert best['id'] == 'rolling_hills', "Должен выбраться биом с synergy!"

# ===== ТЕСТ 8: Все Несовместимы =====
def test_find_best_biome_all_incompatible_returns_none(compatibility_service):
    """
    Если все кандидаты имеют forbidden_combinations с соседями,
    должен вернуться None
    """
    candidate1 = {
        'id': 'underwater_caves',
        'base_tags': ['terrain:aquatic']
    }
    candidate2 = {
        'id': 'deep_ocean',
        'base_tags': ['terrain:aquatic', 'ecology:unique']
    }
    
    neighbor = {
        'id': 'crystal_mines',
        'base_tags': ['terrain:subterranean']
    }
    
    candidates = [candidate1, candidate2]
    neighbors = [neighbor]
    
    best = compatibility_service.find_best_biome_for_region(
        candidates,
        neighbors
    )
    
    assert best is None, "Все кандидаты несовместимы, должен вернуться None!"

# ===== ТЕСТ 9: Нет Соседей =====
def test_find_best_biome_no_neighbors_returns_random(compatibility_service):
    """
    Если соседей нет, должен вернуться один из кандидатов
    """
    candidate1 = {'id': 'hills', 'base_tags': ['terrain:elevated']}
    candidate2 = {'id': 'plains', 'base_tags': ['terrain:flat']}
    
    candidates = [candidate1, candidate2]
    neighbors = []
    
    best = compatibility_service.find_best_biome_for_region(
        candidates,
        neighbors
    )
    
    assert best is not None
    assert best['id'] in ['hills', 'plains']

# ===== ТЕСТ 10: Пустой Список Кандидатов =====
def test_find_best_biome_no_candidates_returns_none(compatibility_service):
    """
    Если кандидатов нет, должен вернуться None
    """
    candidates = []
    neighbors = [{'id': 'plains', 'base_tags': ['terrain:flat']}]
    
    best = compatibility_service.find_best_biome_for_region(
        candidates,
        neighbors
    )
    
    assert best is None

# ===== ТЕСТ 11: Сортировка по Score =====
def test_find_best_biome_sorts_by_score(compatibility_service):
    """
    Должен выбираться кандидат с МАКСИМАЛЬНЫМ score
    
    candidate1: score = 2.0 (synergy)
    candidate2: score = 1.0 (нейтральный)
    candidate3: score = 0.3 (conflict)
    
    Ожидание: candidate1
    """
    candidate1 = {
        'id': 'synergy_biome',
        'base_tags': ['surface:stable', 'lifestyle:sedentary']  # Synergy 2.0
    }
    candidate2 = {
        'id': 'neutral_biome',
        'base_tags': ['ecology:moderate']  # Нет правил
    }
    candidate3 = {
        'id': 'conflict_biome',
        'base_tags': ['surface:unstable', 'lifestyle:sedentary']  # Conflict 0.2
    }
    
    neighbor = {
        'id': 'stable_neighbor',
        'base_tags': ['surface:stable', 'lifestyle:sedentary']
    }
    
    candidates = [candidate3, candidate2, candidate1]  # Специально перемешиваем
    neighbors = [neighbor]
    
    best = compatibility_service.find_best_biome_for_region(
        candidates,
        neighbors
    )
    
    assert best['id'] == 'synergy_biome', "Должен выбраться биом с highest score!"
```

---

#### 2.4 Integration тесты (3 часа)

```python
# ===== ТЕСТ 12: Интеграция с HexWorldService =====
def test_integration_hex_world_uses_compatibility(compatibility_service):
    """
    Проверка, что HexWorldService.discover_region() 
    корректно использует CompatibilityService
    
    ЭТОТ ТЕСТ ПРОВЕРЯЕТ РЕАЛЬНУЮ ГЕНЕРАЦИЮ!
    """
    from services.hex_world_service import HexWorldService
    from services.world_data_service import WorldDataService
    from services.tag_service import TagRegistry
    
    wds = WorldDataService()
    tag_registry = TagRegistry(wds.get_tags_registry())
    
    hex_service = HexWorldService(
        session_id="test_session",
        world_data_service=wds,
        tag_registry=tag_registry,
        compatibility_service=compatibility_service
    )
    
    # Генерируем континент
    center_region_id = hex_service.generate_continent("silgarron", radius=1)
    
    # Открываем регион (генерируем биомы)
    biome_ids = hex_service.discover_region(center_region_id)
    
    assert len(biome_ids) > 0, "Должны сгенерироваться биомы!"
    
    # Проверяем, что биомы НЕ имеют forbidden_combinations
    region = hex_service.regions[center_region_id]
    biome_tag_sets = []
    
    for biome_id in biome_ids:
        biome = hex_service.biomes[biome_id]
        biome_tags = set(biome.tags)
        biome_tag_sets.append(biome_tags)
    
    # Проверяем каждую пару соседних биомов
    forbidden = compatibility_service.rules.get('validation_rules', {}).get('forbidden_combinations', [])
    
    for i, tags1 in enumerate(biome_tag_sets):
        for j, tags2 in enumerate(biome_tag_sets):
            if i == j:
                continue
            
            for forbidden_pair in forbidden:
                # Проверяем, что forbidden_pair НЕ присутствует
                has_forbidden = (
                    forbidden_pair[0] in tags1 and forbidden_pair[1] in tags2
                ) or (
                    forbidden_pair[1] in tags1 and forbidden_pair[0] in tags2
                )
                
                assert not has_forbidden, f"Forbidden combination found: {forbidden_pair}!"
    
    print(f"✅ Сгенерировано {len(biome_ids)} биомов без forbidden combinations")

# ===== ТЕСТ 13: Реальные Данные из YAML =====
def test_real_data_from_yaml(compatibility_service):
    """
    Проверка, что сервис корректно читает данные из tags_registry.yaml
    """
    rules = compatibility_service.rules
    
    # Проверяем наличие ключевых секций
    assert 'global_compatibility_rules' in rules
    assert 'validation_rules' in rules
    
    # Проверяем synergies
    synergies = rules['global_compatibility_rules'].get('synergies', [])
    assert len(synergies) > 0, "В tags_registry.yaml должны быть synergies!"
    
    # Проверяем, что есть synergy для stable + sedentary
    found_synergy = False
    for synergy in synergies:
        if 'surface:stable' in synergy['tags'] and 'lifestyle:sedentary' in synergy['tags']:
            found_synergy = True
            assert synergy['bonus'] == 2.0
            break
    
    assert found_synergy, "Должна быть synergy для stable + sedentary!"
    
    # Проверяем conflicts
    conflicts = rules['global_compatibility_rules'].get('conflicts', [])
    assert len(conflicts) > 0
    
    # Проверяем forbidden_combinations
    forbidden = rules['validation_rules'].get('forbidden_combinations', [])
    assert len(forbidden) > 0
    assert ['terrain:aquatic', 'terrain:subterranean'] in forbidden

# ===== ТЕСТ 14: Кэширование =====
def test_caching_works(compatibility_service):
    """
    Проверка, что повторные вызовы используют кэш
    """
    candidate = {'terrain:elevated', 'surface:stable'}
    neighbors = [{'terrain:elevated'}]
    
    # Первый вызов - должен рассчитать
    score1 = compatibility_service.calculate_biome_compatibility(candidate, neighbors)
    
    # Второй вызов - должен взять из кэша
    score2 = compatibility_service.calculate_biome_compatibility(candidate, neighbors)
    
    # Результаты должны быть идентичны
    assert score1.raw_score == score2.raw_score
    assert score1.is_compatible == score2.is_compatible
    
    # Проверяем, что кэш действительно используется
    # (в реальности нужно мокнуть calculate и проверить call_count)
    assert len(compatibility_service._compatibility_cache) > 0
```

---

### **ЗАДАЧА 3: Обновление HexWorldService** (10 часов)

#### 3.1 Исправление вызова find_best_biome_for_region (3 часа)

**Файл:** `services/hex_world_service.py` строка 135

```python
# БЫЛО (НЕ РАБОТАЕТ):
best_biome_data = self.compatibility.find_best_biome_for_region(
    allowed_biome_candidates,
    placed_neighbors_data
)

# НУЖНО ИЗМЕНИТЬ:
def discover_region(self, region_id: str) -> List[str]:
    """
    Генерация биомов внутри региона с использованием CompatibilityService.
    """
    region = self.regions.get(region_id)
    if not region or region.discovered:
        return region.biome_ids if region else []

    region.discovered = True
    target_biome_count = random.randint(
        self.config.min_biomes_per_region,
        self.config.max_biomes_per_region
    )
    
    # Получаем список всех возможных биомов для этого типа региона
    allowed_biome_candidates = self.world_data.get_all_biome_data_for_region(region.region_type)
    if not allowed_biome_candidates:
        logger.warning(f"No biomes found for region type {region.region_type}")
        return []

    # Генерируем hex layout
    biome_coords = self._generate_local_biome_layout(target_biome_count)
    placed_biomes_map: Dict[HexCoord, Dict] = {}

    # ГЛАВНЫЙ ЦИКЛ: размещаем биомы по одному
    for coord in biome_coords:
        # Находим соседей, которые уже размещены
        neighbor_coords = coord.neighbors()
        placed_neighbors_data = [
            placed_biomes_map[nc] 
            for nc in neighbor_coords 
            if nc in placed_biomes_map
        ]

        # === КРИТИЧЕСКАЯ ЧАСТЬ: используем CompatibilityService ===
        best_biome_data = self.compatibility.find_best_biome_for_region(
            allowed_biome_candidates,
            placed_neighbors_data
        )
        # ==========================================================

        if best_biome_data:
            # Создаём биом
            biome = self._create_biome(region, best_biome_data['id'], coord)
            self.biomes[biome.id] = biome
            region.biome_ids.append(biome.id)
            
            # Запоминаем для следующих соседей
            placed_biomes_map[coord] = best_biome_data
        else:
            # Если не нашли совместимого, логируем и пропускаем
            logger.warning(f"Could not find compatible biome for coord {coord}")

    return region.biome_ids
```

---

#### 3.2 Добавление fallback логики (4 часа)

**Проблема:** Что если `find_best_biome_for_region()` возвращает `None`?

**Решение: Fallback стратегия**

```python
def discover_region(self, region_id: str) -> List[str]:
    # ... существующий код ...
    
    for coord in biome_coords:
        neighbor_coords = coord.neighbors()
        placed_neighbors_data = [
            placed_biomes_map[nc] 
            for nc in neighbor_coords 
            if nc in placed_biomes_map
        ]

        # СТРАТЕГИЯ 1: Пытаемся найти совместимый биом
        best_biome_data = self.compatibility.find_best_biome_for_region(
            allowed_biome_candidates,
            placed_neighbors_data
        )
        
        # СТРАТЕГИЯ 2: Fallback - если не нашли совместимого
        if best_biome_data is None and placed_neighbors_data:
            logger.warning(f"No compatible biome found for {coord}. Trying without compatibility check...")
            
            # Пытаемся найти биом, который хотя бы НЕ имеет forbidden_combinations
            for candidate in allowed_biome_candidates:
                candidate_tags = set(candidate.get('base_tags', []))
                
                # Проверяем только forbidden, игнорируем score
                has_forbidden = False
                for neighbor_data in placed_neighbors_data:
                    neighbor_tags = set(neighbor_data.get('base_tags', []))
                    
                    forbidden = self.compatibility.rules.get('validation_rules', {}).get('forbidden_combinations', [])
                    for forbidden_pair in forbidden:
                        if (forbidden_pair[0] in candidate_tags and forbidden_pair[1] in neighbor_tags) or \
                           (forbidden_pair[1] in candidate_tags and forbidden_pair[0] in neighbor_tags):
                            has_forbidden = True
                            break
                    
                    if has_forbidden:
                        break
                
                if not has_forbidden:
                    best_biome_data = candidate
                    logger.info(f"Fallback: Selected {candidate['id']} (no forbidden combinations)")
                    break
        
        # СТРАТЕГИЯ 3: Last resort - случайный выбор (если даже fallback не помог)
        if best_biome_data is None:
            if allowed_biome_candidates:
                best_biome_data = random.choice(allowed_biome_candidates)
                logger.warning(f"Last resort: Random biome {best_biome_data['id']} selected for {coord}")
            else:
                logger.error(f"No biome candidates available for region type {region.region_type}!")
                continue

        # Создаём биом
        biome = self._create_biome(region, best_biome_data['id'], coord)
        self.biomes[biome.id] = biome
        region.biome_ids.append(biome.id)
        placed_biomes_map[coord] = best_biome_data

    return region.biome_ids
```

---

#### 3.3 Улучшение логирования (2 часа)

```python
def discover_region(self, region_id: str) -> List[str]:
    logger.info(f"=== Discovering region {region_id} ===")
    
    # ... код ...
    
    logger.info(f"Target biome count: {target_biome_count}")
    logger.info(f"Available biome types: {[b['id'] for b in allowed_biome_candidates]}")
    
    for i, coord in enumerate(biome_coords):
        logger.debug(f"Processing biome {i+1}/{len(biome_coords)} at {coord}")
        
        # ... поиск best_biome_data ...
        
        if best_biome_data:
            logger.info(
                f"✅ Placed {best_biome_data['id']} at {coord} "
                f"(neighbors: {len(placed_neighbors_data)})"
            )
        
    logger.info(f"=== Region {region_id} complete: {len(region.biome_ids)} biomes placed ===")
    return region.biome_ids
```

---

#### 3.4 Добавление метрик (1 час)

```python
@dataclass
class BiomePlacementMetrics:
    """Метрики для анализа генерации"""
    total_attempts: int = 0
    successful_placements: int = 0
    fallback_used: int = 0
    random_fallback_used: int = 0
    average_compatibility_score: float = 0.0
    biome_type_distribution: Dict[str, int] = field(default_factory=dict)

class HexWorldService:
    def __init__(self, ...):
        # ... существующий код ...
        self.placement_metrics = BiomePlacementMetrics()
    
    def discover_region(self, region_id: str) -> List[str]:
        # ... код ...
        
        self.placement_metrics.total_attempts += 1
        
        if best_biome_data:
            self.placement_metrics.successful_placements += 1
            biome_type = best_biome_data['id']
            self.placement_metrics.biome_type_distribution[biome_type] = \
                self.placement_metrics.biome_type_distribution.get(biome_type, 0) + 1
        
        # ... после завершения региона ...
        
        logger.info(f"Placement metrics: {self.placement_metrics}")
        return region.biome_ids
```

---

### **ЗАДАЧА 4: Валидация и Визуализация** (12 часов)

#### 4.1 Обновление validators/world_gen_validator.py (4 часа)

```python
def validate_biome_placements(hex_service: HexWorldService) -> List[str]:
    """
    НОВАЯ ФУНКЦИЯ: Проверяет, что сгенерированные биомы не имеют forbidden_combinations
    """
    issues = []
    
    for region_id, region in hex_service.regions.items():
        if not region.discovered:
            continue
        
        logger.info(f"Validating region {region_id}...")
        
        # Получаем все биомы региона
        biomes = [hex_service.biomes[bid] for bid in region.biome_ids]
        
        # Проверяем каждую пару соседних биомов
        for biome in biomes:
            neighbor_coords = biome.hex_coord.neighbors()
            
            for neighbor_coord in neighbor_coords:
                # Ищем соседа с такой координатой
                neighbor_biome = None
                for potential_neighbor_id in region.biome_ids:
                    if hex_service.biomes[potential_neighbor_id].hex_coord == neighbor_coord:
                        neighbor_biome = hex_service.biomes[potential_neighbor_id]
                        break
                
                if neighbor_biome:
                    # Проверяем на forbidden_combinations
                    biome_tags = set(biome.tags)
                    neighbor_tags = set(neighbor_biome.tags)
                    
                    forbidden = hex_service.compatibility.rules.get('validation_rules', {}).get('forbidden_combinations', [])
                    
                    for forbidden_pair in forbidden:
                        has_forbidden = (
                            forbidden_pair[0] in biome_tags and forbidden_pair[1] in neighbor_tags
                        ) or (
                            forbidden_pair[1] in biome_tags and forbidden_pair[0] in neighbor_tags
                        )
                        
                        if has_forbidden:
                            issues.append(
                                f"🔴 FORBIDDEN COMBINATION: {biome.biome_type} ({biome.id}) "
                                f"adjacent to {neighbor_biome.biome_type} ({neighbor_biome.id}) "
                                f"violates rule: {forbidden_pair}"
                            )
    
    return issues


def generate_biome_adjacency_report(hex_service: HexWorldService) -> str:
    """
    НОВАЯ ФУНКЦИЯ: Создаёт отчёт о всех соседствах биомов
    """
    report_lines = ["=== BIOME ADJACENCY REPORT ===\n"]
    
    adjacency_counts = defaultdict(lambda: defaultdict(int))
    
    for region_id, region in hex_service.regions.items():
        if not region.discovered:
            continue
        
        biomes = [hex_service.biomes[bid] for bid in region.biome_ids]
        
        for biome in biomes:
            neighbor_coords = biome.hex_coord.neighbors()
            
            for neighbor_coord in neighbor_coords:
                for potential_neighbor_id in region.biome_ids:
                    neighbor_biome = hex_service.biomes[potential_neighbor_id]
                    if neighbor_biome.hex_coord == neighbor_coord:
                        # Записываем adjacency
                        adjacency_counts[biome.biome_type][neighbor_biome.biome_type] += 1
                        break
    
    # Форматируем отчёт
    for biome_type in sorted(adjacency_counts.keys()):
        report_lines.append(f"\n{biome_type}:")
        neighbors = adjacency_counts[biome_type]
        for neighbor_type in sorted(neighbors.keys()):
            count = neighbors[neighbor_type]
            report_lines.append(f"  → {neighbor_type}: {count} times")
    
    return "\n".join(report_lines)
```

---

#### 4.2 Обновление utils/world_gen_visualizer.py (5 часов)

```python
def visualize_hex_region(hex_service: HexWorldService, region_id: str):
    """
    НОВАЯ ФУНКЦИЯ: Визуализирует биомы региона на hex grid
    """
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.collections import PatchCollection
    
    region = hex_service.regions[region_id]
    biomes = [hex_service.biomes[bid] for bid in region.biome_ids]
    
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Цвета для биомов (можно взять из config или хардкодить)
    biome_colors = {
        'rolling_hills': '#8B7355',
        'pulsating_plains': '#9ACD32',
        'geyser_fields': '#FF6347',
        'biolume_forest': '#00CED1',
        'silt_flats': '#D2B48C',
        'kith_settlement': '#FFD700',
        # ... добавить все биомы ...
    }
    
    # Рисуем каждый биом как гекс
    for biome in biomes:
        hex_coord = biome.hex_coord
        x, y = hex_coord.to_pixel(hex_service.config.hex_size)
        
        # Создаём гексагон
        hex_patch = mpatches.RegularPolygon(
            (x, y),
            numVertices=6,
            radius=hex_service.config.hex_size,
            orientation=0,
            facecolor=biome_colors.get(biome.biome_type, '#CCCCCC'),
            edgecolor='black',
            linewidth=2
        )
        ax.add_patch(hex_patch)
        
        # Подпись
        ax.text(x, y, biome.biome_type[:10], ha='center', va='center', fontsize=8)
    
    ax.set_aspect('equal')
    ax.set_title(f"Region: {region.name} ({region_id})")
    plt.tight_layout()
    plt.show()


def generate_compatibility_heatmap_for_biomes(comp_service: CompatibilityService):
    """
    Создаёт heatmap biome-to-biome совместимости
    """
    # Получаем все типы биомов
    from services.world_data_service import WorldDataService
    wds = WorldDataService()
    all_biomes = wds.get_all_biomes()
    
    biome_ids = [b['id'] for b in all_biomes]
    n = len(biome_ids)
    
    # Создаём матрицу
    matrix = np.zeros((n, n))
    
    for i, biome1 in enumerate(all_biomes):
        tags1 = set(biome1.get('base_tags', []))
        
        for j, biome2 in enumerate(all_biomes):
            if i == j:
                matrix[i][j] = 1.0  # Сам с собой всегда совместим
                continue
            
            tags2 = set(biome2.get('base_tags', []))
            
            score = comp_service.calculate_biome_compatibility(
                tags1,
                [tags2]
            )
            
            matrix[i][j] = score.raw_score if score.is_compatible else 0.0
    
    # Визуализация
    plt.figure(figsize=(16, 14))
    sns.heatmap(
        matrix,
        xticklabels=biome_ids,
        yticklabels=biome_ids,
        annot=True,
        fmt='.2f',
        cmap='RdYlGn',
        center=1.0,
        vmin=0.0,
        vmax=3.0
    )
    plt.title("Biome-to-Biome Compatibility Matrix")
    plt.xlabel("Neighbor Biome")
    plt.ylabel("Candidate Biome")
    plt.tight_layout()
    plt.show()
```

---

#### 4.3 Создание тестового скрипта (3 часа)

```python
# tests/manual/test_hex_generation_manual.py

"""
Ручной тест генерации hex world с визуализацией.
Запускать: python -m tests.manual.test_hex_generation_manual
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from services.world_data_service import WorldDataService
from services.hex_world_service import HexWorldService
from services.compatibility_service import CompatibilityService
from services.tag_service import TagRegistry
from validators.world_gen_validator import validate_biome_placements, generate_biome_adjacency_report
from utils.world_gen_visualizer import visualize_hex_region, generate_compatibility_heatmap_for_biomes

def main():
    print("=== MANUAL HEX GENERATION TEST ===\n")
    
    # Инициализация
    wds = WorldDataService()
    rules = wds.get_generation_rules()
    comp_service = CompatibilityService(rules)
    tag_registry = TagRegistry(wds.get_tags_registry())
    
    hex_service = HexWorldService(
        session_id="manual_test",
        world_data_service=wds,
        tag_registry=tag_registry,
        compatibility_service=comp_service
    )
    
    print("1️⃣ Generating continent...")
    center_region_id = hex_service.generate_continent("silgarron", radius=2)
    print(f"✅ Continent generated. Center region: {center_region_id}")
    print(f"   Total regions: {len(hex_service.regions)}\n")
    
    print("2️⃣ Discovering center region...")
    biome_ids = hex_service.discover_region(center_region_id)
    print(f"✅ Region discovered. Biomes placed: {len(biome_ids)}")
    
    # Выводим метрики
    metrics = hex_service.placement_metrics
    print(f"\n📊 Placement Metrics:")
    print(f"   Total attempts: {metrics.total_attempts}")
    print(f"   Successful: {metrics.successful_placements}")
    print(f"   Fallback used: {metrics.fallback_used}")
    print(f"   Random fallback: {metrics.random_fallback_used}")
    print(f"\n   Biome distribution:")
    for biome_type, count in metrics.biome_type_distribution.items():
        print(f"     - {biome_type}: {count}")
    
    print("\n3️⃣ Validating placements...")
    issues = validate_biome_placements(hex_service)
    
    if issues:
        print(f"❌ Found {len(issues)} issues:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("✅ No forbidden combinations found!")
    
    print("\n4️⃣ Generating adjacency report...")
    report = generate_biome_adjacency_report(hex_service)
    print(report)
    
    print("\n5️⃣ Visualizing...")
    try:
        visualize_hex_region(hex_service, center_region_id)
        generate_compatibility_heatmap_for_biomes(comp_service)
    except Exception as e:
        print(f"⚠️ Visualization failed: {e}")
    
    print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    main()
```

---

### **ЗАДАЧА 5: Документация** (8 часов)

#### 5.1 Создать ADR-012: Biome Compatibility System (3 часа)

# ADR-012: Biome Compatibility System Design

**Дата:** 15 октября 2025  
**Статус:** ✅ Принято  
**Автор:** Development Team

## Контекст

При генерации hex-based мира нужна система, которая:
1. Предотвращает физически невозможные соседства (вода + подземелье)
2. Поощряет логичные переходы (стабильная земля + оседлая жизн
3. Поощряет логичные переходы (стабильная земля + оседлая жизнь)
4. Наказывает нелогичные сочетания (нестабильная земля + постройки)
5. Работает на основе данных из YAML (data-driven подход)

## Проблема

Текущая реализация `CompatibilityService`:
- ❌ Проверяет только race-to-biome совместимость
- ❌ Не проверяет biome-to-biome
- ❌ Не применяет forbidden_combinations из tags_registry.yaml
- ❌ Не использует synergies/conflicts для генерации

Результат: генерируются нелогичные миры (подводные пещеры рядом с подземными шахтами).

## Решение

### Архитектура
```
CompatibilityService (Refactored)
├── calculate_biome_compatibility()  ← НОВОЕ
│   ├── Проверка forbidden_combinations
│   ├── Базовый score = 1.0
│   ├── Применение synergies (multiply)
│   ├── Применение conflicts (multiply)
│   └── Возврат CompatibilityScore
│
├── find_best_biome_for_region()  ← НОВОЕ
│   ├── Для каждого candidate
│   ├── Рассчитать scores с соседями
│   ├── Агрегировать (average)
│   └── Вернуть best candidate
│
└── calculate_race_biome_score()  ← ОБНОВЛЕНО
    └── Теперь также использует synergies/conflicts
```

### Формула Совместимости
```
biome_compatibility_score = 
    base_score (1.0) 
    × synergy_multiplier₁ 
    × synergy_multiplier₂ 
    × ... 
    × conflict_multiplier₁ 
    × conflict_multiplier₂
    × ...

Если forbidden_combination найдена:
    score = 0.0
    is_compatible = False
```

### Источники Данных

1. **tags_registry.yaml:**
   - `global_compatibility_rules.synergies` - бонусы
   - `global_compatibility_rules.conflicts` - штрафы
   - `validation_rules.forbidden_combinations` - жёсткие блокировки

2. **data/biomes/*.yaml:**
   - `base_tags` - теги каждого биома

3. **generation_rules.yaml:**
   - `global_modifiers.race_terrain_affinity` - модификаторы для рас

### Пример Работы
```python
# Кандидат: Rolling Hills
candidate_tags = {'terrain:elevated', 'surface:stable', 'lifestyle:sedentary'}

# Соседи: Stable Plains
neighbor_tags = [{'surface:stable', 'ecology:moderate'}]

# Расчёт:
# 1. forbidden_combinations? Нет → продолжаем
# 2. base_score = 1.0
# 3. Synergy: stable + sedentary → bonus 2.0
# 4. Conflicts? Нет
# 5. final_score = 1.0 × 2.0 = 2.0 ✅

# Результат: Rolling Hills ОТЛИЧНО подходит!
```

## Альтернативы

### Альтернатива 1: Rule-based система без YAML
```python
if biome1 == "underwater" and biome2 == "cave":
    return False
```

**Отклонено:** Хардкод, сложно масштабировать, нужно перекомпилировать при изменениях.

### Альтернатива 2: ML-based подход
Обучить модель на примерах "хороших" миров.

**Отклонено:** Overkill для текущей задачи, требует большой датасет.

### Альтернатива 3: Noise-based генерация без compatibility
Использовать Perlin noise для плавных переходов.

**Отклонено:** Не решает проблему forbidden combinations, можно добавить позже.

## Последствия

### Плюсы
✅ **Data-driven:** Правила в YAML, легко изменять без кода  
✅ **Масштабируемость:** Добавление нового биома = добавление тегов  
✅ **Явная логика:** breakdown показывает, почему выбран биом  
✅ **Тестируемость:** Легко писать unit-тесты для каждого правила  
✅ **Переиспользование:** Та же система для race-biome и biome-biome  

### Минусы
❌ **Производительность:** O(n²) для больших регионов (кэш решает)  
❌ **Сложность YAML:** Дизайнерам нужно понимать систему тегов  
❌ **Возможны тупики:** Все кандидаты могут быть несовместимы (fallback решает)  

### Риски
⚠️ **Плохо настроенные правила:** Могут сделать генерацию слишком однообразной  
⚠️ **Кэш может занимать память:** Лимит в 1000 пар (config)  

## Метрики Успеха

- ✅ 0 forbidden combinations в сгенерированных регионах
- ✅ >70% биомов размещены через compatibility (не fallback)
- ✅ Разнообразие: каждый тип биома появляется в регионе не более 2 раз
- ✅ Все unit-тесты проходят (14+ тестов)

## Ссылки

- `services/compatibility_service.py` - реализация
- `tests/test_services/test_compatibility_service.py` - тесты
- `data/tags_registry.yaml` - правила
- `docs/sprints/SPRINT_HEX_GENERATION_PLAN.md` - детальный план
---

#### 5.2 Обновить docs/Technical_Design_Document.md (3 часа)

Добавить новый раздел:
### 5.3 CompatibilityService (Refactored v2.0)

**Статус:** ✅ Реализовано (Sprint: Hex Generation)  
**Файл:** `services/compatibility_service.py`

#### Назначение
Математическое ядро генерации мира. Отвечает на вопрос: 
"Насколько элемент A совместим с элементом B?"

#### API

```python
class CompatibilityService:
    def __init__(self, generation_rules: Dict):
        """
        Args:
            generation_rules: Данные из tags_registry.yaml и generation_rules.yaml
        """
    
    def calculate_biome_compatibility(
        self,
        candidate_tags: Set[str],
        neighbor_tags: List[Set[str]]
    ) -> CompatibilityScore:
        """
        Рассчитывает совместимость биома с соседями.
        
        Returns:
            CompatibilityScore(
                raw_score: float,
                level: CompatibilityLevel,
                breakdown: Dict[str, float],
                blocking_factors: List[str]
            )
        """
    
    def find_best_biome_for_region(
        self,
        allowed_biome_candidates: List[Dict],
        placed_neighbors_data: List[Dict]
    ) -> Optional[Dict]:
        """
        Выбирает наиболее совместимый биом из кандидатов.
        
        Returns:
            biome_data словарь с лучшим score, или None
        """
    
    def calculate_race_biome_score(
        self,
        race_data: Dict,
        biome_data: Dict
    ) -> CompatibilityScore:
        """
        Рассчитывает совместимость расы и биома.
        (Существующий метод, теперь использует synergies/conflicts)
        """
````

#### Алгоритм calculate_biome_compatibility()

```
1. Проверить forbidden_combinations
   └─ Если найдено → return score=0.0, is_compatible=False

2. Установить base_score = 1.0

3. Для каждого соседа:
   3.1. Проверить все synergy rules
        └─ Если теги совпадают → base_score *= bonus
   3.2. Проверить все conflict rules
        └─ Если теги совпадают → base_score *= penalty

4. return CompatibilityScore(raw_score=base_score, ...)
```

#### Интеграция с HexWorldService

```python
# services/hex_world_service.py
def discover_region(self, region_id: str) -> List[str]:
    # Для каждого гекса в регионе:
    for coord in biome_coords:
        placed_neighbors = [уже размещённые соседи]
        
        # ГЛАВНЫЙ ВЫЗОВ:
        best_biome = self.compatibility.find_best_biome_for_region(
            allowed_candidates,
            placed_neighbors
        )
        
        if best_biome:
            # Размещаем биом
            biome = self._create_biome(region, best_biome['id'], coord)
        else:
            # Fallback логика
```

#### Тестирование

**Файл:** `tests/test_services/test_compatibility_service.py`

```python
# 14 unit-тестов:
test_forbidden_combination_returns_incompatible()
test_synergy_increases_score()
test_conflict_decreases_score()
test_no_neighbors_returns_base_score()
test_multiple_synergies_stack()
test_synergy_and_conflict_both_apply()
test_find_best_biome_prefers_synergistic()
test_find_best_biome_all_incompatible_returns_none()
test_find_best_biome_no_neighbors_returns_random()
test_find_best_biome_no_candidates_returns_none()
test_find_best_biome_sorts_by_score()
test_integration_hex_world_uses_compatibility()
test_real_data_from_yaml()
test_caching_works()
```

#### Производительность

- **Кэширование:** Повторные проверки используют `_compatibility_cache`
- **Лимит кэша:** 1000 пар (config: `max_cached_compatibility_pairs`)
- **Сложность:** O(n × m) где n = candidates, m = neighbors
- **Оптимизация:** Early return при forbidden_combinations

#### Конфигурация

```yaml
# config/world_generation.yaml
performance:
  cache_compatibility_checks: true
  max_cached_compatibility_pairs: 1000

debug:
  log_compatibility_checks: false  # Включить для отладки
```

#### Метрики

```python
class BiomePlacementMetrics:
    total_attempts: int
    successful_placements: int
    fallback_used: int
    random_fallback_used: int
    average_compatibility_score: float
    biome_type_distribution: Dict[str, int]
```

#### Примеры Использования

См. `tests/manual/test_hex_generation_manual.py` для полного примера.

---

#### 5.3 Создать SPRINT_HEX_GENERATION_PLAN.md (2 часа)

**Файл:** `docs/sprints/SPRINT_HEX_GENERATION_PLAN.md`
# SPRINT: Hex Generation Refactoring & Compatibility System

**Дата начала:** 15 октября 2025  
**Дата окончания:** 29 октября 2025  
**Длительность:** 2 недели (80 часов)  
**Приоритет:** 🔴 КРИТИЧЕСКИЙ

---

## 🎯 ЦЕЛЬ СПРИНТА

Реализовать полноценную систему совместимости биомов для корректной hex-based генерации мира.

### Проблемы, Которые Решаем

1. ❌ `HexWorldService.discover_region()` вызывает несуществующий метод
2. ❌ Не проверяются forbidden_combinations
3. ❌ Не применяются synergies/conflicts из tags_registry.yaml
4. ❌ Нет тестов для CompatibilityService

### Definition of Done

- ✅ `CompatibilityService.find_best_biome_for_region()` реализован
- ✅ `CompatibilityService.calculate_biome_compatibility()` реализован
- ✅ Forbidden combinations проверяются
- ✅ Synergies/conflicts применяются
- ✅ 14+ unit-тестов проходят
- ✅ Integration тест с HexWorldService работает
- ✅ Validator подтверждает 0 forbidden combinations
- ✅ Документация обновлена (ADR-012, TDD)

---

## 📋 ЗАДАЧИ

### Неделя 1: Refactoring CompatibilityService

#### День 1-2: calculate_biome_compatibility() (8ч)
- [ ] Написать сигнатуру и docstring
- [ ] Реализовать проверку forbidden_combinations
- [ ] Реализовать применение synergies
- [ ] Реализовать применение conflicts
- [ ] Добавить логирование

**Deliverable:** Метод работает, проходит базовые проверки

---

#### День 3: find_best_biome_for_region() (6ч)
- [ ] Написать сигнатуру и docstring
- [ ] Реализовать алгоритм выбора лучшего кандидата
- [ ] Обработать edge cases (нет соседей, нет кандидатов)
- [ ] Добавить логирование

**Deliverable:** Метод работает, возвращает best biome

---

#### День 4: Обновление существующих методов (4ч)
- [ ] Обновить `calculate_race_biome_score()` для использования synergies
- [ ] Добавить кэширование
- [ ] Улучшить breakdown в CompatibilityScore

**Deliverable:** Все методы используют единую логику

---

#### День 5: Документация (2ч)
- [ ] Обновить docstrings
- [ ] Добавить примеры использования в комментариях
- [ ] Создать README для services/

**Deliverable:** Код хорошо документирован

---

### Неделя 2: Testing & Integration

#### День 6-7: Unit-тесты (15ч)
- [ ] Тесты для calculate_biome_compatibility() (7 тестов)
- [ ] Тесты для find_best_biome_for_region() (5 тестов)
- [ ] Integration тесты (2 теста)
- [ ] Все тесты проходят

**Deliverable:** 14+ тестов, 100% покрытие CompatibilityService

---

#### День 8-9: Обновление HexWorldService (10ч)
- [ ] Исправить вызов find_best_biome_for_region()
- [ ] Добавить fallback логику
- [ ] Улучшить логирование
- [ ] Добавить метрики (BiomePlacementMetrics)

**Deliverable:** HexWorldService корректно генерирует регионы

---

#### День 10: Валидация и Визуализация (12ч)
- [ ] Обновить validators/world_gen_validator.py
- [ ] Создать validate_biome_placements()
- [ ] Создать generate_biome_adjacency_report()
- [ ] Обновить utils/world_gen_visualizer.py
- [ ] Создать visualize_hex_region()
- [ ] Создать generate_compatibility_heatmap_for_biomes()
- [ ] Создать tests/manual/test_hex_generation_manual.py

**Deliverable:** Инструменты для анализа и отладки

---

#### День 11: Документация (8ч)
- [ ] Создать ADR-012: Biome Compatibility System
- [ ] Обновить Technical_Design_Document.md
- [ ] Создать этот файл (SPRINT_HEX_GENERATION_PLAN.md)
- [ ] Обновить CHANGELOG.md

**Deliverable:** Полная документация спринта

---

## 📊 РАСПРЕДЕЛЕНИЕ ВРЕМЕНИ

| Задача | Часы | % от спринта |
|--------|------|--------------|
| 1. Refactoring CompatibilityService | 20ч | 25% |
| 2. Unit-тесты | 15ч | 19% |
| 3. Обновление HexWorldService | 10ч | 13% |
| 4. Валидация и Визуализация | 12ч | 15% |
| 5. Документация | 8ч | 10% |
| **Буфер** | 15ч | 18% |
| **ИТОГО** | **80ч** | **100%** |

---

## 🔬 КЛЮЧЕВЫЕ ТЕСТЫ

### Тест 1: Forbidden Combination
```python
def test_forbidden_combination_returns_incompatible():
    candidate = {'terrain:aquatic'}
    neighbors = [{'terrain:subterranean'}]
    
    score = service.calculate_biome_compatibility(candidate, neighbors)
    
    assert score.is_compatible == False
    assert score.raw_score == 0.0
````

### Тест 2: Synergy Application

```python
def test_synergy_increases_score():
    candidate = {'surface:stable', 'lifestyle:sedentary'}
    neighbors = [{'surface:stable'}]
    
    score = service.calculate_biome_compatibility(candidate, neighbors)
    
    assert score.raw_score == pytest.approx(2.0)  # bonus 2.0
```

### Тест 3: Best Biome Selection

```python
def test_find_best_biome_prefers_synergistic():
    candidates = [hills_data, geyser_data]
    neighbors = [stable_plains_data]
    
    best = service.find_best_biome_for_region(candidates, neighbors)
    
    assert best['id'] == 'rolling_hills'  # Synergy с stable
```

### Тест 4: Integration

```python
def test_integration_hex_world_uses_compatibility():
    hex_service = HexWorldService(...)
    center_region_id = hex_service.generate_continent("silgarron", radius=1)
    biome_ids = hex_service.discover_region(center_region_id)
    
    # Проверяем, что нет forbidden combinations
    validator.validate_biome_placements(hex_service)
    assert len(issues) == 0
```

---

## 📈 МЕТРИКИ УСПЕХА

### Количественные

- ✅ 14+ unit-тестов проходят
- ✅ >95% code coverage для CompatibilityService
- ✅ 0 forbidden combinations в тестовых регионах
- ✅ >70% биомов размещены через compatibility (не fallback)

### Качественные

- ✅ Код читаем и хорошо документирован
- ✅ Легко добавлять новые правила в YAML
- ✅ Визуализация показывает логичные миры
- ✅ Дизайнеры могут настраивать генерацию без программистов

---

## 🚧 РИСКИ И МИТИГАЦИЯ

### Риск 1: Производительность O(n²)

**Вероятность:** Средняя  
**Влияние:** Среднее  
**Митигация:** Кэширование результатов, лимит в 1000 пар

### Риск 2: Все кандидаты несовместимы

**Вероятность:** Низкая  
**Влияние:** Высокое  
**Митигация:** 3-уровневая fallback стратегия:

1. Compatibility-based
2. No forbidden only
3. Random selection

### Риск 3: Плохо настроенные правила в YAML

**Вероятность:** Средняя  
**Влияние:** Среднее  
**Митигация:** Validators и heatmap visualization для анализа

---

## 📚 ССЫЛКИ

- [ADR-012: Biome Compatibility System](https://claude.ai/ARCHITECTURE_DECISION.md#adr-012)
- [Technical Design Document](https://claude.ai/Technical_Design_Document.md#53-compatibilityservice)
- [tags_registry.yaml](https://claude.ai/data/tags_registry.yaml)
- [generation_rules.yaml](https://claude.ai/data/generation_rules.yaml)

---

## 🎉 ПОСЛЕ СПРИНТА

После успешного завершения этого спринта:

1. **Следующий спринт:** Noise-based Generation (опционально)
2. **Возможные улучшения:**
    - Smooth transitions (gradual changes между биомами)
    - Historical context влияет на POI placement
    - Dynamic weather system
3. **Готовность к:** Full world generation pipeline

---

**Версия:** 1.0  
**Последнее обновление:** 15 октября 2025  
**Статус:** 🟢 Активный спринт

## 📊 ИТОГОВЫЙ ЧЕКЛИСТ СПРИНТА

# Чеклист Выполнения

## ✅ ЗАДАЧА 1: Refactoring CompatibilityService (20ч)
- [ ] 1.1 calculate_biome_compatibility() реализован (8ч)
- [ ] 1.2 find_best_biome_for_region() реализован (6ч)
- [ ] 1.3 calculate_race_biome_score() обновлён (4ч)
- [ ] 1.4 Документация и логирование (2ч)

## ✅ ЗАДАЧА 2: Unit-тесты (15ч)
- [ ] 2.1 Тесты для calculate_biome_compatibility() (7ч)
  - [ ] test_forbidden_combination_returns_incompatible
  - [ ] test_synergy_increases_score
  - [ ] test_conflict_decreases_score
  - [ ] test_no_neighbors_returns_base_score
  - [ ] test_multiple_synergies_stack
  - [ ] test_synergy_and_conflict_both_apply
- [ ] 2.2 Тесты для find_best_biome_for_region() (5ч)
  - [ ] test_find_best_biome_prefers_synergistic
  - [ ] test_find_best_biome_all_incompatible_returns_none
  - [ ] test_find_best_biome_no_neighbors_returns_random
  - [ ] test_find_best_biome_no_candidates_returns_none
  - [ ] test_find_best_biome_sorts_by_score
- [ ] 2.3 Integration тесты (3ч)
  - [ ] test_integration_hex_world_uses_compatibility
  - [ ] test_real_data_from_yaml
  - [ ] test_caching_works

## ✅ ЗАДАЧА 3: Обновление HexWorldService (10ч)
- [ ] 3.1 Исправление вызова find_best_biome_for_region (3ч)
- [ ] 3.2 Fallback логика (4ч)
- [ ] 3.3 Логирование (2ч)
- [ ] 3.4 Метрики (1ч)

## ✅ ЗАДАЧА 4: Валидация и Визуализация (12ч)
- [ ] 4.1 validate_biome_placements() (4ч)
- [ ] 4.2 Визуализация (5ч)
- [ ] 4.3 Тестовый скрипт (3ч)

## ✅ ЗАДАЧА 5: Документация (8ч)
- [ ] 5.1 ADR-012 (3ч)
- [ ] 5.2 Technical_Design_Document.md (3ч)
- [ ] 5.3 SPRINT_HEX_GENERATION_PLAN.md (2ч)

## 🎯 КРИТЕРИИ ГОТОВНОСТИ
- [ ] Все 14+ тестов проходят
- [ ] HexWorldService генерирует регионы без ошибок
- [ ] Validator не находит forbidden combinations
- [ ] Heatmap показывает логичные паттерны
- [ ] Документация полная и актуальная

---

## 🎯 ЗАКЛЮЧЕНИЕ

Этот план представляет собой **детальную дорожную карту** для реализации системы совместимости биомов. Основные преимущества подхода:

1. **Data-Driven:** Все правила в YAML, легко менять
2. **Тестируемость:** 14+ unit-тестов покрывают все сценарии
3. **Масштабируемость:** Добавление нового биома = добавление тегов
4. **Отладка:** Validators и visualizers для анализа
5. **Документированность:** ADR, TDD, план спринта

**Следующие шаги после завершения:**

- Sprint: Noise-based Generation (процедурные карты)
- Sprint: POI Placement System (точки интереса)
- Sprint: World Simulation (живой мир)