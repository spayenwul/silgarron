# 02. Perlin Noise - Подробное объяснение

## Что такое Perlin Noise?

**Perlin Noise** - это алгоритм генерации "естественного" шума, изобретённый Кеном Перлином в 1983 году для фильма "Трон".

### Чем отличается от случайного шума?

```
СЛУЧАЙНЫЙ ШУМ (random noise):     PERLIN NOISE:
█▓░█▒▓░▒█░▓█▒░                   ░▒▓███▓▒░░▒▓██▓▒░
▒░█▓▒░█▓░█▒░█▓                   ░░▒▓███▓▒░▒▓██▓▒░
█░▓█▒░█▓▒░█▓░█                   ░░░▒▓███▓▒▓██▓▒░░

Резкие скачки, нет корреляции     Плавные переходы, органично
```

**Ключевая особенность:** Соседние точки имеют похожие значения → плавные холмы и долины.

---

## Зачем это нужно для Сильгаррона?

### Проблема: Как создать "естественный" рельеф?

**❌ Случайные значения:**
```python
elevation = np.random.random((256, 256))
# Результат: хаотичная карта без структуры
```

**✅ Perlin Noise:**
```python
elevation = perlin_noise_2d(256, 256, scale=32)
# Результат: плавные холмы, похожие на реальный ландшафт
```

### Применение в Task 1.2:

1. **Микрорельеф** - базовая "текстура" поверхности
2. **Ridge mask** - вертикальный "позвоночник" (хребет)
3. **Rib mask** - боковые "рёбра"

Комбинируя эти 3 слоя, получаем анатомическую структуру:
```
elevation = perlin_noise + ridge_boost + rib_boost
```

---

## Как работает Perlin Noise? (Упрощённо)

### Шаг 1: Градиентная сетка

Создаём сетку случайных **градиентных векторов**:

```
Сетка 4×4:          Градиенты в узлах:
┌───┬───┬───┬───┐   ↗ ↘ ↖ →
│   │   │   │   │   ↖ → ↓ ↗
├───┼───┼───┼───┤   ← ↗ ↘ ↓
│   │   │   │   │   ↓ ↘ → ↖
├───┼───┼───┼───┤
│   │   │   │   │
├───┼───┼───┼───┤
│   │   │   │   │
└───┴───┴───┴───┘
```

Каждый узел имеет случайный вектор направления.

### Шаг 2: Вычисление для точки

Для каждой точки `(x, y)`:

1. **Найти 4 угловых узла** квадрата, в котором находится точка
2. **Вычислить dot product** с градиентами в этих узлах
3. **Интерполировать** значения (плавно смешать)

```
Точка P внутри квадрата:
┌───────┬───────┐
│   ↗   │   ↘   │  Узлы: A, B, C, D
│       │       │  Градиенты: g_A, g_B, g_C, g_D
├───────P───────┤
│   ↖   │   →   │  Интерполяция: lerp(lerp(A,B), lerp(C,D))
│       │       │
└───────┴───────┘
```

### Шаг 3: Интерполяция (Fade function)

Простая линейная интерполяция даёт **резкие стыки** между квадратами.

**Решение:** Использовать **сглаживающую функцию** (fade function):

```python
def fade(t):
    """Smoothstep function: 6t^5 - 15t^4 + 10t^3"""
    return t * t * t * (t * (t * 6 - 15) + 10)
```

График:
```
1.0 ┤         ┌──────────
    │       ╱
0.5 ┤     ╱
    │   ╱
0.0 ┤──┘
    └────────────────────
    0.0      0.5      1.0
```

Это создаёт **плавные S-образные переходы** между узлами.

---

## Математика (детально)

### Полный алгоритм для 2D:

```python
def perlin_2d(x, y, permutation_table):
    """
    Вычисляет значение Perlin Noise в точке (x, y).

    Args:
        x, y: Координаты точки (float)
        permutation_table: Таблица перестановок [0..255] * 2

    Returns:
        float в диапазоне [-1, 1]
    """
    # 1. Найти координаты угловых узлов
    xi = int(x) & 255  # x целое, маска для зацикливания
    yi = int(y) & 255  # y целое

    # 2. Дробная часть (положение внутри квадрата)
    xf = x - int(x)  # 0.0 - 1.0
    yf = y - int(y)

    # 3. Применить fade function
    u = fade(xf)
    v = fade(yf)

    # 4. Хеши для 4 углов (используем таблицу перестановок)
    aa = permutation_table[permutation_table[xi]     + yi]
    ab = permutation_table[permutation_table[xi]     + yi + 1]
    ba = permutation_table[permutation_table[xi + 1] + yi]
    bb = permutation_table[permutation_table[xi + 1] + yi + 1]

    # 5. Градиенты в 4 углах (dot product с векторами направления)
    g1 = gradient(aa, xf,     yf)      # Левый нижний
    g2 = gradient(ba, xf - 1, yf)      # Правый нижний
    g3 = gradient(ab, xf,     yf - 1)  # Левый верхний
    g4 = gradient(bb, xf - 1, yf - 1)  # Правый верхний

    # 6. Билинейная интерполяция
    x1 = lerp(g1, g2, u)  # Нижняя сторона
    x2 = lerp(g3, g4, u)  # Верхняя сторона

    return lerp(x1, x2, v)  # Финальная интерполяция
```

### Вспомогательные функции:

```python
def fade(t):
    """Smoothstep: 6t^5 - 15t^4 + 10t^3"""
    return t * t * t * (t * (t * 6 - 15) + 10)

def lerp(a, b, t):
    """Линейная интерполяция: a + t*(b-a)"""
    return a + t * (b - a)

def gradient(hash_value, x, y):
    """
    Преобразует хеш в градиентный вектор и вычисляет dot product.

    Используем 4 направления: (1,1), (-1,1), (1,-1), (-1,-1)
    """
    h = hash_value & 3  # Берём последние 2 бита (0, 1, 2, 3)

    if h == 0: return  x + y
    if h == 1: return -x + y
    if h == 2: return  x - y
    if h == 3: return -x - y
```

---

## Octaves (Октавы) - Создание деталей

**Проблема:** Один слой Perlin Noise даёт **гладкую поверхность без деталей**.

**Решение:** Суммировать несколько слоёв с разной **частотой** и **амплитудой**.

### Концепция Octaves:

```
Octave 1 (низкая частота):     ∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿
Крупные холмы

Octave 2 (средняя частота):    ∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿
Средние холмы

Octave 3 (высокая частота):    ∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿
Мелкие детали

СУММА (Fractal Noise):         ╱╲╱╲╱╲╱╲╱╲╱╲╱╲╱╲╱╲
Реалистичный рельеф
```

### Код:

```python
def fractal_perlin_2d(x, y, octaves=4, persistence=0.5, lacunarity=2.0):
    """
    Генерирует фрактальный Perlin Noise (сумма октав).

    Args:
        x, y: Координаты
        octaves: Количество слоёв
        persistence: Уменьшение амплитуды (обычно 0.5)
        lacunarity: Увеличение частоты (обычно 2.0)

    Returns:
        float - сумма октав
    """
    total = 0.0
    frequency = 1.0
    amplitude = 1.0
    max_value = 0.0  # Для нормализации

    for i in range(octaves):
        total += perlin_2d(x * frequency, y * frequency) * amplitude

        max_value += amplitude
        amplitude *= persistence  # Уменьшаем амплитуду
        frequency *= lacunarity   # Увеличиваем частоту

    return total / max_value  # Нормализуем к [-1, 1]
```

**Параметры:**
- `octaves=1`: Гладкая поверхность
- `octaves=4`: Детализированный рельеф
- `octaves=8`: Очень детальный, но медленнее

- `persistence=0.5`: Каждый слой вдвое тише предыдущего
- `persistence=0.8`: Больше деталей (шумнее)

- `lacunarity=2.0`: Каждый слой вдвое чаще предыдущего
- `lacunarity=3.0`: Ещё более частые детали

---

## Применение для Сильгаррона

### 1. Базовый рельеф (Perlin Noise)

```python
def _generate_base_elevation(self):
    """Генерирует базовый микрорельеф"""
    elevation = np.zeros((self.height, self.width))

    for y in range(self.height):
        for x in range(self.width):
            # Нормализуем координаты (scale определяет "zoom")
            nx = x / self.width
            ny = y / self.height

            # Фрактальный Perlin с 4 октавами
            value = fractal_perlin_2d(
                nx * 8,  # scale = 8 (8 "волн" на карту)
                ny * 8,
                octaves=4,
                persistence=0.5
            )

            # Преобразуем из [-1, 1] в [0, 1]
            elevation[y, x] = (value + 1.0) / 2.0

    return elevation
```

### 2. Ridge mask (Вертикальный хребет)

**Цель:** Создать вертикальную полосу повышенных значений по центру.

```python
def _generate_ridge_mask(self):
    """Генерирует маску хребта (вертикальная ось)"""
    ridge = np.zeros((self.height, self.width))

    center_x = self.width // 2  # 128 для карты 256×256

    for y in range(self.height):
        for x in range(self.width):
            # Расстояние от центральной оси
            distance = abs(x - center_x)

            # Нормализуем (0 = центр, 1 = края)
            normalized_dist = distance / (self.width / 2)

            # Гауссова функция: e^(-k*x^2)
            # k=5 даёт узкий хребет, k=1 даёт широкий
            ridge_strength = np.exp(-5 * normalized_dist**2)

            ridge[y, x] = ridge_strength

    return ridge
```

**Визуализация:**
```
Сверху (вид карты):        Сбоку (профиль):

░░░░░███████░░░░░          █
░░░░░███████░░░░░         █ █
░░░░░███████░░░░░        █   █
░░░░░███████░░░░░       █     █
░░░░░███████░░░░░      █       █
                      ░░░░░░░░░░░
Хребет по центру      Гауссова кривая
```

### 3. Rib mask (Боковые "рёбра")

**Цель:** Создать диагональные линии, отходящие от хребта.

```python
def _generate_rib_mask(self):
    """Генерирует маску рёбер (боковые структуры)"""
    ribs = np.zeros((self.height, self.width))

    center_x = self.width // 2
    rib_spacing = 32  # Расстояние между рёбрами
    rib_angle = 30    # Угол наклона (градусы)

    for y in range(self.height):
        for x in range(self.width):
            # Расстояние от центра
            dx = x - center_x

            # Периодическая функция для рёбер
            rib_phase = (y + dx * np.tan(np.radians(rib_angle))) / rib_spacing
            rib_wave = np.cos(rib_phase * 2 * np.pi)

            # Затухание от центра
            distance_from_ridge = abs(dx) / (self.width / 2)
            decay = np.exp(-2 * distance_from_ridge**2)

            ribs[y, x] = max(0, rib_wave) * decay * 0.3  # 0.3 = сила рёбер

    return ribs
```

**Визуализация:**
```
┌─────────────────┐
│  ╱ ╱███╲ ╲      │
│ ╱ ╱ ███ ╲ ╲     │  Рёбра отходят от
│╱ ╱  ███  ╲ ╲    │  центрального хребта
│ ╱   ███   ╲ ╲   │  под углом
│╱    ███    ╲ ╲  │
└─────────────────┘
```

### 4. Финальная комбинация

```python
def _generate_skeletal_structure(self):
    """Генерирует полную скелетную структуру"""
    # 1. Базовый рельеф (0.0-1.0)
    base_elevation = self._generate_base_elevation()

    # 2. Хребет (0.0-1.0)
    ridge_mask = self._generate_ridge_mask()

    # 3. Рёбра (0.0-0.3)
    rib_mask = self._generate_rib_mask()

    # 4. Комбинируем с весами
    elevation = (
        base_elevation * 0.3 +  # 30% базовый шум
        ridge_mask * 0.5 +      # 50% хребет
        rib_mask * 0.2          # 20% рёбра
    )

    # Нормализуем в [0, 1]
    elevation = np.clip(elevation, 0.0, 1.0)

    return {
        'elevation': elevation,
        'ridge_mask': ridge_mask,
        'rib_mask': rib_mask
    }
```

---

## Оптимизация: Векторизация

**Проблема:** Циклы `for y... for x...` очень медленные для 256×256 = 65536 точек.

**Решение:** Использовать NumPy векторизацию:

```python
def _generate_base_elevation_vectorized(self):
    """Быстрая векторизованная версия"""
    # Создаём сетку координат (meshgrid)
    x_coords = np.arange(self.width)
    y_coords = np.arange(self.height)
    X, Y = np.meshgrid(x_coords, y_coords)

    # Нормализуем
    nx = X / self.width * 8
    ny = Y / self.height * 8

    # Генерируем Perlin для всех точек сразу
    elevation = fractal_perlin_2d_vectorized(nx, ny, octaves=4)

    # Преобразуем в [0, 1]
    elevation = (elevation + 1.0) / 2.0

    return elevation
```

**Ускорение:** 100x-1000x быстрее!

---

## Валидация

### Unit Tests:

```python
def test_perlin_noise_deterministic():
    """Perlin Noise детерминирован для seed"""
    gen1 = WorldGenerator(seed="test")
    gen2 = WorldGenerator(seed="test")

    result1 = gen1._generate_skeletal_structure()
    result2 = gen2._generate_skeletal_structure()

    assert np.array_equal(result1['elevation'], result2['elevation'])

def test_elevation_in_range():
    """Elevation в диапазоне [0, 1]"""
    gen = WorldGenerator(seed="test")
    result = gen._generate_skeletal_structure()

    elevation = result['elevation']
    assert np.all(elevation >= 0.0)
    assert np.all(elevation <= 1.0)

def test_ridge_is_vertical():
    """Хребет проходит вертикально по центру"""
    gen = WorldGenerator(seed="test")
    result = gen._generate_skeletal_structure()

    ridge = result['ridge_mask']
    center_x = gen.width // 2

    # Проверяем, что центр имеет максимальные значения
    center_column = ridge[:, center_x]
    assert np.mean(center_column) > 0.8

    # Проверяем, что края имеют минимальные значения
    left_edge = ridge[:, 0]
    right_edge = ridge[:, -1]
    assert np.mean(left_edge) < 0.1
    assert np.mean(right_edge) < 0.1
```

### Visual Validation:

После реализации создадим PNG:
- Слой 1: Базовый Perlin Noise (оттенки серого)
- Слой 2: Ridge mask (красный канал)
- Слой 3: Rib mask (синий канал)
- Composite: Финальный elevation (цветовая карта)

**Критерий успеха:** На composite виден вертикальный "позвоночник" с боковыми "рёбрами".

---

## Ссылки и ресурсы

1. **Ken Perlin's original paper (1985)**
   - "An Image Synthesizer"
   - SIGGRAPH '85

2. **Improved Perlin Noise (2002)**
   - Исправлены артефакты оригинала
   - Используется в современных реализациях

3. **Online визуализации:**
   - https://www.redblobgames.com/maps/terrain-from-noise/
   - https://adrianb.io/2014/08/09/perlinnoise.html

4. **Альтернативы:**
   - Simplex Noise (быстрее, но сложнее)
   - Worley Noise (для клеточных структур)
   - Value Noise (проще, но менее естественный)

---

## Следующие шаги

1. Реализовать Perlin Noise в `core/world_generator.py`
2. Добавить Ridge и Rib masks
3. Написать unit tests
4. Создать визуализацию
5. Тюнинг параметров (octaves, scale, веса)

**Готовность к реализации:** 100%

---

**Автор:** Claude Code
**Дата:** 23 октября 2025
**Статус:** ✅ Документация готова
