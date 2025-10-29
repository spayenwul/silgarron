# Инструменты по этапам генерации

**Категория:** Инструменты на каждом этапе
**Версия:** 2.0 (v2.0 Architecture Migration)
**Дата:** 28 октября 2025

**⚠️ v2.0 ОБНОВЛЕНИЕ:**
- **Spine-Based Generation** теперь ЕДИНСТВЕННЫЙ канонический метод
- Shape Mask генерируется из spine (не Ellipse/Radial!)
- Phase 0.5 → Phase 1a (Spine) + Phase 1b (Continent)
- Все инструменты работают с 512×512 картами (Stage 0)

---

## Обзор

Этот документ описывает **инструменты и алгоритмы**, которые используются на каждом этапе генерации мира Сильгаррон. Каждый инструмент придаёт форму этапу согласно видению.

---

## Phase 1: Инструменты генерации Spine + Continent

### 0. Spine Path Generator ✅ NEW in v2.0

**Назначение:** Создание структурного каркаса континента (позвоночник)

**Метод:** ЕДИНСТВЕННЫЙ КАНОНИЧЕСКИЙ ПОДХОД

```python
def _generate_spine_path(seed: str) -> List[Tuple[int, int]]:
    """
    Генерирует изогнутую ось континента

    Returns:
        List из ~100 точек (x, y) формирующих позвоночник
    """
    # 1. Создать контрольные точки с органическим смещением
    # 2. Добавить синусоидальную "волнистость"
    # 3. Сгладить через Catmull-Rom Spline
    pass
```

**Результат:** Изогнутая ось, вокруг которой вырастет континент

---

## Phase 1b: Инструменты генерации континента

### 1. Perlin Noise Generator

**Назначение:** Создание базового органического рельефа

**Алгоритм:** Градиентный шум с интерполяцией

```python
def generate_perlin_noise(seed, width, height, scale, octaves, persistence, lacunarity):
    """
    Генерирует Perlin Noise карту

    Args:
        seed: Seed для детерминизма
        width, height: Размер карты
        scale: Частота шума (50-300)
        octaves: Слои детализации (1-5)
        persistence: Затухание амплитуды (0.0-1.0)
        lacunarity: Рост частоты (1.5-4.0)

    Returns:
        numpy array (height, width) float [0, 1]
    """
    # Реализация через noise library или собственный алгоритм
    pass
```

**Параметры для континентов (оптимизированные):**
```yaml
scale: 150          # Низкая частота = плавные континенты
octaves: 2          # Минимум детализации
persistence: 0.6    # Умеренное затухание
lacunarity: 2.0     # Стандартное удвоение частоты
```

**Влияние параметров:**

| Параметр | Низкое значение | Оптимальное | Высокое значение |
|----------|----------------|-------------|------------------|
| `scale` | Хаос, мелкие детали | **150-200**: Плавные континенты | Слишком однородно |
| `octaves` | Гладко, просто | **2**: Естественная форма | Много деталей |
| `persistence` | Быстрое затухание | **0.6**: Баланс | Сильные высокочастотные детали |

**Статус:** ✅ Реализовано (`core/perlin_noise.py`)

---

### 2. Threshold Operator

**Назначение:** Разделение суши и океана

```python
def apply_threshold(heightmap, sea_level):
    """
    Применяет порог для определения суши vs океана

    Args:
        heightmap: Perlin Noise карта [0, 1]
        sea_level: Порог (0.0-1.0)

    Returns:
        boolean mask (True = суша, False = океан)
    """
    return heightmap > sea_level
```

**Параметры:**
```yaml
sea_level: 0.35  # БЕЗ shape mask
sea_level: 0.20  # С shape mask (ниже из-за умножения)
```

**Влияние sea_level:**

| Значение | Суша | Океан | Характер |
|----------|------|-------|----------|
| 0.25-0.30 | 90-99% | 1-10% | Почти вся суша |
| **0.35-0.40** | **60-80%** | **20-40%** | **Оптимально** |
| 0.45-0.50 | 0-20% | 80-100% | Архипелаг |

**Статус:** ✅ Реализовано (в `_generate_continent()`)

---

### 3. Морфологические операции

**Назначение:** Сглаживание береговой линии, удаление артефактов

#### Binary Opening

**Эффект:** Удаление маленьких островов

```python
from scipy.ndimage import morphology

continent_mask = morphology.binary_opening(
    continent_mask,
    iterations=3  # Количество проходов
)
```

**Как работает:**
1. Erosion (эрозия) - уменьшает объекты
2. Dilation (расширение) - восстанавливает размер
3. **Результат:** Маленькие острова исчезают, крупные сохраняются

#### Binary Closing

**Эффект:** Заполнение маленьких заливов

```python
continent_mask = morphology.binary_closing(
    continent_mask,
    iterations=2
)
```

**Как работает:**
1. Dilation (расширение) - заполняет дыры
2. Erosion (эрозия) - восстанавливает размер
3. **Результат:** Маленькие заливы заполняются, крупные сохраняются

**Статус:** ✅ Реализовано (в `_generate_continent()`)

---

### 4. Gaussian Blur

**Назначение:** Финальное сглаживание береговой линии

```python
from scipy.ndimage import gaussian_filter

continent_float = gaussian_filter(
    continent_mask.astype(float),
    sigma=3.0  # Радиус размытия
)

# Применяем threshold снова
continent_mask = (continent_float > 0.5).astype(bool)
```

**Эффект:**
- Сглаживает резкие углы
- Создаёт плавные переходы
- Убирает пикселизацию

**Параметры:**

| sigma | Эффект |
|-------|--------|
| 1.0-2.0 | Лёгкое сглаживание |
| **3.0** | **Оптимально для континентов** |
| 5.0+ | Сильное размытие, потеря деталей |

**Статус:** ✅ Реализовано (в `_generate_continent()`)

---

### 5. PCA (Principal Component Analysis)

**Назначение:** Расчёт главной оси континента

```python
def calculate_major_axis(continent_mask):
    """
    Находит главную ось континента через PCA

    Args:
        continent_mask: boolean array

    Returns:
        ((x1, y1), (x2, y2)) - начало и конец оси
    """
    # Координаты всех точек суши
    y_coords, x_coords = np.where(continent_mask)
    coords = np.column_stack([x_coords, y_coords])

    # Центрируем данные
    mean = coords.mean(axis=0)
    centered = coords - mean

    # Ковариационная матрица
    cov_matrix = np.cov(centered.T)

    # Главный eigenvector (максимальная дисперсия)
    eigenvalues, eigenvectors = np.linalg.eig(cov_matrix)
    principal_component = eigenvectors[:, eigenvalues.argmax()]

    # Проекция всех точек на главный компонент
    projections = centered @ principal_component

    # Крайние точки (начало и конец оси)
    min_idx = projections.argmin()
    max_idx = projections.argmax()

    start_point = coords[min_idx]
    end_point = coords[max_idx]

    return (tuple(start_point), tuple(end_point))
```

**Применение:**
- Размещение neural clusters вдоль оси (35%, 65% по длине)
- Ориентация регионов (торакс, органоид)
- Определение "направления" континента

**Статус:** ✅ Реализовано (в `_calculate_major_axis()`)

---

### 6. Center of Mass

**Назначение:** Расчёт центра масс континента

```python
from scipy.ndimage import center_of_mass

def calculate_center_of_mass(continent_mask):
    """
    Находит центр масс континента

    Args:
        continent_mask: boolean array

    Returns:
        (cx, cy) - координаты центра
    """
    cy, cx = center_of_mass(continent_mask)
    return (int(cx), int(cy))
```

**Применение:**
- Размещение metabolic_organ в центре
- Центрирование shape mask

**Статус:** ✅ Реализовано (в `_calculate_center_of_mass()`)

---

## Phase 1a: Shape Mask инструменты

**⚠️ v2.0 КРИТИЧЕСКОЕ ИЗМЕНЕНИЕ:**

**УСТАРЕВШИЕ МЕТОДЫ** (не используются в v2.0):
- ❌ Ellipse Mask - заменён на Spine-Based
- ❌ Radial Mask - заменён на Spine-Based

**ЕДИНСТВЕННЫЙ КАНОНИЧЕСКИЙ МЕТОД в v2.0:**
- ✅ **Spine-Based Shape Mask** - создаётся из процедурно сгенерированного позвоночника

Документация ниже сохранена для справки, но **НЕ используется** в текущей реализации.
См. [SPINE_BASED_GENERATION.md](SPINE_BASED_GENERATION.md) для актуального метода.

---

### Философия (историческая)

**Shape Mask** - это градиентная маска, которая **умножается** на базовый Perlin Noise для центрирования континента.

**Формула:**
```python
final_heightmap = base_noise * shape_mask
```

### 1. Ellipse Mask (эллиптическая маска) ❌ OBSOLETE

**⚠️ СТАТУС:** Устаревший метод, заменён на Spine-Based в v2.0

**Назначение:** Центрирование континента эллиптическим градиентом

```python
def create_ellipse_mask(width, height, radius_x, radius_y):
    """
    Создаёт эллиптический градиент

    Args:
        width, height: Размер карты
        radius_x: Радиус по X (доля ширины, 0-1)
        radius_y: Радиус по Y (доля высоты, 0-1)

    Returns:
        numpy array (height, width) float [0, 1]
        1.0 в центре, 0.0 на краях
    """
    cx, cy = width / 2, height / 2
    rx, ry = width * radius_x, height * radius_y

    y, x = np.ogrid[:height, :width]

    # Нормализованное расстояние от центра (формула эллипса)
    distance = np.sqrt(((x - cx)**2 / rx**2) + ((y - cy)**2 / ry**2))

    # Инвертируем (центр = 1.0, края = 0.0)
    shape_mask = 1.0 - distance

    # Clamp в [0, 1]
    return np.clip(shape_mask, 0, 1)
```

**Параметры:**
```yaml
radius_x: 0.35  # 35% ширины карты
radius_y: 0.45  # 45% высоты карты (вытянутый по вертикали)
```

**Применение:** Стандартное центрирование континента

**Статус:** ✅ Реализовано (в `_create_shape_mask()`)

---

### 2. Radial Mask (круговая маска) ❌ OBSOLETE

**⚠️ СТАТУС:** Устаревший метод, заменён на Spine-Based в v2.0

**Назначение:** Центрирование континента круговым градиентом

```python
def create_radial_mask(width, height, max_radius):
    """
    Создаёт круговой градиент

    Args:
        width, height: Размер карты
        max_radius: Максимальный радиус (доля размера карты, 0-1)

    Returns:
        numpy array (height, width) float [0, 1]
    """
    cx, cy = width / 2, height / 2
    radius = min(width, height) / 2 * max_radius

    y, x = np.ogrid[:height, :width]

    # Евклидово расстояние от центра
    distance = np.sqrt((x - cx)**2 + (y - cy)**2)

    # Инвертируем
    shape_mask = np.maximum(0, 1.0 - distance / radius)

    return shape_mask
```

**Параметры:**
```yaml
max_radius: 0.40  # 40% радиуса карты
```

**Применение:** Создание симметричных континентов

**Статус:** ✅ Реализовано (в `_create_shape_mask()`)

---

### 3. Spine Mask (хребтовая маска) ⭐

**Назначение:** Континент растёт вокруг процедурного "позвоночника"

**Философия:**
> **"От анатомии к географии"** - сначала создаётся хребет (анатомическая структура), затем континент вырастает вокруг него.

#### Шаг 1: Генерация Spine Path

**Процедурная генерация изогнутого позвоночника (север → юг)**

```python
def generate_spine_path(seed, width, height, num_points=100, curvature=0.3):
    """
    Генерирует плавный, изогнутый путь с севера на юг

    Args:
        seed: Seed для детерминизма
        width, height: Размер карты
        num_points: Количество точек вдоль хребта
        curvature: Максимальное отклонение от центра (0-1)

    Returns:
        numpy array (num_points, 2) - координаты [[x1, y1], [x2, y2], ...]
    """
    # 1D Perlin Noise для смещения по X
    noise_1d = generate_perlin_map(
        width=num_points,
        height=1,
        scale=20,  # Низкая частота = плавные изгибы
        octaves=3,
        seed=hash(seed + "spine_x") % (2**31)
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

    return np.array(path)
```

**Параметры:**

| Параметр | Значение | Эффект |
|----------|---------|--------|
| `num_points` | 100 | Количество точек (больше = плавнее) |
| `curvature` | 0.3 | Изгиб (0.1 = прямой, 0.5 = S-образный) |

**Результат:** Массив координат от (256, 0) до (x_end, 511)

#### Шаг 2: Создание Spine Influence Mask

**Distance Transform от пути хребта**

```python
def create_spine_influence_mask(spine_path, width, height, max_influence=200):
    """
    Для каждого пикселя вычисляет расстояние до ближайшей точки на хребте

    Args:
        spine_path: array (N, 2) координат хребта
        width, height: Размер карты
        max_influence: Радиус влияния в пикселях

    Returns:
        numpy array (height, width) float [0, 1]
        1.0 на хребте, 0.0 далеко от хребта
    """
    from scipy.spatial import cKDTree

    # Создаём сетку всех координат
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

**Параметры:**

| Параметр | Значение | Эффект |
|----------|---------|--------|
| `max_influence` | 150-180 | Узкий континент |
| **`max_influence`** | **200-220** | **Оптимально** |
| `max_influence` | 250-280 | Широкий континент |

**Результат:** Поле влияния [0, 1], где:
- **1.0** - на хребте и близко к нему
- **0.0** - далеко от хребта (края карты)
- Плавный градиент между ними

#### Шаг 3: Композиция

```python
# Базовый Perlin Noise
base_noise = generate_perlin_noise(...)

# Поле влияния хребта
spine_influence = create_spine_influence_mask(spine_path, ...)

# КОМБИНАЦИЯ
final_heightmap = base_noise * spine_influence

# Более низкий sea_level (компенсация умножения)
continent_mask = (final_heightmap > 0.20)
```

**Эффект:**
- Где **spine_influence = 1.0** (на хребте) → шум сохраняется
- Где **spine_influence = 0.0** (далеко) → шум обнуляется (океан)
- Континент **растёт вокруг хребта**, следуя его изгибам

**Статус:** ✅ Реализовано (`_generate_spine_path()`, `_create_spine_influence_mask()`)

---

## Конфигурационные инструменты

### 1. WorldGenerationConfigV2

**Назначение:** Загрузка и валидация конфигурации генерации

```python
from services.world_config_v2 import WorldGenerationConfigV2

# Загрузка из YAML
config = WorldGenerationConfigV2.from_yaml('config/world_generation_v2.yaml')

# Доступ к параметрам
scale = config.continent.perlin_noise.scale
sea_level = config.continent.sea_level

# Изменение параметров
config_dict = config.to_dict()
config_dict['continent']['shape_mask']['enabled'] = True

# Сохранение
config.save_to_yaml('config/world_generation_v2_modified.yaml')
```

**Валидация:**
- Проверка типов данных
- Проверка диапазонов значений
- Проверка обязательных полей

**Статус:** ✅ Реализовано (`services/world_config_v2.py`)

---

### 2. Parameter Tuning Tool

**Назначение:** Автоматический поиск оптимальных параметров

```bash
# Grid search по scale и sea_level
python scripts/tune_continent_parameters.py --full-grid

# Тюнинг одного параметра
python scripts/tune_continent_parameters.py --param scale
```

**Метрика качества:**
```python
land_score = 100 - abs(land_pct - 65) * 2  # Целевой процент: 65%
island_penalty = num_islands * 10           # Штраф за острова
score = land_score - island_penalty
```

**Результаты:**
- **Лучшие параметры:** `scale=150`, `sea_level=0.38`
- **Суша:** ~65-70%
- **Острова:** 1-2

**Статус:** ✅ Реализовано (`scripts/tune_continent_parameters.py`)

---

## Визуализационные инструменты

### 1. Continent Visualizer

**Назначение:** Основная визуализация континента (4 панели)

```bash
# Стандартная генерация
python scripts/visualize_continent.py --seed my_seed

# Spine-based генерация
python scripts/visualize_continent.py --seed my_seed --spine

# Сравнение режимов (Standard vs Spine)
python scripts/visualize_continent.py --seed my_seed --compare-modes

# Сравнение нескольких seeds
python scripts/visualize_continent.py --compare seed_A seed_B seed_C
```

**Панели:**
1. **Perlin Noise Heightmap** - сырые данные
2. **Continent Mask** - суша vs океан
3. **Land Elevation** - heightmap только для суши
4. **Continent Geometry** - центр масс + главная ось

**Формат:** PNG, DPI=150, ~4.8 MB

**Статус:** ✅ Реализовано (`scripts/visualize_continent.py`)

---

### 2. Spine Continent Visualizer

**Назначение:** Детальная визуализация spine-based подхода (6 панелей)

```bash
# Полная демонстрация spine-based подхода
python scripts/visualize_spine_continent.py --seed silgarron_world_001

# Сравнение нескольких spine континентов
python scripts/visualize_spine_continent.py --compare
```

**Панели:**
1. **Base Perlin Noise** - без маски
2. **Spine Path + Influence Field** - хребет и поле влияния
3. **Combined** - результат умножения (Noise × Spine)
4. **Continent WITH Spine** - финальный континент
5. **Continent WITH Ellipse** - старый подход (для сравнения)
6. **Comparison Overlay** - наложение обоих

**Формат:** PNG, DPI=150, ~3.9 MB

**Статус:** ✅ Реализовано (`scripts/visualize_spine_continent.py`)

---

### 3. Shape Mask Visualizer

**Назначение:** Визуализация эффекта shape mask (6 панелей)

```bash
# Демонстрация одной маски
python scripts/visualize_shape_mask.py --seed my_continent

# Сравнение типов масок (ellipse vs radial)
python scripts/visualize_shape_mask.py --compare-types
```

**Панели:**
1. **Base Perlin Noise** - исходный шум
2. **Shape Mask** - градиентная маска (центр=1, края=0)
3. **Combined** - результат умножения
4. **Without Shape Mask** - континент без центрирования
5. **With Shape Mask** - континент с центрированием
6. **Comparison** - наложение обоих

**Статус:** ✅ Реализовано (`scripts/visualize_shape_mask.py`)

---

## Phase 1: Инструменты размещения органов (запланировано)

### 1. OrganPlacer

**Назначение:** Размещение органов на континенте

**Методы размещения:**

#### center_of_continent
```python
def place_at_center(continent):
    """Размещение в центре масс континента"""
    return continent.center
```

#### suitable_lowland
```python
def find_suitable_lowland(continent, near_position, direction, radius_range):
    """
    Поиск низины в заданном направлении

    Returns:
        (x, y) - координаты точки с минимальной высотой
    """
    # Зона поиска (южнее near_position)
    search_mask = (y > near_y + min_radius) & (y < near_y + max_radius)

    # Пересечение с сушей
    valid_mask = search_mask & continent.mask

    # Точка с минимальной высотой
    heightmap_masked = np.where(valid_mask, continent.heightmap, np.inf)
    min_y, min_x = np.unravel_index(heightmap_masked.argmin(), heightmap_masked.shape)

    return (min_x, min_y)
```

#### along_axis
```python
def place_along_axis(continent, relative_position):
    """
    Размещение вдоль главной оси континента

    Args:
        relative_position: 0.0-1.0 (0% - начало оси, 100% - конец)

    Returns:
        (x, y) - координаты на оси
    """
    (x1, y1), (x2, y2) = continent.major_axis

    x = int(x1 + (x2 - x1) * relative_position)
    y = int(y1 + (y2 - y1) * relative_position)

    # Проверяем, что точка на суше
    if not continent.mask[y, x]:
        x, y = find_nearest_land(continent.mask, (x, y))

    return (x, y)
```

#### elevated_point
```python
def find_elevated_point(continent, near_position, search_radius):
    """
    Поиск возвышенности рядом с позицией

    Returns:
        (x, y) - координаты точки с максимальной высотой
    """
    # Зона поиска (радиус вокруг near_position)
    search_mask = (distance_to_near < search_radius)

    # Пересечение с сушей
    valid_mask = search_mask & continent.mask

    # Точка с максимальной высотой
    heightmap_masked = np.where(valid_mask, continent.heightmap, -np.inf)
    max_y, max_x = np.unravel_index(heightmap_masked.argmax(), heightmap_masked.shape)

    return (max_x, max_y)
```

**Статус:** 🚧 Запланировано (Sprint 3.6, Phase 3)

---

### 2. RegionDefiner

**Назначение:** Определение региональных масок

**Методы определения:**

#### organ_proximity (для ORGANOID)
```python
def define_organoid_region(continent, organs):
    """Зона вокруг метаболических органов"""
    mask = np.zeros_like(continent.mask)

    for organ in organs:
        if organ.type in ['metabolic_organ', 'digestive']:
            cx, cy = organ.position
            distance = np.sqrt((x - cx)**2 + (y - cy)**2)
            mask |= (distance < 80)  # Радиус 80 пикселей

    return mask & continent.mask
```

#### skeletal_density (для THORAX)
```python
def define_thorax_region(continent, skeleton):
    """Зона с высокой плотностью костей"""
    # В Sprint 3.6 упрощённо: северная треть континента
    # В Sprint 3.7: реальная костная структура
    mask = continent.mask.copy()
    mask[axis_y1:, :] = False
    return mask
```

#### muscle_layer (для DIAPHRAGM)
```python
def define_diaphragm_region(thorax_mask, organoid_mask):
    """Граница между thorax и organoid"""
    # Дилатация обеих масок
    thorax_dilated = binary_dilation(thorax_mask, iterations=10)
    organoid_dilated = binary_dilation(organoid_mask, iterations=10)

    # Пересечение = граница
    return thorax_dilated & organoid_dilated
```

**Статус:** 🚧 Запланировано (Sprint 3.6, Phase 3)

---

## Phase 2+: Инструменты будущих фаз (Sprint 3.7-3.9)

### Phase 2: Артерии (Sprint 3.7)

**Инструменты:**
- Minimum Spanning Tree (MST) - для сети артерий
- B-spline сглаживание - для плавных путей
- Catmull-Rom interpolation - альтернатива B-spline

### Phase 3: Геология (Sprint 3.7)

**Инструменты:**
- Костный генератор (хребет, рёбра, фаланги)
- Композиция слоёв (региональный bias + текстура + кости)
- Distance transform - для влияния артерий

### Phase 4: Гидрология (Sprint 3.8)

**Инструменты:**
- D8 Flow Accumulation - расчёт стока воды
- D8 Flow Direction - направление потока
- Arterial outlet placement - выходы артерий на поверхность

### Phase 5: Климат (Sprint 3.8)

**Инструменты:**
- Radial gradient generator - для тепла от органов
- Inverse square law - затухание по расстоянию
- Exponential decay - для влажности

### Phase 6: Дыхательная система (Sprint 3.8)

**Инструменты:**
- Structural stress analysis - напряжение скелета
- Poisson Disk Sampling (variable density) - размещение каверн
- BFS с затуханием - распространение выдоха

### Phase 7: Ткани (Sprint 3.9)

**Инструменты:**
- Rule-based tissue assignment - назначение по правилам
- Context aggregation - сбор контекста клетки
- Tissue rules YAML parser - парсинг правил из конфига

**Статус всех:** 🚧 Запланировано

---

## Команды Cheat Sheet

### Основные визуализации
```bash
# Стандартная визуализация
python scripts/visualize_continent.py --seed my_seed

# Spine-based визуализация
python scripts/visualize_continent.py --seed my_seed --spine

# Сравнение режимов
python scripts/visualize_continent.py --seed my_seed --compare-modes
```

### Сравнение seeds
```bash
# Стандартный
python scripts/visualize_continent.py --compare seed_A seed_B seed_C

# Со spine
python scripts/visualize_continent.py --compare seed_A seed_B seed_C --spine
```

### Детальная визуализация
```bash
# 6 панелей spine демонстрация
python scripts/visualize_spine_continent.py --seed my_seed

# Сравнение spine континентов
python scripts/visualize_spine_continent.py --compare

# Shape mask эффект
python scripts/visualize_shape_mask.py --seed my_continent

# Сравнение типов масок
python scripts/visualize_shape_mask.py --compare-types
```

### Тестирование
```bash
# Все тесты
python -m pytest tests/models/ tests/core/ -v

# Быстрая проверка
python -m pytest tests/models/ tests/core/ -q

# Только континент
python -m pytest tests/core/test_continent_generation.py -v
```

### Тюнинг параметров
```bash
# Grid search оптимизация
python scripts/tune_continent_parameters.py --full-grid

# Тюнинг одного параметра
python scripts/tune_continent_parameters.py --param scale
python scripts/tune_continent_parameters.py --param sea_level
python scripts/tune_continent_parameters.py --param octaves
```

---

## Рецепты параметров

### Spine континенты

#### "Прямой позвоночник"
```yaml
spine:
  curvature: 0.15
  max_influence: 180.0
```
Почти прямой континент, симметричный.

#### "Средний изгиб" (рекомендуется)
```yaml
spine:
  curvature: 0.3
  max_influence: 200.0
```
Естественные плавные изгибы.

#### "Извивающийся дракон"
```yaml
spine:
  curvature: 0.45
  max_influence: 220.0
```
S-образная форма, драматичные изгибы.

#### "Массивное тело"
```yaml
spine:
  curvature: 0.3
  max_influence: 280.0
sea_level_override: 0.15
```
Огромный континент, максимум суши.

#### "Тонкий хребет"
```yaml
spine:
  curvature: 0.35
  max_influence: 150.0
sea_level_override: 0.25
```
Тонкий, изогнутый континент.

### Стандартные континенты

#### "Больше океана"
```yaml
sea_level: 0.40  # Было 0.35
```
60-70% суши, 30-40% океана.

#### "Крупные формы"
```yaml
perlin_noise:
  scale: 200  # Было 150
```
Очень плавные континенты.

#### "Больше деталей"
```yaml
perlin_noise:
  octaves: 3  # Было 2
```
Архипелаги, острова.

#### "Гладкая береговая линия"
```yaml
smoothing:
  gaussian_sigma: 5.0  # Было 3.0
```
Минимум углов и неровностей.

---

**Версия:** 1.0
**Статус:** Phase 0.5 инструменты реализованы, Phase 1+ запланированы
**Следующий шаг:** Реализация OrganPlacer и RegionDefiner (Sprint 3.7)
