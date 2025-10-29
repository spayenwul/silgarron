# Phase 5: Climate (Temperature & Moisture)

**Статус:** 🚧 Запланировано (Sprint 3.8)

## Задачи реализации

1. Расчёт базовой температуры (world_phase)
2. Наложение температурных градиентов от органов
3. Влияние костей (охлаждение) и артерий (нагрев)
4. Высотная коррекция температуры
5. Расчёт влажности от рек и биоактивных зон
6. Композиция финальных карт (temperature, moisture)

## Инструменты

- **NumPy**: массивы, векторные операции
- **SciPy**: `scipy.ndimage.gaussian_filter` для распространения градиентов

## Входные данные

```python
world_phase: str  # "EXHALE" | "INHALE"
organs: dict
vessels: list
elevation: np.ndarray  # (512, 512)
bone_density_map: np.ndarray  # (512, 512)
river_mask: np.ndarray  # (512, 512) bool

# Параметры
organ_temp_radius: float = 80.0  # Радиус температурного влияния
river_moisture_radius: float = 20.0
```

## Выходные данные

```python
temperature: np.ndarray  # (512, 512) float [0, 1]
moisture: np.ndarray  # (512, 512) float [0, 1]
```

## Пошаговый план

### 1. Базовая температура (world_phase)

```python
def _calculate_base_temperature(world_phase: str, map_size: tuple) -> np.ndarray:
    """
    Базовая температура зависит от фазы дыхания

    EXHALE: тёплая фаза (базовая 0.6)
    INHALE: холодная фаза (базовая 0.4)
    """
    if world_phase == "EXHALE":
        base_temp = 0.6
    elif world_phase == "INHALE":
        base_temp = 0.4
    else:
        base_temp = 0.5

    temperature = np.ones(map_size, dtype=np.float32) * base_temp

    return temperature
```

### 2. Температурные градиенты от органов

```python
def _apply_organ_temperature(temperature: np.ndarray, organs: dict,
                             radius: float = 80.0) -> np.ndarray:
    """
    Органы излучают тепло (радиальные градиенты)

    Metabolic core: +0.95 (очень горячий)
    Stomach: +0.85 (горячий)
    """
    for organ_id, organ in organs.items():
        cx, cy = organ.position
        organ_temp = organ.temperature  # Из organ properties

        # Радиальный градиент
        y, x = np.ogrid[:temperature.shape[0], :temperature.shape[1]]
        distance = np.sqrt((x - cx)**2 + (y - cy)**2)

        # Экспоненциальное затухание
        influence = np.exp(-distance / radius)

        # Накладываем температуру
        temperature += influence * organ_temp * 0.3  # 30% влияния

    return temperature
```

### 3. Влияние костей и артерий

```python
def _apply_skeleton_climate(temperature: np.ndarray, bone_density_map: np.ndarray,
                            vessels: list) -> np.ndarray:
    """
    Кости: охлаждение (-0.4)
    Артерии: нагрев (+0.3)
    """
    # Кости охлаждают (хитино-силикат радиирует тепло)
    bone_cooling = bone_density_map * -0.4
    temperature += bone_cooling

    # Артерии нагревают (горячая кровь/лимфа)
    for vessel in vessels:
        if vessel['type'] != 'arterial':
            continue

        x, y = int(vessel['to'][0]), int(vessel['to'][1])
        if 0 <= x < 512 and 0 <= y < 512:
            # Локальный нагрев
            temperature[y, x] += 0.3 * vessel['flow_strength']

    return temperature
```

### 4. Высотная коррекция

```python
def _apply_elevation_temperature(temperature: np.ndarray, elevation: np.ndarray) -> np.ndarray:
    """
    Высота охлаждает (адиабатический градиент)

    Высокогорье (elevation > 0.7): -0.3
    """
    # Линейная коррекция
    elevation_penalty = elevation * -0.3

    temperature += elevation_penalty

    return temperature
```

### 5. Влажность от рек

```python
def _calculate_moisture_from_rivers(river_mask: np.ndarray, radius: float = 20.0) -> np.ndarray:
    """
    Реки создают влажность (экспоненциальное затухание)

    У реки: 0.9
    Затухание: exp(-distance / radius)
    """
    from scipy.ndimage import distance_transform_edt

    moisture = np.zeros_like(river_mask, dtype=np.float32)

    # Distance transform от рек
    distance_to_river = distance_transform_edt(~river_mask)

    # Экспоненциальное затухание
    moisture = 0.9 * np.exp(-distance_to_river / radius)

    return moisture
```

### 6. Биоактивные зоны (споры)

```python
def _apply_bioactive_moisture(moisture: np.ndarray, organs: dict) -> np.ndarray:
    """
    Органы выделяют споры → локальная влажность

    Metabolic core: высокая биоактивность
    """
    for organ_id, organ in organs.items():
        if organ.type == 'metabolic_organ':
            cx, cy = organ.position
            radius = organ.radius * 2

            y, x = np.ogrid[:moisture.shape[0], :moisture.shape[1]]
            distance = np.sqrt((x - cx)**2 + (y - cy)**2)

            influence = np.maximum(0, 1.0 - distance / radius)
            moisture += influence * 0.4

    return moisture
```

### 7. Интеграция в генератор

```python
class WorldGeneratorV2:
    def _generate_climate(self, world_phase, organs, vessels, elevation,
                         bone_density_map, river_mask) -> tuple:
        """
        Phase 5: Генерация климата
        """
        # Параметры из конфига
        climate_config = self.config['climate']

        # 1. Базовая температура
        temperature = self._calculate_base_temperature(world_phase, (512, 512))

        # 2. Органы
        temperature = self._apply_organ_temperature(
            temperature, organs, radius=climate_config['organ_temp_radius']
        )

        # 3. Кости и артерии
        temperature = self._apply_skeleton_climate(temperature, bone_density_map, vessels)

        # 4. Высота
        temperature = self._apply_elevation_temperature(temperature, elevation)

        # 5. Нормализация
        temperature = np.clip(temperature, 0, 1)

        # 6. Влажность от рек
        moisture = self._calculate_moisture_from_rivers(
            river_mask, radius=climate_config['river_moisture_radius']
        )

        # 7. Биоактивные зоны
        moisture = self._apply_bioactive_moisture(moisture, organs)

        # 8. Высотная осушка
        moisture -= elevation * 0.2

        # 9. Нормализация
        moisture = np.clip(moisture, 0, 1)

        return temperature, moisture
```

## Конфигурация

```yaml
# config/world_generation_v2.yaml
climate:
  base_temperature:
    exhale: 0.6
    inhale: 0.4

  organ_temp_radius: 80.0  # px
  river_moisture_radius: 20.0  # px

  modifiers:
    bone_cooling: -0.4
    arterial_heating: 0.3
    elevation_cooling: -0.3
    elevation_drying: -0.2
```

## Тестирование

```python
def test_organ_temperature():
    organs = {
        'organ_metabolic_core': Organ(position=(256, 256), temperature=0.95, radius=30)
    }
    temperature = np.ones((512, 512)) * 0.5

    temperature = _apply_organ_temperature(temperature, organs, radius=80.0)

    # Вокруг органа должна быть повышенная температура
    assert temperature[256, 256] > 0.7
    assert temperature[100, 100] < 0.6  # Вдали = базовая

def test_river_moisture():
    river_mask = np.zeros((512, 512), dtype=bool)
    river_mask[256, :] = True  # Горизонтальная река

    moisture = _calculate_moisture_from_rivers(river_mask, radius=20.0)

    assert moisture[256, 256] > 0.8  # У реки высокая влажность
    assert moisture[200, 256] < 0.3  # Вдали низкая
```

## Метрики

- **Время выполнения**: ~0.2-0.5 секунды
- **Память**: ~4 MB (temperature + moisture)

## Зависимости

**Зависит от:**
- Phase 0 (world_phase)
- Phase 1 (organs)
- Phase 2 (elevation, bone_density_map)
- Phase 3 (vessels)
- Phase 4 (river_mask)

**Используется в:**
- Phase 7 (Tissues) - температура и влажность для биомов

## Визуализация

```bash
python scripts/visualize_climate.py --seed my_seed
```
