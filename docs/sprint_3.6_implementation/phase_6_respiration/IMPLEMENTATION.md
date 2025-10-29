# Phase 6: Respiration System (Alveolar Caverns)

**Статус:** 🚧 Запланировано (Sprint 3.8)

## Задачи реализации

1. Расчёт карты respiratory_potential (bone density + structural stress + regional bias)
2. Генерация cavern positions через Poisson Disk Sampling с переменной плотностью
3. Классификация каверн по причине формирования (spine, rib, bone cavity, ectopic)
4. BFS-симуляция выдоха (bioactive saturation распространение)
5. Создание cavern metadata и bioactive_saturation map

## Инструменты

- **NumPy**: массивы, векторные операции
- **Poisson Disk Sampling**: custom implementation или `scipy.spatial`
- **BFS**: Breadth-First Search для распространения выдоха
- **SciPy**: `scipy.ndimage.distance_transform_edt` для proximity

## Входные данные

```python
bone_density_map: np.ndarray  # (512, 512)
spine_path: np.ndarray  # (N, 2)
skeleton_structure: dict  # vertebrae, ribs
regions: dict  # THORAX, DIAPHRAGM, etc.

# Параметры
cavern_density: float = 0.002  # Доля клеток с каверами
min_distance: float = 10.0  # Минимальное расстояние между каверами
bioactive_decay_rate: float = 0.05  # Скорость затухания выдоха
```

## Выходные данные

```python
caverns: List[dict] = [
    {
        'position': (x, y),
        'bioactive_output': 0.9,
        'radius': 5,
        'formation_cause': 'spine_vertebrae'  # spine/rib/bone_cavity/ectopic
    },
    ...
]

bioactive_saturation: np.ndarray  # (512, 512) float [0, 1]
```

## Пошаговый план

### 1. Расчёт respiratory_potential

```python
def _calculate_respiratory_potential(
    bone_density_map: np.ndarray,
    regions: dict,
    spine_path: np.ndarray
) -> np.ndarray:
    """
    Потенциал формирования каверн зависит от:
    1. Плотность костей (высокая плотность = высокий потенциал)
    2. Структурное напряжение (вдоль позвоночника)
    3. Региональный bias (THORAX максимум)
    """
    potential = np.zeros((512, 512), dtype=np.float32)

    # 1. Bone density (60% влияния)
    potential += bone_density_map * 0.6

    # 2. Proximity to spine (20%)
    from scipy.ndimage import distance_transform_edt

    spine_mask = np.zeros((512, 512), dtype=bool)
    for (sx, sy) in spine_path:
        if 0 <= int(sx) < 512 and 0 <= int(sy) < 512:
            spine_mask[int(sy), int(sx)] = True

    distance_to_spine = distance_transform_edt(~spine_mask)
    spine_influence = np.exp(-distance_to_spine / 50.0)  # Затухание
    potential += spine_influence * 0.2

    # 3. Regional bias (20%)
    regional_potential = np.zeros_like(potential)
    if 'THORAX' in regions:
        regional_potential += regions['THORAX'].mask * 0.9  # Максимум в грудной клетке
    if 'DIAPHRAGM' in regions:
        regional_potential += regions['DIAPHRAGM'].mask * 0.4

    potential += regional_potential * 0.2

    # Нормализация
    potential = np.clip(potential, 0, 1)

    return potential
```

### 2. Poisson Disk Sampling с переменной плотностью

```python
def _poisson_disk_sampling_weighted(
    potential_map: np.ndarray,
    min_distance: float = 10.0,
    seed: int = 0
) -> list:
    """
    Poisson Disk Sampling где плотность зависит от potential_map

    Args:
        potential_map: Карта вероятности [0, 1]
        min_distance: Минимальное расстояние между точками

    Returns:
        List[(x, y)] cavern positions
    """
    np.random.seed(seed)
    height, width = potential_map.shape
    caverns = []

    # Упрощённая реализация: grid-based sampling
    grid_size = int(min_distance)

    for y in range(0, height, grid_size):
        for x in range(0, width, grid_size):
            potential = potential_map[y, x]

            # Вероятность размещения пропорциональна potential
            if np.random.rand() < potential * 0.1:  # 10% базовая вероятность
                caverns.append((x, y))

    return caverns
```

### 3. Классификация каверн

```python
def _classify_caverns(
    cavern_positions: list,
    spine_path: np.ndarray,
    skeleton_structure: dict
) -> list:
    """
    Классификация каверн по причине формирования

    - spine_vertebrae: <15px от позвонка
    - rib_based: <20px от ребра
    - bone_cavity: внутри костной структуры
    - ectopic: аномальные (случайные)
    """
    classified_caverns = []

    for (cx, cy) in cavern_positions:
        formation_cause = 'ectopic'
        min_dist_to_spine = float('inf')

        # Проверка proximity к позвоночнику
        for (sx, sy) in spine_path:
            dist = np.sqrt((cx - sx)**2 + (cy - sy)**2)
            if dist < min_dist_to_spine:
                min_dist_to_spine = dist

        if min_dist_to_spine < 15:
            formation_cause = 'spine_vertebrae'
        else:
            # Проверка proximity к рёбрам
            for rib in skeleton_structure.get('ribs', []):
                # Distance to rib segment (упрощённо)
                # ...
                pass

            if formation_cause == 'ectopic':
                formation_cause = 'bone_cavity'

        classified_caverns.append({
            'position': (cx, cy),
            'bioactive_output': 0.9 if formation_cause == 'spine_vertebrae' else 0.7,
            'radius': 5,
            'formation_cause': formation_cause
        })

    return classified_caverns
```

### 4. BFS симуляция выдоха

```python
def _simulate_bioactive_exhalation(
    caverns: list,
    continent_mask: np.ndarray,
    decay_rate: float = 0.05
) -> np.ndarray:
    """
    BFS-распространение биоактивного выдоха от каверн

    Args:
        caverns: Список каверн
        continent_mask: Маска суши
        decay_rate: Скорость затухания (0.05 = 5% на шаг)

    Returns:
        bioactive_saturation [0, 1]
    """
    from collections import deque

    saturation = np.zeros((512, 512), dtype=np.float32)
    visited = np.zeros((512, 512), dtype=bool)

    # Инициализация BFS
    queue = deque()
    for cavern in caverns:
        x, y = cavern['position']
        output = cavern['bioactive_output']

        saturation[y, x] = output
        visited[y, x] = True
        queue.append((x, y, output))

    # BFS
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    while queue:
        cx, cy, current_saturation = queue.popleft()

        # Распространение на соседей
        for dx, dy in directions:
            nx, ny = cx + dx, cy + dy

            if 0 <= nx < 512 and 0 <= ny < 512:
                if continent_mask[ny, nx] and not visited[ny, nx]:
                    # Затухание
                    new_saturation = current_saturation * (1.0 - decay_rate)

                    if new_saturation > 0.01:  # Порог отсечения
                        saturation[ny, nx] = new_saturation
                        visited[ny, nx] = True
                        queue.append((nx, ny, new_saturation))

    return saturation
```

### 5. Интеграция в генератор

```python
class WorldGeneratorV2:
    def _generate_respiration(
        self, seed: str, bone_density_map, spine_path, skeleton_structure,
        regions, continent_mask
    ) -> tuple:
        """
        Phase 6: Генерация дыхательной системы
        """
        respiration_seed = self._hash_seed(seed, "respiration")

        # Параметры из конфига
        resp_config = self.config['respiration']

        # 1. Respiratory potential
        potential = self._calculate_respiratory_potential(
            bone_density_map, regions, spine_path
        )

        # 2. Poisson Disk Sampling
        cavern_positions = self._poisson_disk_sampling_weighted(
            potential,
            min_distance=resp_config['min_distance'],
            seed=respiration_seed
        )

        # 3. Классификация
        caverns = self._classify_caverns(
            cavern_positions, spine_path, skeleton_structure
        )

        # 4. BFS выдох
        bioactive_saturation = self._simulate_bioactive_exhalation(
            caverns,
            continent_mask,
            decay_rate=resp_config['decay_rate']
        )

        return caverns, bioactive_saturation
```

## Конфигурация

```yaml
# config/world_generation_v2.yaml
respiration:
  cavern_density: 0.002  # 0.2% клеток
  min_distance: 10.0  # px между каверами
  decay_rate: 0.05  # 5% затухание на шаг BFS

  potential_weights:
    bone_density: 0.6
    spine_proximity: 0.2
    regional_bias: 0.2
```

## Тестирование

```python
def test_respiratory_potential():
    bone_density = np.zeros((512, 512))
    bone_density[100:200, 200:300] = 0.8  # Костная зона

    spine_path = np.array([[256, i*5] for i in range(100)])

    regions = {'THORAX': Region(mask=np.ones((512, 512), dtype=bool))}

    potential = _calculate_respiratory_potential(bone_density, regions, spine_path)

    # У позвоночника потенциал высокий
    assert potential[256, 256] > 0.5

def test_bioactive_exhalation():
    caverns = [{'position': (256, 256), 'bioactive_output': 1.0, 'radius': 5}]
    continent_mask = np.ones((512, 512), dtype=bool)

    saturation = _simulate_bioactive_exhalation(caverns, continent_mask, decay_rate=0.05)

    assert saturation[256, 256] == 1.0  # Источник
    assert saturation[270, 256] > 0.5  # Близко к источнику
    assert saturation[400, 400] < 0.1  # Далеко от источника
```

## Метрики

- **Время выполнения**: ~0.5-1.0 секунды (BFS зависит от количества каверн)
- **Память**: ~2 MB (bioactive_saturation + cavern metadata)

## Статистика (ожидаемое распределение)

```
Spine-based: 36% (вдоль позвоночника)
Rib-based: 45% (у рёберных дуг)
Bone cavity: 15% (в костных полостях)
Ectopic: 3% (аномальные)
```

## Зависимости

**Зависит от:**
- Phase 1a (spine_path)
- Phase 1.1 (regions)
- Phase 1b (continent_mask)
- Phase 2 (bone_density_map, skeleton_structure)

**Используется в:**
- Phase 7 (Tissues) - bioactive_saturation для биомов

## Визуализация

```bash
python scripts/visualize_caverns.py --seed my_seed
```
