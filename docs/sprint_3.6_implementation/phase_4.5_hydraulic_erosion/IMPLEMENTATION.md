# Phase 4.5: Hydraulic Erosion [🆕 NEW in v3.0]

**Статус:** 🚧 Запланировано (Sprint 3.8)

**🆕 НОВАЯ ФАЗА v3.0:** Гидравлическая эрозия создаёт реалистичные речные долины в точках выхода артерий (лимфатическая эрозия).

## Задачи реализации

1. **Gaussian pre-processing** (sigma=2.0) - убирает артефакты L-Systems
2. **Фокусированная эрозия** - мощные источники в vein_outlets, слабый фон
3. **Bone protection** - кости эродируются в 3× медленнее
4. Итеративная симуляция водного потока (D8)
5. Вычисление eroded elevation

## Инструменты

- **NumPy**: массивы, векторные операции
- **SciPy**: `scipy.ndimage.gaussian_filter` для сглаживания
- **Custom**: Hydraulic erosion simulation

**Рекомендация:** См. `HYDRAULIC_EROSION_GUIDE.md` для подробной спецификации алгоритма.

## Входные данные

```python
elevation: np.ndarray  # (512, 512) из Phase 2
bone_density_map: np.ndarray  # (512, 512) из Phase 2
vein_outlets: List[dict]  # Из Phase 3

# Параметры
iterations: int = 50
erosion_rate: float = 0.3
bone_protection: bool = True
source_strength_multiplier: float = 100.0
background_rain: float = 0.01
gaussian_sigma: float = 2.0
```

## Выходные данные

```python
elevation_eroded: np.ndarray  # (512, 512) float [0, 1]
```

## Пошаговый план

### 1. Gaussian Pre-processing

```python
from scipy.ndimage import gaussian_filter

def _preprocess_elevation(elevation: np.ndarray, sigma: float = 2.0) -> np.ndarray:
    """
    Предварительное сглаживание для удаления L-Systems артефактов

    Args:
        elevation: Исходный elevation map
        sigma: Параметр Gaussian blur

    Returns:
        Сглаженный elevation
    """
    # Применяем Gaussian filter
    elevation_smooth = gaussian_filter(elevation, sigma=sigma)

    return elevation_smooth
```

### 2. Создание карты воды (фокусированная)

```python
def _create_focused_water_map(vein_outlets: list, map_size: tuple,
                              source_strength: float = 100.0,
                              background_rain: float = 0.01) -> np.ndarray:
    """
    Создание карты воды с фокусировкой на vein_outlets

    ⭐ КЛЮЧЕВОЕ ОТЛИЧИЕ: источники ×100 сильнее фона
    """
    water_map = np.ones(map_size, dtype=np.float32) * background_rain

    # Мощные источники в vein_outlets
    for outlet in vein_outlets:
        x, y = outlet['position']
        strength = outlet['strength']

        water_map[y, x] += strength * source_strength

    return water_map
```

### 3. Симуляция эрозии (с bone protection)

```python
def _hydraulic_erosion_iteration(
    elevation: np.ndarray,
    water_map: np.ndarray,
    bone_density_map: np.ndarray,
    erosion_rate: float = 0.3,
    bone_protection: bool = True
) -> np.ndarray:
    """
    Одна итерация гидравлической эрозии

    Args:
        elevation: Текущий elevation
        water_map: Карта воды (источники + дождь)
        bone_density_map: Плотность костей [0, 1]
        erosion_rate: Скорость эрозии
        bone_protection: Защита костей (True = кости в 3× прочнее)

    Returns:
        Eroded elevation
    """
    height, width = elevation.shape
    eroded = elevation.copy()

    # D8 flow accumulation (упрощённая версия)
    flow_map = _calculate_d8_flow_simple(elevation, water_map)

    # Эрозия
    for y in range(height):
        for x in range(width):
            flow = flow_map[y, x]

            if flow < 1.0:
                continue

            # Базовая эрозия пропорциональна потоку
            erosion_amount = erosion_rate * np.log1p(flow)

            # ⭐ BONE PROTECTION
            if bone_protection:
                bone_density = bone_density_map[y, x]
                if bone_density > 0.5:
                    erosion_amount *= 0.3  # Кости в 3 раза прочнее

            # Применяем эрозию
            eroded[y, x] = max(0, eroded[y, x] - erosion_amount)

    return eroded


def _calculate_d8_flow_simple(elevation: np.ndarray, water_map: np.ndarray) -> np.ndarray:
    """
    Упрощённый расчёт flow accumulation для эрозии

    Returns:
        flow_map: накопленный поток воды
    """
    # Реализация D8 (аналогично Phase 4)
    # ...
    pass  # Детали опущены для краткости
```

### 4. Итеративная эрозия

```python
def _hydraulic_erosion_focused(
    elevation: np.ndarray,
    bone_density_map: np.ndarray,
    vein_outlets: list,
    iterations: int = 50,
    erosion_rate: float = 0.3,
    bone_protection: bool = True,
    source_strength: float = 100.0,
    background_rain: float = 0.01,
    gaussian_sigma: float = 2.0
) -> np.ndarray:
    """
    Полная гидравлическая эрозия с фокусировкой

    Алгоритм:
    1. Gaussian pre-processing
    2. Создание focused water map
    3. N итераций эрозии
    """
    # 1. Предобработка
    elevation_smooth = _preprocess_elevation(elevation, sigma=gaussian_sigma)

    # 2. Карта воды
    water_map = _create_focused_water_map(
        vein_outlets, elevation_smooth.shape,
        source_strength, background_rain
    )

    # 3. Итеративная эрозия
    eroded = elevation_smooth.copy()

    for i in range(iterations):
        eroded = _hydraulic_erosion_iteration(
            eroded, water_map, bone_density_map,
            erosion_rate, bone_protection
        )

    return eroded
```

### 5. Интеграция в генератор

```python
class WorldGeneratorV2:
    def _apply_hydraulic_erosion(
        self, elevation, bone_density_map, vein_outlets
    ) -> np.ndarray:
        """
        Phase 4.5: Гидравлическая эрозия [v3.0]
        """
        # Параметры из конфига
        erosion_config = self.config['hydraulic_erosion']

        eroded_elevation = _hydraulic_erosion_focused(
            elevation=elevation,
            bone_density_map=bone_density_map,
            vein_outlets=vein_outlets,
            iterations=erosion_config['iterations'],
            erosion_rate=erosion_config['erosion_rate'],
            bone_protection=erosion_config['bone_protection'],
            source_strength=erosion_config['source_strength'],
            background_rain=erosion_config['background_rain'],
            gaussian_sigma=erosion_config['gaussian_sigma']
        )

        return eroded_elevation
```

## Конфигурация

```yaml
# config/world_generation_v2.yaml
hydraulic_erosion:
  iterations: 50  # Количество циклов
  erosion_rate: 0.3  # Скорость эрозии
  bone_protection: true  # Защита костей
  source_strength: 100.0  # Мощность vein_outlets (×100)
  background_rain: 0.01  # Слабый фоновый дождь
  gaussian_sigma: 2.0  # Сглаживание L-Systems артефактов
```

## Тестирование

```python
def test_gaussian_preprocessing():
    # Создаём elevation с резкими скачками (L-Systems артефакт)
    elevation = np.zeros((512, 512))
    elevation[100:110, 250:260] = 1.0  # Резкая стена

    elevation_smooth = _preprocess_elevation(elevation, sigma=2.0)

    # После сглаживания должны быть плавные переходы
    assert elevation_smooth[99, 250] > 0  # Градиент распространился
    assert elevation_smooth[105, 255] < 1.0  # Пик снижен

def test_bone_protection():
    elevation = np.ones((512, 512)) * 0.5
    bone_density_map = np.zeros((512, 512))
    bone_density_map[256, 256] = 1.0  # Кость в центре

    water_map = np.ones((512, 512)) * 10  # Сильная эрозия

    eroded = _hydraulic_erosion_iteration(
        elevation, water_map, bone_density_map,
        erosion_rate=0.3, bone_protection=True
    )

    # Кость должна эродироваться медленнее
    bone_erosion = elevation[256, 256] - eroded[256, 256]
    soft_erosion = elevation[100, 100] - eroded[100, 100]

    assert bone_erosion < soft_erosion, "Кость должна эродироваться медленнее"

def test_focused_erosion():
    elevation = np.ones((512, 512)) * 0.5
    vein_outlets = [{'position': (256, 256), 'strength': 1.0}]
    bone_density_map = np.zeros((512, 512))

    eroded = _hydraulic_erosion_focused(
        elevation, bone_density_map, vein_outlets,
        iterations=10, source_strength=100.0, background_rain=0.01
    )

    # У vein_outlet эрозия должна быть сильнее
    outlet_erosion = elevation[256, 256] - eroded[256, 256]
    edge_erosion = elevation[0, 0] - eroded[0, 0]

    assert outlet_erosion > edge_erosion * 10, "Вокруг outlet эрозия мощнее"
```

## Метрики

- **Время выполнения**: ~5-15 секунд (Python), ~1-3 секунды (NumPy оптимизация)
- **Память**: ~2 MB (temporary arrays)

## Оптимизация производительности

### NumPy векторизация

```python
# Вместо циклов for:
for y in range(height):
    for x in range(width):
        erosion_amount = ...

# Использовать NumPy broadcasting:
erosion_amount = erosion_rate * np.log1p(flow_map)
erosion_amount = np.where(
    bone_density_map > 0.5,
    erosion_amount * 0.3,
    erosion_amount
)
eroded = np.maximum(0, elevation - erosion_amount)
```

## Зависимости

**Зависит от:**
- Phase 2 (elevation, bone_density_map)
- Phase 3 (vein_outlets)
- Phase 4 (flow accumulation helper)

**Используется в:**
- Phase 5 (Climate) - eroded elevation для температуры
- Phase 7 (Tissues) - речные долины влияют на биомы

## Визуализация

```bash
python scripts/visualize_erosion.py --seed my_seed --iterations 50
```

## См. также

- **HYDRAULIC_EROSION_GUIDE.md** - Детальная спецификация алгоритма с примерами
- **LAYERED_GENERATION_ANALYSIS_v2.md** - Обоснование Phase 4.5 в v3.0
