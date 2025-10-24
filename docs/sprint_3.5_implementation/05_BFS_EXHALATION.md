# 05. BFS Exhalation - Распространение спор от каверн

## Что это?

**BFS (Breadth-First Search)** - это алгоритм обхода графа, который посещает узлы **слоями** от исходной точки.

В контексте Сильгаррона используется для моделирования **распространения спор выдоха** от альвеолярных каверн.

---

## Зачем это нужно для Сильгаррона?

### Биологическая модель:

```
АЛЬВЕОЛЯРНЫЕ КАВЕРНЫ (источники)
         |
         | Выдох (exhalation)
         v
   РАСПРОСТРАНЕНИЕ СПОР
         |
         | Decay (затухание)
         v
  БИОАКТИВНАЯ САТУРАЦИЯ
    (bioactive zones)
```

### Проблема: Как распространить споры от каверн?

**Альвеолярные каверны** - это "легкие" Сильгаррона, которые:
1. Выдыхают споры в окружающие ткани
2. Споры распространяются во все стороны
3. Интенсивность спор затухает с расстоянием
4. Создают зоны биоактивности

**BFS с затуханием** идеально подходит для этой задачи!

---

## Как работает BFS?

### Идея:

1. Начинаем с исходных точек (каверны)
2. Распространяемся на соседей слой за слоем
3. Применяем затухание (decay) при каждом шаге
4. Останавливаемся, когда интенсивность падает до нуля

### Визуализация процесса:

```
Шаг 0: Каверны (источники)
┌─────────────┐
│             │
│      X      │  X = каверна (интенсивность = 1.0)
│             │
└─────────────┘

Шаг 1: Первый слой (decay = 0.9)
┌─────────────┐
│      9      │  9 = 0.9 интенсивности
│    9 X 9    │  X = каверна (1.0)
│      9      │
└─────────────┘

Шаг 2: Второй слой (decay = 0.9)
┌─────────────┐
│    8 9 8    │  8 = 0.9 * 0.9 = 0.81
│  8 9 X 9 8  │  9 = 0.9
│    8 9 8    │  X = 1.0
└─────────────┘

Шаг 3: Третий слой (decay = 0.9)
┌─────────────┐
│  7 8 9 8 7  │  7 = 0.9^3 = 0.729
│7 8 9 X 9 8 7│
│  7 8 9 8 7  │
└─────────────┘

...продолжаем, пока интенсивность > порог (например, 0.01)
```

### Результат:

Каждая каверна окружена **градиентом затухающей интенсивности** спор.

---

## Алгоритм BFS с затуханием

### Псевдокод:

```python
def bfs_exhalation(caverns, decay_rate, threshold):
    # Инициализация
    intensity_map = zeros(height, width)
    queue = Queue()
    visited = set()

    # Добавляем каверны (интенсивность = 1.0)
    for cavern in caverns:
        queue.put((cavern, 1.0))
        intensity_map[cavern] = 1.0
        visited.add(cavern)

    # BFS
    while not queue.empty():
        (y, x), intensity = queue.get()

        # Затухающая интенсивность для соседей
        neighbor_intensity = intensity * decay_rate

        if neighbor_intensity < threshold:
            continue  # Слишком слабо - останавливаемся

        # Распространяемся на 4 соседей (N, S, E, W)
        for dy, dx in [(-1,0), (1,0), (0,-1), (0,1)]:
            ny, nx = y + dy, x + dx

            if not in_bounds(ny, nx):
                continue

            if (ny, nx) in visited:
                continue

            # Обновляем интенсивность (максимум, если уже есть)
            intensity_map[ny, nx] = max(
                intensity_map[ny, nx],
                neighbor_intensity
            )

            queue.put(((ny, nx), neighbor_intensity))
            visited.add((ny, nx))

    return intensity_map
```

---

## Реализация для Сильгаррона

### Функция `spread_exhalation`:

```python
def spread_exhalation(
    caverns: List[Tuple[int, int]],
    width: int,
    height: int,
    decay_rate: float = 0.92,
    min_threshold: float = 0.01,
    elevation: np.ndarray = None,
    elevation_penalty: float = 0.1
) -> np.ndarray:
    """
    Распространяет выдох (споры) от альвеолярных каверн через BFS.

    Споры распространяются во все стороны с затуханием (decay).
    Интенсивность = начальная * (decay_rate ^ distance).

    Args:
        caverns: List[(y, x)] - координаты каверн (источников)
        width, height: Размеры карты
        decay_rate: Коэффициент затухания (0.0-1.0)
                    0.92 = 92% интенсивности сохраняется на каждом шаге
        min_threshold: Порог остановки (споры слабее этого не распространяются)
        elevation: Карта высот (опционально для учёта рельефа)
        elevation_penalty: Штраф за подъём (опционально)

    Returns:
        exhalation_intensity: np.ndarray (height, width) float32
                              Интенсивность выдоха в каждой ячейке [0.0, 1.0]

    Биологическая интерпретация:
        - Каверны = "альвеолы" (выдыхают споры)
        - Споры распространяются в окружающие ткани
        - Затухают с расстоянием (decay)
        - Создают зоны биоактивной сатурации
    """
    from collections import deque

    intensity = np.zeros((height, width), dtype=np.float32)
    queue = deque()
    visited = set()

    # Инициализация: каверны с интенсивностью 1.0
    for y, x in caverns:
        intensity[y, x] = 1.0
        queue.append((y, x, 1.0))
        visited.add((y, x))

    # 4 направления (N, S, E, W)
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    # BFS с затуханием
    while queue:
        y, x, current_intensity = queue.popleft()

        for dy, dx in directions:
            ny, nx = y + dy, x + dx

            # Проверка границ
            if not (0 <= ny < height and 0 <= nx < width):
                continue

            # Вычисляем затухание
            neighbor_intensity = current_intensity * decay_rate

            # Опционально: учитываем рельеф
            if elevation is not None:
                # Подъём = дополнительное затухание
                height_diff = elevation[ny, nx] - elevation[y, x]
                if height_diff > 0:
                    neighbor_intensity *= (1.0 - elevation_penalty * height_diff)

            # Порог остановки
            if neighbor_intensity < min_threshold:
                continue

            # Обновляем интенсивность (максимум, если уже есть)
            if (ny, nx) in visited:
                # Если уже посещали, обновляем только если новая интенсивность выше
                if neighbor_intensity > intensity[ny, nx]:
                    intensity[ny, nx] = neighbor_intensity
                    # Повторно добавляем в очередь с новой интенсивностью
                    queue.append((ny, nx, neighbor_intensity))
            else:
                intensity[ny, nx] = neighbor_intensity
                queue.append((ny, nx, neighbor_intensity))
                visited.add((ny, nx))

    return intensity
```

---

## Параметры для настройки

### `decay_rate` (коэффициент затухания):

Контролирует **скорость затухания** спор.

| Значение | Эффект | Биологическая интерпретация |
|----------|--------|------------------------------|
| **0.95** | Медленное затухание → большой радиус | "Летучие" споры, далеко распространяются |
| **0.92** | Умеренное затухание → средний радиус | Баланс (рекомендуется) |
| **0.85** | Быстрое затухание → малый радиус | "Тяжёлые" споры, оседают быстро |

**Формула радиуса:**
```python
# Сколько шагов до затухания ниже порога?
# intensity = decay_rate ^ steps
# 0.01 = 0.92 ^ steps
# steps = log(0.01) / log(0.92) ≈ 55 шагов

radius_steps = log(min_threshold) / log(decay_rate)
```

### `min_threshold` (порог остановки):

Контролирует **минимальную интенсивность** для распространения.

| Значение | Эффект |
|----------|--------|
| **0.001** | Очень далёкое распространение (даже слабые споры) |
| **0.01** | Умеренное распространение (рекомендуется) |
| **0.05** | Близкое распространение (только сильные споры) |

### `elevation_penalty` (штраф за подъём):

Опциональный параметр для учёта рельефа.

| Значение | Эффект |
|----------|--------|
| **0.0** | Споры игнорируют рельеф |
| **0.1** | Малый штраф (споры частично задерживаются холмами) |
| **0.3** | Большой штраф (споры почти не поднимаются в гору) |

**Применение:**
- Споры легче распространяются **вниз** (в низины)
- Труднее подниматься **вверх** (на возвышенности)
- Реалистичнее с физической точки зрения

---

## Биоактивная сатурация

### Что это?

**Биоактивная зона** - область с высокой интенсивностью выдоха.

Используется для:
1. **Определения типов тканей** (высокая сатурация = активная ткань)
2. **Геймплея** (зоны с особыми эффектами)
3. **Визуализации** ("горячие" зоны на карте)

### Формула:

```python
# Нормализуем интенсивность к [0, 1]
bioactive_saturation = exhalation_intensity

# Опционально: порог для бинарной маски
bioactive_mask = (exhalation_intensity > 0.3).astype(float)
```

### Интерпретация:

```
Интенсивность    Биологическая зона
==============   ==================
0.8 - 1.0        Альвеолярные каверны (источник)
0.5 - 0.8        Активная ткань (высокая метаболическая активность)
0.2 - 0.5        Периферийная ткань (умеренная активность)
0.0 - 0.2        Инертная зона (низкая активность)
```

---

## Интеграция в WorldGenerator

### Шаг 1: Разместить каверны (Poisson Disk Sampling)

```python
from core.poisson_sampling import place_alveolar_caverns

caverns = place_alveolar_caverns(
    width=256,
    height=256,
    elevation=elevation,
    min_distance=30.0,
    elevation_range=(0.2, 0.7),
    rng=self.rng
)
```

### Шаг 2: Распространить выдох (BFS)

```python
from core.exhalation import spread_exhalation

exhalation_intensity = spread_exhalation(
    caverns=caverns,
    width=256,
    height=256,
    decay_rate=0.92,
    min_threshold=0.01,
    elevation=elevation,
    elevation_penalty=0.1
)
```

### Шаг 3: Создать маску биоактивности

```python
# Зоны с интенсивностью > 30% считаются биоактивными
bioactive_mask = (exhalation_intensity > 0.3).astype(np.float32)

# Подсчёт биоактивных ячеек
bioactive_count = np.sum(bioactive_mask)
bioactive_ratio = bioactive_count / (width * height)
```

---

## Валидация

### Unit Tests:

```python
def test_exhalation_from_single_cavern():
    """Выдох распространяется от одной каверны с затуханием"""
    caverns = [(128, 128)]  # Центр карты

    intensity = spread_exhalation(
        caverns=caverns,
        width=256,
        height=256,
        decay_rate=0.9,
        min_threshold=0.01
    )

    # 1. Исходная точка = максимальная интенсивность
    assert intensity[128, 128] == 1.0

    # 2. Соседи имеют decay_rate интенсивности
    assert np.isclose(intensity[128, 129], 0.9)
    assert np.isclose(intensity[127, 128], 0.9)

    # 3. Интенсивность убывает с расстоянием
    center_intensity = intensity[128, 128]
    near_intensity = intensity[128, 130]  # 2 шага
    far_intensity = intensity[128, 150]   # 22 шага

    assert center_intensity > near_intensity > far_intensity


def test_exhalation_multiple_caverns():
    """Выдох от нескольких каверн накладывается"""
    caverns = [(100, 100), (156, 156)]

    intensity = spread_exhalation(
        caverns=caverns,
        width=256,
        height=256,
        decay_rate=0.9,
        min_threshold=0.01
    )

    # Оба источника имеют интенсивность 1.0
    assert intensity[100, 100] == 1.0
    assert intensity[156, 156] == 1.0

    # Промежуточная область имеет наложение обеих зон
    # (максимум из двух затухающих значений)
    midpoint = (128, 128)
    assert intensity[midpoint] > 0.0


def test_exhalation_elevation_penalty():
    """Выдох учитывает рельеф (труднее подниматься в гору)"""
    # Создаём наклон: слева низко, справа высоко
    elevation = np.tile(np.linspace(0.0, 1.0, 256), (256, 1))

    caverns = [(128, 50)]  # Исток слева (низина)

    intensity = spread_exhalation(
        caverns=caverns,
        width=256,
        height=256,
        decay_rate=0.92,
        min_threshold=0.01,
        elevation=elevation,
        elevation_penalty=0.3  # Большой штраф за подъём
    )

    # Интенсивность должна быть выше ВЛЕВО (вниз) чем ВПРАВО (вверх)
    intensity_left = intensity[128, 30]   # Вниз
    intensity_right = intensity[128, 70]  # Вверх

    assert intensity_left > intensity_right
```

### Visual Validation:

После реализации проверяем PNG:
- Каверны = яркие точки
- Концентрические круги затухания вокруг каверн
- Радиус ~ 50-60 пикселей (при decay=0.92, threshold=0.01)
- Наложение зон от разных каверн

---

## Преимущества BFS

### Почему BFS, а не Dijkstra или A*?

| Алгоритм | Сложность | Применимость | Почему не для выдоха? |
|----------|-----------|--------------|----------------------|
| **BFS** | O(V + E) | Невзвешенный граф | ✅ Подходит! Все шаги равны |
| **Dijkstra** | O(E log V) | Взвешенный граф | ❌ Избыточно (нет переменных весов) |
| **A*** | O(E log V) | Поиск пути | ❌ Нет целевой точки |

### Преимущества BFS для выдоха:

1. **Простота**: Легко понять и реализовать
2. **Производительность**: O(n) для карты размером n
3. **Естественность**: Споры распространяются равномерно во все стороны
4. **Предсказуемость**: Чёткие концентрические круги

---

## Альтернативы

### 1. Gaussian Blur (размытие):
```python
from scipy.ndimage import gaussian_filter

# Каверны = 1.0, остальное = 0.0
cavern_mask = np.zeros((256, 256))
for y, x in caverns:
    cavern_mask[y, x] = 1.0

# Применяем размытие
exhalation = gaussian_filter(cavern_mask, sigma=20)
```

**Проблемы:**
- ❌ Нет контроля над затуханием
- ❌ Споры проходят сквозь стены (нет учёта препятствий)
- ❌ Неестественная форма (гауссиан слишком гладкий)

### 2. Distance Transform:
```python
from scipy.ndimage import distance_transform_edt

# Расстояние до ближайшей каверны
distances = distance_transform_edt(~cavern_mask)

# Затухание = exp(-distance / decay_radius)
exhalation = np.exp(-distances / 30.0)
```

**Проблемы:**
- ❌ Игнорирует препятствия
- ❌ Нет пошагового контроля
- ⚠️ Быстрее BFS, но менее гибко

### 3. BFS с затуханием:
- ✅ Пошаговый контроль
- ✅ Учёт препятствий (будущее расширение)
- ✅ Естественное распространение
- ✅ Легко настраивается (decay, threshold)

**Для Сильгаррона:** BFS - лучший выбор!

---

## Следующий шаг

После BFS Exhalation → **Реализация кода** (Task 1.4 implementation)

Документация готова → теперь пишем код:
1. `core/poisson_sampling.py` (Poisson Disk Sampling)
2. `core/exhalation.py` (BFS Exhalation)
3. Интеграция в `core/world_generator.py`
4. Unit tests в `tests/test_respiratory.py`
5. Визуализация `output/respiratory_system_*.png`

---

## Ссылки

1. **BFS Algorithm**
   - Cormen et al., "Introduction to Algorithms" (Chapter 22)
   - Wikipedia: https://en.wikipedia.org/wiki/Breadth-first_search

2. **Spatial Spread Algorithms**
   - Dijkstra's Algorithm for weighted graphs
   - Cellular Automata for complex spread patterns

3. **Applications**
   - Pathfinding in games
   - Flood fill algorithms
   - Disease spread simulation
   - Fire spread modeling

---

**Автор:** Claude Code
**Дата:** 24 октября 2025
**Статус:** ✅ Документация готова
