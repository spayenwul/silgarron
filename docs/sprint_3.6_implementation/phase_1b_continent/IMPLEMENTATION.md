# Phase 1b: Continent Growth

**Статус:** ✅ Реализовано (Sprint 3.6)

## Задачи реализации

1. Генерация базового heightmap (Perlin Noise)
2. Применение spine influence mask (опционально)
3. Threshold для разделения суша/океан
4. Морфологические операции (сглаживание береговой линии)
5. Расчёт геометрии (center of mass, major axis через PCA)
6. Размещение органов на континенте

## Инструменты

- **Perlin Noise**: `noise` library или custom implementation
- **NumPy**: массивы, математика
- **SciPy**: `scipy.ndimage` для морфологических операций, center_of_mass
- **SciPy**: `scipy.ndimage.binary_opening`, `binary_closing`
- **SciPy**: `scipy.ndimage.gaussian_filter`
- **NumPy**: `np.linalg.eig` для PCA

## Входные данные

```python
seed: int  # Hash от world seed
spine_influence_mask: np.ndarray  # (512, 512) float [0, 1] (опционально)

# Параметры из конфига
scale: float = 150.0  # Perlin scale (низкая частота)
octaves: int = 2
persistence: float = 0.6
lacunarity: float = 2.0
sea_level: float = 0.35  # Порог суша/океан
```

## Выходные данные

```python
ContinentData(
    mask: np.ndarray,  # (512, 512) bool
    heightmap: np.ndarray,  # (512, 512) float [0, 1]
    center: Tuple[int, int],  # (cx, cy)
    major_axis: Tuple[Tuple[int, int], Tuple[int, int]],  # ((x1, y1), (x2, y2))
    spine_path: np.ndarray  # (N, 2) - если spine mode
)
```

## Пошаговый план

### 1. Генерация базового heightmap

```python
from noise import pnoise2
import numpy as np

def _generate_heightmap(seed: int, width: int = 512, height: int = 512,
                        scale: float = 150.0, octaves: int = 2,
                        persistence: float = 0.6, lacunarity: float = 2.0) -> np.ndarray:
    """
    Генерация базового heightmap через Perlin Noise
    """
    heightmap = np.zeros((height, width), dtype=np.float32)

    for y in range(height):
        for x in range(width):
            # Perlin Noise в диапазоне [-1, 1]
            noise_val = pnoise2(
                x / scale,
                y / scale,
                octaves=octaves,
                persistence=persistence,
                lacunarity=lacunarity,
                repeatx=9999,
                repeaty=9999,
                base=seed
            )
            heightmap[y, x] = noise_val

    # Нормализация в [0, 1]
    heightmap = (heightmap - heightmap.min()) / (heightmap.max() - heightmap.min())

    return heightmap
```

### 2. Применение spine influence

```python
def _apply_spine_influence(heightmap: np.ndarray, spine_mask: np.ndarray,
                           sea_level_override: float = 0.20) -> tuple:
    """
    Модуляция heightmap через spine influence

    Returns:
        (heightmap_masked, sea_level)
    """
    # Умножение на influence field
    heightmap_masked = heightmap * spine_mask

    # Компенсация умножения: ниже sea_level
    return heightmap_masked, sea_level_override
```

### 3. Threshold и морфологические операции

```python
from scipy.ndimage import binary_opening, binary_closing, gaussian_filter

def _create_continent_mask(heightmap: np.ndarray, sea_level: float = 0.35) -> np.ndarray:
    """
    Создание маски континента с морфологическим сглаживанием
    """
    # 1. Базовый threshold
    mask = (heightmap > sea_level).astype(bool)

    # 2. Удаление маленьких островов
    mask = binary_opening(mask, iterations=3)

    # 3. Заполнение маленьких заливов
    mask = binary_closing(mask, iterations=2)

    # 4. Gaussian blur для финального сглаживания
    mask_float = gaussian_filter(mask.astype(float), sigma=3.0)
    mask = (mask_float > 0.5).astype(bool)

    return mask
```

### 4. Расчёт геометрии (PCA для major axis)

```python
from scipy import ndimage

def _calculate_continent_geometry(mask: np.ndarray) -> tuple:
    """
    Вычисление center of mass и major axis (через PCA)

    Returns:
        (center, major_axis)
    """
    # Center of mass
    cy, cx = ndimage.center_of_mass(mask)
    center = (int(cx), int(cy))

    # Координаты всех точек суши
    y_coords, x_coords = np.where(mask)
    coords = np.column_stack([x_coords, y_coords])

    # PCA
    mean = coords.mean(axis=0)
    centered = coords - mean

    # Covariance matrix
    cov_matrix = np.cov(centered.T)
    eigenvalues, eigenvectors = np.linalg.eig(cov_matrix)

    # Главный компонент (максимальная дисперсия)
    principal_component = eigenvectors[:, eigenvalues.argmax()]

    # Проекции на главную ось
    projections = centered @ principal_component

    # Крайние точки
    min_idx = projections.argmin()
    max_idx = projections.argmax()

    start_point = tuple(coords[min_idx])
    end_point = tuple(coords[max_idx])

    major_axis = (start_point, end_point)

    return center, major_axis
```

### 5. Размещение органов

```python
def _place_organs(continent_data: ContinentData) -> dict:
    """
    Phase 1: Размещение органов на континенте
    """
    organs = {}

    # 1. Metabolic Core (центр масс)
    organs['organ_metabolic_core'] = Organ(
        id='organ_metabolic_core',
        type='metabolic_organ',
        position=continent_data.center,
        radius=30,
        temperature=0.95,
        nutrient_output=0.9
    )

    # 2. Stomach (южная низина)
    stomach_pos = _find_lowland(continent_data, region='south')
    organs['organ_stomach'] = Organ(
        id='organ_stomach',
        type='digestive',
        position=stomach_pos,
        radius=25,
        temperature=0.85,
        acid_level=0.8
    )

    # 3. Neural Clusters (вдоль major axis)
    (x1, y1), (x2, y2) = continent_data.major_axis

    ganglion_thoracic_pos = (
        int(x1 + (x2 - x1) * 0.35),
        int(y1 + (y2 - y1) * 0.35)
    )
    organs['ganglion_0'] = Organ(
        id='ganglion_0',
        type='neural_cluster',
        position=ganglion_thoracic_pos,
        radius=15,
        control_strength=0.7
    )

    ganglion_abdominal_pos = (
        int(x1 + (x2 - x1) * 0.65),
        int(y1 + (y2 - y1) * 0.65)
    )
    organs['ganglion_1'] = Organ(
        id='ganglion_1',
        type='neural_cluster',
        position=ganglion_abdominal_pos,
        radius=15,
        control_strength=0.6
    )

    # 4. Lymph Node (возвышенность у ганглия)
    lymph_pos = _find_elevation(continent_data, near=ganglion_thoracic_pos, radius=50)
    organs['lymph_node_sclerite'] = Organ(
        id='lymph_node_sclerite',
        type='immune_node',
        position=lymph_pos,
        radius=10,
        cell_production=0.9
    )

    return organs
```

### 6. Интеграция в генератор

```python
class WorldGeneratorV2:
    def _generate_continent(self, seed: str, spine_data: tuple = None) -> ContinentData:
        """
        Phase 1b: Генерация континента
        """
        continent_seed = self._hash_seed(seed, "continent")

        # Параметры из конфига
        config = self.config['continent_generation']

        # 1. Базовый heightmap
        heightmap = self._generate_heightmap(
            seed=continent_seed,
            scale=config['perlin_scale'],
            octaves=config['perlin_octaves'],
            persistence=config['perlin_persistence'],
            lacunarity=config['perlin_lacunarity']
        )

        # 2. Применение spine (если есть)
        sea_level = config['sea_level']
        if spine_data is not None:
            spine_path, spine_influence = spine_data
            heightmap, sea_level = self._apply_spine_influence(
                heightmap, spine_influence, sea_level_override=0.20
            )
        else:
            spine_path = None

        # 3. Создание маски
        mask = self._create_continent_mask(heightmap, sea_level)

        # 4. Геометрия
        center, major_axis = self._calculate_continent_geometry(mask)

        return ContinentData(
            mask=mask,
            heightmap=heightmap,
            center=center,
            major_axis=major_axis,
            spine_path=spine_path
        )
```

## Конфигурация

```yaml
# config/world_generation_v2.yaml
continent_generation:
  perlin_scale: 150.0  # Низкая частота
  perlin_octaves: 2
  perlin_persistence: 0.6
  perlin_lacunarity: 2.0
  sea_level: 0.35  # 35% threshold
  morphology:
    opening_iterations: 3
    closing_iterations: 2
    gaussian_sigma: 3.0
```

## Тестирование

```python
def test_continent_generation():
    continent = _generate_continent(seed=12345)

    assert continent.mask.shape == (512, 512)
    assert 0.5 < continent.mask.mean() < 0.9  # 50-90% суша
    assert continent.center[0] > 0 and continent.center[0] < 512
    assert len(continent.major_axis) == 2

def test_spine_mode():
    spine_path, spine_influence = _generate_spine(seed=12345)
    continent = _generate_continent(seed=12345, spine_data=(spine_path, spine_influence))

    assert continent.spine_path is not None
    assert continent.spine_path.shape[0] == 100
```

### Визуализация

```bash
# Стандартная генерация
python scripts/visualize_continent.py --seed my_seed

# Spine-based генерация
python scripts/visualize_continent.py --seed my_seed --spine

# Сравнение режимов
python scripts/visualize_continent.py --seed my_seed --compare-modes
```

## Метрики

- **Время выполнения**: ~0.15-0.20 секунды
- **Память**: ~2 MB (heightmap + mask)

## Зависимости

**Зависит от:**
- Phase 0 (seed)
- Phase 1a (spine_path, spine_influence) - опционально

**Используется в:**
- Phase 1 (Organ Placement)
- Phase 1.1 (Regional Division)
- Phase 2 (Skeleton)
- Phase 4 (Hydrology)

---

## Тестирование и валидация (WP1)

**Рабочий пакет:** WP1 (Основа мира)
**Файл тестов:** `tests/core/test_continent_generation.py`, `tests/core/test_organ_placement.py`

### Unit тесты для реализации

✅ **test_array_dimensions** - Все массивы (mask, heightmap) имеют размер 512×512
✅ **test_continent_connectivity** - Continent mask состоит из 1 связной компоненты
✅ **test_land_percentage** - Суша занимает 55-90% карты
✅ **test_pca_major_axis** - Длина major axis > 400px, проходит через continent
✅ **test_center_of_mass** - Центр масс внутри континента
✅ **test_spine_mode** - В spine mode континент "притянут" к spine (больше суши вдоль spine)
✅ **test_organ_metabolic_core** - Metabolic core в центре масс ± 10px
✅ **test_organ_stomach** - Stomach в южной половине, в низине
✅ **test_organ_ganglions** - Ganglions на 35% и 65% вдоль major_axis
✅ **test_organ_lymph_node** - Lymph node на возвышенности, близко к ganglion

### Визуализация для создания

**Скрипт:** `scripts/visualize_wp1_foundation.py` (главный артефакт WP1)

**Выходные изображения:**
- `wp1_foundation_bw.png` - Чёрно-белая маска континента
- `wp1_spine_overlay.png` - Spine path + center + major axis
- `wp1_organs_placement.png` - Все органы на континенте (цветные точки)
- `wp1_full_composite.png` - Всё вместе (итоговый артефакт WP1)

**Скрипт валидации:** `scripts/validate_wp1_schema.py`

### Критерии валидации WP1

#### Функциональная валидация
- ✅ Континент = единая масса суши (не россыпь островов)
- ✅ PCA корректно находит главную ось
- ✅ Органы размещены согласно спецификации

#### Визуальная валидация
- 👁️ Береговая линия естественная (не рваная, не слишком гладкая)
- 👁️ Spine mode: континент притянут к позвоночнику
- 👁️ Органы в правильных местах (metabolic в центре, stomach на юге, и т.д.)

#### Валидация схемы данных
- 📋 ContinentData имеет все поля (mask, heightmap, center, major_axis, spine_path)
- 📋 Типы корректны (mask=bool, heightmap=float32, center=tuple, и т.д.)
- 📋 5 органов с правильными типами (metabolic_organ, digestive, neural_cluster, immune_node)
