# Phase 3: Vessel Network Generation [⚠️ v3.0 ИЗМЕНЕНИЕ]

**Статус:** 🚧 Запланировано (Sprint 3.8)

**⚠️ КРИТИЧЕСКОЕ ИЗМЕНЕНИЕ v3.0:** Vessels теперь генерируются ПОСЛЕ Skeleton с использованием **Space Colonization Algorithm + density-aware pathfinding**.

## Задачи реализации

1. Генерация attraction points из органов
2. Реализация Space Colonization Algorithm
3. **Модификация: density-aware pathfinding** (артерии огибают кости)
4. Типизация сосудов (arterial vs lymphatic)
5. Вычисление vein_outlets (точки выхода артерий на поверхность)

## Инструменты

- **NumPy**: массивы, векторные операции
- **SciPy**: `scipy.spatial.KDTree` для nearest neighbor search
- **Custom**: Space Colonization implementation

**Рекомендация:** См. `SPACE_COLONIZATION_GUIDE.md` для подробной спецификации алгоритма.

## Входные данные

```python
organs: dict  # Из Phase 1
bone_density_map: np.ndarray  # (512, 512) float [0, 1] ⭐ ИЗ PHASE 2!
elevation: np.ndarray  # Для vein_outlets

# Параметры алгоритма
influence_radius: float = 50.0
kill_distance: float = 10.0
segment_length: float = 5.0
bone_density_penalty: float = 3.0  # ⭐ Ключевой параметр!
```

## Выходные данные

```python
vessels: List[dict] = [
    {
        'from': 'organ_metabolic_core',
        'to': 'organ_stomach',
        'type': 'arterial',
        'width': 10,
        'flow_strength': 1.0,
        'waypoints': [(x1, y1), (x2, y2), ...]  # Огибают кости!
    },
    ...
]

vein_outlets: List[dict] = [
    {
        'position': (x, y),
        'strength': 0.8,
        'source_organ': 'organ_metabolic_core'
    },
    ...
]
```

## Пошаговый план

### 1. Создание attraction points из органов

```python
def _create_attraction_points(organs: dict, density: int = 30) -> list:
    """
    Генерация attraction points вокруг органов

    Args:
        organs: Словарь органов
        density: Количество точек на орган

    Returns:
        List[dict] с attraction points
    """
    attraction_points = []

    for organ_id, organ in organs.items():
        cx, cy = organ.position
        radius = organ.radius

        # Равномерное распределение вокруг органа
        angles = np.linspace(0, 2*np.pi, density, endpoint=False)

        for angle in angles:
            x = cx + radius * 1.5 * np.cos(angle)
            y = cy + radius * 1.5 * np.sin(angle)

            attraction_points.append({
                'position': np.array([x, y]),
                'organ_id': organ_id,
                'reached': False
            })

    return attraction_points
```

### 2. Space Colonization с density-aware cost

```python
def _generate_vessel_network_density_aware(
    organs: dict,
    bone_density_map: np.ndarray,
    influence_radius: float = 50.0,
    kill_distance: float = 10.0,
    segment_length: float = 5.0,
    bone_density_penalty: float = 3.0
) -> list:
    """
    Space Colonization с учётом плотности костей

    ⭐ КЛЮЧЕВОЕ ИЗМЕНЕНИЕ v3.0: cost = distance × (1.0 + bone_density × penalty)
    """

    # 1. Инициализация
    attraction_points = _create_attraction_points(organs, density=30)

    # Стартовая точка: metabolic_core
    metabolic_core = organs['organ_metabolic_core']
    active_tips = [
        {
            'position': np.array(metabolic_core.position),
            'parent': None,
            'organ_id': 'organ_metabolic_core'
        }
    ]

    vessels = []
    max_iterations = 1000

    # 2. Итеративный рост
    for iteration in range(max_iterations):
        if not any(not ap['reached'] for ap in attraction_points):
            break  # Все органы достигнуты

        # Для каждой attraction point: найти ближайший tip
        for ap in attraction_points:
            if ap['reached']:
                continue

            best_tip = None
            best_cost = float('inf')

            for tip in active_tips:
                # Евклидово расстояние
                distance = np.linalg.norm(ap['position'] - tip['position'])

                if distance > influence_radius:
                    continue

                # ⭐ DENSITY-AWARE COST
                ap_x, ap_y = int(ap['position'][0]), int(ap['position'][1])
                if 0 <= ap_x < 512 and 0 <= ap_y < 512:
                    bone_density = bone_density_map[ap_y, ap_x]
                else:
                    bone_density = 0.0

                cost = distance * (1.0 + bone_density * bone_density_penalty)

                if cost < best_cost:
                    best_cost = cost
                    best_tip = tip

            # Grow toward attraction point
            if best_tip is not None:
                direction = ap['position'] - best_tip['position']
                direction = direction / np.linalg.norm(direction)

                new_position = best_tip['position'] + direction * segment_length

                new_tip = {
                    'position': new_position,
                    'parent': best_tip,
                    'organ_id': ap['organ_id']
                }

                active_tips.append(new_tip)

                vessels.append({
                    'from': tuple(best_tip['position']),
                    'to': tuple(new_position),
                    'organ_id': ap['organ_id']
                })

                # Kill if reached
                if np.linalg.norm(ap['position'] - new_position) < kill_distance:
                    ap['reached'] = True

    return vessels
```

### 3. Типизация сосудов

```python
def _classify_vessels(vessels: list, organs: dict) -> list:
    """
    Классификация сосудов на arterial vs lymphatic

    Arterial: от metabolic_core к другим органам (питание)
    Lymphatic: обратный поток (лимфа)
    """
    classified = []

    for vessel in vessels:
        # Направление потока
        if vessel['organ_id'] == 'organ_metabolic_core':
            vessel_type = 'arterial'
            flow_strength = 1.0
            width = 10
        else:
            vessel_type = 'lymphatic'
            flow_strength = 0.6
            width = 6

        classified.append({
            'from': vessel['from'],
            'to': vessel['to'],
            'type': vessel_type,
            'width': width,
            'flow_strength': flow_strength,
            'organ_id': vessel['organ_id']
        })

    return classified
```

### 4. Вычисление vein_outlets

```python
def _calculate_vein_outlets(vessels: list, elevation: np.ndarray, threshold: float = 0.4) -> list:
    """
    Определение точек выхода артерий на поверхность

    Outlets возникают в местах где:
    - Артерия близка к поверхности (elevation < threshold)
    - Артерия находится в низине (локальный минимум)
    """
    outlets = []

    for vessel in vessels:
        if vessel['type'] != 'arterial':
            continue

        x, y = int(vessel['to'][0]), int(vessel['to'][1])
        if not (0 <= x < 512 and 0 <= y < 512):
            continue

        # Проверка близости к поверхности
        local_elevation = elevation[y, x]

        if local_elevation < threshold:
            # Проверка локального минимума (упрощённо)
            is_lowland = True
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < 512 and 0 <= ny < 512:
                    if elevation[ny, nx] < local_elevation:
                        is_lowland = False
                        break

            if is_lowland:
                outlets.append({
                    'position': (x, y),
                    'strength': vessel['flow_strength'],
                    'source_organ': vessel['organ_id']
                })

    return outlets
```

### 5. Интеграция в генератор

```python
class WorldGeneratorV2:
    def _generate_vessels(self, seed: str, organs, bone_density_map, elevation) -> tuple:
        """
        Phase 3: Генерация сосудов [v3.0]
        """
        vessel_seed = self._hash_seed(seed, "vessels")
        np.random.seed(vessel_seed)

        # Параметры из конфига
        vessel_config = self.config['vessel_generation']

        # 1. Space Colonization с density awareness
        vessels = self._generate_vessel_network_density_aware(
            organs=organs,
            bone_density_map=bone_density_map,
            influence_radius=vessel_config['influence_radius'],
            kill_distance=vessel_config['kill_distance'],
            segment_length=vessel_config['segment_length'],
            bone_density_penalty=vessel_config['bone_density_penalty']
        )

        # 2. Типизация
        vessels = self._classify_vessels(vessels, organs)

        # 3. Vein outlets (для Phase 4)
        vein_outlets = self._calculate_vein_outlets(vessels, elevation, threshold=0.4)

        return vessels, vein_outlets
```

## Конфигурация

```yaml
# config/world_generation_v2.yaml
vessel_generation:
  influence_radius: 50.0  # px
  kill_distance: 10.0
  segment_length: 5.0
  bone_density_penalty: 3.0  # ⭐ Ключевой параметр!
  # penalty = 3.0 → кости в 4 раза "дороже" для артерий

  vein_outlets:
    elevation_threshold: 0.4
```

## Тестирование

```python
def test_density_aware_pathfinding():
    """
    Проверка что артерии огибают плотные кости
    """
    # Mock данные: кость между двумя органами
    bone_density_map = np.zeros((512, 512))
    bone_density_map[200:300, 250:260] = 1.0  # Вертикальная стена

    organs = {
        'organ_a': Organ(position=(256, 100), radius=30),
        'organ_b': Organ(position=(256, 400), radius=30)
    }

    vessels = _generate_vessel_network_density_aware(
        organs, bone_density_map, bone_density_penalty=3.0
    )

    # Проверка: путь должен огибать кость (не через 250-260 по X)
    for vessel in vessels:
        x = int(vessel['to'][0])
        y = int(vessel['to'][1])
        if 200 <= y <= 300:
            assert not (250 <= x <= 260), "Артерия прошла через кость!"

def test_vein_outlets():
    vessels = [
        {'type': 'arterial', 'to': (100, 100), 'flow_strength': 1.0, 'organ_id': 'test'}
    ]
    elevation = np.ones((512, 512)) * 0.5
    elevation[100, 100] = 0.3  # Низина

    outlets = _calculate_vein_outlets(vessels, elevation, threshold=0.4)

    assert len(outlets) > 0
    assert outlets[0]['position'] == (100, 100)
```

## Метрики

- **Время выполнения**: ~1-2 секунды (зависит от количества органов)
- **Память**: ~1 MB (vessel waypoints)

## Зависимости

**Зависит от:**
- Phase 1 (organs)
- **Phase 2 (bone_density_map)** ⭐ Критическая зависимость!
- Phase 2 (elevation) - для vein_outlets

**Используется в:**
- Phase 4 (Hydrology) - vein_outlets как источники рек
- Phase 4.5 (Hydraulic Erosion) - vein_outlets как фокусы эрозии
- Phase 5 (Climate) - артерии влияют на температуру
- Phase 7 (Tissues) - proximity к артериям влияет на биомы

---

## Тестирование и валидация (WP2)

**Рабочий пакет:** WP2 (Анатомия и рельеф) ⭐ КРИТИЧЕСКИЙ ДЛЯ v3.0
**Файл тестов:** `tests/core/test_vessel_pathfinding.py` ⭐, `tests/core/test_space_colonization.py`

### Unit тесты для реализации

⭐ **test_density_aware_pathfinding** - **САМЫЙ КРИТИЧЕСКИЙ ТЕСТ v3.0!**
```python
def test_density_aware_pathfinding():
    """
    Проверка что артерии огибают плотные костные структуры

    Критерий: На искусственной карте с "костяной стеной" между двумя
              органами, путь сосуда НЕ должен пересекать стену
    """
    # Искусственная карта: кость между органами
    bone_density_map = np.zeros((512, 512))
    bone_density_map[200:300, 250:260] = 1.0  # Вертикальная стена (высокая плотность)

    organs = {
        'organ_a': Organ(position=(256, 100), radius=30),  # Север
        'organ_b': Organ(position=(256, 400), radius=30)   # Юг
    }

    vessels = _generate_vessel_network_density_aware(
        organs, bone_density_map, bone_density_penalty=3.0
    )

    # КРИТИЧЕСКАЯ ПРОВЕРКА: путь не через стену
    for vessel in vessels:
        for waypoint_x, waypoint_y in vessel['waypoints']:
            # Проверяем что waypoint не в зоне высокой плотности костей
            if 200 <= waypoint_y <= 300:
                assert not (250 <= waypoint_x <= 260), \
                    f"Артерия прошла через костяную стену в точке ({waypoint_x}, {waypoint_y})!"
```

✅ **test_space_colonization_convergence** - Все органы достигнуты (нет "зависших" attraction points)
✅ **test_vessel_types** - Типизация arterial vs lymphatic корректна
✅ **test_vein_outlets_in_lowlands** - Все vein_outlets в низинах (elevation < threshold)
✅ **test_vein_outlets_on_continent** - Все outlets на суше (не в океане)
✅ **test_vessel_waypoints_not_empty** - Все vessels имеют waypoints (не пустые пути)
✅ **test_bone_density_along_path** - Средняя bone_density вдоль всех путей < 0.5 (избегание костей)

### Визуализация для создания

**Скрипт:** `scripts/visualize_wp2_anatomy.py` (часть главного артефакта WP2)

**Выходные изображения:**
4. `wp2_vessels_on_bones.png` ⭐ **САМАЯ КРИТИЧЕСКАЯ ВИЗУАЛИЗАЦИЯ v3.0**
   - bone_density_map (градации серого) + vessels (красные/синие линии)
   - Должно быть ВИЗУАЛЬНО ВИДНО что артерии огибают белые (плотные) зоны

**Скрипт валидации:** `scripts/validate_wp2_pathfinding.py` ⭐
- Анализирует каждый waypoint в vessels
- Проверяет инвариант v3.0: `bone_density[waypoint] < 0.7`
- Выводит статистику: % путей через кости (должен быть ≈ 0%)

**Скрипт сравнения:** `scripts/compare_v2_vs_v3_vessels.py` (если доступен v2.0)

### Критерии валидации WP2

#### Функциональная валидация
- ⭐ **test_density_aware_pathfinding ПРОХОДИТ** - артерии обходят искусственную стену
- ✅ Все органы соединены
- ✅ Vein outlets в правильных местах

#### Визуальная валидация ⭐ САМАЯ ГЛАВНАЯ
- 👁️ **На wp2_vessels_on_bones.png:** Артерии ЯВНО избегают белых зон (плотных костей)
- 👁️ Сосуды проходят по серым/тёмным зонам (мягким тканям)
- 👁️ Нет прямых пересечений с позвонками или крупными рёбрами

#### Валидация схемы данных
- 📋 vessels: список с полем `waypoints` (доказательство обходных путей)
- 📋 **Инвариант v3.0:** Для всех waypoints: `bone_density_map[waypoint] < 0.7`

## См. также

- **SPACE_COLONIZATION_GUIDE.md** - Детальная спецификация алгоритма
- **LAYERED_GENERATION_ANALYSIS_v2.md** - Обоснование v3.0 изменений
