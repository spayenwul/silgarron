# ПОСЛОЙНЫЙ АНАЛИЗ ГЕНЕРАЦИИ МИРА СИЛЬГАРРОН
## От органов к тканям: логика первичности систем

**Дата:** 25 октября 2025
**Версия:** 2.0 - CANONICAL MODEL (v2.0 Architecture Migration)

---

## 🌟 UNIFIED CONCEPT: Анатомическая Структура → Географическое Воплощение → Детальная Физиология

**Ключевая идея v2.0:**

Сильгаррон - это не "континент с наложенными органами" и не "органы, игнорирующие географию". Это **единый живой организм**, где анатомия и география - две стороны одной сущности.

### Три фазы воплощения:

#### 1️⃣ Анатомическая Структура (Anatomical Framework)
**"Скелет организма"**

Первым возникает **структурный каркас** - позвоночный хребет (spine):
- Процедурно генерируется изогнутая ось континента
- Определяет направление роста и симметрию
- Создаёт фундамент для всей последующей физиологии

**Метод:** Spine-Based Generation (единственный канонический подход)

#### 2️⃣ Географическое Воплощение (Geographic Embodiment)
**"Плоть на костях"**

Вокруг структурного каркаса **нарастает плоть** - континент:
- Perlin Noise модулируется формой позвоночника
- Континент растёт вокруг spine, следуя его изгибам
- Создаётся органичная форма с естественными границами (океан/суша)

**Результат:** Живой организм обретает географическую форму

#### 3️⃣ Детальная Физиология (Detailed Physiology)
**"Внутренние системы"**

На сформированном континенте размещаются **органы и системы**:
- Органы привязываются к точкам вдоль spine
- Сосуды следуют анатомической логике
- Ткани отражают физиологическое состояние

**Результат:** География становится анатомией, анатомия определяет географию

### Почему это решает противоречие "Organs vs Continent"?

**Старая дилемма:**
- ❌ Если Organs First → континент игнорирует их
- ❌ Если Continent First → органы выглядят наложенными

**Новое решение:**
- ✅ **Spine First** → создаёт структуру
- ✅ **Continent FROM Spine** → география следует анатомии
- ✅ **Organs ALONG Spine** → анатомия интегрирована в географию

**Аналогия:** Дерево не растёт "сначала крона, потом ствол" и не "сначала ствол, потом корни". Оно растёт **одновременно**, следуя единой логике развития. Так же и Сильгаррон: spine → continent → organs - это единый процесс **органического роста**.

---

## 🎯 ФУНДАМЕНТАЛЬНАЯ СМЕНА ПАРАДИГМЫ

### ЧТО БЫЛО (Sprint 3.5):
**Подход:** "Снизу вверх" - сначала текстуры (Perlin), потом смысл (ткани)

```
Perlin Noise (elevation)
    ↓
Ridge mask (хребет)
    ↓
Flow accumulation (лимфа)
    ↓
Poisson caverns (каверны)
    ↓
Temperature synthesis
    ↓
Tissue assignment (назначаем биомы задним числом)
```

**Проблема:** Генератор не знает, ЧТО он создаёт. Он делает красивые шумы, а потом говорит "пусть это будет хребет".

---

### ЧТО ДОЛЖНО БЫТЬ (после ADR-016, ADR-019, Лор v3.0):
**Подход:** "Сверху вниз" - сначала ОРГАНЫ (анатомия), потом текстуры (физика)

```
АНАТОМИЯ (placement органов)
    ↓
ФИЗИОЛОГИЯ (связи между органами)
    ↓
ГЕОЛОГИЯ (как физиология влияет на рельеф)
    ↓
ГИДРОЛОГИЯ (как всё это влияет на реки)
    ↓
КЛИМАТ (как всё это влияет на температуру)
    ↓
ЭКОЛОГИЯ (назначение типов тканей с пониманием)
```

**Суть:** Генератор **ЗНАЕТ**, что он создаёт. Он размещает желудок, зная что там будет жарко и влажно.

---

## 📐 ИЕРАРХИЯ ПЕРВИЧНОСТИ: 7 СЛОЁВ ГЕНЕРАЦИИ

### 🔴 СЛОЙ 0: SEED И МЕТА-ПАРАМЕТРЫ (детерминизм)

**Первичность:** АБСОЛЮТНАЯ - всё начинается отсюда

**Что создаётся:**
```python
# Мета-конфигурация мира
world_config = {
    'seed': 'silgarron_alpha',
    'world_phase': 'EXHALE',  # Фаза дыхания (10-15 тыс. лет цикла)
    'age': 'LATE_EXHALE',     # Текущая эпоха
    'size': (512, 512),       # Размер глобальной карты (Stage 0: Global Skeletons)
    'scale_factor': 8,        # Stage 1: 4096×4096 детализация (Sprint 3.9)
}
```

**Метод:** Конфигурационный файл + hash(seed)

**Влияет на всё:**
- `world_phase` определяет:
  - Атмосферное давление (1.0 vs 1.8)
  - Гравитацию (1.0 vs 0.7)
  - Плодородие почвы (+0.2 в Exhale)
  - Активность альвеолярных каверн

**Зависит от:** Ничего (это точка отсчёта)

---

### 🟡 ФАЗА 1: ФОРМИРОВАНИЕ ЖИВОГО КОНТИНЕНТА (Spine + Geographic Embodiment)

**Первичность:** 1 - определяет анатомическую структуру и её географическое воплощение

**Философия:**
> Сильгаррон - это не искусственный квадрат 512×512. Это **живой организм**, который "вырос" на первичном океане. Первым формируется **позвоночный хребет (spine)**, затем вокруг него нарастает **плоть континента**, и только потом размещаются **внутренние органы**.

**Проблема старого подхода:**
- ❌ Органы размещались на абстрактной карте
- ❌ Мир заполнял весь квадрат 512×512 искусственно
- ❌ Не было понятия "океан" vs "суша"
- ❌ Континент не имел анатомической структуры

**Новый подход (v2.0):**
- ✅ **Spine First** - сначала структурный каркас
- ✅ **Continent FROM Spine** - география следует анатомии
- ✅ **Organs ALONG Spine** - органы интегрированы с географией

---

## PHASE 1a: SPINE CREATION (Анатомическая Структура)

**Статус:** ✅ Implemented (`_generate_spine_path()`)

**Метод:** Spine-Based Generation (ЕДИНСТВЕННЫЙ КАНОНИЧЕСКИЙ МЕТОД)

**Что создаётся:**

### 1a.1. Процедурная генерация позвоночника

```python
def _generate_spine_path(self, seed: str) -> List[Tuple[int, int]]:
    """
    Генерирует изогнутый позвоночный хребет континента

    Это НЕ прямая линия, а органическая кривая:
    - Следует естественным изгибам
    - Создаёт асимметрию (живой организм)
    - Определяет "ось роста" континента
    """
    rng = np.random.RandomState(hash_seed(seed + "spine"))

    # Параметры spine
    spine_points = []
    start_y = 100  # Начало в верхней трети
    end_y = 400    # Конец в нижней трети
    center_x = 256 # Центр карты 512×512

    # Генерируем контрольные точки с органическим смещением
    num_control_points = 12
    for i in range(num_control_points):
        progress = i / (num_control_points - 1)
        y = start_y + (end_y - start_y) * progress

        # Случайное смещение по X (создаёт изгибы)
        curvature = rng.normal(0, 30)  # Умеренная кривизна
        x = center_x + curvature

        # Добавляем "волнистость" (синусоидальный компонент)
        wave = np.sin(progress * np.pi * 3) * 20  # 3 "волны"
        x += wave

        spine_points.append((int(x), int(y)))

    # Сглаживание кривой (Catmull-Rom Spline)
    smooth_spine = catmull_rom_spline(spine_points, num_samples=100)

    return smooth_spine
```

**Результат:** Изогнутая ось длиной ~100 точек, определяющая "позвоночник" континента

### 1a.2. Вычисление width profile (профиль расширения)

```python
def _calculate_width_profile(self, spine_length: int) -> np.ndarray:
    """
    Определяет, насколько "толстым" должен быть континент
    в каждой точке вдоль позвоночника

    Аналогия: тело шире в грудной клетке, уже в "шее" и "хвосте"
    """
    widths = np.zeros(spine_length)

    for i in range(spine_length):
        progress = i / spine_length

        if progress < 0.2:  # "Голова" - узкая
            widths[i] = 40 + progress * 100
        elif progress < 0.5:  # "Торакс" - широкая
            widths[i] = 120 + np.sin(progress * np.pi) * 40
        elif progress < 0.8:  # "Брюшная полость" - средняя
            widths[i] = 100 - (progress - 0.5) * 60
        else:  # "Конечность" - узкая
            widths[i] = 60 - (progress - 0.8) * 100

    return widths
```

**Зависит от:** СЛОЙ 0 (seed)

**Влияет на:** Phase 1b (continent shape), Phase 2 (organ placement)

---

## PHASE 1b: CONTINENT GROWTH (Географическое Воплощение + Органы)

**Статус:** ✅ Implemented (`_generate_continent()` with spine)

**Метод:** Spine-Modulated Perlin Noise + Morphological Smoothing

**Что создаётся:**

### 1b.1. Макро-рельеф континента (модулированный spine)

**Метод:** Perlin Noise с Shape Mask из spine

```python
# ШАГ 1: Создаём Shape Mask из spine (см. Phase 1a)
shape_mask = self._create_spine_shape_mask(spine_path, width_profile)
# Результат: gradient mask где 1.0 = вдоль spine, 0.0 = далеко от spine

# ШАГ 2: Генерируем базовый Perlin Noise
base_noise = generate_perlin_noise(
    seed=hash(world_seed + "continent"),
    size=(512, 512),
    scale=150,        # ОЧЕНЬ низкая частота (плавные контуры)
    octaves=2,        # Минимум октав (макро-формы)
    persistence=0.6
)

# ШАГ 3: КЛЮЧЕВОЙ МОМЕНТ - модулируем noise через shape_mask
# Континент растёт ВОКРУГ spine, а не случайно
modulated_heightmap = base_noise * shape_mask

# ШАГ 4: Threshold: где "суша", где "океан"
sea_level = 0.38  # Оптимизировано (см. PARAMETER_TUNING.md)
continent_mask = (modulated_heightmap > sea_level)

# ШАГ 5: Морфологическое сглаживание береговой линии
continent_mask = morphology.binary_opening(continent_mask, iterations=3)
continent_mask = morphology.binary_closing(continent_mask, iterations=2)
continent_mask = gaussian_filter(continent_mask.astype(float), sigma=3.0) > 0.5
```

**Результат:** Органичная форма континента с:
- Заливами и бухтами
- Полуостровами
- Возможно, несколькими островами
- Естественной береговой линией
- **Форма следует за spine** - континент вытянут вдоль позвоночной оси

### 1b.2. Размещение органов ВДОЛЬ spine (Detailed Physiology)

**КРИТИЧЕСКОЕ ОТЛИЧИЕ от старого подхода:**
- ❌ Было: Органы в фиксированных координатах (128, 180), (80, 120)
- ✅ Стало: Органы привязаны к **точкам вдоль spine** (progress = 0.3, 0.5, 0.7)

**Метод:** Параметрическое размещение относительно spine

```python
# НОВЫЙ ПОДХОД: Органы привязаны к spine, не к фиксированным координатам!
def place_organs_along_spine(spine_path: List[Tuple[int, int]], world_seed: str):
    """
    Размещает органы вдоль позвоночника на заданных параметрических позициях

    progress=0.0 → начало spine (голова)
    progress=0.5 → середина spine (торакс)
    progress=1.0 → конец spine (конечность)
    """
    organs = {}
    spine_length = len(spine_path)

    # Метаболическое ядро - в середине торакса (прогресс 0.35)
    core_idx = int(spine_length * 0.35)
    organs['organ_metabolic_core'] = {
        'type': 'metabolic_organ',
        'position': spine_path[core_idx],  # Прямо НА spine!
        'spine_progress': 0.35,
        'radius': 30,
        'temperature': 0.95,
        'nutrient_output': 0.9
    }

    # Желудок - в брюшной полости (прогресс 0.65)
    stomach_idx = int(spine_length * 0.65)
    organs['organ_stomach'] = {
        'type': 'digestive',
        'position': spine_path[stomach_idx],
        'spine_progress': 0.65,
        'radius': 25,
        'temperature': 0.85,
        'acid_level': 0.8
    }

    # ❌ УДАЛЕНО: 'organ_lung_left' и 'organ_lung_right'
    # Дыхательная система теперь генерируется в Phase 6 (skeleton-driven)!

    # Ганглии - распределены вдоль spine
    ganglion_positions = [0.25, 0.45, 0.75]  # Торакальный, диафрагмальный, абдоминальный
    for i, progress in enumerate(ganglion_positions):
        idx = int(spine_length * progress)
        organs[f'ganglion_{i}'] = {
            'type': 'neural_cluster',
            'position': spine_path[idx],
            'spine_progress': progress,
            'radius': 12 + i*2,
            'control_strength': 0.7 - i*0.1
        }

    # Иммунный узел - в возвышенности (прогресс 0.30)
    immune_idx = int(spine_length * 0.30)
    organs['lymph_node_sclerite'] = {
        'type': 'immune_node',
        'position': spine_path[immune_idx],
        'spine_progress': 0.30,
        'radius': 10,
        'cell_production': 0.9
    }

    return organs
```

**Зависит от:** Phase 1a (spine_path)

**Влияет на:** Phase 2 (vessels), Phase 3 (geology), Phase 5 (climate)

### 1b.3. Региональное деление (зоны на основе spine + анатомии)

**КРИТИЧЕСКОЕ ОТЛИЧИЕ от старого подхода:**
- ❌ Было: Прямоугольные bounds (x1, y1, x2, y2)
- ✅ Стало: Органические маски, определяемые **spine + ширина + органы**

**Метод:** Регионы - это маски, определяемые анатомией

```python
# Вместо жёстких bounds: (0, 0, 512, 300)
# Теперь регионы - это маски, полученные комбинацией spine + органов

def define_regions(spine_path, continent_mask, organ_positions, skeleton):
    regions = {}
    
    # THORAX = где есть рёбра + кости + дыхательный потенциал
    thorax_mask = np.zeros_like(continent_mask)
    thorax_mask = (skeleton['ribs'] > 0.3) & continent_mask
    thorax_mask = expand_region(thorax_mask, radius=20)
    
    regions['THORAX'] = {
        'mask': thorax_mask,
        'characteristics': {
            'elevation_bias': +0.3,
            'bone_density': 0.8,
            'respiratory_potential': 0.9  # НОВОЕ: вероятность каверн
        }
    }
    
    # ORGANOID = зона вокруг метаболических органов
    organoid_mask = create_radial_mask(
        center=organ_positions['organ_metabolic_core'],
        radius=50,
        continent_mask=continent_mask
    )
    
    regions['ORGANOID'] = {
        'mask': organoid_mask,
        'characteristics': {
            'elevation_bias': -0.2,
            'nutrient_richness': 0.9,
            'respiratory_potential': 0.1  # Каверн почти нет
        }
    }
    
    return regions
```

**Зависит от:** СЛОЙ 0 (seed), Phase 1a (spine)

**Влияет на:** Phase 2 (vessels), Phase 3 (geology), Phase 6 (caverns)

**ИТОГО Phase 1 (Spine + Continent + Organs):**
- ✅ Создан позвоночник (spine) - структурный каркас
- ✅ Континент вырос вокруг spine - географическое воплощение
- ✅ Органы размещены вдоль spine - детальная физиология
- ✅ Регионы определены анатомически - не прямоугольники!

---

### 🟢 PHASE 2: ГЕОЛОГИЧЕСКАЯ СТРУКТУРА (Elevation, Skeleton)

**Статус:** 🚧 Not Implemented (planned for Sprint 3.7)

**Философия:**
> Рельеф - это НЕ случайный шум. Это результат анатомии:
> - Где **кости** (хребет, рёбра) → высоко
> - Где **мягкие ткани** (органы, мышцы) → низко
> - Скелет ПЕРВИЧЕН - артерии будут огибать кости, а не бурить их

**⚠️ КРИТИЧЕСКОЕ ИЗМЕНЕНИЕ v3.0:** Skeleton теперь генерируется ДО Vessels, чтобы артерии могли огибать плотные костные структуры.

**Что создаётся:**

### 2.1. Базовый рельеф (Base Elevation)

**Метод:** Композиция из нескольких источников

```python
elevation = np.zeros((512, 512))  # Stage 0: Global Skeletons

# Источник 1: Региональный bias (от регионов)
for region in regions:
    mask = create_region_mask(region['bounds'])
    elevation += mask * region['characteristics']['elevation_bias']

# Источник 2: Органическая текстура (Perlin Noise - фоновая шероховатость)
organic_texture = generate_perlin_noise(
    seed=hash(world_seed + "organic"),
    scale=50,
    octaves=3,
    weight=0.2  # Слабое влияние (20%)
)
elevation += organic_texture

# Источник 3: Костная структура (главный фактор!)
bone_structure = np.zeros((512, 512))

# 3a. Позвоночный хребет (центральная ось мира)
spine_mask = create_vertical_ridge(
    center_x=128,
    width=40,
    height_boost=0.5  # +50% к высоте
)
bone_structure += spine_mask

# 3b. Рёбра (боковые хребты от позвоночника)
for i, rib_y in enumerate(range(60, 140, 10)):  # 8 пар рёбер
    rib_mask = create_rib_structure(
        origin=(128, rib_y),
        angle=30 + i*5,  # Изгиб
        length=60,
        width=8,
        height_boost=0.3
    )
    bone_structure += rib_mask

# 3c. Фаланги (пальцы конечности)
for finger_x in [50, 90, 130, 170, 210]:
    phalanx_mask = create_finger_bone(
        x=finger_x,
        y_range=(240, 256),
        height_boost=0.4
    )
    bone_structure += phalanx_mask

elevation += bone_structure * 0.6  # Кости - главный фактор (60%)

# Источник 4: Влияние органов (локальные возвышенности/впадины)
for organ_id, organ in organs.items():
    if organ['type'] == 'metabolic_organ':
        # Желудок создаёт ВПАДИНУ (тяжёлый, проседает вниз)
        organ_mask = create_radial_gradient(
            center=organ['position'],
            radius=organ['radius'],
            falloff='quadratic'
        )
        elevation -= organ_mask * 0.3  # Понижение
    
    elif organ['type'] == 'respiratory':
        # Лёгкие - пористые, слегка приподняты
        organ_mask = create_radial_gradient(
            center=organ['position'],
            radius=organ['radius'],
            falloff='linear'
        )
        elevation += organ_mask * 0.15  # Небольшое повышение

# Источник 5: Артерии прорезают долины
for vessel in vessels:
    valley_mask = create_vessel_valley(
        waypoints=vessel['waypoints'],
        width=vessel['width'] * 2,
        depth=0.1  # Лёгкая впадина вдоль артерии
    )
    elevation -= valley_mask

# Нормализация в [0, 1]
elevation = (elevation - elevation.min()) / (elevation.max() - elevation.min())
```

**Результат:** Карта высот и плотности костей, где:
- Торакс (грудная клетка) - высокий (кости, хребет)
- Диафрагма - средний (мышечная стена)
- Органоид - низкий (брюшная полость, впадина)
- Конечность - фаланговые плато (отдельные возвышенности)
- Bone density map - для Phase 3 (vessels pathfinding)

**Зависит от:** Phase 1 (organs, regions), региональный bias

**Влияет на:** Phase 3 (vessels - через bone density), Phase 4 (hydrology), Phase 5 (climate), Phase 7 (tissues)

---

### 🟠 PHASE 3: ФИЗИОЛОГИЧЕСКИЕ СВЯЗИ (Vessels & Nerves)

**Статус:** 🚧 Not Implemented (planned for Sprint 3.8)

**Философия:**
> Органы не существуют изолированно. Между ними текут **АРТЕРИИ** (ихор/лимфа) и **НЕРВЫ**. Артерии — это ПОДЗЕМНАЯ инфраструктура, которая **огибает** массивные костные структуры.

**⚠️ КРИТИЧЕСКОЕ ИЗМЕНЕНИЕ v3.0:** Vessels теперь генерируются ПОСЛЕ Skeleton (Phase 2) с использованием **density-aware pathfinding**.

**Что создаётся:**

### 3.1. Магистральные артерии с Space Colonization

**Метод:** Space Colonization Algorithm с чувствительностью к плотности костей

```python
# Алгоритм Space Colonization для артерий
def generate_vessel_network_with_density(organs, bone_density_map):
    """
    Генерирует сеть артерий, избегающих плотных костных структур

    Алгоритм:
    1. Расположить attraction points (целевые точки) в позициях органов
    2. Вырастить ветви от metabolic_core к другим органам
    3. При расчёте пути учитывать "стоимость" прохождения через кости
    4. Ветви огибают плотные участки, следуя пути наименьшего сопротивления
    """
    # Определяем attraction points (органы как цели)
    attraction_points = []
    for organ_id, organ in organs.items():
        if organ_id != 'organ_metabolic_core':  # Кроме источника
            attraction_points.append({
                'position': organ['position'],
                'importance': organ.get('nutrient_demand', 0.5)
            })

    # Начальная точка: metabolic_core
    root_position = organs['organ_metabolic_core']['position']

    # Параметры Space Colonization
    influence_radius = 50.0  # Радиус влияния attraction point
    kill_distance = 10.0     # Расстояние "достижения" цели
    segment_length = 5.0     # Длина сегмента ветви

    # КЛЮЧЕВОЙ ПАРАМЕТР: штраф за плотность костей
    bone_density_penalty = 3.0  # Множитель стоимости

    branches = []
    active_tips = [{'position': root_position, 'direction': np.array([0, 1])}]

    while attraction_points and active_tips:
        for tip in active_tips:
            # Найти ближайший attraction point
            closest_point = None
            min_distance = float('inf')

            for ap in attraction_points:
                dist = np.linalg.norm(np.array(ap['position']) - tip['position'])
                if dist < influence_radius and dist < min_distance:
                    # НОВОЕ: учитываем плотность костей
                    bone_density = bone_density_map[int(ap['position'][1]), int(ap['position'][0])]
                    cost = dist * (1.0 + bone_density * bone_density_penalty)

                    if cost < min_distance:
                        min_distance = cost
                        closest_point = ap

            if closest_point:
                # Направление к цели
                direction = np.array(closest_point['position']) - tip['position']
                direction = direction / np.linalg.norm(direction)

                # Новая позиция (с учётом огибания костей)
                new_position = tip['position'] + direction * segment_length

                # Сохраняем ветвь
                branches.append({
                    'from': tip['position'],
                    'to': new_position,
                    'type': 'arterial'
                })

                # Обновляем tip
                tip['position'] = new_position
                tip['direction'] = direction

                # Проверка достижения цели
                if np.linalg.norm(new_position - np.array(closest_point['position'])) < kill_distance:
                    attraction_points.remove(closest_point)

    return branches

# Пример результата:
vessels = [
    {
        'from': 'organ_metabolic_core',
        'to': 'organ_stomach',
        'type': 'arterial',
        'width': 10,
        'flow_strength': 1.0,
        'waypoints': [(128,180), (135,190), (128,200)]  # Огибает кость!
    }
]

# КРИТИЧЕСКАЯ КОНЦЕПЦИЯ:
# Эти артерии - НЕ реки на поверхности!
# Это ПОДЗЕМНЫЕ каналы, по которым течёт ихор.
# Они ОГИБАЮТ кости, используя путь наименьшего сопротивления.
```

**Параметры:**
- `bone_density_penalty = 3.0`: Артерии предпочитают мягкие ткани
- `influence_radius = 50.0`: Дальность "притяжения" к органам
- `segment_length = 5.0`: Детализация пути

### 3.2. Нервные связи

**Метод:** Нервы "следуют" за сосудами (как и раньше)

```python
# Нервы спаяны с сосудами (из лора)
nerves = []
for vessel in vessels:
    nerve = {
        'follows_vessel': vessel['id'],
        'control_range': 3,  # Радиус влияния вокруг сосуда
        'signal_strength': vessel['flow_strength'] * 0.8
    }
    nerves.append(nerve)
```

**Зависит от:** Phase 1 (organs), Phase 2 (bone_density_map)

**Влияет на:** Phase 4 (hydrology - vein outlets), Phase 5 (climate - heat transport), Phase 7 (tissues)

---

### 🔵 PHASE 4: ГИДРОЛОГИЧЕСКАЯ СИСТЕМА (Rivers, Veins)

**Первичность:** ЧЕТВЁРТАЯ - вода течёт ПО рельефу и ИЗ артерий

**Статус:** 🚧 Not Implemented (planned for Sprint 3.8)

**Философия:** (из ADR-019 v2)
> Реки в Сильгарроне - это НЕ только поверхностный сток. Они питаются из **выходов подземных артерий** (вен). Артерия → выход на поверхность → исток реки.

**Что создаётся:**

### 4.1. Карта источников (Vein Outlets)

**Метод:** Преобразование артерий в поверхностные источники

```python
vein_outlets = []

for vessel in vessels:
    if vessel['type'] == 'arterial':  # Артерии, не лимфа
        # Артерия периодически "выходит на поверхность"
        for i in range(0, len(vessel['waypoints'])-1, 3):  # Каждые 3 точки
            outlet = {
                'position': vessel['waypoints'][i],
                'strength': vessel['flow_strength'] * 0.5,  # Половина потока
                'type': 'arterial_outlet'
            }
            vein_outlets.append(outlet)

# Также добавляем "естественные" источники в высокогорье
for y in range(60, 140):  # Вдоль хребта
    if random_from_seed(seed, y) > 0.8:  # 20% вероятность
        outlet = {
            'position': (128 + random.randint(-10, 10), y),
            'strength': 0.2,  # Слабый источник
            'type': 'natural_spring'
        }
        vein_outlets.append(outlet)
```

### 4.2. D8 Flow Accumulation с источниками

**Метод:** (из ADR-019 v2) Модифицированный D8

```python
# Создаём карту "осадков" = источники воды
precipitation_map = np.ones((512, 512)) * 0.01  # Фоновые осадки (слабые)

# Добавляем мощные источники из вен
for outlet in vein_outlets:
    x, y = outlet['position']
    precipitation_map[y, x] += outlet['strength'] * 100  # Мощный источник!

# Запускаем D8 Flow Accumulation
flow_accumulation = calculate_d8_flow(
    elevation=elevation,
    precipitation=precipitation_map  # НОВОЕ: источники из вен
)

# Порог: где flow > threshold → река
river_threshold = np.percentile(flow_accumulation, 95)  # Топ 5%
river_mask = (flow_accumulation > river_threshold)

# Ширина реки зависит от накопленного потока
river_width = np.zeros((512, 512))
river_width[river_mask] = np.log1p(flow_accumulation[river_mask]) * 2
```

**Результат:**
- Реки НЕ случайны - они текут из артериальных выходов
- Магистральные реки идут от органов к периферии
- Соответствует лору: "Лимфатические реки" = поверхностное проявление артерий
- **Базовая гидрология** готова для Phase 4.5 (Hydraulic Erosion)

**Зависит от:** Phase 2 (elevation), Phase 3 (vessels - vein outlets)

**Влияет на:** Phase 4.5 (erosion), Phase 5 (climate), Phase 7 (tissues)

---

### 🌊 PHASE 4.5: ГИДРАВЛИЧЕСКАЯ ЭРОЗИЯ (Hydraulic Erosion)

**Статус:** 🆕 NEW in v3.0 - Not Implemented (planned for Sprint 3.8)

**Философия:**
> Гидравлическая эрозия симулирует реалистичное "вымывание" ландшафта водными потоками. В Сильгарроне это **"Лимфатическая эрозия"** - подземная лимфа выходит на поверхность в точках артерий, создавая глубокие речные долины.

**⚠️ v3.0 УЛУЧШЕНИЯ:**
1. **Предварительная обработка рельефа**: Гауссово размытие перед эрозией (убирает резкие артефакты от L-Systems в будущем)
2. **Фокусировка источников**: Мощные источники в точках выхода артерий, слабый фоновый "дождь"

**Что создаётся:**

### 4.5.1. Предварительная обработка (Gaussian Smoothing)

**Метод:** Сглаживание рельефа перед эрозией

```python
from scipy.ndimage import gaussian_filter

# Проблема: L-Systems (Phase 2) могут создавать резкие вертикальные структуры
# Решение: Легкое размытие для гидравлической эрозии (сохраняя макро-структуру)

elevation_for_erosion = gaussian_filter(elevation, sigma=2.0)

# sigma=2.0: Убирает резкие пиксельные артефакты
# Макро-структура (хребты, долины) сохраняется
```

**Результат:** Сглаженная карта высот, пригодная для симуляции водного потока

### 4.5.2. Фокусированная эрозия (Focused Hydraulic Erosion)

**Метод:** Симуляция водного потока с переменной "силой осадков"

```python
def hydraulic_erosion_focused(
    elevation,
    vein_outlets,      # Точки выхода артерий
    iterations=50,
    erosion_rate=0.3,
    bone_protection=True
):
    """
    Гидравлическая эрозия с фокусировкой на выходы артерий

    Ключевые параметры:
    - Мощные источники в vein_outlets (strength × 100)
    - Слабый фоновый "дождь" (0.01)
    - Bone protection: кости эродируются медленнее
    """
    eroded_elevation = elevation.copy()

    for iteration in range(iterations):
        # 1. Распределение воды
        water_map = np.ones_like(elevation) * 0.01  # Фоновый дождь (слабый!)

        # 2. ФОКУСИРОВКА: Мощные источники в точках выхода артерий
        for outlet in vein_outlets:
            x, y = outlet['position']
            water_map[y, x] += outlet['strength'] * 100  # Мощный поток!

        # 3. Симуляция потока (D8 или particle-based)
        flow_map = calculate_water_flow(eroded_elevation, water_map)

        # 4. Эрозия и осаждение
        for y in range(elevation.shape[0]):
            for x in range(elevation.shape[1]):
                flow = flow_map[y, x]

                if flow > 0:
                    # Эрозия: вода уносит материал
                    erosion_amount = erosion_rate * flow

                    # ЗАЩИТА КОСТЕЙ: кости эродируются медленнее
                    if bone_protection and bone_density_map[y, x] > 0.5:
                        erosion_amount *= 0.3  # Кости в 3 раза прочнее

                    eroded_elevation[y, x] -= erosion_amount

                    # Осаждение: материал откладывается ниже по течению
                    # (упрощённо: в соседней клетке вниз)

    return eroded_elevation
```

**Параметры:**
- `iterations = 50`: Количество циклов симуляции
- `erosion_rate = 0.3`: Скорость эрозии
- `bone_protection = True`: Кости эродируются медленнее (30% скорости)
- Мощность источника в vein_outlet: `strength × 100` (в 100 раз сильнее дождя!)
- Фоновый дождь: `0.01` (очень слабый)

### 4.5.3. Результат эрозии

**Эффект:**
- **Глубокие речные долины** вдоль артериальных выходов
- Плавные переходы высот (нет резких ступеней)
- Кости сохраняют форму (защищены от эрозии)
- Реки "прорезают" ландшафт, создавая каньоны

```python
# Пример результата:
elevation_eroded = hydraulic_erosion_focused(
    elevation=elevation_smoothed,
    vein_outlets=vein_outlets,
    iterations=50,
    erosion_rate=0.3
)

# Визуализация:
# - До эрозии: плавные холмы
# - После эрозии: глубокие V-образные долины вдоль рек
```

**Зависит от:** Phase 2 (elevation, bone_density), Phase 3 (vessels), Phase 4 (vein_outlets, river_mask)

**Влияет на:** Phase 5 (climate - влажность вдоль долин), Phase 7 (tissues - речные биомы)

---

### 🟣 PHASE 5: КЛИМАТИЧЕСКАЯ СИСТЕМА (Temperature, Moisture)

**Первичность:** ПЯТАЯ - климат зависит от органов, рельефа и рек

**Статус:** 🚧 Not Implemented (planned for Sprint 3.8)

**Философия:**
> Температура - это не абстрактный шум. Это результат **метаболической активности органов**.

**Что создаётся:**

### 5.1. Температурная карта

**Метод:** Композиция источников тепла

```python
temperature = np.zeros((512, 512))

# Источник 1: Базовая температура от world_phase
if world_phase == 'EXHALE':
    base_temp = 0.6  # Тёплая фаза
else:  # INHALE
    base_temp = 0.4  # Холодная фаза
temperature += base_temp

# Источник 2: Органы выделяют тепло
for organ_id, organ in organs.items():
    if 'temperature' in organ:
        heat_map = create_radial_gradient(
            center=organ['position'],
            radius=organ['radius'] * 2,  # Зона теплового влияния
            falloff='inverse_square'     # Затухание по закону обратных квадратов
        )
        temperature += heat_map * (organ['temperature'] - base_temp)

# Источник 3: Костная структура ОХЛАЖДАЕТ (мёртвая ткань)
temperature -= bone_structure * 0.4

# Источник 4: Артерии НАГРЕВАЮТ (горячий ихор)
for vessel in vessels:
    heat_trail = create_vessel_trail(
        waypoints=vessel['waypoints'],
        width=vessel['width'],
        intensity=vessel['flow_strength'] * 0.3
    )
    temperature += heat_trail

# Источник 5: Биоактивные зоны (дыхание) НАГРЕВАЮТ
for organ in organs.values():
    if organ['type'] == 'respiratory' and 'bioactive_output' in organ:
        bioactive_heat = create_radial_gradient(
            center=organ['position'],
            radius=organ['radius'] * 3,
            falloff='exponential'
        )
        temperature += bioactive_heat * organ['bioactive_output'] * 0.25

# Источник 6: Высота охлаждает (градиент -0.006°C/метр)
altitude_factor = elevation * -0.3
temperature += altitude_factor

# Нормализация в [0, 1]
temperature = np.clip(temperature, 0, 1)
```

### 5.2. Влажность

**Метод:** Близость к рекам + дыхательные зоны

```python
moisture = np.zeros((512, 512))

# Источник 1: Реки и водоёмы
for y in range(512):
    for x in range(512):
        if river_mask[y, x]:
            moisture[y, x] = 0.9  # У реки влажно
        else:
            # Расстояние до ближайшей реки
            dist_to_river = distance_to_nearest_river(x, y, river_mask)
            moisture[y, x] = 0.3 + 0.5 * np.exp(-dist_to_river / 20)

# Источник 2: Биоактивные зоны (споры увлажняют воздух)
for organ in organs.values():
    if organ['type'] == 'respiratory':
        humid_zone = create_radial_gradient(
            center=organ['position'],
            radius=organ['radius'] * 2.5
        )
        moisture += humid_zone * 0.4

# Источник 3: Высота осушает
moisture -= elevation * 0.2

moisture = np.clip(moisture, 0, 1)
```

**Зависит от:** Phase 1 (organs), Phase 3 (elevation), Phase 4 (rivers), world_phase

**Влияет на:** Phase 7 (tissues)

---

### 🟤 PHASE 6: ДЫХАТЕЛЬНАЯ СИСТЕМА (Skeleton-Driven Caverns)

**Первичность:** ШЕСТАЯ - детализация дыхательной системы

**Статус:** 🚧 Not Implemented (planned for Sprint 3.9)

**КРИТИЧЕСКОЕ ИЗМЕНЕНИЕ:** Дыхание - это свойство скелета, а не дискретных органов!

**Философия:**
> Альвеолярные каверны - это НЕ случайные точки и НЕ "два лёгких". Они **формируются в зонах структурного напряжения скелета** - вдоль позвоночного хребта и у основания рёбер. Весь скелет "дышит" ("Тектоника Костного Дыхания").

**Что создаётся:**

### 6.1. Карта дыхательного потенциала (Respiratory Potential Map)

**Метод:** Анализ напряжения скелетной структуры

```python
# Источник 1: Плотность костей (из СЛОЯ 3)
bone_density = self.maps['bone_structure']

# Источник 2: Структурное напряжение (новая карта!)
# Напряжение максимально в местах изгиба и соединения костей
structural_stress = calculate_structural_stress(
    elevation=elevation,
    bone_density=bone_density,
    method='curvature'  # Где кости изгибаются - там стресс
)

# Источник 3: Региональный bias (из Phase 1b)
regional_bias = np.zeros((512, 512))
for region_name, region in regions.items():
    regional_bias[region['mask']] = region['characteristics']['respiratory_potential']

# Композиция: вероятность появления каверны
respiratory_potential = (
    bone_density * 0.4 +           # 40% - плотность костей
    structural_stress * 0.4 +      # 40% - напряжение скелета
    regional_bias * 0.2            # 20% - региональный bias
)

# Нормализация
respiratory_potential = np.clip(respiratory_potential, 0, 1)
```

### 6.2. Генерация каверн с переменной плотностью

**Метод:** Poisson Disk Sampling с density map

```python
# НОВЫЙ АЛГОРИТМ: Плотность зависит от respiratory_potential
caverns = []

# Используем Variable Density Poisson Disk Sampling
candidate_points = poisson_disk_sampling_variable_density(
    density_map=respiratory_potential,
    min_distance_base=25,      # Базовое минимальное расстояние
    min_distance_range=(15, 40),  # Диапазон (где potential выше - плотнее)
    max_candidates=500,        # Больше кандидатов
    rejection_limit=30
)

# Фильтрация: оставляем только точки с высоким potential
for point in candidate_points:
    x, y = point
    local_potential = respiratory_potential[y, x]
    
    # Вероятность принятия зависит от potential
    if random.random() < local_potential:
        cavern = {
            'position': (x, y),
            'bioactive_output': local_potential * 0.9,  # Сильнее в зонах стресса
            'radius': 3 + local_potential * 5,  # Размер зависит от potential
            'formation_cause': classify_cause(x, y, bone_density, structural_stress)
        }
        caverns.append(cavern)

# Классификация причины формирования каверны
def classify_cause(x, y, bone_density, structural_stress):
    if bone_density[y, x] > 0.7:
        return 'spine_vertebrae'      # У позвоночника
    elif structural_stress[y, x] > 0.6:
        return 'rib_junction'         # У соединения рёбер
    elif bone_density[y, x] > 0.4:
        return 'bone_cavity'          # В костной полости
    else:
        return 'ectopic'              # Эктопическая (аномальная)

# Результат: ~150-300 каверн, сконцентрированных вдоль скелета
print(f"Generated {len(caverns)} caverns")
print(f"Spine-based: {sum(1 for c in caverns if c['formation_cause'] == 'spine_vertebrae')}")
print(f"Rib-based: {sum(1 for c in caverns if c['formation_cause'] == 'rib_junction')}")
print(f"Ectopic: {sum(1 for c in caverns if c['formation_cause'] == 'ectopic')}")
```

**Ожидаемое распределение:**
```
Generated 247 caverns
Spine-based: 89 (36%)  ← Вдоль позвоночника
Rib-based: 112 (45%)   ← У рёберных дуг (торакс)
Bone cavity: 38 (15%)  ← В костных полостях
Ectopic: 8 (3%)        ← Аномальные (редко)
```

### 6.3. Выдох (Exhalation Influence)

**Метод:** BFS от каверн (без изменений из Sprint 3.5)

```python
exhalation_map = np.zeros((512, 512))
queue = deque()

# Инициализация: каверны как источники
for cavern in caverns:
    x, y = cavern['position']
    intensity = cavern['bioactive_output']
    exhalation_map[y, x] = intensity
    queue.append(((x, y), intensity))

# BFS с затуханием
decay_rate = 0.92 if world_phase == 'EXHALE' else 0.85
visited = set([c['position'] for c in caverns])

while queue:
    (x, y), intensity = queue.popleft()

    for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
        nx, ny = x + dx, y + dy
        if 0 <= nx < 512 and 0 <= ny < 512:
            if (nx, ny) not in visited:
                new_intensity = intensity * decay_rate
                
                # Подъём в гору замедляет распространение
                elevation_penalty = (elevation[ny, nx] - elevation[y, x]) * 0.1
                new_intensity *= (1 - elevation_penalty)
                
                if new_intensity > 0.05:
                    exhalation_map[ny, nx] = new_intensity
                    queue.append(((nx, ny), new_intensity))
                    visited.add((nx, ny))

bioactive_saturation = exhalation_map.copy()
```

**Результат:**
- Зоны выдоха **НЕ круглые** и **НЕ симметричные**
- Максимальная сатурация **вдоль всего хребта и рёберных дуг**
- Распространение следует за рельефом (стекает вниз)
- **Эмерджентный результат**: "дышит" вся грудная клетка, а не два локализованных пятна

**Зависит от:** Phase 1 (regions), Phase 3 (skeleton!), world_phase

**Влияет на:** Phase 7 (tissues)

---

### ⚫ PHASE 7: НАЗНАЧЕНИЕ ТИПОВ ТКАНЕЙ (Biomes)

**Первичность:** СЕДЬМАЯ (ПОСЛЕДНЯЯ) - теперь мы ЗНАЕМ, что назначаем

**Статус:** 🚧 Not Implemented (planned for Sprint 3.9-4.0)

**Философия:**
> Теперь ткани назначаются НЕ вслепую, а с **полным пониманием контекста**.

**Что создаётся:**

```python
tissue_map = np.zeros((512, 512), dtype='U32')  # Строки (названия тканей)

for y in range(512):
    for x in range(512):
        # Собираем ВСЕ данные о клетке
        cell_data = {
            'elevation': elevation[y, x],
            'temperature': temperature[y, x],
            'moisture': moisture[y, x],
            'lymph_flow': lymph_flow[y, x],
            'bioactive': bioactive_saturation[y, x],
            'bone_density': bone_structure[y, x],
            'region': get_region(x, y),
            'nearest_organ': find_nearest_organ(x, y, organs),
            'dist_to_vessel': distance_to_nearest_vessel(x, y, vessels),
            'is_cavern': (x, y) in [c['position'] for c in caverns],
            'infection_level': infection_noise[y, x]  # НОВОЕ (из Зон заражения)
        }
        
        # Теперь правила могут быть НАМНОГО умнее:
        tissue = assign_tissue_with_context(cell_data, tissue_rules)
        tissue_map[y, x] = tissue

# Пример улучшенного правила:
def assign_tissue_with_context(cell, rules):
    # Специальные случаи (высший приоритет)
    if cell['is_cavern']:
        return 'alveolar_cavern'
    
    if cell['lymph_flow'] > 0.8:
        return 'lymphatic_channel'
    
    # Зоны заражения (Новые Боги)
    if cell['infection_level'] > 0.7:
        if cell['infection_level'] > 0.9:
            return 'necrotic_follicle'  # Некротический фолликул
        elif cell['temperature'] > 0.6:
            return 'unity_biomass'      # Единство
        else:
            return 'scab_formation'     # Струп
    
    # НОВОЕ: Учитываем близость к органам
    if cell['nearest_organ']['type'] == 'metabolic_organ':
        if cell['dist_to_organ'] < 20:
            # Рядом с желудком
            if cell['elevation'] < 0.3:
                return 'stagnant_delta'    # Стоячая дельта
            else:
                return 'nutrient_rich_dermis'  # Питательная дерма
    
    if cell['nearest_organ']['type'] == 'digestive':
        if cell['elevation'] < 0.25:
            return 'acidic_lake'  # Кислотные озёра желудка
    
    # Региональные особенности
    if cell['region'] == 'DIAPHRAGM':
        if cell['temperature'] > 0.5:
            return 'pulsating_plains'  # Пульсирующие равнины
        else:
            return 'tendon_tissue'     # Сухожильная ткань
    
    # Стандартные правила (из tissue_rules.yaml)
    return match_standard_rules(cell, rules)
```

**Результат:** Карта тканей, где:
- Каждая ткань назначена **осознанно**, с учётом анатомии
- Есть чёткая **логика размещения** (желудок → кислотные озёра)
- **Нет случайности** - всё определяется органами и физиологией

**Зависит от:** ВСЕ предыдущие фазы (0-6)

**Влияет на:** Геймплей, нарратив, POI placement (Sprint 4+)

---

## 📊 СВОДНАЯ ТАБЛИЦА ЗАВИСИМОСТЕЙ (v2.0)

| Phase | Название | Метод генерации | Зависит от | Влияет на | Статус |
|------|----------|----------------|------------|-----------|--------|
| **0** | Seed & Meta | Config (512×512) | - | ВСЁ | ✅ Config |
| **1a** | Spine Creation | Procedural curve generation | 0 | 1b, 2, 3 | ✅ Implemented |
| **1b** | Continent Growth + Organs | Spine-Modulated Perlin Noise | 0, 1a | 2,3,4,5,6,7 | ✅ Implemented |
| **2** | Физиология (Vessels) | MST + Spline along spine | 1a, 1b | 3,4,7 | 🚧 Planned |
| **3** | Геология (Elevation, Skeleton) | Композиция (spine, кости, органы, сосуды) | 1a, 1b, 2 | 4,5,6,7 | 🚧 Planned |
| **4** | Гидрология (Rivers) | D8 + Vein outlets | 2, 3 | 5, 7 | 🚧 Planned |
| **5** | Климат (Temperature, Moisture) | Радиальные градиенты от органов | 1b, 3, 4 | 7 | 🚧 Planned |
| **6** | Дыхание (Caverns) | Poisson + stress analysis **от скелета** | 1b, 3 | 7 | 🚧 Planned |
| **7** | Ткани (Biomes) | Rule-based с full context | 1b,2,3,4,5,6 | Gameplay | 🚧 Planned |

**Ключевое изменение:**
- ✅ **Phase 1 разделена на 1a (Spine) + 1b (Continent+Organs)** - реализует Unified Concept
- ✅ **Все органы привязаны к spine** (параметрическое размещение)
- ✅ **512×512 карты** для Stage 0 (было 256×256)

---

## 🔄 СРАВНЕНИЕ: БЫЛО vs СТАЛО (v2.0 Architecture)

### БЫЛО (Sprint 3.5 - Proof of Concept):
```
1. Perlin Noise → elevation (случайно)
2. Ridge mask → хребет (косметически)
3. D8 flow → лимфа (по рельефу)
4. Poisson → каверны (случайно)
5. Temperature = f(elevation, lymph, bioactive) (формула)
6. Tissue assignment (по таблице правил)

Размер карты: 256×256 (фиксированный квадрат)

Проблемы:
- ❌ Нет анатомического смысла
- ❌ Всё случайно или по формулам
- ❌ Не соответствует лору (органы не влияют)
- ❌ Мир заполняет весь квадрат 256×256 искусственно
- ❌ Нет понятия "континент" vs "океан"
- ❌ "Два лёгких" - грубое упрощение
- ❌ Органы в фиксированных координатах
```

### СТАЛО (v2.0 - Unified Concept):
```
0. Seed → world_phase (512×512)

UNIFIED CONCEPT: Anatomical Framework → Geographic Embodiment → Detailed Physiology

1a. SPINE (Анатомическая Структура)
    └─ Процедурная генерация позвоночника (изогнутая ось)
    └─ Width profile (органическая форма тела)

1b. CONTINENT + ORGANS (Географическое Воплощение + Физиология)
    ├─ Континент растёт ВОКРУГ spine (Perlin × Shape Mask)
    ├─ Органы привязаны К ТОЧКАМ ВДОЛЬ spine (параметрическое размещение)
    └─ Регионы определяются spine + анатомией (не прямоугольники!)

2. Артерии (вдоль spine между органами)
3. Рельеф = f(spine, кости, органы, сосуды)
   ├─ Скелет следует за spine
   └─ Структурное напряжение (для каверн)
4. Реки = D8(рельеф) + outlets(артерии)
5. Климат = f(органы, рельеф, реки)
6. Каверны = f(структурное_напряжение_скелета)
   ├─ Концентрация вдоль позвоночника (spine!)
   ├─ Концентрация у рёберных дуг
   └─ "Весь скелет дышит"
7. Ткани = match(всё вышеперечисленное + контекст)

Размер карты: 512×512 (Stage 0: Global Skeletons)

Преимущества v2.0:
- ✅ **Spine First** - структурный каркас определяет всё
- ✅ **Continent FROM Spine** - география следует анатомии
- ✅ **Organs ALONG Spine** - параметрическое размещение
- ✅ Полная анатомическая логика
- ✅ Соответствие лору v3.0
- ✅ Органичная форма континента (не квадрат!)
- ✅ Дыхательная система как распределённая сеть
- ✅ "Тектоника Костного Дыхания" реализована
- ✅ Масштабируемость для Stage 1 (4096×4096)
```

---

## 🎯 КЛЮЧЕВЫЕ ИСПРАВЛЕНИЯ (v2.0)

### 1. Unified Concept: Spine → Continent → Organs

**Было:** Противоречие "Organs First vs Continent First"

**Стало (v2.0):**
1. **Phase 1a: SPINE FIRST** - создаём структурный каркас (позвоночник)
2. **Phase 1b: CONTINENT FROM SPINE** - континент растёт вокруг spine
3. **Phase 1b: ORGANS ALONG SPINE** - органы привязаны к точкам вдоль spine

**Результат:**
- География следует анатомии
- Анатомия интегрирована с географией
- Нет искусственного разделения "сначала что?"

### 2. Параметрическое размещение органов

**Было:** Фиксированные координаты (128, 180), (80, 120) на карте 256×256

**Стало:**
- Органы привязаны к **параметрическим позициям вдоль spine**
- `progress=0.35` → Метаболическое ядро (35% по позвоночнику)
- `progress=0.65` → Желудок (65% по позвоночнику)
- Координаты вычисляются ДИНАМИЧЕСКИ на основе формы spine

**Результат:** Органы всегда "на своих местах" относительно анатомической структуры

### 3. Дыхательная система как свойство скелета (Phase 6)

**Было:** Два дискретных "лёгких" → каверны вокруг них

**Стало:**
1. ❌ Убираем "лёгкие" из списка органов
2. Генерируем карту **структурного напряжения** скелета (который следует за spine!)
3. Каверны появляются там, где скелет **изгибается и сочленяется**
4. Концентрация вдоль позвоночника (spine!) и рёбер

**Результат:** "Весь скелет дышит" - концепция "Тектоники Костного Дыхания" реализована

### 4. Размер карты: 256×256 → 512×512

**Было:** Stage 0 использовал 256×256 (исторический размер)

**Стало:**
- **Stage 0 (Global Skeletons): 512×512** - оптимальный баланс детализации и производительности
- **Stage 1 (Chunk Detailing): 4096×4096** - каждая ячейка 512×512 делится на 8×8 chunks (Sprint 3.9)

**Результат:** Больше деталей континента, лучшая подготовка к Stage 1

---

## 🚀 ЧТО ЭТО ЗНАЧИТ ДЛЯ РАЗРАБОТКИ? (СТАТУС v2.0)

### Что уже реализовано? ✅

**Sprint 3.6 (ТЕКУЩИЙ СТАТУС):**

```python
# core/world_generator_v2.py - РЕАЛИЗОВАНО

class WorldGeneratorV2:
    """
    ✅ Phase 1a: Spine Creation - IMPLEMENTED
       - _generate_spine_path() - процедурная генерация позвоночника
       - _calculate_width_profile() - профиль расширения континента

    ✅ Phase 1b: Continent Growth - IMPLEMENTED
       - _create_spine_shape_mask() - Shape Mask из spine
       - _generate_continent() - Perlin Noise × Shape Mask
       - Morphological smoothing (binary opening/closing, gaussian)

    ✅ Phase 1b: Organ Placement - PARTIALLY IMPLEMENTED
       - Органы размещаются, но НЕ привязаны к spine пока
       - TODO: Переделать на параметрическое размещение вдоль spine
    ```

**Что работает прямо сейчас:**
- ✅ Генерация органичного континента с spine (512×512)
- ✅ Морфологическое сглаживание береговой линии
- ✅ Оптимизированные параметры (sea_level=0.38, scale=150)
- ✅ 37 passing tests

### Что надо доделать? 🚧

**Sprint 3.7 (Phase 2):** 🚧 PLANNED
- 🚧 Phase 2: Skeleton + Elevation (L-Systems для рёбер, композиция рельефа)
- 🚧 Bone density map для Phase 3

**Sprint 3.8 (Phase 3-5):** 🚧 PLANNED
- 🚧 Phase 3: Vessel network (Space Colonization с density-aware pathfinding)
- 🚧 Phase 4: Hydrology (D8 + Vein outlets)
- 🚧 Phase 4.5: Hydraulic Erosion (фокусированная эрозия с защитой костей) 🆕
- 🚧 Phase 5: Climate (Temperature, Moisture)

**Sprint 3.9 (Phase 6-7):** 🚧 PLANNED
- 🚧 Phase 6: Skeleton-driven caverns (stress analysis)
- 🚧 Phase 7: Tissue assignment (rule-based с контекстом, Worley noise варианты) 🆕

### Что можно сохранить из Sprint 3.5?

**Переиспользуемые алгоритмы:**
- ✅ Perlin noise → используется в Phase 1b
- ✅ Morphological operations → используются в Phase 1b
- ✅ D8 flow → будет использоваться в Phase 4
- ✅ Poisson sampling → будет использоваться в Phase 6
- ✅ BFS exhalation → будет использоваться в Phase 6

**Что переписываем:**
- ✅ Архитектура: Монолитная → Композиционная (DONE в v2)
- 🚧 Последовательность: 5 слоёв → 8 фаз (0, 1a, 1b, 2-7)
- 🚧 Data models: Добавить Spine, Vessel, параметрическое размещение органов
- 🚧 `tissue_rules.yaml`: Новые правила с полным контекстом

---

## 🎯 ROADMAP v2.0

**Sprint 3.6 (CURRENT - Phase 1a+1b):** ✅ **COMPLETE**
- ✅ Spine-Based Generation
- ✅ Continent Growth around spine
- ✅ 512×512 map size
- ✅ Parameter tuning
- ✅ Documentation migration to v2.0

**Sprint 3.7 (Phase 2: Skeleton):** 🚧 PLANNED
- Skeleton generation (L-Systems для рёбер)
- Elevation composition
- Bone density map для Phase 3
- Update ADR with v3.0 changes

**Sprint 3.8 (Phase 3-5: Vessels + Hydrology + Erosion + Climate):** 🚧 PLANNED
- Vessel network (Space Colonization с density-aware pathfinding)
- D8 flow with vein outlets
- 🆕 Hydraulic Erosion (Gaussian pre-processing + focused erosion)
- Temperature/Moisture maps

**Sprint 3.9 (Phase 6-7: Caverns + Tissues):** 🚧 PLANNED
- Skeleton stress analysis
- Variable-density Poisson for caverns
- Tissue assignment with full context
- 🆕 Worley noise варианты (вариативность метрик, комбинирование шумов)
- Stage 1 preparation (4096×4096 detailing)

---

**Конец анализа v2.0.**
**Документ обновлён:** 2025-10-28 (v2.0 Architecture Migration)
