# Быстрый старт - Sprint 3.6 (Обновлено)

## Что было создано

### Phase 1: Модели данных и конфигурация
- `core/models/world.py` - Organ, Region, ContinentData (+ spine_path), World
- `services/world_config_v2.py` - WorldGenerationConfigV2
- 18 unit-тестов для моделей

### Phase 2: Генерация континента с Perlin Noise
- `core/world_generator_v2.py` - WorldGeneratorV2 с методами генерации
- `core/perlin_noise.py` - Perlin Noise алгоритм
- 15 unit-тестов для генерации континента

### Phase 2.5: Shape Mask (Ellipse/Radial)
- Маски формы для центрирования континентов
- Эллиптические и круглые градиенты

### Phase 2.6: **Spine-Based Generation** (НОВОЕ!)
- `_generate_spine_path()` - процедурная генерация хребта
- `_create_spine_influence_mask()` - поле влияния вокруг хребта
- **Философия:** "От анатомии к географии" - континент растет вокруг позвоночника

---

## Как запустить

### 1. Визуализация стандартной генерации

```bash
# Стандартная генерация (pure Perlin Noise)
python scripts/visualize_continent.py --seed silgarron_alpha_01
```

**Результат:** `output/continent_silgarron_alpha_01.png`

**Показывает:**
- Perlin Noise heightmap
- Continent mask (суша vs океан)
- Land elevation (только суша)
- Geometry (центр масс + главная ось через PCA)

---

### 2. Визуализация spine-based генерации ⭐

```bash
# Генерация на основе хребта (anatomy → geography)
python scripts/visualize_continent.py --seed silgarron_alpha_01 --spine
```

**Результат:** `output/continent_silgarron_alpha_01_spine.png`

**Показывает:**
- Heightmap с наложенным spine path (красная линия)
- Continent mask с spine path (север = круг, юг = квадрат)
- Land elevation с хребтом
- Geometry: spine path + центр масс + ось PCA

**Что такое spine path?**
- Процедурно сгенерированный изогнутый "позвоночник" (север → юг)
- Континент **растет вокруг хребта** через поле влияния
- В Phase 3 органы будут размещаться вдоль этого хребта

---

### 3. Сравнение нескольких seeds

```bash
# Стандартная генерация
python scripts/visualize_continent.py --compare seed_A seed_B seed_C

# Spine-based генерация
python scripts/visualize_continent.py --compare seed_A seed_B seed_C --spine
```

**Результат:**
- `output/continent_comparison.png` (стандартная)
- `output/continent_comparison_spine.png` (со spine)

---

### 4. Сравнение режимов (Standard vs Spine) ⭐

```bash
# Сравнение двух подходов для одного seed
python scripts/visualize_continent.py --seed my_seed --compare-modes
```

**Результат:** `output/continent_mode_comparison_my_seed.png`

**Показывает:**
- **Слева:** Standard (чистый Perlin Noise)
- **Справа:** Spine-Based (Noise × Spine Influence)

**Визуально демонстрирует** разницу между "географией" и "анатомией → географии".

---

### 5. Детальная визуализация spine (6 панелей)

```bash
# Полная демонстрация spine-based подхода
python scripts/visualize_spine_continent.py --seed silgarron_world_001
```

**Результат:** `output/spine_continent_silgarron_world_001.png` (~3.9 MB)

**Панели:**
1. Base Perlin Noise (без маски)
2. Spine Path + Influence Field (хребет и его поле влияния)
3. Combined (Noise × Spine) - результат умножения
4. Continent WITH Spine - финальный континент
5. Continent WITH Ellipse (old) - старый подход
6. Comparison Overlay - наложение обоих

---

### 6. Сравнение типов масок

```bash
# Сравнение ellipse и radial масок
python scripts/visualize_shape_mask.py --compare-types

# Сравнение нескольких spine континентов
python scripts/visualize_spine_continent.py --compare
```

---

## Параметры конфигурации

### Файл: `config/world_generation_v2.yaml`

```yaml
continent:
  perlin_noise:
    scale: 150  # Низкая частота для плавных континентов
    octaves: 2  # Умеренная детализация
    persistence: 0.6
    lacunarity: 2.0

  sea_level: 0.36  # Используется БЕЗ shape mask

  # Маска формы (центрирование континента)
  shape_mask:
    enabled: false  # true = включить spine-based generation
    type: "spine"   # spine | ellipse | radial

    # Параметры для spine
    spine:
      num_points: 100       # Количество точек вдоль хребта
      curvature: 0.3        # Изгиб хребта (0-1)
      max_influence: 200.0  # Радиус влияния (пиксели)

    sea_level_override: 0.20  # Порог для spine (ниже стандартного)
```

---

## Изменение конфигурации

### Через Python API

```python
from core.world_generator_v2 import WorldGeneratorV2

gen = WorldGeneratorV2()

# Включаем spine-based generation
gen.config['continent']['shape_mask']['enabled'] = True
gen.config['continent']['shape_mask']['type'] = 'spine'

# Настраиваем параметры хребта
gen.config['continent']['shape_mask']['spine']['curvature'] = 0.4  # Сильнее изгиб
gen.config['continent']['shape_mask']['spine']['max_influence'] = 250.0  # Шире континент

# Генерируем
continent = gen._generate_continent('my_seed')

# Доступ к хребту
if continent.spine_path is not None:
    print(f"Spine: {continent.spine_path.shape[0]} точек")
    print(f"North: {continent.spine_path[0]}")
    print(f"South: {continent.spine_path[-1]}")
```

### Через YAML

Откройте `config/world_generation_v2.yaml` и измените:

```yaml
shape_mask:
  enabled: true   # Было false
  type: "spine"   # spine | ellipse | radial
```

---

## Тестирование

### Все тесты (37 штук)

```bash
python -m pytest tests/models/ tests/core/ -v
```

**Результат:** ✅ 37/37 passed

### Тесты моделей

```bash
python -m pytest tests/models/test_world.py -v
# 18 passed
```

### Тесты генерации континента

```bash
python -m pytest tests/core/test_continent_generation.py -v
# 15 passed
```

### Тесты генератора v2

```bash
python -m pytest tests/core/test_world_generator_v2.py -v
# 4 passed
```

---

## Параметры Spine (Рецепты)

### "Прямой позвоночник" (минимальный изгиб)

```yaml
spine:
  curvature: 0.15
  max_influence: 180.0
```

**Результат:** Почти прямой континент, симметричный.

### "Средний изгиб" (рекомендуется)

```yaml
spine:
  curvature: 0.3
  max_influence: 200.0
```

**Результат:** Естественные плавные изгибы.

### "Извивающийся дракон" (сильный изгиб)

```yaml
spine:
  curvature: 0.45
  max_influence: 220.0
```

**Результат:** S-образная форма, драматичные изгибы.

### "Массивное тело" (широкий континент)

```yaml
spine:
  curvature: 0.3
  max_influence: 280.0
sea_level_override: 0.15
```

**Результат:** Огромный континент, максимум суши.

### "Тонкий хребет" (узкий континент)

```yaml
spine:
  curvature: 0.35
  max_influence: 150.0
sea_level_override: 0.25
```

**Результат:** Тонкий, изогнутый континент.

---

## Команды для тюнинга параметров

### Тюнинг одного параметра

```bash
# Эксперимент с scale
python scripts/tune_continent_parameters.py --param scale

# Эксперимент с sea_level
python scripts/tune_continent_parameters.py --param sea_level

# Эксперимент с octaves
python scripts/tune_continent_parameters.py --param octaves
```

### Полный grid search

```bash
# Поиск оптимальных параметров (scale × sea_level)
python scripts/tune_continent_parameters.py --full-grid
```

**Результат:** `output/tuning_grid_search.png` (707 KB)

**Лучшие найденные параметры:**
- `scale: 150`
- `sea_level: 0.36`
- Суша: ~70-80%
- Острова: 1-2

---

## Структура файлов

```
neuro_rpg/
├── config/
│   └── world_generation_v2.yaml  # Конфигурация (ОБНОВЛЕНО: + spine)
│
├── core/
│   ├── models/
│   │   └── world.py  # Модели (ОБНОВЛЕНО: + spine_path)
│   ├── world_generator_v2.py  # Генератор (ОБНОВЛЕНО: + spine methods)
│   └── perlin_noise.py  # Perlin Noise
│
├── services/
│   └── world_config_v2.py  # Менеджер конфигов
│
├── scripts/
│   ├── visualize_continent.py  # Основной визуализатор (ОБНОВЛЕНО!)
│   ├── visualize_spine_continent.py  # Spine-специфик визуализация (НОВОЕ!)
│   ├── visualize_shape_mask.py  # Shape mask эффекты
│   └── tune_continent_parameters.py  # Тюнинг параметров
│
├── tests/
│   ├── models/
│   │   └── test_world.py  # 18 тестов
│   └── core/
│       ├── test_world_generator_v2.py  # 4 теста
│       └── test_continent_generation.py  # 15 тестов
│
├── output/  # Визуализации сохраняются сюда
│
└── docs/
    └── sprint_3.6_implementation/
        ├── SPRINT_3.6_PLAN.md  # Полный план
        ├── QUICKSTART_UPDATED.md  # Этот файл
        ├── SPINE_BASED_GENERATION.md  # Документация spine (НОВОЕ!)
        ├── SHAPE_MASK_GUIDE.md  # Руководство по shape mask
        ├── PARAMETER_TUNING.md  # Тюнинг параметров
        └── PHASE2_RESULTS.md  # Результаты Phase 2
```

---

## Философия Spine-Based Approach

### Старая парадигма (Ellipse Mask):
```
1. Создать бесформенный континент (геометрия)
2. Попытаться вписать анатомию (хребет, органы)
```

**Проблема:** Континент = "остров в форме организма"

### Новая парадигма (Spine-Based):
```
1. Создать ХРЕБЕТ (позвоночник) - анатомическая структура
2. Вырастить континент вокруг хребта
```

**Результат:** Континент = "тело, выросшее на скелете" ✨

**ADR-016 Compliance:** Полная - от анатомии к географии!

---

## Готово к Phase 3

**Phase 2 Complete:** ✅ Континент готов
**Spine Path Ready:** ✅ Хребет сгенерирован
**Next Step:** Phase 3 - Размещение органов вдоль хребта

```python
# Phase 3 Preview: Размещение органов
continent = gen._generate_continent('my_seed')

if continent.spine_path is not None:
    # Метаболический орган в центре хребта
    metabolic_pos = continent.spine_path[50]

    # Neural clusters вдоль хребта
    neural_1 = continent.spine_path[35]  # 35% вдоль позвоночника
    neural_2 = continent.spine_path[65]  # 65% вдоль позвоночника

    # Digestive рядом с хребтом
    # ...
```

---

## FAQ

### Q: Spine-based generation включен по умолчанию?

**A:** Нет. По умолчанию `enabled: false` для обратной совместимости. Включайте через `--spine` флаг или конфигурацию.

### Q: Можно ли использовать старый ellipse подход?

**A:** Да. Установите `type: "ellipse"` в конфигурации. Spine, ellipse и radial все поддерживаются.

### Q: Почему sea_level_override ниже стандартного?

**A:** Умножение на spine влияние уменьшает значения heightmap. Более низкий порог компенсирует это.

### Q: Как визуализировать разницу между подходами?

**A:** Используйте `--compare-modes`:
```bash
python scripts/visualize_continent.py --seed my_seed --compare-modes
```

### Q: Spine path доступен только со spine mask?

**A:** Да. Если `shape_mask.enabled = false` или `type != "spine"`, то `continent.spine_path = None`.

---

## Команды Cheat Sheet

```bash
# === Основное ===
# Стандартная визуализация
python scripts/visualize_continent.py --seed my_seed

# Spine-based визуализация
python scripts/visualize_continent.py --seed my_seed --spine

# Сравнение режимов
python scripts/visualize_continent.py --seed my_seed --compare-modes

# === Сравнение seeds ===
# Стандартный
python scripts/visualize_continent.py --compare seed_A seed_B seed_C

# Со spine
python scripts/visualize_continent.py --compare seed_A seed_B seed_C --spine

# === Детальная spine визуализация ===
# 6 панелей (полная демонстрация)
python scripts/visualize_spine_continent.py --seed my_seed

# Сравнение нескольких spine континентов
python scripts/visualize_spine_continent.py --compare

# === Тесты ===
# Все тесты
python -m pytest tests/models/ tests/core/ -v

# Быстрая проверка
python -m pytest tests/models/ tests/core/ -q

# === Тюнинг ===
# Grid search оптимизация
python scripts/tune_continent_parameters.py --full-grid

# Тюнинг одного параметра
python scripts/tune_continent_parameters.py --param scale
```

---

**Дата:** 2025-10-25
**Статус:** Phase 2 Complete + Spine-Based Generation ✅
**Тестов:** 37/37 passing
**Философия:** "От анатомии к географии" 🦴 → 🌍
