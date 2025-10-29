# Рабочие пакеты Sprint 3.6

**Версия:** v3.0
**Дата:** 29 октября 2025

## Обзор

Sprint 3.6 разделён на 4 рабочих пакета (Work Packages), каждый из которых представляет собой логически завершённый этап с собственными артефактами и критериями валидации.

---

## WP1: Основа мира (Макро-структура)

### Описание

Этот пакет отвечает за создание базовой формы мира — его контуров, оси и ключевых точек.

### Состав фаз

- **Phase 0:** Seed и Meta-параметры
- **Phase 1a:** Spine Creation
- **Phase 1b:** Continent Growth & Organ Placement

### Цель

Получить детерминированную базовую 2D-форму континента, его центральную ось и расположение "органов". Это фундамент, на котором будет строиться всё остальное.

### Выходные артефакты

#### 1. Визуализация

- **Чёрно-белое изображение 512×512** с маской континента
- Наложенная линия "позвоночника" (spine)
- Визуализация центра масс и главной оси
- Визуализация размещённых органов

**Инструмент:** `scripts/visualize_wp1_foundation.py`

#### 2. Данные

```python
World(
    seed="...",
    world_phase="EXHALE",
    age="LATE_EXHALE",
    global_size=(512, 512)
)

ContinentData(
    mask=np.ndarray,           # (512, 512) bool
    heightmap=np.ndarray,      # (512, 512) float [0, 1]
    center=(cx, cy),
    major_axis=((x1, y1), (x2, y2)),
    spine_path=np.ndarray      # (N, 2)
)

organs = {
    'organ_metabolic_core': Organ(...),
    'organ_stomach': Organ(...),
    'ganglion_0': Organ(...),
    'ganglion_1': Organ(...),
    'lymph_node_sclerite': Organ(...)
}
```

### Критерии валидации

#### Функциональная валидация (Unit-тесты)

✅ **test_seed_determinism**
- `_hash_seed` возвращает одинаковый `int` для одинаковых `seed` и `suffix`
- Разные `suffix` дают разные хеши

✅ **test_config_loading**
- YAML конфигурация успешно загружается
- Все ожидаемые параметры присутствуют

✅ **test_array_dimensions**
- Все массивы имеют размер строго 512×512
- Типы данных корректны (bool для mask, float для heightmap)

✅ **test_pca_major_axis**
- PCA корректно находит главную ось на тестовом наборе точек
- Длина оси > 400px

✅ **test_spine_generation**
- Spine path начинается на севере (y≈0) и заканчивается на юге (y≈512)
- Количество точек = `num_points` из конфига
- X координаты центрированы (среднее ≈ 256)

✅ **test_continent_connectivity**
- Континент состоит из 1 связной компоненты (не россыпь островов)
- Суша занимает 55-90% карты

#### Визуальная валидация

👁️ **Континент:**
- Единая крупная масса суши (не россыпь мелких островов)
- Естественная береговая линия (не слишком рваная, не слишком гладкая)

👁️ **Позвоночник:**
- Плавная кривая север → юг
- Проходит примерно по центру карты
- В spine_mode: континент визуально "притянут" к позвоночнику

👁️ **Органы:**
- Metabolic core в центре масс
- Stomach в южной низине
- Ganglions вдоль главной оси (35% и 65%)
- Lymph node на возвышенности

#### Валидация схемы данных

📋 **Структура:**
- `World` имеет поля: `seed`, `world_phase`, `age`, `global_size`
- `ContinentData` имеет поля: `mask`, `heightmap`, `center`, `major_axis`, `spine_path`
- `organs` — словарь с 5 органами

📋 **Типы:**
- `mask`: `np.ndarray` dtype=bool
- `heightmap`: `np.ndarray` dtype=float32
- `center`: `tuple(int, int)`
- `major_axis`: `tuple(tuple(int, int), tuple(int, int))`
- `spine_path`: `np.ndarray` shape=(N, 2)

### Инструменты для создания

**Тесты:**
- `tests/core/test_world_initialization.py`
- `tests/core/test_spine_generation.py`
- `tests/core/test_continent_generation.py`
- `tests/core/test_organ_placement.py`

**Визуализация:**
- `scripts/visualize_wp1_foundation.py` — комплексная визуализация WP1
- `scripts/validate_wp1_schema.py` — валидация схемы данных

---

## WP2: Ключевая анатомия и рельеф

### Описание

Мир обретает трехмерность, скелет и внутреннюю "кровеносную" систему. **Самый важный этап для проверки v3.0 логики.**

### Состав фаз

- **Phase 2:** Skeleton Generation
- **Phase 3:** Vessel Network Generation

### Цель

Сгенерировать финальный рельеф, основанный на костной структуре, и проложить по нему сосудистую сеть, которая **реалистично огибает кости**.

### Выходные артефакты

#### 1. Визуализация

Набор из **трёх ключевых изображений** для сравнения:

1. **bone_density_map.png** — карта плотности костей (градации серого, кости = белые)
2. **elevation_final.png** — итоговая карта высот (градации серого, горы = белые)
3. **vessels_on_bones.png** — bone_density_map + сеть сосудов поверх ⭐ **КРИТИЧЕСКАЯ ВИЗУАЛИЗАЦИЯ**

**Инструмент:** `scripts/visualize_wp2_anatomy.py`

#### 2. Данные

```python
elevation: np.ndarray  # (512, 512) float [0, 1]
bone_density_map: np.ndarray  # (512, 512) float [0, 1] ⭐

skeleton_structure = {
    'vertebrae': List[dict],
    'ribs': List[dict],
    'phalanges': List[dict]
}

vessels: List[dict] = [
    {
        'from': 'organ_metabolic_core',
        'to': 'organ_stomach',
        'type': 'arterial',
        'waypoints': [(x1, y1), (x2, y2), ...],  # Доказательство обхода!
        'width': 10,
        'flow_strength': 1.0
    },
    ...
]

vein_outlets: List[dict] = [
    {'position': (x, y), 'strength': 0.8, 'source_organ': '...'},
    ...
]
```

### Критерии валидации

#### Функциональная валидация (Unit-тесты)

✅ **test_vertebrae_placement**
- Позвонки размещены вдоль spine_path с интервалом ≈ `spacing`
- Все позвонки внутри континента

✅ **test_lsystems_ribs**
- L-система генерирует ветвящуюся структуру без ошибок
- Количество рёбер = `num_ribs` × 2 (левые + правые)

✅ **test_bone_density_map_creation**
- bone_density_map имеет максимумы в местах позвонков
- Плотность затухает с расстоянием от костей

✅ **test_density_aware_pathfinding** ⭐ **КРИТИЧЕСКИ ВАЖЕН!**
- На искусственной карте с "костяной стеной" между двумя органами
- Путь сосуда НЕ проходит через стену (не пересекает зону bone_density > 0.8)
- Путь идёт в обход

✅ **test_space_colonization_convergence**
- Алгоритм успешно соединяет все органы
- Нет "зависших" attraction points

✅ **test_vein_outlets_generation**
- Все vein_outlets находятся в низинах (elevation < threshold)
- Все outlets на континенте (не в океане)

#### Визуальная валидация

👁️ **Карта высот:**
- Четко прослеживаются возвышенности вдоль позвоночника
- Рёберные дуги видны как отходящие хребты
- Соответствие с bone_density_map

👁️ **САМАЯ ГЛАВНАЯ ПРОВЕРКА:**
- На `vessels_on_bones.png` сосуды **явно избегают** белых (плотных) зон
- Артерии проходят по "мягким тканям" (серым/тёмным зонам)
- Нет прямых пересечений сосудов с позвонками или крупными рёбрами

👁️ **Vein outlets:**
- Расположены в низинах
- На пути артерий от органов

#### Валидация схемы данных

📋 **Структура:**
- `elevation`, `bone_density_map`: `np.ndarray` (512, 512) float32
- `vessels`: список словарей с полями `waypoints` (доказательство обхода)
- `vein_outlets`: список словарей с `position`, `strength`

📋 **Инвариант v3.0:** ⭐
- Для каждого waypoint в vessels:
  - `bone_density_map[waypoint_y, waypoint_x] < 0.7` (артерии избегают плотных костей)

### Инструменты для создания

**Тесты:**
- `tests/core/test_skeleton_generation.py`
- `tests/core/test_bone_density_map.py`
- `tests/core/test_vessel_pathfinding.py` ⭐ **КРИТИЧЕСКИЙ**
- `tests/core/test_space_colonization.py`

**Визуализация:**
- `scripts/visualize_wp2_anatomy.py` — комплексная визуализация WP2
- `scripts/validate_wp2_pathfinding.py` — анализ путей артерий ⭐
- `scripts/compare_v2_vs_v3_vessels.py` — сравнение с v2.0 (если есть)

---

## WP3: Системы жизнеобеспечения (Гидрология и Климат)

### Описание

"Статичная" анатомия оживает: по ней текут реки, формируется эрозия и климат.

### Состав фаз

- **Phase 4:** Hydrology
- **Phase 4.5:** Hydraulic Erosion ⭐ NEW in v3.0
- **Phase 5:** Climate

### Цель

Создать реалистичную гидрологическую сеть, сформировать речные долины через эрозию и рассчитать климатические карты.

### Выходные артефакты

#### 1. Визуализация

1. **rivers_on_elevation.png** — эродированная карта высот + синяя маска рек
2. **temperature_map.png** — тепловая карта (от синего к красному)
3. **moisture_map.png** — тепловая карта (от жёлтого к синему)
4. **erosion_comparison.png** — до/после эрозии (side-by-side)

**Инструмент:** `scripts/visualize_wp3_systems.py`

#### 2. Данные

```python
flow_accumulation: np.ndarray  # (512, 512) float
river_mask: np.ndarray  # (512, 512) bool
water_sources: List[dict]  # vein_outlets + natural_springs

elevation_eroded: np.ndarray  # (512, 512) float [0, 1]

temperature: np.ndarray  # (512, 512) float [0, 1]
moisture: np.ndarray  # (512, 512) float [0, 1]
```

### Критерии валидации

#### Функциональная валидация (Unit-тесты)

✅ **test_d8_flow_direction**
- На тестовом уклоне (пик в центре) поток направлен "вниз"
- Нет циклических потоков

✅ **test_flow_accumulation**
- В устьях рек (низины) накопление максимально
- Накопление монотонно растёт вниз по течению

✅ **test_vein_outlets_as_sources**
- Все vein_outlets присутствуют в water_sources
- Их strength > 0

✅ **test_bone_protection** ⭐
- На тестовой карте с костями и мягкими тканями
- Эрозия на костях (bone_density > 0.5) в 3× слабее

✅ **test_gaussian_preprocessing**
- После Gaussian фильтра (sigma=2.0) резкие скачки сглажены
- Средняя высота сохранена

✅ **test_organ_temperature_influence**
- Вокруг metabolic_core температура > базовой
- Затухание с расстоянием

✅ **test_river_moisture**
- У реки (distance=0) влажность ≈ 0.9
- На расстоянии > river_moisture_radius влажность < 0.3

#### Визуальная валидация

👁️ **Гидрология:**
- Реки текут из высокогорья / vein_outlets в низины
- Речная сеть древовидная (притоки сливаются)
- Реки впадают в "океан" (края карты)

👁️ **Эрозия:**
- Вдоль рек видны чёткие долины/каньоны
- Кости сохраняют форму (не размыты)
- Переходы высот плавные (нет резких ступеней)

👁️ **Климат:**
- **Температура:** Горячо у metabolic_core, холодно в горах/на севере
- **Влажность:** Влажно вдоль рек и в низинах, сухо в горах

#### Валидация схемы данных

📋 **Структура:**
- Все карты: `np.ndarray` (512, 512) float32
- `river_mask`: bool
- `water_sources`: список словарей

📋 **Диапазоны:**
- `temperature`, `moisture`, `elevation_eroded`: [0, 1]
- `flow_accumulation`: [0, max_flow]

### Инструменты для создания

**Тесты:**
- `tests/core/test_hydrology_d8.py`
- `tests/core/test_hydraulic_erosion.py`
- `tests/core/test_bone_protection_erosion.py` ⭐
- `tests/core/test_climate_generation.py`

**Визуализация:**
- `scripts/visualize_wp3_systems.py` — комплексная визуализация WP3
- `scripts/compare_erosion_before_after.py` — до/после эрозии
- `scripts/validate_climate_ranges.py` — проверка диапазонов

---

## WP4: Финальная детализация и классификация

### Описание

Финальный штрих — заселение мира "живыми" тканями на основе всех собранных данных.

### Состав фаз

- **Phase 6:** Respiration System
- **Phase 7:** Tissues (Biome Assignment)

### Цель

Классифицировать каждую клетку мира, присвоив ей тип ткани (биом) на основе сложного набора правил и всех предыдущих карт.

### Выходные артефакты

#### 1. Визуализация

1. **bioactive_saturation.png** — тепловая карта "облаков" выдоха
2. **tissue_map_final.png** — полноцветная карта мира (каждый цвет = тип ткани)
3. **caverns_overlay.png** — каверны поверх bone_density_map
4. **tissue_legend.png** — легенда с названиями тканей

**Инструмент:** `scripts/visualize_wp4_final.py`

#### 2. Данные

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

tissue_map: np.ndarray  # (512, 512) dtype='U32' (строковые ID тканей)
```

### Критерии валидации

#### Функциональная валидация (Unit-тесты)

✅ **test_respiratory_potential**
- Потенциал максимален у позвоночника
- THORAX регион имеет высокий потенциал

✅ **test_poisson_disk_sampling**
- Расстояние между каверами ≥ min_distance
- Плотность каверн пропорциональна potential_map

✅ **test_cavern_classification**
- Каверны <15px от позвоночника классифицированы как 'spine_vertebrae'
- Статистика распределения соответствует ожидаемой (36% spine, 45% rib, и т.д.)

✅ **test_bfs_exhalation**
- BFS корректно распространяет сигнал от каверн
- Затухание пропорционально decay_rate
- Сигнал не распространяется в океан

✅ **test_tissue_assignment_priority**
- Специальные случаи (каверны, артерии, реки) имеют высший приоритет
- Контекстные от органов переопределяют стандартные
- Нет неклассифицированных клеток (кроме океана)

✅ **test_tissue_rules_loading**
- tissue_rules.yaml загружается без ошибок
- Все условия в правилах валидны

#### Визуальная валидация

👁️ **Биоактивность:**
- "Облака" bioactive_saturation исходят из каверн
- Наибольшая концентрация вдоль позвоночника (THORAX)

👁️ **Карта тканей:**
- **Логичное распределение:**
  - `chitinous_plates` на костяных хребтах
  - `acid_lake` у желудка (в низине)
  - `spore_fields` в зонах высокой биоактивности
  - `lymph_river` совпадает с river_mask
  - `alveolar_cavern` в точках каверн
  - `pulsating_plains` в диафрагме
  - `thermal_vents` у metabolic_core
- **Нет артефактов:**
  - Нет больших неклассифицированных областей
  - Границы тканей не слишком резкие
  - Нет "шахматного" паттерна

👁️ **Каверны:**
- Концентрация вдоль позвоночника и рёберных дуг
- Минимум в ORGANOID регионе

#### Валидация схемы данных

📋 **Структура:**
- `caverns`: список словарей с полями `position`, `formation_cause`
- `bioactive_saturation`: `np.ndarray` (512, 512) float32 [0, 1]
- `tissue_map`: `np.ndarray` (512, 512) dtype='U32'

📋 **Полнота:**
- Все клетки континента классифицированы (не пустые строки)
- Все типы тканей из tissue_rules.yaml присутствуют хотя бы 1 раз

### Инструменты для создания

**Тесты:**
- `tests/core/test_respiration_system.py`
- `tests/core/test_cavern_classification.py`
- `tests/core/test_tissue_assignment.py`
- `tests/core/test_tissue_rules.py`

**Визуализация:**
- `scripts/visualize_wp4_final.py` — комплексная визуализация WP4
- `scripts/generate_tissue_legend.py` — создание легенды
- `scripts/validate_tissue_coverage.py` — статистика покрытия тканей

---

## Сквозная интеграционная проверка

### Инструмент: `scripts/validate_full_pipeline.py`

Запускает полную генерацию мира от Phase 0 до Phase 7 и проверяет:

1. **Сквозное прохождение:** Нет ошибок на всех фазах
2. **Инварианты v3.0:**
   - Артерии огибают кости (WP2)
   - Эрозия слабее на костях (WP3)
   - Tissue_map покрывает весь континент (WP4)
3. **Производительность:** Полная генерация < 10 секунд
4. **Детерминизм:** Два запуска с одним seed дают идентичные результаты

### Критерии успеха Sprint 3.6

✅ Все 4 рабочих пакета прошли валидацию
✅ Все unit-тесты зелёные
✅ Все визуальные артефакты созданы и соответствуют критериям
✅ Интеграционный тест `validate_full_pipeline.py` проходит
✅ v3.0 инвариант подтверждён: артерии реалистично огибают кости

---

## Структура тестов

```
tests/
├── core/
│   ├── test_world_initialization.py          # WP1
│   ├── test_spine_generation.py              # WP1
│   ├── test_continent_generation.py          # WP1
│   ├── test_organ_placement.py               # WP1
│   ├── test_skeleton_generation.py           # WP2
│   ├── test_bone_density_map.py              # WP2
│   ├── test_vessel_pathfinding.py            # WP2 ⭐
│   ├── test_space_colonization.py            # WP2
│   ├── test_hydrology_d8.py                  # WP3
│   ├── test_hydraulic_erosion.py             # WP3
│   ├── test_bone_protection_erosion.py       # WP3 ⭐
│   ├── test_climate_generation.py            # WP3
│   ├── test_respiration_system.py            # WP4
│   ├── test_cavern_classification.py         # WP4
│   ├── test_tissue_assignment.py             # WP4
│   └── test_tissue_rules.py                  # WP4
└── integration/
    └── test_full_pipeline.py                 # Сквозной тест
```

## Структура визуализации

```
scripts/
├── visualize_wp1_foundation.py               # WP1 артефакты
├── validate_wp1_schema.py                    # WP1 валидация
├── visualize_wp2_anatomy.py                  # WP2 артефакты
├── validate_wp2_pathfinding.py               # WP2 ⭐ критическая проверка
├── compare_v2_vs_v3_vessels.py               # WP2 сравнение версий
├── visualize_wp3_systems.py                  # WP3 артефакты
├── compare_erosion_before_after.py           # WP3 сравнение эрозии
├── validate_climate_ranges.py               # WP3 валидация
├── visualize_wp4_final.py                    # WP4 артефакты
├── generate_tissue_legend.py                 # WP4 легенда
├── validate_tissue_coverage.py               # WP4 статистика
└── validate_full_pipeline.py                 # Интеграция ⭐
```

---

**Версия документа:** 1.0
**Статус:** Ready for Implementation
**Следующий шаг:** Начать с WP1 (Sprint 3.7)
