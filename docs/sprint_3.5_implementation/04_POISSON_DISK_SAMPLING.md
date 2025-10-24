# 04. Poisson Disk Sampling - Равномерное распределение точек

## Что это?

**Poisson Disk Sampling** - это алгоритм для размещения точек на плоскости так, чтобы они были:
1. **Равномерно распределены** (не кучкуются)
2. **На минимальном расстоянии друг от друга** (не слишком близко)
3. **Максимально плотно** (заполняют всё пространство)

Результат выглядит **органично** и **естественно**, как семена в подсолнухе или клетки в ткани.

---

## Зачем это нужно для Сильгаррона?

### Проблема: Как разместить альвеолярные каверны?

**❌ Случайное размещение:**
```python
caverns = []
for i in range(num_caverns):
    x, y = random.randint(0, width), random.randint(0, height)
    caverns.append((y, x))
```

**Проблемы:**
- Каверны кучкуются (могут быть очень близко)
- Большие пустые области (неравномерность)
- Выглядит неестественно

**✅ Poisson Disk Sampling:**
```python
caverns = poisson_disk_sampling(
    width=256,
    height=256,
    min_distance=30  # Минимум 30 пикселей между кавернами
)
```

**Преимущества:**
- Равномерное распределение по карте
- Никакие две каверны не ближе 30 пикселей
- Органичный, естественный вид
- Максимально плотное заполнение

---

## Как работает алгоритм? (Bridson's Algorithm)

### Идея:

1. Начинаем с одной случайной точки
2. Генерируем кандидатов вокруг существующих точек
3. Принимаем кандидата, если он достаточно далеко от всех других
4. Повторяем, пока не заполним пространство

### Пошагово:

#### Шаг 1: Инициализация

```python
min_distance = 30  # Минимальное расстояние между точками
k = 30             # Количество попыток для каждой точки

# Создаём сетку для быстрого поиска соседей
cell_size = min_distance / np.sqrt(2)
grid = {}  # Словарь: (grid_x, grid_y) → точка

# Активный список (точки, вокруг которых ищем кандидатов)
active_list = []

# Добавляем первую случайную точку
first_point = (random.uniform(0, width), random.uniform(0, height))
active_list.append(first_point)
grid[point_to_grid(first_point)] = first_point
```

#### Шаг 2: Генерация кандидатов

Для каждой точки в `active_list`:

```python
while active_list:
    # Берём случайную точку из активного списка
    point = active_list[random.randint(0, len(active_list) - 1)]

    # Пытаемся k раз найти подходящего кандидата
    found = False
    for attempt in range(k):
        # Генерируем кандидата в кольце [min_distance, 2*min_distance]
        angle = random.uniform(0, 2 * np.pi)
        radius = random.uniform(min_distance, 2 * min_distance)

        candidate = (
            point[0] + radius * np.cos(angle),
            point[1] + radius * np.sin(angle)
        )

        # Проверяем валидность
        if is_valid(candidate, grid, min_distance):
            # Добавляем кандидата
            active_list.append(candidate)
            grid[point_to_grid(candidate)] = candidate
            found = True
            break

    # Если не нашли кандидата, удаляем точку из активного списка
    if not found:
        active_list.remove(point)
```

#### Шаг 3: Проверка валидности

```python
def is_valid(candidate, grid, min_distance, width, height):
    # 1. Проверка границ
    if not (0 <= candidate[0] < width and 0 <= candidate[1] < height):
        return False

    # 2. Проверка расстояния до соседей (используем сетку для быстроты)
    grid_pos = point_to_grid(candidate)
    cell_size = min_distance / np.sqrt(2)

    # Проверяем только соседние ячейки сетки
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            neighbor_cell = (grid_pos[0] + dx, grid_pos[1] + dy)

            if neighbor_cell in grid:
                neighbor_point = grid[neighbor_cell]
                distance = euclidean_distance(candidate, neighbor_point)

                if distance < min_distance:
                    return False  # Слишком близко!

    return True  # Кандидат подходит
```

---

## Визуализация процесса

```
Шаг 1: Первая точка
┌─────────────┐
│             │
│      ●      │  ← Первая случайная точка
│             │
└─────────────┘

Шаг 2: Кандидаты вокруг первой точки
┌─────────────┐
│    ○   ○    │  ○ = кандидаты в кольце
│  ○   ●   ○  │  ● = принятая точка
│    ○   ○    │
└─────────────┘

Шаг 3: Принимаем подходящие кандидаты
┌─────────────┐
│    ●       ●│  ● = принятые точки
│       ●     │  (расстояние >= min_distance)
│  ●       ●  │
└─────────────┘

Итерация...
┌─────────────┐
│ ● ● ● ● ● ● │
│ ● ● ● ● ● ● │  Равномерное заполнение
│ ● ● ● ● ● ● │
│ ● ● ● ● ● ● │
└─────────────┘
```

---

## Применение для Сильгаррона

### Размещение альвеолярных каверн:

```python
def place_alveolar_caverns(
    width: int,
    height: int,
    elevation: np.ndarray,
    min_distance: float = 30.0,
    elevation_range: Tuple[float, float] = (0.2, 0.7),
    rng: np.random.Generator = None
) -> List[Tuple[int, int]]:
    """
    Размещает альвеолярные каверны (источники выдоха) через Poisson Disk Sampling.

    Критерии:
    - Равномерно распределены (Poisson)
    - Минимальное расстояние min_distance между кавернами
    - Только в определённом диапазоне высот (не на пиках, не в низинах)

    Args:
        width, height: Размеры карты
        elevation: Карта высот
        min_distance: Минимальное расстояние между кавернами
        elevation_range: Диапазон высот для размещения
        rng: Random generator для детерминизма

    Returns:
        List[(y, x)] - координаты каверн
    """
    min_elev, max_elev = elevation_range
    caverns = []

    # Используем Bridson's Algorithm с фильтром по высоте
    cell_size = min_distance / np.sqrt(2)
    grid = {}
    active_list = []

    # Первая точка (случайная в валидной зоне)
    attempts = 0
    while attempts < 1000:
        x = rng.uniform(0, width)
        y = rng.uniform(0, height)

        if min_elev <= elevation[int(y), int(x)] <= max_elev:
            first_point = (y, x)
            active_list.append(first_point)
            grid[point_to_grid(first_point, cell_size)] = first_point
            caverns.append((int(y), int(x)))
            break

        attempts += 1

    # Генерируем остальные точки
    k = 30  # Попытки для каждой точки
    while active_list and len(caverns) < 100:  # Лимит 100 каверн
        # Случайная точка из активного списка
        point_idx = rng.integers(0, len(active_list))
        point = active_list[point_idx]

        found = False
        for _ in range(k):
            # Кандидат в кольце [min_distance, 2*min_distance]
            angle = rng.uniform(0, 2 * np.pi)
            radius = rng.uniform(min_distance, 2 * min_distance)

            candidate_y = point[0] + radius * np.sin(angle)
            candidate_x = point[1] + radius * np.cos(angle)

            # Проверка валидности
            if (0 <= candidate_x < width and
                0 <= candidate_y < height and
                min_elev <= elevation[int(candidate_y), int(candidate_x)] <= max_elev and
                is_valid_distance(candidate_y, candidate_x, grid, min_distance, cell_size)):

                # Добавляем
                candidate = (candidate_y, candidate_x)
                active_list.append(candidate)
                grid[point_to_grid(candidate, cell_size)] = candidate
                caverns.append((int(candidate_y), int(candidate_x)))
                found = True
                break

        if not found:
            active_list.pop(point_idx)

    return caverns
```

### Биологическая интерпретация:

| Параметр | Значение | Биологический смысл |
|----------|----------|---------------------|
| `min_distance` | 30 пикселей | Каверны = "альвеолы" лёгких, не слишком близко |
| `elevation_range` | [0.2, 0.7] | В мягких тканях (не в кости, не в низинах) |
| `k` | 30 попыток | Плотность заполнения |

---

## Оптимизация: Сетка для быстрого поиска

**Проблема:** Проверка расстояния до всех точек = O(n) для каждого кандидата → медленно!

**Решение:** Используем **пространственную сетку** (spatial grid).

```python
# Размер ячейки сетки
cell_size = min_distance / np.sqrt(2)

# Преобразование координат в индексы сетки
def point_to_grid(point, cell_size):
    return (
        int(point[0] / cell_size),
        int(point[1] / cell_size)
    )

# Проверяем только соседние ячейки (3x3 = 9 ячеек)
for dx in [-1, 0, 1]:
    for dy in [-1, 0, 1]:
        neighbor_cell = (grid_x + dx, grid_y + dy)
        if neighbor_cell in grid:
            check_distance(grid[neighbor_cell])
```

**Ускорение:** O(n) → O(1) для проверки расстояния!

---

## Параметры для настройки

### `min_distance` (минимальное расстояние):
- **Маленькое** (10-20) → много каверн, плотно
- **Среднее** (30-40) → умеренная плотность
- **Большое** (50+) → мало каверн, разреженно

### `k` (количество попыток):
- **Маленькое** (10-20) → быстро, но неполное заполнение
- **Среднее** (30) → баланс
- **Большое** (50+) → медленнее, но плотнее заполнение

### `elevation_range` (диапазон высот):
- **[0.0, 1.0]** → каверны везде
- **[0.2, 0.7]** → в мягких тканях (рекомендуется)
- **[0.5, 0.8]** → в предгорьях

---

## Валидация

### Unit Tests:

```python
def test_poisson_min_distance():
    """Все каверны на минимальном расстоянии друг от друга"""
    caverns = place_alveolar_caverns(
        width=256,
        height=256,
        elevation=np.random.random((256, 256)),
        min_distance=30
    )

    # Проверяем попарно
    for i, (y1, x1) in enumerate(caverns):
        for y2, x2 in caverns[i+1:]:
            distance = np.sqrt((y1 - y2)**2 + (x1 - x2)**2)
            assert distance >= 30, f"Distance {distance} < 30"

def test_poisson_elevation_filter():
    """Каверны только в заданном диапазоне высот"""
    elevation = np.linspace(0, 1, 256*256).reshape(256, 256)

    caverns = place_alveolar_caverns(
        width=256,
        height=256,
        elevation=elevation,
        elevation_range=(0.3, 0.7)
    )

    for y, x in caverns:
        assert 0.3 <= elevation[y, x] <= 0.7
```

### Visual Validation:

После реализации проверяем PNG:
- Каверны равномерно распределены (не кучкуются)
- Нет больших пустых областей
- Визуально "органичное" распределение

---

## Альтернативы

### 1. Uniform Random (случайное):
- ❌ Кучкуется
- ❌ Неравномерно
- ✅ Очень быстро

### 2. Grid (регулярная сетка):
- ❌ Выглядит искусственно
- ✅ Гарантированно равномерно
- ✅ Быстро

### 3. Poisson Disk Sampling:
- ✅ Равномерно
- ✅ Органично
- ✅ Контроль плотности
- ⚠️ Чуть медленнее (но приемлемо)

**Для Сильгаррона:** Poisson Disk Sampling - лучший выбор!

---

## Ссылки

1. **Robert Bridson (2007)**
   - "Fast Poisson Disk Sampling in Arbitrary Dimensions"
   - SIGGRAPH 2007

2. **Online визуализации:**
   - https://www.jasondavies.com/poisson-disc/
   - https://observablehq.com/@techsture/poisson-disc-sampling

3. **Применения:**
   - Размещение деревьев/растений в играх
   - Генерация текстур
   - Размещение городов на картах
   - Научная визуализация

---

## Следующий шаг

После Poisson Disk Sampling → **BFS Exhalation** (05_BFS_EXHALATION.md)

Каверны размещены → теперь нужно распространить споры от них!

---

**Автор:** Claude Code
**Дата:** 23 октября 2025
**Статус:** ✅ Документация готова
