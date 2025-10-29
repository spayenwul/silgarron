# Phase 2: Skeleton Generation [⚠️ v3.0 ИЗМЕНЕНИЕ]

**Статус:** 🚧 Запланировано (Sprint 3.7)

**⚠️ КРИТИЧЕСКОЕ ИЗМЕНЕНИЕ v3.0:** Skeleton теперь генерируется ДО Vessels (Phase 3), чтобы артерии могли огибать плотные костные структуры.

## Задачи реализации

1. Генерация позвоночных сегментов (vertebrae) вдоль spine_path
2. Генерация рёбер через L-Systems
3. Генерация фаланг (phalanges) в конечностях
4. Создание **bone_density_map** для Phase 3 (vessel pathfinding)
5. Композиция финального elevation map (региональный bias + кости + Perlin)

## Инструменты

- **NumPy**: массивы, векторные операции
- **L-Systems**: custom implementation для рёбер
- **Perlin Noise**: текстурная детализация
- **SciPy**: `scipy.ndimage.gaussian_filter` для сглаживания
- **Distance Transform**: для расчёта proximity к костям

## Входные данные

```python
continent_data: ContinentData  # Из Phase 1b
spine_path: np.ndarray  # (N, 2) координаты позвоночника
organs: dict  # Из Phase 1
regions: dict  # Из Phase 1.1
seed: int
```

## Выходные данные

```python
elevation: np.ndarray  # (512, 512) float [0, 1]
bone_density_map: np.ndarray  # (512, 512) float [0, 1] ⭐ ДЛЯ PHASE 3
skeleton_structure: dict  # Метаданные (vertebrae, ribs, phalanges)
```

## Пошаговый план

### 1. Генерация позвонков (vertebrae)

```python
def _generate_vertebrae(spine_path: np.ndarray, spacing: int = 20) -> list:
    """
    Размещение позвонков вдоль spine_path с равным интервалом

    Args:
        spine_path: (N, 2) координаты хребта
        spacing: Расстояние между позвонками (px)

    Returns:
        List[dict] с позициями и радиусами
    """
    vertebrae = []
    accumulated_distance = 0
    last_placed = spine_path[0]

    for i in range(1, len(spine_path)):
        prev = spine_path[i-1]
        curr = spine_path[i]

        segment_length = np.linalg.norm(curr - prev)
        accumulated_distance += segment_length

        if accumulated_distance >= spacing:
            vertebrae.append({
                'position': tuple(curr),
                'radius': 15,  # Позвонки крупнее рёбер
                'elevation_bonus': 0.5,
                'bone_density': 1.0  # Максимальная плотность
            })
            accumulated_distance = 0

    return vertebrae
```

### 2. Генерация рёбер (L-Systems)

```python
def _generate_ribs_lsystem(spine_path: np.ndarray, num_ribs: int = 12,
                           rib_length: float = 80.0, angle: float = 60.0,
                           seed: int = 0) -> list:
    """
    Генерация рёбер через L-Systems

    L-System правила:
    - Axiom: F
    - F → F[+F][-F]F  (ветвление)

    Args:
        spine_path: Позвоночник
        num_ribs: Количество пар рёбер
        rib_length: Длина ребра (px)
        angle: Угол ветвления (градусы)

    Returns:
        List[dict] рёберных сегментов
    """
    np.random.seed(seed)
    ribs = []

    # Равномерное распределение по позвоночнику
    rib_indices = np.linspace(20, len(spine_path) - 50, num_ribs, dtype=int)

    for idx in rib_indices:
        base_pos = spine_path[idx]

        # Направление перпендикулярное позвоночнику
        tangent = spine_path[idx+1] - spine_path[idx-1]
        perpendicular_left = np.array([-tangent[1], tangent[0]])
        perpendicular_left = perpendicular_left / np.linalg.norm(perpendicular_left)
        perpendicular_right = -perpendicular_left

        # Генерация левого и правого ребра
        for direction in [perpendicular_left, perpendicular_right]:
            rib_segments = _lsystem_branch(
                start=base_pos,
                direction=direction,
                length=rib_length,
                angle=angle,
                iterations=2
            )
            ribs.extend(rib_segments)

    return ribs


def _lsystem_branch(start, direction, length, angle, iterations):
    """
    Рекурсивная генерация L-System ветви

    F[+F][-F]F → прямо, +ветвь, -ветвь, прямо
    """
    segments = []

    # Простая имплементация (детали опущены для краткости)
    # TODO: Полная реализация L-Systems с turtle graphics

    segments.append({
        'start': tuple(start),
        'end': tuple(start + direction * length),
        'bone_density': 0.7,
        'elevation_bonus': 0.3
    })

    return segments
```

### 3. Генерация фаланг (phalanges)

```python
def _generate_phalanges(region_mask: np.ndarray, num_phalanges: int = 5) -> list:
    """
    Размещение фаланг в регионе GRASPING_LIMB

    Args:
        region_mask: Маска региона конечности
        num_phalanges: Количество фаланг

    Returns:
        List[dict] фаланг
    """
    phalanges = []

    # Находим "пальцы" конечности (выступающие части)
    # Упрощённая логика: берём крайние точки региона по X
    y_coords, x_coords = np.where(region_mask)

    # Нижняя часть региона (юг)
    y_threshold = y_coords.max() - 50
    limb_tip = region_mask.copy()
    limb_tip[:y_threshold, :] = False

    # Кластеризация выступов (упрощённо: сегменты по X)
    for i in range(num_phalanges):
        x_segment = int(x_coords.min() + (x_coords.max() - x_coords.min()) * i / num_phalanges)
        y_segment = np.where(limb_tip[:, x_segment])[0]

        if len(y_segment) > 0:
            phalanges.append({
                'position': (x_segment, int(y_segment.mean())),
                'length': 30,
                'bone_density': 0.6,
                'elevation_bonus': 0.4
            })

    return phalanges
```

### 4. Создание bone_density_map ⭐

```python
def _create_bone_density_map(skeleton_structure: dict, map_size: tuple) -> np.ndarray:
    """
    Создание карты плотности костей для vessel pathfinding

    Args:
        skeleton_structure: Позвонки, рёбра, фаланги
        map_size: (512, 512)

    Returns:
        bone_density_map [0, 1] - 0=мягкая ткань, 1=кость
    """
    bone_density_map = np.zeros(map_size, dtype=np.float32)

    # 1. Позвонки (максимальная плотность)
    for vertebra in skeleton_structure['vertebrae']:
        x, y = vertebra['position']
        radius = vertebra['radius']
        density = vertebra['bone_density']

        # Радиальный градиент
        yy, xx = np.ogrid[:map_size[0], :map_size[1]]
        distance = np.sqrt((xx - x)**2 + (yy - y)**2)
        influence = np.maximum(0, 1.0 - distance / radius)

        bone_density_map = np.maximum(bone_density_map, influence * density)

    # 2. Рёбра (средняя плотность)
    for rib in skeleton_structure['ribs']:
        # Line drawing для рёберных сегментов
        # TODO: Bresenham's line algorithm
        pass

    # 3. Фаланги (низкая плотность)
    for phalanx in skeleton_structure['phalanges']:
        # Аналогично позвонкам
        pass

    # 4. Сглаживание (убираем резкие границы)
    from scipy.ndimage import gaussian_filter
    bone_density_map = gaussian_filter(bone_density_map, sigma=2.0)

    return bone_density_map
```

### 5. Композиция elevation map

```python
def _generate_elevation(continent_data, skeleton_structure, regions, seed) -> np.ndarray:
    """
    Композиция финального elevation map

    Композиция:
    - 20% Региональный bias
    - 60% Костная структура ⭐ (главный фактор!)
    - 20% Perlin Noise (текстурная детализация)
    """
    elevation = np.zeros((512, 512), dtype=np.float32)

    # 1. Региональный bias (20%)
    regional_bias = _calculate_regional_bias(regions)
    elevation += regional_bias * 0.2

    # 2. Костная структура (60%)
    bone_elevation = np.zeros_like(elevation)

    # Позвонки
    for vertebra in skeleton_structure['vertebrae']:
        x, y = vertebra['position']
        radius = vertebra['radius']
        bonus = vertebra['elevation_bonus']

        yy, xx = np.ogrid[:512, :512]
        distance = np.sqrt((xx - x)**2 + (yy - y)**2)
        influence = np.maximum(0, 1.0 - distance / (radius * 2))
        bone_elevation += influence * bonus

    # Рёбра, фаланги (аналогично)
    # ...

    elevation += bone_elevation * 0.6

    # 3. Perlin Noise (20%)
    perlin_texture = _generate_heightmap(seed, scale=80.0, octaves=3)
    elevation += perlin_texture * 0.2

    # 4. Нормализация
    elevation = np.clip(elevation, 0, 1)

    # 5. Применение continent mask
    elevation *= continent_data.mask

    return elevation
```

### 6. Интеграция в генератор

```python
class WorldGeneratorV2:
    def _generate_skeleton(self, seed: str, continent_data, spine_path, regions) -> tuple:
        """
        Phase 2: Генерация скелета [v3.0]
        """
        skeleton_seed = self._hash_seed(seed, "skeleton")

        # 1. Позвонки
        vertebrae = self._generate_vertebrae(spine_path, spacing=20)

        # 2. Рёбра (L-Systems)
        ribs = self._generate_ribs_lsystem(spine_path, num_ribs=12, seed=skeleton_seed)

        # 3. Фаланги
        limb_region = regions['GRASPING_LIMB'].mask
        phalanges = self._generate_phalanges(limb_region, num_phalanges=5)

        skeleton_structure = {
            'vertebrae': vertebrae,
            'ribs': ribs,
            'phalanges': phalanges
        }

        # 4. Bone density map ⭐ (для Phase 3)
        bone_density_map = self._create_bone_density_map(skeleton_structure, (512, 512))

        # 5. Elevation map
        elevation = self._generate_elevation(
            continent_data, skeleton_structure, regions, skeleton_seed
        )

        return elevation, bone_density_map, skeleton_structure
```

## Конфигурация

```yaml
# config/world_generation_v2.yaml
skeleton_generation:
  vertebrae:
    spacing: 20  # px
    radius: 15
    elevation_bonus: 0.5

  ribs:
    num_pairs: 12
    length: 80.0  # px
    angle: 60.0  # degrees
    lsystem_iterations: 2

  phalanges:
    count: 5
    length: 30

  composition:
    regional_weight: 0.2
    bone_weight: 0.6  # Главный фактор!
    texture_weight: 0.2
```

## Тестирование

```python
def test_vertebrae_generation():
    spine = np.array([[256, i*5] for i in range(100)])
    vertebrae = _generate_vertebrae(spine, spacing=20)

    assert len(vertebrae) > 0
    assert all(v['bone_density'] == 1.0 for v in vertebrae)

def test_bone_density_map():
    skeleton = {
        'vertebrae': [{'position': (256, 256), 'radius': 15, 'bone_density': 1.0}],
        'ribs': [],
        'phalanges': []
    }
    bone_map = _create_bone_density_map(skeleton, (512, 512))

    assert bone_map.shape == (512, 512)
    assert bone_map[256, 256] > 0.9  # Высокая плотность в центре позвонка
    assert bone_map[0, 0] < 0.1  # Низкая плотность вдали
```

## Метрики

- **Время выполнения**: ~0.5-1.0 секунды (L-Systems + distance transforms)
- **Память**: ~4 MB (elevation + bone_density_map)

## Зависимости

**Зависит от:**
- Phase 0 (seed)
- Phase 1a (spine_path)
- Phase 1b (continent_data)
- Phase 1 (organs)
- Phase 1.1 (regions)

**Используется в:**
- **Phase 3 (Vessels)** ⭐ bone_density_map для pathfinding!
- Phase 4 (Hydrology) - elevation для flow
- Phase 4.5 (Hydraulic Erosion) - bone protection
- Phase 5 (Climate) - elevation для температуры
- Phase 6 (Respiration) - bone density для cavern placement

---

## Тестирование и валидация (WP2)

**Рабочий пакет:** WP2 (Анатомия и рельеф) ⭐ КРИТИЧЕСКИЙ ДЛЯ v3.0
**Файл тестов:** `tests/core/test_skeleton_generation.py`, `tests/core/test_bone_density_map.py`

### Unit тесты для реализации

✅ **test_vertebrae_placement** - Позвонки вдоль spine_path с интервалом ≈ `spacing` (20px)
✅ **test_vertebrae_inside_continent** - Все позвонки внутри continent mask
✅ **test_lsystems_ribs** - L-система генерирует ветвящуюся структуру без ошибок
✅ **test_rib_count** - Количество рёбер = `num_ribs` × 2 (левые + правые пары)
✅ **test_bone_density_map_maxima** - bone_density_map имеет максимумы (>0.9) в позвонках
✅ **test_bone_density_decay** - Плотность затухает с расстоянием от костей
✅ **test_elevation_bones_correspondence** - Возвышения на elevation соответствуют костям на bone_density_map
✅ **test_elevation_range** - elevation в диапазоне [0, 1]
✅ **test_skeleton_structure_schema** - skeleton_structure имеет поля: vertebrae, ribs, phalanges

### Визуализация для создания

**Скрипт:** `scripts/visualize_wp2_anatomy.py` (главный артефакт WP2)

**Выходные изображения (3 ключевых):**
1. `wp2_bone_density_map.png` - Карта плотности костей (градации серого, белое = кости)
2. `wp2_elevation_final.png` - Итоговая карта высот (градации серого, белое = горы)
3. `wp2_skeleton_structure.png` - Визуализация позвонков + рёбер + фаланг поверх bone_density_map

### Критерии валидации WP2

#### Функциональная валидация
- ✅ Позвонки вдоль позвоночника с равномерным spacing
- ✅ L-Systems без ошибок, рёбра ветвятся
- ✅ bone_density_map корректен (максимумы у костей, затухание)

#### Визуальная валидация
- 👁️ **Elevation:** Четко видны возвышенности вдоль позвоночника и рёбер
- 👁️ **Соответствие:** Возвышенности на elevation соответствуют белым зонам на bone_density_map
- 👁️ **Рёбра:** Видны как отходящие от позвоночника хребты
