# Phase 4: Hydrology (River Network)

**Статус:** 🚧 Запланировано (Sprint 3.8)

## Задачи реализации

1. Использование vein_outlets как источников рек
2. Добавление natural springs в высокогорье
3. Реализация D8 Flow Accumulation
4. Расчёт flow_accumulation map
5. Создание river_mask через threshold

## Инструменты

- **NumPy**: массивы, векторные операции
- **SciPy**: `scipy.ndimage` для fill sinks (опционально)
- **Custom**: D8 flow direction algorithm

## Входные данные

```python
elevation: np.ndarray  # (512, 512) float [0, 1]
vein_outlets: List[dict]  # Из Phase 3
continent_mask: np.ndarray  # (512, 512) bool

# Параметры
river_threshold: float = 100.0  # Минимум flow для реки
spring_density: float = 0.001  # Доля высокогорных источников
```

## Выходные данные

```python
flow_accumulation: np.ndarray  # (512, 512) float
river_mask: np.ndarray  # (512, 512) bool
water_sources: List[dict]  # vein_outlets + natural_springs
```

## Пошаговый план

### 1. Создание карты источников воды

```python
def _create_water_sources(vein_outlets: list, elevation: np.ndarray,
                         spring_density: float = 0.001, seed: int = 0) -> tuple:
    """
    Создание источников воды: vein outlets + natural springs

    Vein outlets: выходы артерий (главные источники)
    Natural springs: высокогорные источники (elevation > 0.7)
    """
    water_map = np.zeros_like(elevation, dtype=np.float32)
    water_sources = []

    # 1. Vein outlets (мощные источники)
    for outlet in vein_outlets:
        x, y = outlet['position']
        strength = outlet['strength']

        water_map[y, x] += strength * 100  # Мощность ×100
        water_sources.append({
            'position': (x, y),
            'type': 'vein_outlet',
            'strength': strength * 100
        })

    # 2. Natural springs (высокогорье)
    np.random.seed(seed)
    highlands = elevation > 0.7
    num_springs = int(highlands.sum() * spring_density)

    highland_coords = np.argwhere(highlands)
    if len(highland_coords) > 0:
        spring_indices = np.random.choice(len(highland_coords), num_springs, replace=False)

        for idx in spring_indices:
            y, x = highland_coords[idx]
            water_map[y, x] += 10  # Слабые источники

            water_sources.append({
                'position': (x, y),
                'type': 'natural_spring',
                'strength': 10
            })

    return water_map, water_sources
```

### 2. Реализация D8 Flow Direction

```python
def _calculate_d8_flow_direction(elevation: np.ndarray) -> np.ndarray:
    """
    Вычисление направления стока для каждой клетки (D8 алгоритм)

    Направления кодируются:
    6 7 0
    5 X 1
    4 3 2

    Returns:
        flow_direction [0-7] или -1 (sink/ocean)
    """
    height, width = elevation.shape
    flow_direction = np.full((height, width), -1, dtype=np.int8)

    # D8 offsets
    directions = [
        (-1, 1), (0, 1), (1, 1),   # 0, 1, 2
        (1, 0),                     # 3
        (1, -1), (0, -1), (-1, -1), # 4, 5, 6
        (-1, 0)                     # 7
    ]

    for y in range(height):
        for x in range(width):
            current_elevation = elevation[y, x]
            max_slope = -np.inf
            best_direction = -1

            for d, (dy, dx) in enumerate(directions):
                ny, nx = y + dy, x + dx

                if 0 <= ny < height and 0 <= nx < width:
                    neighbor_elevation = elevation[ny, nx]
                    slope = current_elevation - neighbor_elevation

                    if slope > max_slope:
                        max_slope = slope
                        best_direction = d

            # Сток только если есть понижение
            if max_slope > 0:
                flow_direction[y, x] = best_direction

    return flow_direction
```

### 3. Расчёт Flow Accumulation

```python
def _calculate_flow_accumulation(flow_direction: np.ndarray, water_map: np.ndarray) -> np.ndarray:
    """
    Расчёт накопления воды через D8 алгоритм

    Args:
        flow_direction: (512, 512) int8 [0-7 или -1]
        water_map: (512, 512) float (источники воды)

    Returns:
        flow_accumulation: (512, 512) float
    """
    height, width = flow_direction.shape
    flow_accumulation = water_map.copy()

    # D8 offsets (соответствуют направлениям)
    directions = [
        (-1, 1), (0, 1), (1, 1),
        (1, 0),
        (1, -1), (0, -1), (-1, -1),
        (-1, 0)
    ]

    # Топологическая сортировка (обработка от истоков к устьям)
    # Упрощённый подход: многопроходный алгоритм
    for _ in range(100):  # Достаточно итераций для 512×512
        changed = False

        for y in range(height):
            for x in range(width):
                direction = flow_direction[y, x]

                if direction == -1:
                    continue  # Sink

                dy, dx = directions[direction]
                ny, nx = y + dy, x + dx

                if 0 <= ny < height and 0 <= nx < width:
                    # Передача воды вниз по течению
                    if flow_accumulation[y, x] > 0:
                        flow_accumulation[ny, nx] += flow_accumulation[y, x]
                        flow_accumulation[y, x] = 0
                        changed = True

        if not changed:
            break

    return flow_accumulation
```

### 4. Создание river mask

```python
def _create_river_mask(flow_accumulation: np.ndarray, threshold: float = 100.0) -> np.ndarray:
    """
    Создание маски рек через threshold

    Args:
        flow_accumulation: Карта накопления воды
        threshold: Минимум накопления для реки

    Returns:
        river_mask (bool)
    """
    return flow_accumulation > threshold
```

### 5. Интеграция в генератор

```python
class WorldGeneratorV2:
    def _generate_hydrology(self, seed: str, elevation, vein_outlets, continent_mask) -> tuple:
        """
        Phase 4: Генерация гидрологии
        """
        hydro_seed = self._hash_seed(seed, "hydrology")

        # Параметры из конфига
        hydro_config = self.config['hydrology']

        # 1. Источники воды
        water_map, water_sources = self._create_water_sources(
            vein_outlets,
            elevation,
            spring_density=hydro_config['spring_density'],
            seed=hydro_seed
        )

        # 2. D8 Flow Direction
        flow_direction = self._calculate_d8_flow_direction(elevation)

        # 3. Flow Accumulation
        flow_accumulation = self._calculate_flow_accumulation(flow_direction, water_map)

        # 4. River Mask
        river_mask = self._create_river_mask(
            flow_accumulation,
            threshold=hydro_config['river_threshold']
        )

        # 5. Применение continent mask
        river_mask &= continent_mask

        return flow_accumulation, river_mask, water_sources
```

## Конфигурация

```yaml
# config/world_generation_v2.yaml
hydrology:
  river_threshold: 100.0  # Минимум flow для реки
  spring_density: 0.001  # 0.1% высокогорья = источники
  vein_outlet_multiplier: 100  # Мощность vein outlets
```

## Тестирование

```python
def test_d8_flow_direction():
    # Простая возвышенность в центре
    elevation = np.ones((10, 10)) * 0.5
    elevation[5, 5] = 1.0  # Пик

    flow_direction = _calculate_d8_flow_direction(elevation)

    # Вокруг пика должны быть стоки от пика
    assert flow_direction[5, 5] != -1  # Пик стекает
    assert flow_direction[4, 4] >= 0  # Соседи стекают

def test_river_generation():
    elevation = np.random.rand(512, 512)
    vein_outlets = [{'position': (256, 100), 'strength': 1.0}]

    water_map, sources = _create_water_sources(vein_outlets, elevation)

    assert water_map[100, 256] > 0  # Источник есть
    assert len(sources) > 0
```

## Метрики

- **Время выполнения**: ~0.5-1.0 секунды (D8 алгоритм)
- **Память**: ~2 MB (flow_accumulation + river_mask)

## Зависимости

**Зависит от:**
- Phase 2 (elevation)
- Phase 3 (vein_outlets) ⭐
- Phase 1b (continent_mask)

**Используется в:**
- Phase 4.5 (Hydraulic Erosion) - river network
- Phase 5 (Climate) - moisture от рек
- Phase 7 (Tissues) - водные биомы
