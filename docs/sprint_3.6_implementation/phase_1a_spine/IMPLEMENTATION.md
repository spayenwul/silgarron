# Phase 1a: Spine Creation

**Статус:** ✅ Реализовано (Sprint 3.6)

## Задачи реализации

1. Генерация процедурного "позвоночника" (spine path) север → юг
2. Применение Perlin Noise для естественной кривизны
3. Сглаживание пути B-spline интерполяцией
4. Создание influence field вокруг хребта
5. Сохранение spine_path для последующих фаз

## Инструменты

- **NumPy**: массивы, векторные операции
- **Perlin Noise**: `noise` library или custom implementation
- **SciPy**: `scipy.interpolate.splprep`, `splev` для B-spline сглаживания
- **SciPy**: `scipy.ndimage` для distance transform

## Входные данные

```python
seed: str  # "silgarron_alpha_01"
num_points: int = 100  # Количество точек хребта
curvature: float = 0.3  # Кривизна [0, 1]
max_influence: float = 200.0  # Радиус влияния (px)
```

## Выходные данные

```python
spine_path: np.ndarray  # (100, 2) массив координат (x, y)
spine_influence_mask: np.ndarray  # (512, 512) float [0, 1]
```

## Пошаговый план

### 1. Генерация базовой траектории

```python
import numpy as np

def _generate_spine_path(seed: int, num_points: int = 100, curvature: float = 0.3) -> np.ndarray:
    """
    Генерация изогнутого позвоночника север → юг

    Args:
        seed: Детерминированный seed
        num_points: Количество точек хребта
        curvature: Кривизна [0, 1] (0 = прямая, 1 = сильная кривизна)

    Returns:
        (num_points, 2) массив координат
    """
    # Y координаты: линейное распределение север → юг
    y_values = np.linspace(0, 512, num_points)

    # X координаты: центр ± случайное смещение
    x_noise = generate_perlin_noise_1d(
        seed=seed,
        length=num_points,
        scale=50,  # Низкая частота = плавные изгибы
        octaves=2
    )

    # Применяем кривизну (±60px от центра при curvature=0.3)
    x_values = 256 + x_noise * curvature * 200

    return np.column_stack([x_values, y_values])
```

### 2. Сглаживание B-spline

```python
from scipy.interpolate import splprep, splev

def _smooth_spine(spine_raw: np.ndarray, smoothing: float = 100.0) -> np.ndarray:
    """
    Сглаживание хребта B-spline интерполяцией

    Args:
        spine_raw: (N, 2) сырые координаты
        smoothing: Параметр сглаживания (больше = глаже)

    Returns:
        (N, 2) сглаженные координаты
    """
    x_raw, y_raw = spine_raw[:, 0], spine_raw[:, 1]

    # B-spline fit
    tck, u = splprep([x_raw, y_raw], s=smoothing, k=3)

    # Вычисление сглаженных точек
    u_new = np.linspace(0, 1, len(spine_raw))
    x_smooth, y_smooth = splev(u_new, tck)

    return np.column_stack([x_smooth, y_smooth])
```

### 3. Создание influence field

```python
def _create_spine_influence_mask(spine_path: np.ndarray, max_influence: float = 200.0) -> np.ndarray:
    """
    Создание поля влияния хребта (затухание по расстоянию)

    Args:
        spine_path: (N, 2) координаты хребта
        max_influence: Максимальное расстояние влияния (px)

    Returns:
        (512, 512) influence map [0, 1]
    """
    influence_mask = np.zeros((512, 512), dtype=np.float32)

    for (sx, sy) in spine_path:
        # Сетка координат
        y, x = np.ogrid[:512, :512]

        # Евклидово расстояние
        distance = np.sqrt((x - sx)**2 + (y - sy)**2)

        # Линейное затухание
        influence = np.maximum(0, 1.0 - distance / max_influence)

        # Максимум из всех точек (overlay)
        influence_mask = np.maximum(influence_mask, influence)

    return influence_mask
```

### 4. Интеграция в генератор

```python
class WorldGeneratorV2:
    def _generate_spine(self, seed: str) -> tuple:
        """
        Phase 1a: Генерация позвоночника
        """
        spine_seed = self._hash_seed(seed, "spine")

        # Параметры из конфига
        spine_config = self.config['spine_generation']
        num_points = spine_config.get('num_points', 100)
        curvature = spine_config.get('curvature', 0.3)
        max_influence = spine_config.get('max_influence', 200.0)

        # 1. Генерация сырого пути
        spine_raw = self._generate_spine_path(spine_seed, num_points, curvature)

        # 2. Сглаживание
        spine_smooth = self._smooth_spine(spine_raw, smoothing=100.0)

        # 3. Influence field
        influence_mask = self._create_spine_influence_mask(spine_smooth, max_influence)

        return spine_smooth, influence_mask
```

## Конфигурация

```yaml
# config/world_generation_v2.yaml
spine_generation:
  num_points: 100
  curvature: 0.3  # [0, 1]
  max_influence: 200.0  # pixels
  smoothing: 100.0
```

## Тестирование

### Unit тесты

```python
def test_spine_generation():
    spine_path = _generate_spine_path(seed=12345, num_points=100, curvature=0.3)

    assert spine_path.shape == (100, 2)
    assert spine_path[0, 1] == 0  # Север (y=0)
    assert spine_path[-1, 1] == 512  # Юг (y=512)
    assert 200 < spine_path[:, 0].mean() < 300  # Центрирован

def test_influence_mask():
    spine_path = np.array([[256, i*5.12] for i in range(100)])
    mask = _create_spine_influence_mask(spine_path, max_influence=100.0)

    assert mask.shape == (512, 512)
    assert mask[256, 256] == 1.0  # Максимум на хребте
    assert mask[0, 0] < 0.5  # Затухание на краях
```

### Визуализация

```bash
python scripts/visualize_spine_continent.py --seed test_seed
```

## Метрики

- **Время выполнения**: ~0.02-0.03 секунды
- **Память**: ~2 MB (influence mask 512×512 float32)

## Зависимости

**Зависит от:**
- Phase 0 (seed)

**Используется в:**
- Phase 1b (Continent Growth - spine mask)
- Phase 2 (Skeleton - vertebrae placement)

---

## Тестирование и валидация (WP1)

**Рабочий пакет:** WP1 (Основа мира)
**Файл тестов:** `tests/core/test_spine_generation.py`

### Unit тесты для реализации

✅ **test_spine_north_to_south** - Spine начинается на севере (y≈0), заканчивается на юге (y≈512)
✅ **test_spine_point_count** - Количество точек = `num_points` из конфига
✅ **test_spine_centering** - X координаты центрированы (среднее ≈ 256)
✅ **test_spine_curvature** - Кривизна соответствует параметру (max deviation ≈ curvature × 200)
✅ **test_influence_mask_shape** - Influence mask имеет размер (512, 512)
✅ **test_influence_max_at_spine** - Максимум influence = 1.0 на точках spine_path

### Визуализация для создания

**Скрипт:** Входит в `scripts/visualize_wp1_foundation.py`

**Выходные изображения:**
- `spine_path_overlay.png` - Spine path поверх континента
- `spine_influence_field.png` - Тепловая карта influence field

### Критерии валидации WP1
- ✅ Spine — плавная кривая север → юг по центру карты
- ✅ Influence field затухает с расстоянием от spine
