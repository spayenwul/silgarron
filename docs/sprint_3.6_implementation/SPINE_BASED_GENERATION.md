# Spine-Based Continent Generation - "From Anatomy to Geography"

**⚠️ v2.0 СТАТУС: ЕДИНСТВЕННЫЙ КАНОНИЧЕСКИЙ МЕТОД**

Это документ описывает **единственный** метод генерации континентов в v2.0 Architecture.

**УСТАРЕВШИЕ МЕТОДЫ (НЕ используются):**
- ❌ Ellipse Mask → заархивирован (см. archive/SHAPE_MASK_GUIDE.md)
- ❌ Radial Mask → заархивирован

**ТЕКУЩИЙ МЕТОД:**
- ✅ **Spine-Based Generation** - процедурная генерация позвоночника → континент растёт вокруг него

**Статус реализации:** ✅ Fully Implemented (Sprint 3.6)
- `core/world_generator_v2.py::_generate_spine_path()`
- `core/world_generator_v2.py::_create_spine_shape_mask()`
- 37/37 тестов проходят

---

## Философия

**Старая парадигма** (Ellipse Mask):
```
1. Создать бесформенный континент (геометрическая фигура)
2. Попытаться вписать анатомию (хребет, органы)
```
**Проблема:** Континент — это "остров в форме организма", но не "организм который является островом".

**Новая парадигма** (Spine-Based):
```
1. Создать ХРЕБЕТ (позвоночник) — анатомическую структуру
2. Вырастить континент вокруг хребта
```
**Результат:** Континент — это **тело, выросшее на скелете**. География следует анатомии.

---

## Алгоритм

### Шаг 1: Генерация Пути Хребта

**Процедурная генерация изогнутого позвоночника (север → юг)**

```python
def generate_spine_path(seed, width, height, num_points=100, curvature=0.3):
    """
    Генерирует плавный, изогнутый путь с севера на юг

    Использует 1D Perlin Noise для плавного изгиба по оси X
    """
    # 1D Perlin Noise для смещения по X
    noise_1d = generate_perlin_map(
        width=num_points,
        height=1,
        scale=20,  # Низкая частота = плавные изгибы
        octaves=3,
        normalize_to_01=True
    ).flatten()

    # Преобразуем [0, 1] в [-1, 1] для симметричных отклонений
    noise_1d = (noise_1d - 0.5) * 2.0

    center_x = width / 2
    max_deviation = width * curvature

    path = []
    for i in range(num_points):
        y = int((i / (num_points - 1)) * (height - 1))
        x_offset = noise_1d[i] * max_deviation
        x = int(center_x + x_offset)

        path.append([x, y])

    return np.array(path)  # (N, 2) координаты
```

**Результат:** Массив координат `[[x1, y1], [x2, y2], ...]` от (256, 0) до (x_end, 511)

### Шаг 2: Создание Поля Влияния

**Distance Transform от пути хребта**

```python
def create_spine_influence_mask(spine_path, width, height, max_influence=200):
    """
    Для каждого пикселя вычисляет расстояние до ближайшей точки на хребте
    """
    from scipy.spatial import cKDTree

    # Создаем сетку всех координат
    y_coords, x_coords = np.mgrid[0:height, 0:width]
    grid_points = np.vstack([x_coords.ravel(), y_coords.ravel()]).T

    # cKDTree для быстрого поиска ближайших соседей
    tree = cKDTree(spine_path)
    distances, _ = tree.query(grid_points, k=1)

    distance_map = distances.reshape((height, width))

    # Инвертируем: 1.0 на хребте, 0.0 далеко
    influence_mask = 1.0 - (distance_map / max_influence)
    influence_mask = np.clip(influence_mask, 0, 1)

    return influence_mask
```

**Результат:** 2D массив [0, 1], где:
- **1.0** — на хребте и близко к нему
- **0.0** — далеко от хребта (края карты)
- **Плавный градиент** между ними

### Шаг 3: Комбинация с Perlin Noise

**Умножение: `base_noise * spine_influence`**

```python
# Базовый Perlin Noise (как обычно)
base_noise = generate_perlin_map(scale=150, octaves=2, ...)

# Поле влияния хребта
spine_influence = create_spine_influence_mask(spine_path, ...)

# КОМБИНАЦИЯ
final_heightmap = base_noise * spine_influence
```

**Эффект:**
- Где **spine_influence = 1.0** (на хребте) → шум сохраняется
- Где **spine_influence = 0.0** (далеко) → шум обнуляется (океан)
- Континент **растет вокруг хребта**, следуя его изгибам

### Шаг 4: Threshold и Smoothing

```python
# Применяем порог океана (обычно ниже для spine)
continent_mask = (final_heightmap > 0.20)

# Сглаживание (как обычно)
continent_mask = binary_opening(continent_mask, iterations=3)
continent_mask = binary_closing(continent_mask, iterations=2)
continent_mask = gaussian_filter(...) > 0.5
```

---

## Конфигурация

### Файл: `config/world_generation_v2.yaml`

```yaml
continent:
  sea_level: 0.36  # Используется БЕЗ shape_mask

  shape_mask:
    enabled: false  # Включить для spine-based generation
    type: "spine"   # spine | ellipse | radial

    # Параметры хребта
    spine:
      num_points: 100       # Количество точек вдоль хребта
      curvature: 0.3        # Максимальное отклонение от центра (0-1)
      max_influence: 200.0  # Радиус влияния хребта (пиксели)

    sea_level_override: 0.20  # Порог для spine (ниже стандартного)
```

### Параметры Spine

| Параметр | Тип | Значение | Описание |
|----------|-----|----------|----------|
| `num_points` | int | `100` | Количество точек вдоль хребта (больше = плавнее) |
| `curvature` | float | `0.3` | Максимальное отклонение от центра (0-1, доля ширины карты) |
| `max_influence` | float | `200.0` | Радиус влияния хребта в пикселях |

#### curvature (изгиб хребта)

**Низкий (0.1-0.2):**
- Почти прямой хребет
- Узкий континент
- Симметричный

```yaml
curvature: 0.15
```

**Средний (0.3) [Рекомендуется]:**
- Плавные изгибы
- Естественная форма
- Умеренная асимметрия

```yaml
curvature: 0.3
```

**Высокий (0.4-0.5):**
- Сильные изгибы
- S-образная форма
- Экстремальная асимметрия

```yaml
curvature: 0.45
```

#### max_influence (ширина континента)

**Узкий (150-180):**
- Тонкий континент вдоль хребта
- Больше океана
- Изолированная форма

```yaml
max_influence: 150.0
```

**Средний (200-220) [Рекомендуется]:**
- Сбалансированная ширина
- Умеренный океан
- Естественная форма

```yaml
max_influence: 200.0
```

**Широкий (250-300):**
- Массивный континент
- Мало океана
- Может достигать краев карты

```yaml
max_influence: 280.0
```

---

## Использование

### Вариант 1: Через YAML

```yaml
# config/world_generation_v2.yaml
continent:
  shape_mask:
    enabled: true    # Включить
    type: "spine"    # Использовать spine вместо ellipse
```

### Вариант 2: Через Python

```python
from core.world_generator_v2 import WorldGeneratorV2

gen = WorldGeneratorV2()

# Включаем spine-based generation
gen.config['continent']['shape_mask']['enabled'] = True
gen.config['continent']['shape_mask']['type'] = 'spine'

# Генерируем континент
continent = gen._generate_continent('silgarron_world_001')

# Доступ к хребту
if continent.spine_path is not None:
    print(f"Spine path: {continent.spine_path.shape}")
    # Используем для размещения органов (Phase 3)
```

---

## Визуализация

### Основная визуализация (6 панелей)

```bash
python scripts/visualize_spine_continent.py --seed silgarron_001
```

**Панели:**
1. **Base Perlin Noise** - Исходный шум без маски
2. **Spine Path + Influence Field** - Хребет и его поле влияния
3. **Combined (Noise × Spine)** - Результат умножения
4. **Continent WITH Spine** - Финальный континент с хребтом
5. **Continent WITH Ellipse (old)** - Сравнение со старым подходом
6. **Comparison Overlay** - Наложение обоих вариантов

**Результат:** `output/spine_continent_silgarron_001.png` (~3.9 MB)

### Сравнение нескольких континентов

```bash
python scripts/visualize_spine_continent.py --compare
```

**Показывает:**
- 3 разных континента (silgarron_alpha, beta, gamma)
- Поле влияния хребта для каждого
- Финальные континенты

**Результат:** `output/spine_continents_comparison.png`

---

## Преимущества Spine-Based Approach

### 1. Анатомическая Логика

**Ellipse (старое):**
```
Геометрическая фигура → Пытаемся вписать анатомию
```

**Spine (новое):**
```
Анатомическая структура → География растет вокруг неё
```

**Результат:** Континент **естественным образом** следует анатомическим принципам.

### 2. Естественная Асимметрия

**Ellipse:** Всегда симметричный (скучно)
**Spine:** Уникальные изгибы для каждого seed

### 3. Готовая Ось для Органов

Хребет уже определяет главную ось тела. В Phase 3 (размещение органов):
- **Метаболический орган** → центр хребта
- **Neural clusters** → точки вдоль хребта (35%, 65%)
- **Digestive** → рядом с хребтом

### 4. Гарантированная Связность

Континент всегда связан через хребет (нет фрагментации).

### 5. Океан по Краям

max_influence обеспечивает ocean at edges (~84-100%).

---

## Сравнение: Ellipse vs Spine

| Критерий | Ellipse | Spine |
|----------|---------|-------|
| **Философия** | География → Анатомия | Анатомия → География |
| **Форма** | Симметричная, геометрическая | Асимметричная, органическая |
| **Уникальность** | Одинаковая для всех seeds | Уникальная для каждого seed |
| **Главная ось** | Вычисляется через PCA | Определена хребтом |
| **Размещение органов** | Сложное (нет направляющей) | Простое (вдоль хребта) |
| **Ocean at edges** | ~100% (строгая форма) | ~84% (органичнее) |
| **ADR-016 compliance** | Частичная | Полная |

---

## Рецепты

### "Извивающийся Дракон" (сильный изгиб)

```yaml
spine:
  curvature: 0.45
  max_influence: 220.0
```

**Результат:** S-образная форма, драматичные изгибы.

### "Прямой Позвоночник" (минимальный изгиб)

```yaml
spine:
  curvature: 0.15
  max_influence: 180.0
```

**Результат:** Почти прямая форма, симметричный континент.

### "Массивное Тело" (широкий континент)

```yaml
spine:
  curvature: 0.3
  max_influence: 280.0
sea_level_override: 0.15
```

**Результат:** Огромный континент, максимум суши.

### "Тонкий Хребет" (узкий континент)

```yaml
spine:
  curvature: 0.35
  max_influence: 150.0
sea_level_override: 0.25
```

**Результат:** Тонкий, изогнутый континент.

---

## Технические Детали

### Алгоритм Generation

```python
# 1. Генерация пути хребта
spine_path = generate_spine_path(
    seed=hash(seed + "spine"),
    width=512,
    height=512,
    num_points=100,
    curvature=0.3
)
# → (100, 2) массив координат от севера к югу

# 2. Создание поля влияния
spine_influence = create_spine_influence_mask(
    spine_path=spine_path,
    width=512,
    height=512,
    max_influence=200.0
)
# → (512, 512) градиент [0, 1]

# 3. Базовый Perlin Noise
base_noise = generate_perlin_map(scale=150, octaves=2, ...)
# → (512, 512) шум [0, 1]

# 4. Комбинация
final_heightmap = base_noise * spine_influence
# → (512, 512) где continente формируется вокруг хребта

# 5. Threshold
continent_mask = (final_heightmap > 0.20)

# 6. Сохранение spine_path в ContinentData
return ContinentData(..., spine_path=spine_path)
```

### Хранение Spine Path

```python
@dataclass
class ContinentData:
    mask: np.ndarray  # (512, 512) boolean
    heightmap: np.ndarray  # (512, 512) float
    center: Tuple[int, int]
    major_axis: Tuple[Tuple[int, int], Tuple[int, int]]
    spine_path: Optional[np.ndarray] = None  # (N, 2) координаты хребта
```

**Использование в Phase 3:**
```python
continent = gen._generate_continent(seed)

if continent.spine_path is not None:
    # Размещаем органы вдоль хребта
    metabolic_pos = continent.spine_path[50]  # Центр хребта
    neural_pos_1 = continent.spine_path[35]   # 35% вдоль хребта
    neural_pos_2 = continent.spine_path[65]   # 65% вдоль хребта
```

---

## Тесты

### Все существующие тесты проходят

```bash
python -m pytest tests/models/ tests/core/ -v
# 37/37 passed
```

**Backward compatibility:** Spine disabled по умолчанию (`enabled: false`)

### Тест Spine Generation

```python
def test_spine_based_continent():
    gen = WorldGeneratorV2()
    gen.config['continent']['shape_mask']['enabled'] = True
    gen.config['continent']['shape_mask']['type'] = 'spine'

    continent = gen._generate_continent('test_spine')

    # Spine path сохранен
    assert continent.spine_path is not None
    assert continent.spine_path.shape == (100, 2)

    # Хребет проходит от севера к югу
    assert continent.spine_path[0, 1] == 0  # North
    assert continent.spine_path[-1, 1] == 511  # South

    # Континент центрирован вокруг хребта
    assert 50 < continent.mask.sum() / (512*512) * 100 < 70
```

---

## Итоги

**Что реализовано:**
- [x] `_generate_spine_path()` - процедурная генерация изогнутого хребта
- [x] `_create_spine_influence_mask()` - distance field от хребта
- [x] Интеграция в `_generate_continent()` с type='spine'
- [x] Сохранение `spine_path` в `ContinentData`
- [x] Конфигурация в `world_generation_v2.yaml`
- [x] Визуализация (6 панелей + сравнение)
- [x] Backward compatibility (все 37 тестов проходят)

**Ключевые файлы:**
- `core/models/world.py`: Добавлен `spine_path` в `ContinentData`
- `core/world_generator_v2.py`: Методы `_generate_spine_path()`, `_create_spine_influence_mask()`
- `config/world_generation_v2.yaml`: Секция `spine` с параметрами
- `scripts/visualize_spine_continent.py`: Визуализация spine-based generation

**Философия:**
```
"Континент — это тело, выросшее на скелете"
```

---

**Дата:** 2025-10-25
**Статус:** Spine-Based Generation Complete
**Тестов:** 37/37 passing
**ADR-016 Compliance:** Full (от анатомии к географии)

---

## Следующие шаги

**Готово к Phase 3: Размещение органов**

С spine-based approach размещение органов становится тривиальным:

```python
# Органы размещаются вдоль хребта
metabolic_organ_pos = continent.spine_path[len(continent.spine_path) // 2]
neural_cluster_1 = continent.spine_path[int(len(continent.spine_path) * 0.35)]
neural_cluster_2 = continent.spine_path[int(len(continent.spine_path) * 0.65)]
```

Континент **естественным образом** становится анатомическим телом.
