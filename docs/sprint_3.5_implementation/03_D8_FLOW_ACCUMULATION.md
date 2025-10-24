# 03. D8 Flow Accumulation - Гидрологический алгоритм

## Что это?

**D8 Flow Accumulation** - это гидрологический алгоритм для моделирования течения воды по рельефу.

В контексте Сильгаррона: моделирует **лимфатическую систему** (каналы циркуляции "крови" организма).

### Название "D8"
- **D** = Deterministic (детерминированный)
- **8** = 8 направлений (все 8 соседей: N, NE, E, SE, S, SW, W, NW)

---

## Зачем это нужно?

### Проблема: Как вода течёт по рельефу?

Представьте дождь на горе:
```
    ⛰️ Вершина
   💧💧💧 Капли дождя
  ↓  ↓  ↓
 ~~~💧💧💧~~~ Ручьи
↓    ↓    ↓
🌊🌊🌊 Река внизу
```

**Вопросы:**
1. В какую сторону течёт каждая капля?
2. Где формируются русла рек?
3. Сколько воды проходит через каждую точку?

**D8 Flow Accumulation даёт ответы!**

### Применение для Сильгаррона:

Лимфатическая система = "кровеносные сосуды" мира:
- **Истоки** - возвышенности на хребте (где "сердце")
- **Лимфотоки** - каналы циркуляции (как вены)
- **Аккумуляция** - интенсивность потока (толщина сосудов)

---

## Как работает алгоритм? (Пошагово)

### Шаг 1: D8 Flow Direction

Для каждой ячейки определяем: **куда течёт вода?**

**Правило:** Вода течёт в соседа с **наименьшей высотой**.

```
Пример рельефа (цифры = высота):

┌───┬───┬───┐
│ 9 │ 8 │ 7 │   Центральная ячейка (5)
├───┼───┼───┤   Соседи: 9,8,7,6,4,3,2,1
│ 6 │ 5 │ 4 │   Минимум = 1 (внизу-слева)
├───┼───┼───┤   → Вода течёт туда ↙
│ 3 │ 2 │ 1 │
└───┴───┴───┘
```

**D8 кодирование направлений:**
```
Числа означают направление потока:

32  64  128
   ↖ ↑ ↗
16 ← ● → 1
   ↙ ↓ ↘
 8   4   2

Пример выше: направление = 8 (вниз-влево)
```

**Код:**
```python
def calculate_flow_direction(elevation):
    """
    Вычисляет направление потока для каждой ячейки.

    Returns:
        flow_dir: np.ndarray - направление (1,2,4,8,16,32,64,128)
    """
    height, width = elevation.shape
    flow_dir = np.zeros((height, width), dtype=np.uint8)

    # 8 направлений: (dy, dx, code)
    directions = [
        (-1,  0, 64),   # N (вверх)
        (-1,  1, 128),  # NE
        ( 0,  1, 1),    # E (вправо)
        ( 1,  1, 2),    # SE
        ( 1,  0, 4),    # S (вниз)
        ( 1, -1, 8),    # SW
        ( 0, -1, 16),   # W (влево)
        (-1, -1, 32),   # NW
    ]

    for y in range(height):
        for x in range(width):
            current_height = elevation[y, x]

            # Найти соседа с минимальной высотой
            min_height = current_height
            flow_code = 0  # 0 = нет потока (локальный минимум)

            for dy, dx, code in directions:
                ny, nx = y + dy, x + dx

                # Проверка границ
                if 0 <= ny < height and 0 <= nx < width:
                    neighbor_height = elevation[ny, nx]

                    if neighbor_height < min_height:
                        min_height = neighbor_height
                        flow_code = code

            flow_dir[y, x] = flow_code

    return flow_dir
```

### Шаг 2: Flow Accumulation

Для каждой ячейки считаем: **сколько ячеек в неё втекает?**

**Правило:** Аккумуляция = количество всех ячеек выше по течению + 1 (сама ячейка).

```
Пример потока:

A → B → C → D
    ↑   ↑
    E   F

Flow Accumulation:
A = 1 (только сама)
E = 1 (только сама)
B = 3 (A + E + B)
F = 1 (только сама)
C = 5 (A + E + B + F + C)
D = 6 (A + E + B + F + C + D)

D имеет самую высокую аккумуляцию → главное русло!
```

**Алгоритм:**
1. Сортируем ячейки от высоких к низким (топологическая сортировка)
2. Для каждой ячейки (от высоких к низким):
   - Начальная аккумуляция = 1
   - Передаём аккумуляцию в направлении потока
   - Ячейка-приёмник += аккумуляция текущей

**Код:**
```python
def calculate_flow_accumulation(elevation, flow_dir):
    """
    Вычисляет аккумуляцию потока (количество втекающих ячеек).

    Returns:
        accumulation: np.ndarray - количество ячеек, которые втекают
    """
    height, width = elevation.shape
    accumulation = np.ones((height, width), dtype=np.float32)

    # Создаём список ячеек, отсортированных по высоте (от высоких к низким)
    cells = []
    for y in range(height):
        for x in range(width):
            cells.append((elevation[y, x], y, x))

    cells.sort(reverse=True)  # От высоких к низким

    # Обрабатываем от истоков к устьям
    for elev, y, x in cells:
        current_accum = accumulation[y, x]
        direction = flow_dir[y, x]

        if direction == 0:
            continue  # Локальный минимум (сток)

        # Находим следующую ячейку
        dy, dx = decode_direction(direction)
        ny, nx = y + dy, x + dx

        # Проверка границ
        if 0 <= ny < height and 0 <= nx < width:
            # Передаём аккумуляцию вниз по потоку
            accumulation[ny, nx] += current_accum

    return accumulation

def decode_direction(code):
    """Преобразует код направления в (dy, dx)"""
    direction_map = {
        64: (-1,  0),   # N
        128: (-1,  1),  # NE
        1: ( 0,  1),    # E
        2: ( 1,  1),    # SE
        4: ( 1,  0),    # S
        8: ( 1, -1),    # SW
        16: ( 0, -1),   # W
        32: (-1, -1),   # NW
    }
    return direction_map.get(code, (0, 0))
```

---

## Применение для Сильгаррона

### 1. Найти истоки лимфотоков

**Критерий:** Высокие точки на хребте с низкой аккумуляцией.

```python
def find_lymph_sources(elevation, ridge_mask, flow_accumulation, num_sources=8):
    """
    Находит истоки лимфатических каналов.

    Критерии:
    - Находятся на хребте (ridge_mask > 0.5)
    - Высокие точки (elevation > 0.6)
    - Малая аккумуляция (локальные пики)
    """
    # Маска кандидатов
    candidates = (
        (ridge_mask > 0.5) &          # На хребте
        (elevation > 0.6) &            # Высокие точки
        (flow_accumulation < 5)        # Малая аккумуляция (истоки)
    )

    # Находим координаты
    y_coords, x_coords = np.where(candidates)

    # Выбираем num_sources самых высоких
    if len(y_coords) > num_sources:
        heights = elevation[y_coords, x_coords]
        top_indices = np.argsort(heights)[-num_sources:]
        y_coords = y_coords[top_indices]
        x_coords = x_coords[top_indices]

    sources = list(zip(y_coords.tolist(), x_coords.tolist()))
    return sources
```

### 2. Создать маску лимфатических каналов

**Критерий:** Высокая аккумуляция = главные русла.

```python
def create_lymph_channels_mask(flow_accumulation, threshold_percentile=90):
    """
    Создаёт маску лимфатических каналов.

    Ячейки с высокой аккумуляцией = главные каналы.
    """
    # Определяем порог (например, верхние 10% аккумуляции)
    threshold = np.percentile(flow_accumulation, threshold_percentile)

    # Маска каналов
    lymph_mask = (flow_accumulation >= threshold).astype(np.float32)

    # Нормализуем интенсивность
    lymph_intensity = flow_accumulation / flow_accumulation.max()
    lymph_intensity = np.clip(lymph_intensity, 0.0, 1.0)

    return lymph_mask, lymph_intensity
```

### 3. Визуализация

**Что покажем:**
1. **Flow Direction** - стрелки направлений
2. **Flow Accumulation** - heatmap интенсивности
3. **Lymph Sources** - красные точки истоков
4. **Lymph Channels** - золотые "реки"

---

## Особенности D8

### Преимущества ✅
1. **Простота** - понятная логика
2. **Скорость** - O(n) после сортировки
3. **Детерминизм** - всегда одинаковый результат
4. **Топологическая корректность** - вода не течёт вверх

### Недостатки ⚠️
1. **8 направлений только** - диагонали имеют тот же вес, что и прямые
2. **Артефакты "линий"** - поток идёт строго по 8 направлениям
3. **Не учитывает инерцию** - каждая ячейка независима

### Альтернативы:
- **D-Infinity (D∞)** - бесконечное количество направлений
- **MFD (Multiple Flow Direction)** - вода течёт в несколько соседей
- **Dinf** - более точное моделирование

Для Сильгаррона **D8 достаточно** - мы моделируем анатомию, а не реальную гидрологию.

---

## Решение проблем

### Проблема 1: Плоские области (flat areas)

**Что происходит:** В плоских зонах нет градиента → вода не знает, куда течь.

**Решение:** Добавить малый случайный шум к elevation перед вычислением.

```python
# Добавляем микрошум (1e-6) для разрешения ties
elevation_perturbed = elevation + np.random.random(elevation.shape) * 1e-6
```

### Проблема 2: Замкнутые впадины (sinks)

**Что происходит:** Ячейка ниже всех соседей → вода "застревает".

**Решение 1:** Найти и "заполнить" впадины до уровня минимального выхода.

**Решение 2:** Игнорировать (для Сильгаррона это "озёра" лимфы).

### Проблема 3: Края карты

**Что происходит:** На границе нет соседей → вода "исчезает".

**Решение:** Края считаются естественными "стоками" (вода уходит за границу).

---

## Валидация

### Unit Tests:

```python
def test_flow_goes_downhill():
    """Поток течёт от высоких точек к низким"""
    # Создаём простой рельеф: наклон вправо
    elevation = np.tile(np.arange(10, 0, -1), (10, 1))

    flow_dir = calculate_flow_direction(elevation)

    # Все ячейки (кроме края) должны течь вправо (code=1)
    assert np.all(flow_dir[:, :-1] == 1)

def test_accumulation_increases_downstream():
    """Аккумуляция растёт вниз по потоку"""
    elevation = np.arange(100).reshape(10, 10)[::-1, :]

    flow_dir = calculate_flow_direction(elevation)
    accumulation = calculate_flow_accumulation(elevation, flow_dir)

    # Левый верхний угол (исток) должен иметь малую аккумуляцию
    assert accumulation[0, 0] == 1

    # Правый нижний угол (устье) должен иметь высокую
    assert accumulation[-1, -1] > 50

def test_sources_on_ridge():
    """Истоки находятся на хребте"""
    gen = WorldGenerator(seed="test")
    result = gen.generate()

    lymphatic = result['lymphatic']
    sources = lymphatic['source_points']
    ridge_mask = result['skeletal']['ridge_mask']

    for y, x in sources:
        # Каждый исток должен быть на хребте (ridge > 0.5)
        assert ridge_mask[y, x] > 0.5
```

### Visual Validation:

После реализации проверяем PNG:
- **Flow Accumulation:** Видны "реки" (яркие линии от хребта к краям)
- **Sources:** Красные точки на хребте
- **Channels:** Золотые линии текут вниз от истоков

**Критерий успеха:** Лимфотоки текут **от хребта к краям**, а не хаотично.

---

## Оптимизация

### Узкое место: Сортировка ячеек

**Проблема:** Сортировка 65536 ячеек (256×256) занимает время.

**Решение:** Используем NumPy vectorization:

```python
# Вместо явной сортировки списка:
cells = [(elevation[y, x], y, x) for y in range(h) for x in range(w)]
cells.sort(reverse=True)

# Используем np.argsort:
flat_elevation = elevation.flatten()
sorted_indices = np.argsort(flat_elevation)[::-1]  # От высоких к низким
y_coords = sorted_indices // width
x_coords = sorted_indices % width
```

**Ускорение:** ~10x

---

## Параметры для Сильгаррона

```python
# Количество истоков лимфотоков
NUM_LYMPH_SOURCES = 8  # По "рёбрам" организма

# Порог для каналов (percentile)
LYMPH_CHANNEL_THRESHOLD = 90  # Верхние 10% аккумуляции

# Минимальная высота истоков
SOURCE_MIN_ELEVATION = 0.6  # Только на возвышенностях

# Минимальное значение ridge для истоков
SOURCE_MIN_RIDGE = 0.5  # Только на хребте
```

---

## Биологическая интерпретация

| Гидрология | Сильгаррон (Лимфатическая система) |
|------------|-------------------------------------|
| Дождь | Выделение лимфы "сердцем" на хребте |
| Русло реки | Лимфатический канал |
| Аккумуляция | Интенсивность циркуляции |
| Исток | Источник лимфы (на хребте) |
| Устье | Выход лимфы (на краях организма) |
| Водораздел | Граница между "долями" организма |

---

## Ссылки и ресурсы

1. **Jenson & Domingue (1988)**
   - "Extracting Topographic Structure from Digital Elevation Data"
   - Оригинальная статья о D8

2. **Tarboton (1997)**
   - "A new method for the determination of flow directions"
   - D-Infinity algorithm

3. **O'Callaghan & Mark (1984)**
   - "The extraction of drainage networks from digital elevation data"
   - Ранняя работа по flow direction

4. **Online визуализации:**
   - https://desktop.arcgis.com/en/arcmap/latest/tools/spatial-analyst-toolbox/flow-direction.htm
   - https://www.whiteboxgeo.com/manual/wbt_book/available_tools/hydrological_analysis.html

---

## Следующие шаги

1. Реализовать `calculate_flow_direction()`
2. Реализовать `calculate_flow_accumulation()`
3. Реализовать `find_lymph_sources()`
4. Реализовать `create_lymph_channels_mask()`
5. Интегрировать в `_generate_lymphatic_system()`
6. Написать unit tests
7. Создать визуализацию

**Готовность к реализации:** 100%

---

**Автор:** Claude Code
**Дата:** 23 октября 2025
**Статус:** ✅ Документация готова
