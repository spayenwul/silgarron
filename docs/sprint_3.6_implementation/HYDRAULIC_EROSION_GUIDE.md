# Hydraulic Erosion для "Лимфатической эрозии" Сильгаррона

**Категория:** Алгоритмическая документация
**Версия:** 3.0
**Дата:** 29 октября 2025
**Статус:** 🆕 Новая фаза v3.0 - в планировании (Sprint 3.8)

**Phase:** 4.5 (Hydraulic Erosion)

---

## Обзор

Гидравлическая эрозия - это симуляция реалистичного "вымывания" ландшафта водными потоками. В контексте Сильгаррона это **"Лимфатическая эрозия"** - подземная лимфа выходит на поверхность в точках артериальных выходов (vein outlets), создавая глубокие речные долины.

**Ключевая особенность v3.0:**
1. **Фокусировка источников** - мощные источники в точках выхода артерий
2. **Bone protection** - кости эродируются значительно медленнее мягких тканей
3. **Gaussian pre-processing** - сглаживание рельефа перед эрозией

---

## Философия

> В Сильгарроне реки - это НЕ только поверхностный сток. Они питаются из **выходов подземных артерий** (лимфатических каналов). Артерия → выход на поверхность → исток реки → эрозия → глубокая долина.

**Аналогия:** Представьте грунтовые воды, выходящие на поверхность через родники. В местах выхода формируются мощные потоки, которые со временем прорезают глубокие каньоны.

---

## Проблемы базовой гидравлической эрозии

### Проблема 1: Резкие вертикальные артефакты

**Проблема:**
Если рельеф создан L-Systems (Phase 2), он может содержать резкие вертикальные структуры (рёбра, хребты). Базовая гидравлическая эрозия некорректно обрабатывает такие артефакты.

**Решение:**
Предварительная обработка - Gaussian smoothing (sigma=2.0) перед эрозией.

### Проблема 2: Равномерное "смывание" ландшафта

**Проблема:**
Стандартная эрозия использует равномерный "дождь" по всей карте, что приводит к равномерному сглаживанию всего рельефа.

**Решение:**
Фокусировка источников - мощные источники в vein_outlets (×100), очень слабый фоновый дождь (0.01).

### Проблема 3: Эрозия костей

**Проблема:**
Кости - это твёрдая хитино-кремниевая ткань, прочнее стали. Они НЕ должны эродироваться с той же скоростью, что мягкие ткани.

**Решение:**
Bone protection - кости эродируются в 3 раза медленнее (30% скорости).

---

## Алгоритм

### Шаг 0: Предварительная обработка (Gaussian Smoothing)

```python
from scipy.ndimage import gaussian_filter

# Сглаживание рельефа перед эрозией
elevation_for_erosion = gaussian_filter(elevation, sigma=2.0)

# sigma=2.0: Убирает резкие пиксельные артефакты
# Макро-структура (хребты, долины) сохраняется
```

**Эффект:**
- Резкие "ступени" от L-Systems сглаживаются
- Общая форма хребтов и долин сохраняется
- Алгоритм эрозии работает корректно

### Шаг 1: Инициализация карты воды

```python
# Базовая карта "осадков"
water_map = np.ones((512, 512)) * 0.01  # Очень слабый фоновый дождь

# ФОКУСИРОВКА: Мощные источники в точках выхода артерий
for outlet in vein_outlets:
    x, y = outlet['position']
    water_map[y, x] += outlet['strength'] * 100  # В 100 раз сильнее дождя!
```

**Параметры:**
- Background rain: `0.01` (очень слабый, почти отсутствует)
- Vein outlet strength: `outlet['strength'] × 100`

**Результат:** Вода концентрируется в точках выхода артерий.

### Шаг 2: Симуляция водного потока (D8 или Particle-based)

```python
# D8 Flow Direction
def calculate_d8_flow(elevation, water_map):
    """
    Для каждой клетки определяет направление стока воды
    """
    flow_map = np.zeros_like(elevation)

    for y in range(1, elevation.shape[0] - 1):
        for x in range(1, elevation.shape[1] - 1):
            # Найти соседа с минимальной высотой
            neighbors = [
                (elevation[y-1, x-1], -1, -1),  # NW
                (elevation[y-1, x  ], -1,  0),  # N
                (elevation[y-1, x+1], -1,  1),  # NE
                (elevation[y  , x-1],  0, -1),  # W
                (elevation[y  , x+1],  0,  1),  # E
                (elevation[y+1, x-1],  1, -1),  # SW
                (elevation[y+1, x  ],  1,  0),  # S
                (elevation[y+1, x+1],  1,  1),  # SE
            ]

            min_neighbor = min(neighbors, key=lambda n: n[0])

            # Если соседняя клетка ниже текущей - вода течёт туда
            if min_neighbor[0] < elevation[y, x]:
                dy, dx = min_neighbor[1], min_neighbor[2]
                flow_map[y + dy, x + dx] += water_map[y, x]

    return flow_map
```

**Результат:** Карта накопленного потока (flow_map).

### Шаг 3: Эрозия и осаждение

```python
def apply_erosion_step(elevation, flow_map, bone_density_map, erosion_rate, bone_protection=True):
    """
    Применяет один шаг эрозии
    """
    eroded_elevation = elevation.copy()

    for y in range(elevation.shape[0]):
        for x in range(elevation.shape[1]):
            flow = flow_map[y, x]

            if flow > 0:
                # Эрозия: вода уносит материал
                erosion_amount = erosion_rate * flow

                # BONE PROTECTION: кости эродируются медленнее
                if bone_protection:
                    bone_density = bone_density_map[y, x]
                    if bone_density > 0.5:  # Плотная кость
                        erosion_amount *= 0.3  # В 3 раза медленнее!

                # Применяем эрозию
                eroded_elevation[y, x] -= erosion_amount

                # Осаждение: материал откладывается ниже по течению
                # (В упрощённой версии можно пропустить)

    return eroded_elevation
```

### Шаг 4: Итеративное применение

```python
def hydraulic_erosion_focused(
    elevation,
    bone_density_map,
    vein_outlets,
    iterations=50,
    erosion_rate=0.3,
    bone_protection=True
):
    """
    Полная гидравлическая эрозия с фокусировкой
    """
    # Предварительная обработка
    elevation = gaussian_filter(elevation, sigma=2.0)

    eroded_elevation = elevation.copy()

    for iteration in range(iterations):
        # 1. Распределение воды
        water_map = np.ones_like(elevation) * 0.01  # Фоновый дождь

        # Мощные источники в vein_outlets
        for outlet in vein_outlets:
            x, y = outlet['position']
            water_map[y, x] += outlet['strength'] * 100

        # 2. Симуляция потока
        flow_map = calculate_d8_flow(eroded_elevation, water_map)

        # 3. Эрозия
        eroded_elevation = apply_erosion_step(
            eroded_elevation,
            flow_map,
            bone_density_map,
            erosion_rate,
            bone_protection
        )

    return eroded_elevation
```

---

## Параметры

### Основные параметры

| Параметр | Тип | Значение | Описание |
|----------|-----|----------|----------|
| `iterations` | int | `50` | Количество циклов симуляции |
| `erosion_rate` | float | `0.3` | Скорость эрозии [0.1-1.0] |
| `bone_protection` | bool | `True` | Защита костей от эрозии |
| `bone_protection_multiplier` | float | `0.3` | Кости эродируются на 30% скорости |
| `sigma` (Gaussian) | float | `2.0` | Радиус сглаживания перед эрозией |
| `source_multiplier` | float | `100.0` | Множитель силы vein_outlets |
| `background_rain` | float | `0.01` | Фоновый дождь (очень слабый) |

### Настройка параметров

#### iterations (количество итераций)

**Низкое (20-30):**
- Лёгкая эрозия
- Неглубокие долины
- Быстрее генерация

**Среднее (50) [Рекомендуется]:**
- Естественные V-образные долины
- Баланс между реализмом и производительностью

**Высокое (100-200):**
- Очень глубокие каньоны
- Риск чрезмерного сглаживания
- Медленнее генерация

#### erosion_rate (скорость эрозии)

**Низкая (0.1-0.2):**
- Медленная эрозия
- Требует больше итераций
- Более контролируемый результат

**Средняя (0.3) [Рекомендуется]:**
- Естественная скорость эрозии
- 50 итераций достаточно

**Высокая (0.5-1.0):**
- Агрессивная эрозия
- Риск разрушения рельефа
- Нужно меньше итераций

#### source_multiplier (сила источников)

**Низкий (50):**
- Слабые источники
- Неглубокие долины

**Средний (100) [Рекомендуется]:**
- Мощные источники создают глубокие долины
- Чёткая связь "артерия → река → долина"

**Высокий (200-500):**
- Экстремально глубокие каньоны в точках выхода
- Риск чрезмерной эрозии

---

## Полный код (Python + NumPy)

```python
import numpy as np
from scipy.ndimage import gaussian_filter
from typing import List, Dict

def hydraulic_erosion_focused(
    elevation: np.ndarray,
    bone_density_map: np.ndarray,
    vein_outlets: List[Dict],
    iterations: int = 50,
    erosion_rate: float = 0.3,
    bone_protection: bool = True,
    bone_protection_multiplier: float = 0.3,
    sigma: float = 2.0,
    source_multiplier: float = 100.0,
    background_rain: float = 0.01
) -> np.ndarray:
    """
    Гидравлическая эрозия с фокусировкой на выходы артерий

    Args:
        elevation: Карта высот (512, 512) float [0, 1]
        bone_density_map: Карта плотности костей (512, 512) float [0, 1]
        vein_outlets: Список точек выхода артерий
            [{'position': (x, y), 'strength': float}, ...]
        iterations: Количество циклов симуляции
        erosion_rate: Скорость эрозии
        bone_protection: Включить защиту костей
        bone_protection_multiplier: Множитель эрозии для костей
        sigma: Радиус Gaussian smoothing
        source_multiplier: Множитель силы источников
        background_rain: Сила фонового дождя

    Returns:
        Эродированная карта высот (512, 512) float [0, 1]
    """

    # Шаг 0: Предварительная обработка
    print(f"  → Gaussian smoothing (sigma={sigma})...")
    elevation_smooth = gaussian_filter(elevation, sigma=sigma)

    eroded_elevation = elevation_smooth.copy()
    height, width = elevation.shape

    for iteration in range(iterations):
        if iteration % 10 == 0:
            print(f"  → Erosion iteration {iteration}/{iterations}")

        # Шаг 1: Распределение воды
        water_map = np.ones((height, width)) * background_rain

        # Фокусировка на vein_outlets
        for outlet in vein_outlets:
            x, y = outlet['position']
            if 0 <= x < width and 0 <= y < height:
                water_map[y, x] += outlet['strength'] * source_multiplier

        # Шаг 2: D8 Flow Accumulation (упрощённая версия)
        flow_map = np.zeros_like(water_map)

        for y in range(1, height - 1):
            for x in range(1, width - 1):
                # Найти направление стока (к соседу с минимальной высотой)
                current_height = eroded_elevation[y, x]

                neighbors = [
                    (y-1, x-1), (y-1, x), (y-1, x+1),
                    (y,   x-1),           (y,   x+1),
                    (y+1, x-1), (y+1, x), (y+1, x+1)
                ]

                min_neighbor_height = current_height
                min_neighbor_pos = None

                for ny, nx in neighbors:
                    if eroded_elevation[ny, nx] < min_neighbor_height:
                        min_neighbor_height = eroded_elevation[ny, nx]
                        min_neighbor_pos = (ny, nx)

                # Вода течёт к соседу
                if min_neighbor_pos is not None:
                    ny, nx = min_neighbor_pos
                    flow_map[ny, nx] += water_map[y, x]

        # Шаг 3: Эрозия
        for y in range(height):
            for x in range(width):
                flow = flow_map[y, x]

                if flow > 0:
                    # Базовая эрозия
                    erosion_amount = erosion_rate * flow

                    # Bone protection
                    if bone_protection and bone_density_map[y, x] > 0.5:
                        erosion_amount *= bone_protection_multiplier

                    # Применяем эрозию
                    eroded_elevation[y, x] -= erosion_amount

    # Нормализация обратно в [0, 1]
    eroded_elevation = (eroded_elevation - eroded_elevation.min()) / (eroded_elevation.max() - eroded_elevation.min())

    print(f"  ✅ Erosion complete ({iterations} iterations)")
    return eroded_elevation
```

---

## Пример использования

```python
# Загружаем данные
elevation = np.load('elevation.npy')  # (512, 512) float [0, 1]
bone_density_map = np.load('bone_density.npy')  # (512, 512) float [0, 1]

vein_outlets = [
    {'position': (256, 150), 'strength': 0.9},  # Мощный выход
    {'position': (200, 200), 'strength': 0.5},  # Средний выход
    {'position': (300, 250), 'strength': 0.3},  # Слабый выход
]

# Применяем эрозию
elevation_eroded = hydraulic_erosion_focused(
    elevation=elevation,
    bone_density_map=bone_density_map,
    vein_outlets=vein_outlets,
    iterations=50,
    erosion_rate=0.3,
    bone_protection=True
)

# Сохраняем результат
np.save('elevation_eroded.npy', elevation_eroded)

print("Erosion complete!")
print(f"Elevation range: [{elevation_eroded.min():.3f}, {elevation_eroded.max():.3f}]")
```

---

## Визуализация

### Рекомендуемая визуализация (сравнение до/после)

```python
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# До эрозии
axes[0].imshow(elevation, cmap='terrain')
axes[0].set_title('Elevation (Before Erosion)')
axes[0].axis('off')

# После эрозии
axes[1].imshow(elevation_eroded, cmap='terrain')
axes[1].set_title('Elevation (After Erosion)')
axes[1].axis('off')

# Разница (delta)
delta = elevation - elevation_eroded
im = axes[2].imshow(delta, cmap='RdBu', vmin=-0.1, vmax=0.1)
axes[2].set_title('Erosion Delta (Red = eroded)')
axes[2].axis('off')

# Отметить vein_outlets
for outlet in vein_outlets:
    x, y = outlet['position']
    for ax in axes:
        ax.plot(x, y, 'ro', markersize=8, markerfacecolor='none', markeredgewidth=2)

plt.colorbar(im, ax=axes[2], label='Height change')
plt.tight_layout()
plt.show()
```

**Ожидаемый результат:**
- Глубокие V-образные долины в точках vein_outlets (красные круги)
- Кости (хребты) сохраняют форму
- Плавные переходы высот

---

## Лор-соответствие

### Анатомическая логика

1. **"Лимфатическая эрозия"** ✅
   - Реки питаются из выходов артерий (lore-accurate)
   - Мощные потоки в точках выхода создают глубокие долины

2. **Кости прочнее мягких тканей** ✅
   - `bone_protection = True`
   - Хребты сохраняют форму даже после эрозии

3. **Связь артерии → реки → эрозия** ✅
   - Phase 3 (Vessels) → Phase 4 (Hydrology) → Phase 4.5 (Erosion)
   - Логическая последовательность

4. **Глубокие каньоны вдоль лимфотоков** ✅
   - Результат эрозии - V-образные долины
   - Соответствует описанию лора

---

## Производительность

### Сложность

- **Временная:** O(I × W × H)
  - I = iterations (50)
  - W, H = размеры карты (512 × 512)

- **Пространственная:** O(W × H)

### Производительность

**Для карты 512×512:**
- Iterations: 50
- Время генерации: **~5-15 сек** (чистый Python)
- Время генерации: **~1-3 сек** (с NumPy оптимизацией)

### Возможные оптимизации

1. **Numba JIT:** Компиляция критических циклов
   ```python
   from numba import jit

   @jit(nopython=True)
   def erosion_step_optimized(...):
       # Скомпилированная версия
   ```
   - Ускорение: **5-10x**

2. **Vectorization:** Использовать NumPy операции вместо циклов

3. **GPU acceleration:** CUDA/OpenCL для массивно-параллельных вычислений

---

## Статус

- **Разработка:** 🚧 В планировании
- **Тестирование:** ⏳ Ожидает реализации
- **Документация:** ✅ Готова
- **Интеграция:** ⏳ Sprint 3.8 (Phase 4.5)

---

**Версия:** 3.0
**Дата последнего обновления:** 29 октября 2025
**Следующий шаг:** Реализация в `core/hydraulic_erosion.py` (Sprint 3.8)
