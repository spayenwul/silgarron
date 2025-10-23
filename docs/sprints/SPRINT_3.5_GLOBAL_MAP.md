# 🗺️ SPRINT 3.5: Anatomical Global Map - Living World Generator

**Проект:** Silgarron RPG — Живой мир-организм
**Даты:** 21 октября - 4 ноября 2025
**Приоритет:** 🔴 КРИТИЧЕСКИЙ #1
**Статус:** Запланировано
**Время (оценка):** 48-55 часов (~2-3 недели)
**Версия:** 2.1 (Добавлен Poisson Disk Sampling + итеративный тюнинг)

---

## 📋 Содержание

1. [Фундаментальное различие: Мир-Организм](#фундаментальное-различие-мир-организм)
2. [Цели спринта](#цели-спринта)
3. [Архитектурное видение](#архитектурное-видение)
4. [Детальный план задач](#детальный-план-задач)
5. [Definition of Done](#definition-of-done)
6. [Риски и митигация](#риски-и-митигация)
7. [Материалы для изучения](#материалы-для-изучения)

---

## 🧬 Фундаментальное различие: Мир-Организм

### Почему стандартный генератор мира НЕ подходит?

**Типичная процедурная генерация:**
```
Perlin noise → Континенты → Климатические зоны → Биомы
(геология, тектоника, эрозия)
```

**Сильгаррон — это НЕ планета. Это СУЩЕСТВО:**
```
Анатомическая структура → Метаболизм → "Дыхание" → Ткани/Органы
(физиология, кровообращение, нервная система)
```

### Ключевые отличия генерации

| Аспект | Обычный мир | Сильгаррон |
|--------|-------------|------------|
| **Высота** | Случайный шум (горы/равнины) | Костяной хребет (позвоночник) + мягкие ткани (равнины) |
| **Температура** | Широта (экватор/полюс) | Метаболическое тепло (активность тканей) |
| **Влажность** | Расстояние до океана | Лимфатическая система (артерии, капилляры) |
| **Движение** | Статичная топография | **"Дыхание"** — циклическое расширение/сжатие поверхности |
| **Биомы** | Климатические зоны | **Типы тканей** (дерма, хитин, костехитин, лимфа) |
| **Океан** | Вода | Первичная жидкость / Протоплазменный океан |
| **Реки** | Эрозия | Лимфотоки (кровь/лимфа мира) |
| **Погода** | Атмосфера | Метаболические циклы + фазы "Дыхания" (Вдох/Выдох) |

### Система "Дыхания" мира ⚠️ ОБНОВЛЕНО (см. ADR-014)

**Из лора:** Весь мир участвует в циклическом "Дыхании" — расширении и сжатии поверхности. **Текущая эпоха - фаза позднего ВЫДОХА**.

**Ключевая механика (фаза Выдоха):**
- **Выдох**: **Альвеолярные каверны источают** биоактивные газы и споры из недр мира
- **Эмиссия создаёт зоны биологической активности** вокруг каверн
- **Биоактивность насыщает атмосферу**, создавая туманы спор (Биолюм)

**Это означает:**
- Атмосфера зависит НЕ только от лимфотоков, но и от **интенсивности выдоха** из каверн
- Нужно моделировать "каверны-источники" и концентрацию выбросов вокруг них
- Высокая концентрация → Споровые туманы, токсичность, мутации

---

## 🎯 Цели спринта

### Основная цель
**Создать seed-based генератор *живого* мира 256×256 гексов с анатомической структурой (костяной хребет, лимфатическая система, дыхательные каверны) и автоматическим назначением типов тканей (биомов).**

### Конкретные результаты

1. **Работающий анатомический генератор** (`core/world_generator.py`)
   - Генерация костяного хребта (ridge-biased Perlin noise)
   - Лимфатическая система (симуляция потоков)
   - Система "Дыхания" (BFS для концентрации выдоха от каверн) ⚠️ **ОБНОВЛЕНО:** Выдох вместо Вдоха
   - Метаболическое тепло (активность тканей)

2. **Модели данных** (`models/global_map.py`)
   - `GlobalSector` с **анатомическими свойствами** (tissue_type, metabolic_heat, exhalation_influence) ⚠️ **ОБНОВЛЕНО:** exhalation_influence
   - `GlobalMapData` с кэшами потоков
   - `DeltaTracker` для изменений

3. **Визуализатор медицинского сканирования** (`tools/visualize_global_map.py`)
   - 5 слоёв: Structural Anatomy, Tissue Morphology, Metabolic Heatmap, Fluid Saturation, Exhalation/Spore Density ⚠️ **ОБНОВЛЕНО**
   - PNG экспорт с анатомической цветовой палитрой

4. **Конфигурация** (`config/world_generation.yaml`, `data/tissue_rules.yaml`)
   - Настраиваемые параметры анатомии (сила хребта, количество каверн)
   - Правила тканей (вместо биомов)

5. **Тесты** (95%+ pass rate)
   - Воспроизводимость seed (через `hashlib`)
   - Логичность анатомии (хребет, потоки)
   - Биологическое правдоподобие (нет пустынь в лимфотоках)

---

## 🏗️ Архитектурное видение

### Философия генерации: "Сверху вниз — от скелета к коже"

```
1. СКЕЛЕТ (Skeleton)
   ├─ Генерация Костяного Хребта (ridge-biased noise)
   └─ Определение крупных костных структур

2. КРОВЕНОСНАЯ СИСТЕМА (Circulatory System)
   ├─ Размещение "сердец" (истоков лимфотоков)
   ├─ Flow Accumulation для русел
   └─ Лимфатическая сеть (артерии → капилляры)

3. ДЫХАТЕЛЬНАЯ СИСТЕМА (Respiratory System) ⚠️ **ОБНОВЛЕНО:** Выдох вместо Вдоха
   ├─ Размещение Альвеолярных каверн (источники выброса)
   ├─ BFS для концентрации выдыхаемых спор/газов
   └─ Карта интенсивности "выдоха" (exhalation_influence)

4. МЕТАБОЛИЗМ (Metabolism)
   ├─ Расчёт активности тканей
   ├─ Температурная карта (не климат, а жизнедеятельность)
   └─ Распределение ресурсов (лимфа, споры, хитин)

5. ТКАНИ (Tissues)
   ├─ Назначение типов тканей (биомов) на основе всех слоёв
   ├─ Система приоритетов
   └─ Плавные переходы (мембрана → мышцы → кость)

6. ДИНАМИКА ("Дыхание" и пульсация)
   ├─ Фазы дыхательного цикла
   ├─ Поверхность, участвующая в "Дыхании"
   └─ Стабильные vs динамические зоны
```

---

## 📝 Детальный план задач

### ФАЗА 1: Ядро анатомического генератора (14-16 часов)

#### Задача 1.1: Базовая структура WorldGenerator с детерминированным seed
**Файл:** `core/world_generator.py`
**Время:** 2 часа

```python
import hashlib
import numpy as np
from noise import pnoise2
from datetime import datetime
from models.global_map import GlobalMapData, GlobalSector
from models.hex_coord import HexCoord

class WorldGenerator:
    """
    Генератор живого мира Сильгаррон.

    Мир — это не планета, а гигантский организм. Генератор симулирует:
    - Анатомию (костяной хребет, мягкие ткани)
    - Метаболизм (тепло активности)
    - Лимфатическую систему (потоки жидкости)
    - Дыхательную систему (воздушные потоки к кавернам)
    """

    def __init__(self, seed: str, width: int = 256, height: int = 256):
        self.seed = seed
        self.width = width
        self.height = height

        # ⚠️ КРИТИЧНО: Детерминированный seed через hashlib
        seed_bytes = seed.encode('utf-8')
        hash_object = hashlib.sha256(seed_bytes)
        int_seed = int.from_bytes(hash_object.digest()[:4], 'little')

        self.rng = np.random.default_rng(int_seed)
        self.base_seed = int_seed

    def generate(self) -> GlobalMapData:
        """Генерирует полную анатомическую карту мира"""
        print(f"🧬 Генерация живого мира '{self.seed}' ({self.width}×{self.height})...")

        # 1. СКЕЛЕТ: Костяной хребет
        structure_map = self._generate_skeletal_structure()

        # 2. КРОВЕНОСНАЯ СИСТЕМА: Лимфотоки
        lymph_network = self._generate_lymphatic_system(structure_map)

        # 3. ДЫХАТЕЛЬНАЯ СИСТЕМА: Каверны и потоки
        respiratory_data = self._generate_respiratory_system(structure_map)

        # 4. МЕТАБОЛИЗМ: Температура
        metabolism_map = self._generate_metabolic_activity(structure_map, lymph_network)

        # 5. ТКАНИ: Назначение типов
        sectors = self._assign_tissue_types(
            structure_map,
            lymph_network,
            respiratory_data,
            metabolism_map
        )

        return GlobalMapData(
            seed=self.seed,
            width=self.width,
            height=self.height,
            sectors=sectors,
            generation_timestamp=datetime.now()
        )
```

**Критерии завершения:**
- ✅ Генератор создаёт объект `GlobalMapData` без ошибок
- ✅ Seed воспроизводится детерминированно

---

#### Задача 1.2: Генерация костяного хребта (Skeletal Structure)
**Время:** 3-4 часа (включая тюнинг)

**Концепция:**
Вместо случайных гор создаём **доминирующий хребет** (позвоночник) с отходящими "рёбрами".

```python
def _generate_skeletal_structure(self) -> np.ndarray:
    """
    Генерирует костяную структуру мира.

    Хребет-Остов (Склеритовый хребет) должен:
    - Проходить по центру карты (или диагонально)
    - Иметь ответвления ("рёбра")
    - Быть более выражен, чем случайные возвышенности
    """

    # Шаг 1: Базовый Perlin noise (микрорельеф)
    base_noise = np.zeros((self.height, self.width))

    for y in range(self.height):
        for x in range(self.width):
            noise_val = pnoise2(
                x / 100.0,  # scale
                y / 100.0,
                octaves=6,
                persistence=0.5,
                lacunarity=2.0,
                base=self.base_seed
            )
            base_noise[y, x] = (noise_val + 1.0) / 2.0  # [0, 1]

    # Шаг 2: Создание "позвоночника" (ridge mask)
    spine_bias = self._create_spine_mask()

    # Шаг 3: Создание "рёбер" (ответвлений)
    rib_bias = self._create_rib_mask()

    # Шаг 4: Комбинация слоёв
    # 60% базовый шум + 30% хребет + 10% рёбра
    structural_map = (
        base_noise * 0.6 +
        spine_bias * 0.3 +
        rib_bias * 0.1
    )

    # Нормализация
    structural_map = (structural_map - np.min(structural_map)) / \
                     (np.max(structural_map) - np.min(structural_map))

    return structural_map

def _create_spine_mask(self) -> np.ndarray:
    """
    Создаёт маску для Костяного Хребта.

    Хребет проходит по центру с небольшими изгибами.
    """
    spine_mask = np.zeros((self.height, self.width))

    # Параметры хребта
    spine_center = self.width // 2
    spine_width = self.width // 10  # Ширина хребта
    spine_height_mult = 1.5  # Насколько хребет выше окружения

    for y in range(self.height):
        # Добавляем изгибы через синусоиду
        wiggle = int(np.sin(y / 20.0) * 10)  # Плавные изгибы
        spine_x = spine_center + wiggle

        for x in range(self.width):
            # Расстояние от оси хребта
            distance_from_spine = abs(x - spine_x)

            # Параболический спад
            if distance_from_spine < spine_width:
                # Чем ближе к оси, тем выше
                height_factor = 1.0 - (distance_from_spine / spine_width) ** 2
                spine_mask[y, x] = height_factor * spine_height_mult

    return spine_mask

def _create_rib_mask(self) -> np.ndarray:
    """
    Создаёт маску для "рёбер" — ответвлений от хребта.
    """
    rib_mask = np.zeros((self.height, self.width))

    # Количество рёбер
    num_ribs = 8
    rib_spacing = self.height // num_ribs

    for i in range(num_ribs):
        rib_y = rib_spacing * i + rib_spacing // 2

        for x in range(self.width):
            # Рёбра идут от центра к краям
            distance_from_rib_line = abs(self.height - rib_y)

            # Экспоненциальный спад
            if distance_from_rib_line < 30:
                rib_mask[rib_y, x] = np.exp(-distance_from_rib_line / 10.0) * 0.5

    return rib_mask
```

**Критерии завершения:**
- ✅ На карте виден чёткий центральный хребет
- ✅ Есть ответвления от хребта
- ✅ Хребет выглядит "органично", не как прямая линия

---

#### Задача 1.3: Генерация лимфатической системы
**Время:** 4-5 часов

**Концепция:**
Лимфотоки (аналог рек) текут **ПО законам физиологии**, а не эрозии:
- Истоки в возвышенных зонах (фильтрующие органы)
- Текут к низинам и "дельтам" (очистные зоны)
- Могут проходить через "органы" (Лимфатические узлы)

```python
def _generate_lymphatic_system(self, structure_map: np.ndarray) -> dict:
    """
    Генерирует лимфатическую сеть (аналог рек).

    Лимфотоки:
    - Начинаются в Истоках (springheads) — возвышенные фильтры
    - Текут к Дельтам (filter beds) — низинные очистители
    - Проходят через Лимфатические узлы (бассейны)
    """

    # 1. Найти истоки (elevated + moisture source)
    sources = self._find_lymph_sources(structure_map)

    # 2. Flow Accumulation Algorithm (D8)
    flow_accumulation = self._calculate_flow_accumulation(structure_map, sources)

    # 3. Определить, где flow > threshold = лимфоток
    lymph_threshold = 50  # Параметр тюнинга
    lymph_network_map = flow_accumulation > lymph_threshold

    # 4. Классификация по ширине (капилляры → артерии)
    lymph_intensity = np.clip(flow_accumulation / 500.0, 0.0, 1.0)

    return {
        'network_map': lymph_network_map,  # bool[height, width]
        'intensity': lymph_intensity,      # float[height, width] (0-1)
        'sources': sources                 # List[Tuple[int, int]]
    }

def _find_lymph_sources(self, structure_map: np.ndarray) -> list:
    """Находит точки-истоки лимфотоков"""
    sources = []

    # Истоки находятся на холмах/предгорьях (не на вершинах!)
    for y in range(self.height):
        for x in range(self.width):
            elevation = structure_map[y, x]

            # Истоки на высоте 0.5-0.7 (холмы, не пики)
            if 0.5 <= elevation <= 0.7:
                # Случайное размещение (1% вероятность)
                if self.rng.random() < 0.01:
                    sources.append((x, y))

    return sources

def _calculate_flow_accumulation(self, structure_map: np.ndarray, sources: list) -> np.ndarray:
    """
    Flow Accumulation Algorithm (D8).

    Каждая клетка направляет поток к самому низкому соседу.
    """
    flow = np.zeros_like(structure_map)

    # Сортируем все гексы по убыванию высоты
    coords = [(x, y) for y in range(self.height) for x in range(self.width)]
    coords_sorted = sorted(coords, key=lambda c: structure_map[c[1], c[0]], reverse=True)

    # D8 directions
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)]

    for x, y in coords_sorted:
        current_elevation = structure_map[y, x]

        # Найти самого низкого соседа
        lowest_neighbor = None
        lowest_elevation = current_elevation

        for dx, dy in directions:
            nx, ny = x + dx, y + dy

            if 0 <= nx < self.width and 0 <= ny < self.height:
                neighbor_elev = structure_map[ny, nx]
                if neighbor_elev < lowest_elevation:
                    lowest_elevation = neighbor_elev
                    lowest_neighbor = (nx, ny)

        # Если есть сосед ниже, направляем поток
        if lowest_neighbor:
            nx, ny = lowest_neighbor
            flow[ny, nx] += flow[y, x] + 1  # Накопление

    return flow
```

**Критерии завершения:**
- ✅ Видны крупные "артерии" лимфотоков
- ✅ Лимфотоки текут от возвышенностей к низинам
- ✅ Есть дельты (зоны стока)

---

#### Задача 1.4: Генерация дыхательной системы (Respiratory System)
**Время:** 5-6 часов (самая сложная задача)

**Концепция:**
**"Вдох"** — ключевая механика Сильгаррона:
- Воздух втягивается в Альвеолярные каверны (подземные "лёгкие")
- Создаёт **воздушные потоки** от поверхности вниз
- **Высушивает** территории на пути

```python
def _generate_respiratory_system(self, structure_map: np.ndarray) -> dict:
    """
    Генерирует дыхательную систему мира.

    Альвеолярные каверны втягивают воздух, создавая:
    - Воздушные потоки (airflow)
    - Зоны высушивания (низкая влажность)
    - "Ветровые коридоры"
    """

    # 1. Разместить Альвеолярные каверны
    caverns = self._place_alveolar_caverns(structure_map)

    # 2. BFS для расчёта воздушных потоков
    airflow_map = self._calculate_airflow_to_caverns(caverns)

    # 3. Рассчитать влияние на влажность
    desiccation_map = self._calculate_desiccation_effect(airflow_map)

    return {
        'caverns': caverns,              # List[Tuple[int, int]]
        'airflow_intensity': airflow_map, # float[height, width] (0-1)
        'desiccation': desiccation_map   # float[height, width] (0-1)
    }

def _place_alveolar_caverns(self, structure_map: np.ndarray) -> list:
    """
    Размещает Альвеолярные каверны (входы в "лёгкие").

    Каверны находятся:
    - В низинах (elevation < 0.3)
    - Не на хребте
    - Равномерно распределены
    """
    caverns = []

    # Параметр: количество каверн
    num_caverns = 6  # Настраиваемый параметр

    # Кандидаты: низины
    candidates = []
    for y in range(self.height):
        for x in range(self.width):
            if structure_map[y, x] < 0.3:
                candidates.append((x, y))

    # Выбираем N самых удалённых друг от друга точек (k-means или greedy)
    if len(candidates) > num_caverns:
        caverns = self._select_distributed_points(candidates, num_caverns)
    else:
        caverns = candidates

    return caverns

def _select_distributed_points(self, candidates: list, n: int) -> list:
    """
    Выбирает N равномерно распределённых точек.

    Поддерживает два алгоритма:
    - "greedy": Жадный алгоритм (быстрый, но может создавать паттерны)
    - "poisson": Poisson Disk Sampling (медленнее, но более органичный)
    """
    method = self.config.get('cavern_placement_method', 'poisson')

    if method == 'poisson':
        return self._poisson_disk_sampling(candidates, n)
    else:
        return self._greedy_distributed_selection(candidates, n)

def _greedy_distributed_selection(self, candidates: list, n: int) -> list:
    """Жадный алгоритм: выбирает точки максимально удалённые друг от друга"""
    if not candidates:
        return []

    selected = [self.rng.choice(candidates)]

    while len(selected) < n and len(candidates) > len(selected):
        # Найти точку, максимально удалённую от уже выбранных
        max_min_dist = -1
        best_point = None

        for candidate in candidates:
            if candidate in selected:
                continue

            # Минимальное расстояние до уже выбранных
            min_dist = min(
                ((candidate[0] - s[0])**2 + (candidate[1] - s[1])**2)**0.5
                for s in selected
            )

            if min_dist > max_min_dist:
                max_min_dist = min_dist
                best_point = candidate

        if best_point:
            selected.append(best_point)

    return selected

def _poisson_disk_sampling(self, candidates: list, n: int) -> list:
    """
    Poisson Disk Sampling для более органичного распределения.

    Гарантирует минимальное расстояние между точками без предсказуемых паттернов.
    Идеально для биологических структур (альвеолярные каверны).
    """
    if not candidates or n == 0:
        return []

    # Минимальное расстояние между кавернами
    min_distance = (self.width * self.height / n) ** 0.5 * 0.8

    selected = []
    candidates_array = np.array(candidates)

    # Первая точка - случайная
    first_idx = self.rng.integers(0, len(candidates))
    selected.append(tuple(candidates_array[first_idx]))

    # Активный список для расширения
    active_list = [selected[0]]

    max_attempts = 30  # Попыток на точку

    while active_list and len(selected) < n:
        # Выбрать случайную активную точку
        active_idx = self.rng.integers(0, len(active_list))
        active_point = active_list[active_idx]

        found = False

        for _ in range(max_attempts):
            # Генерировать случайную точку в кольце вокруг активной
            angle = self.rng.random() * 2 * np.pi
            radius = min_distance + self.rng.random() * min_distance

            new_x = int(active_point[0] + radius * np.cos(angle))
            new_y = int(active_point[1] + radius * np.sin(angle))

            # Проверить, что точка в списке кандидатов
            if (new_x, new_y) not in candidates:
                continue

            # Проверить минимальное расстояние до всех выбранных
            too_close = False
            for selected_point in selected:
                dist = ((new_x - selected_point[0])**2 + (new_y - selected_point[1])**2)**0.5
                if dist < min_distance:
                    too_close = True
                    break

            if not too_close:
                selected.append((new_x, new_y))
                active_list.append((new_x, new_y))
                found = True
                break

        if not found:
            # Убрать из активного списка
            active_list.pop(active_idx)

    return selected

def _calculate_airflow_to_caverns(self, caverns: list) -> np.ndarray:
    """
    BFS для расчёта интенсивности воздушного потока к кавернам.

    Чем ближе к каверне, тем сильнее "тяга".
    """
    from collections import deque

    airflow_map = np.zeros((self.height, self.width))
    visited = np.zeros((self.height, self.width), dtype=bool)
    queue = deque()

    # Инициализация: каверны = максимальная тяга
    for x, y in caverns:
        airflow_map[y, x] = 1.0
        visited[y, x] = True
        queue.append((x, y, 1.0))

    # BFS с затуханием
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)]

    while queue:
        x, y, intensity = queue.popleft()

        # Затухание с расстоянием
        new_intensity = intensity * 0.95  # 5% затухание на каждый шаг

        if new_intensity < 0.01:  # Слишком слабо
            continue

        for dx, dy in directions:
            nx, ny = x + dx, y + dy

            if 0 <= nx < self.width and 0 <= ny < self.height:
                if not visited[ny, nx]:
                    visited[ny, nx] = True
                    airflow_map[ny, nx] = new_intensity
                    queue.append((nx, ny, new_intensity))

    return airflow_map

def _calculate_desiccation_effect(self, airflow_map: np.ndarray) -> np.ndarray:
    """
    Рассчитывает эффект высушивания от воздушных потоков.

    Сильный воздушный поток → низкая влажность.
    """
    # Прямая зависимость: airflow 1.0 → desiccation 1.0
    desiccation_map = airflow_map.copy()

    return desiccation_map
```

**Критерии завершения:**
- ✅ Видны зоны высокой интенсивности airflow вокруг каверн
- ✅ Визуализация показывает "воронки" притяжения
- ✅ Тест: гексы рядом с кавернами имеют high airflow

---

#### Задача 1.5: Генерация метаболической активности
**Время:** 2-3 часа

**Концепция:**
Температура = НЕ климат, а **активность тканей**:
- Хребет может быть "холодным" (кость мертва)
- Лимфотоки "тёплые" (активная циркуляция)
- Равнины умеренно тёплые (дыхание)

```python
def _generate_metabolic_activity(self, structure_map: np.ndarray,
                                 lymph_network: dict) -> np.ndarray:
    """
    Генерирует карту метаболического тепла.

    Температура зависит от:
    - Типа ткани (кость холодная, мышцы тёплые)
    - Близости к лимфотокам (кровь тёплая)
    - Активности "Дыхания"
    """

    temp_map = np.zeros((self.height, self.width))
    lymph_intensity = lymph_network['intensity']

    for y in range(self.height):
        for x in range(self.width):
            elevation = structure_map[y, x]

            # Базовая температура: умеренная
            base_temp = 15.0  # °C

            # Модификаторы:

            # 1. Хребет (кость) холодный
            if elevation > 0.7:
                bone_penalty = (elevation - 0.7) * 40  # До -12°C
                base_temp -= bone_penalty

            # 2. Лимфотоки тёплые
            lymph_bonus = lymph_intensity[y, x] * 15  # До +15°C
            base_temp += lymph_bonus

            # 3. Низины (активные ткани) умеренно тёплые
            if elevation < 0.4:
                activity_bonus = (0.4 - elevation) * 10  # До +4°C
                base_temp += activity_bonus

            temp_map[y, x] = base_temp

    return temp_map
```

**Критерии завершения:**
- ✅ Хребет холодный
- ✅ Лимфотоки тёплые
- ✅ Низины умеренные

---

### ФАЗА 2: Назначение тканей (Tissue Assignment) (6-8 часов)

#### Задача 2.1: Создание tissue_rules.yaml
**Файл:** `data/tissue_rules.yaml`
**Время:** 3 часа

```yaml
# ТИПЫ ТКАНЕЙ СИЛЬГАРРОНА (вместо биомов)

tissues:
  # --- ПРОТОПЛАЗМЕННАЯ ЖИДКОСТЬ (Океан) ---
  primordial_fluid:
    name: "Первичная жидкость"
    description: "Окружающая мир протоплазма, аналог океана"
    priority: 100

    # Физические условия
    structural_elevation: [0.0, 0.3]
    metabolic_temp: [-10, 50]
    fluid_saturation: [0.9, 1.0]
    airflow_intensity: [0.0, 0.5]

    color: "#1A0F2E"  # Тёмно-фиолетовый
    tags: [surface:fluid, danger_level:5]

  # --- ДЕРМАЛЬНЫЕ ТКАНИ (Кожа) ---
  membranous_plains:
    name: "Мембранные равнины"
    description: "Эластичная кожа мира, участвующая в Дыхании"
    priority: 10

    structural_elevation: [0.4, 0.55]
    metabolic_temp: [10, 25]
    fluid_saturation: [0.3, 0.7]
    airflow_intensity: [0.0, 0.6]

    color: "#D4A59A"  # Бледно-розовый (цвет кожи)
    tags: [surface:elastic, surface:dynamic, ecology:moderate]

  pulsating_dermis:
    name: "Пульсирующая дерма"
    description: "Участки кожи с активным Дыханием"
    priority: 12

    structural_elevation: [0.3, 0.6]
    metabolic_temp: [15, 30]
    fluid_saturation: [0.4, 0.8]
    airflow_intensity: [0.6, 1.0]  # Высокая активность вдоха

    color: "#E8B4B8"  # Розовый (живая ткань)
    tags: [surface:dynamic, ecology:moderate, breathing:active]

  # --- МЫШЕЧНЫЕ ТКАНИ ---
  fibrous_thicket:
    name: "Волокнистые заросли"
    description: "Плотные мышечные волокна, похожие на лес"
    priority: 25

    structural_elevation: [0.45, 0.65]
    metabolic_temp: [18, 35]  # Мышцы тёплые
    fluid_saturation: [0.5, 0.95]  # Высокая васкуляризация
    airflow_intensity: [0.0, 0.4]

    color: "#8B1A1A"  # Тёмно-красный (мышцы)
    tags: [surface:stable, ecology:dense_vegetation, terrain:rough]

  # --- ЛИМФАТИЧЕСКИЕ ТКАНИ ---
  lymph_channels:
    name: "Лимфатические каналы"
    description: "Видимые русла лимфотоков"
    priority: 30

    structural_elevation: [0.2, 0.5]
    metabolic_temp: [20, 40]  # Очень тёплые (активная циркуляция)
    fluid_saturation: [0.8, 1.0]
    is_lymph_channel: true  # Специальное условие

    color: "#FFD700"  # Золотой (лимфа)
    tags: [resource:pure_lymph, location:trade_route]

  # --- ХИТИНОВЫЕ ПОКРОВЫ ---
  chitinous_expanse:
    name: "Хитиновая поверхность"
    description: "Твёрдые защитные покровы"
    priority: 35

    structural_elevation: [0.5, 0.75]
    metabolic_temp: [0, 15]  # Холодные (мёртвая защита)
    fluid_saturation: [0.0, 0.3]
    airflow_intensity: [0.0, 0.3]

    color: "#2F4F4F"  # Тёмно-серый (хитин)
    tags: [surface:stable, ecology:barren, terrain:elevated]

  # --- КОСТНАЯ ТКАНЬ ---
  osseous_ridge:
    name: "Костяной хребет"
    description: "Скелетная основа мира"
    priority: 50

    structural_elevation: [0.7, 1.0]
    metabolic_temp: [-20, 10]  # Очень холодный (мёртвая кость)
    fluid_saturation: [0.0, 0.2]
    airflow_intensity: [0.0, 0.2]

    color: "#E8E8D0"  # Костяной белый
    tags: [surface:stable, terrain:elevated, resource:bone_chitin, danger_level:5]

  # --- ВЫСОХШИЕ ТКАНИ ---
  desiccated_tissue:
    name: "Высохшая ткань"
    description: "Зоны, высушенные воздушными потоками"
    priority: 20

    structural_elevation: [0.45, 0.65]
    metabolic_temp: [25, 50]  # Жаркие (от ветра)
    fluid_saturation: [0.0, 0.2]  # Сухо!
    airflow_intensity: [0.7, 1.0]  # Сильный вдох

    color: "#C19A6B"  # Коричневый (сухая кожа)
    tags: [surface:unstable, ecology:barren, climate:arid]

  # --- ТОКСИЧНЫЕ ТКАНИ ---
  necrotic_tissue:
    name: "Некротическая ткань"
    description: "Гниющие, токсичные участки (дельты, болота)"
    priority: 15

    structural_elevation: [0.0, 0.25]
    metabolic_temp: [15, 35]
    fluid_saturation: [0.8, 1.0]
    toxicity: [0.7, 1.0]  # Специальный слой (добавить)

    color: "#2C5F2D"  # Болотно-зелёный
    tags: [surface:unstable, ecology:toxic, danger:disease]

  # --- АЛЬВЕОЛЯРНЫЕ КАВЕРНЫ ---
  alveolar_vent:
    name: "Альвеолярная каверна"
    description: "Вход в лёгкие мира"
    priority: 80

    structural_elevation: [0.0, 0.3]
    is_alveolar_cavern: true  # Специальное условие

    color: "#000080"  # Тёмно-синий (глубина)
    tags: [terrain:subterranean, location:underground, breathing:intake]

# Специальные правила назначения
special_conditions:
  - condition: "is_lymph_channel == true"
    tissue: "lymph_channels"
    override_priority: 90

  - condition: "is_alveolar_cavern == true"
    tissue: "alveolar_vent"
    override_priority: 95
```

**Критерии завершения:**
- ✅ Все ткани описаны
- ✅ Приоритеты логичны
- ✅ Цвета подобраны (анатомическая палитра)

---

#### Задача 2.2: Реализация назначения тканей
**Время:** 3-4 часа

```python
def _assign_tissue_types(self, structure_map, lymph_network,
                        respiratory_data, metabolism_map) -> dict:
    """Назначает тип ткани каждому сектору"""

    sectors = {}
    tissue_rules = self._load_tissue_rules()

    lymph_network_map = lymph_network['network_map']
    lymph_intensity = lymph_network['intensity']
    airflow_map = respiratory_data['airflow_intensity']
    desiccation = respiratory_data['desiccation']
    caverns = respiratory_data['caverns']

    for y in range(self.height):
        for x in range(self.width):
            # Физические свойства
            elevation = structure_map[y, x]
            temp = metabolism_map[y, x]
            fluid_sat = lymph_intensity[y, x]
            airflow = airflow_map[y, x]

            # Специальные условия
            is_lymph = lymph_network_map[y, x]
            is_cavern = (x, y) in caverns

            # Выбор ткани
            tissue_type = self._select_tissue(
                elevation, temp, fluid_sat, airflow,
                is_lymph, is_cavern, tissue_rules
            )

            # Создание сектора
            sector = GlobalSector(
                coord=HexCoord(x, y),
                elevation=elevation,
                temperature=temp,
                moisture=fluid_sat,  # Насыщенность флюидами
                biome_type=tissue_type,  # Теперь это "тип ткани"

                # НОВЫЕ ПОЛЯ для биопанка:
                metabolic_heat=temp,
                airflow_intensity=airflow,
                is_lymph_channel=is_lymph,
                vent_attractor_coord=self._find_nearest_cavern(x, y, caverns) if airflow > 0.3 else None,

                tags=tissue_rules[tissue_type]['tags']
            )

            sectors[(x, y)] = sector

    return sectors

def _select_tissue(self, elev, temp, fluid_sat, airflow,
                  is_lymph, is_cavern, rules) -> str:
    """
    Выбирает ткань с учётом приоритетов.

    Текущая реализация (Sprint 3.5):
    - Простая система приоритетов
    - Проверка попадания в диапазоны
    - Ткань с наивысшим приоритетом побеждает

    TODO (Sprint 4+): Рассмотреть систему "очков соответствия"
    для более плавных переходов между тканями.

    Пример будущей системы очков:
    ```python
    score = 0
    # Попадание в центр диапазона даёт больше очков
    if elev_min <= elev <= elev_max:
        center = (elev_min + elev_max) / 2
        distance_from_center = abs(elev - center)
        score += (1.0 - distance_from_center) * weight
    # Аналогично для temp, fluid_sat, airflow
    # Ткань с максимальным score побеждает
    ```

    Это позволит создавать более плавные и сложные переходы.
    """

    # Специальные условия (высший приоритет)
    if is_cavern:
        return 'alveolar_vent'
    if is_lymph and fluid_sat > 0.7:
        return 'lymph_channels'

    # Общий выбор по правилам
    candidates = []

    for tissue_name, rule in rules.items():
        # Проверка диапазонов
        elev_min, elev_max = rule['structural_elevation']
        temp_min, temp_max = rule['metabolic_temp']
        fluid_min, fluid_max = rule['fluid_saturation']
        air_min, air_max = rule.get('airflow_intensity', [0.0, 1.0])

        if (elev_min <= elev <= elev_max and
            temp_min <= temp <= temp_max and
            fluid_min <= fluid_sat <= fluid_max and
            air_min <= airflow <= air_max):

            priority = rule.get('priority', 0)
            candidates.append((priority, tissue_name))

    if not candidates:
        return 'membranous_plains'  # Fallback

    # Сортировка по приоритету
    candidates.sort(reverse=True)
    return candidates[0][1]

def _find_nearest_cavern(self, x: int, y: int, caverns: list) -> tuple:
    """Находит ближайшую каверну"""
    if not caverns:
        return None

    min_dist = float('inf')
    nearest = None

    for cx, cy in caverns:
        dist = ((x - cx)**2 + (y - cy)**2)**0.5
        if dist < min_dist:
            min_dist = dist
            nearest = (cx, cy)

    return nearest
```

**Критерии завершения:**
- ✅ Все сектора имеют валидный тип ткани
- ✅ Специальные условия работают (каверны, лимфотоки)
- ✅ Приоритеты разрешаются корректно

---

### ФАЗА 3: Модели данных (4 часа)

#### Задача 3.1: Расширенная модель GlobalSector
**Файл:** `models/global_map.py`
**Время:** 2 часа

```python
from dataclasses import dataclass, field
from typing import Optional, List, Tuple
from models.hex_coord import HexCoord

@dataclass
class GlobalSector:
    """
    Атомарная единица живого мира Сильгаррон.

    Это не просто "тайл карты", а участок ткани организма.
    """
    coord: HexCoord

    # === ФИЗИЧЕСКИЕ СВОЙСТВА (генерируются, не меняются) ===

    # Структурная высота (аналог elevation)
    elevation: float  # 0.0-1.0 (низина → костяной пик)

    # Метаболическое тепло (НЕ климатическая температура!)
    temperature: float  # -20 до +50°C (активность тканей)
    metabolic_heat: float  # Дублирует temperature (для ясности)

    # Насыщенность флюидами (лимфа, не вода!)
    moisture: float  # 0.0-1.0 (сухо → пропитано лимфой)

    # Тип ткани (вместо biome_type)
    biome_type: str  # "osseous_ridge", "fibrous_thicket", etc.

    # === АНАТОМИЧЕСКИЕ ОСОБЕННОСТИ (NEW!) ===

    # Интенсивность воздушного потока (Дыхание)
    airflow_intensity: float = 0.0  # 0.0-1.0 (нет → сильный вдох)

    # Координаты каверны, к которой тянется воздух
    vent_attractor_coord: Optional[Tuple[int, int]] = None

    # Является ли частью лимфатической сети
    is_lymph_channel: bool = False

    # Опциональные системы
    has_river: bool = False  # Устаревшее, заменено на is_lymph_channel
    is_river_navigable: bool = False

    # === ДИНАМИЧЕСКИЕ СВОЙСТВА (меняются во время игры) ===

    poi_type: Optional[str] = None
    poi_name: Optional[str] = None
    faction_id: Optional[str] = None
    is_burned: bool = False
    is_explored: bool = False

    # Мета-информация
    cluster_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Сериализация"""
        return {
            "coord": (self.coord.q, self.coord.r),
            "elevation": self.elevation,
            "temperature": self.temperature,
            "metabolic_heat": self.metabolic_heat,
            "moisture": self.moisture,
            "biome_type": self.biome_type,
            "airflow_intensity": self.airflow_intensity,
            "vent_attractor_coord": self.vent_attractor_coord,
            "is_lymph_channel": self.is_lymph_channel,
            "has_river": self.has_river,
            "poi_type": self.poi_type,
            "poi_name": self.poi_name,
            "faction_id": self.faction_id,
            "is_burned": self.is_burned,
            "is_explored": self.is_explored,
            "cluster_id": self.cluster_id,
            "tags": self.tags
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'GlobalSector':
        """Десериализация"""
        q, r = data['coord']
        data['coord'] = HexCoord(q, r)
        return cls(**data)

    def get_tissue_description(self) -> str:
        """Человекочитаемое описание ткани"""
        tissue_names = {
            'osseous_ridge': "Костяной хребет",
            'fibrous_thicket': "Волокнистые заросли",
            'membranous_plains': "Мембранные равнины",
            'lymph_channels': "Лимфатический канал",
            'desiccated_tissue': "Высохшая ткань",
            # ... остальные
        }
        return tissue_names.get(self.biome_type, self.biome_type)
```

**Критерии завершения:**
- ✅ Модель расширена новыми полями
- ✅ Сериализация работает
- ✅ Описательные методы добавлены

---

#### Задача 3.2: GlobalMapData и DeltaTracker
**Время:** 2 часа

(Код из предыдущей версии плана остаётся актуальным)

---

### ФАЗА 4: Визуализация "медицинского сканирования" (6-7 часов)

#### Задача 4.1: Визуализатор с анатомическими слоями
**Файл:** `tools/visualize_global_map.py`
**Время:** 4 часа

```python
import matplotlib.pyplot as plt
import numpy as np
from models.global_map import GlobalMapData

def visualize_anatomical_map(map_data: GlobalMapData, output_path: str):
    """
    Создаёт медицинское сканирование живого мира.

    5 слоёв:
    1. Structural Anatomy (костяная структура)
    2. Tissue Morphology (типы тканей)
    3. Metabolic Heatmap (активность)
    4. Fluid Saturation (лимфа)
    5. Airflow Map (дыхание)
    """

    fig, axes = plt.subplots(2, 3, figsize=(24, 16))

    # Слой 1: Структурная анатомия
    plot_structural_anatomy(axes[0, 0], map_data)
    axes[0, 0].set_title('Structural Anatomy', fontsize=16, fontweight='bold')

    # Слой 2: Морфология тканей
    plot_tissue_morphology(axes[0, 1], map_data)
    axes[0, 1].set_title('Tissue Morphology', fontsize=16, fontweight='bold')

    # Слой 3: Метаболическая карта
    plot_metabolic_heatmap(axes[0, 2], map_data)
    axes[0, 2].set_title('Metabolic Heatmap', fontsize=16, fontweight='bold')

    # Слой 4: Насыщенность флюидами
    plot_fluid_saturation(axes[1, 0], map_data)
    axes[1, 0].set_title('Fluid Saturation (Lymph)', fontsize=16, fontweight='bold')

    # Слой 5: Карта воздушных потоков
    plot_airflow_map(axes[1, 1], map_data)
    axes[1, 1].set_title('Airflow Map (Breathing)', fontsize=16, fontweight='bold')

    # Слой 6: Composite (все слои)
    plot_composite_scan(axes[1, 2], map_data)
    axes[1, 2].set_title('Composite Scan', fontsize=16, fontweight='bold')

    plt.suptitle(f'🧬 Anatomical Scan: {map_data.seed} ({map_data.width}×{map_data.height})',
                 fontsize=22, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✅ Medical scan saved: {output_path}")

def plot_structural_anatomy(ax, map_data):
    """Отображает костяную структуру"""
    elevations = np.zeros((map_data.height, map_data.width))

    for (q, r), sector in map_data.sectors.items():
        elevations[r, q] = sector.elevation

    # Цветовая карта: bone (костяная)
    im = ax.imshow(elevations, cmap='bone', origin='lower', vmin=0, vmax=1)
    plt.colorbar(im, ax=ax, label='Structural Height (0=soft tissue, 1=bone)')
    ax.set_xlabel('X (hexes)')
    ax.set_ylabel('Y (hexes)')

def plot_tissue_morphology(ax, map_data):
    """Отображает типы тканей цветом"""
    # Загружаем цвета из tissue_rules.yaml
    tissue_rules = load_tissue_rules()

    image = np.zeros((map_data.height, map_data.width, 3))

    for (q, r), sector in map_data.sectors.items():
        color_hex = tissue_rules[sector.biome_type]['color']
        color_rgb = hex_to_rgb(color_hex)
        image[r, q] = color_rgb

    ax.imshow(image, origin='lower')

    # Легенда
    create_tissue_legend(ax, tissue_rules)

def plot_metabolic_heatmap(ax, map_data):
    """Отображает метаболическое тепло"""
    temps = np.zeros((map_data.height, map_data.width))

    for (q, r), sector in map_data.sectors.items():
        temps[r, q] = sector.metabolic_heat

    # Цветовая карта: hot (огненная)
    im = ax.imshow(temps, cmap='afmhot', origin='lower')
    plt.colorbar(im, ax=ax, label='Metabolic Heat (°C)')

def plot_fluid_saturation(ax, map_data):
    """Отображает насыщенность лимфой"""
    fluids = np.zeros((map_data.height, map_data.width))

    for (q, r), sector in map_data.sectors.items():
        fluids[r, q] = sector.moisture

    # Цветовая карта: viridis (лимфа)
    im = ax.imshow(fluids, cmap='viridis', origin='lower', vmin=0, vmax=1)
    plt.colorbar(im, ax=ax, label='Lymph Saturation (0=dry, 1=saturated)')

def plot_airflow_map(ax, map_data):
    """Отображает интенсивность воздушных потоков"""
    airflow = np.zeros((map_data.height, map_data.width))

    for (q, r), sector in map_data.sectors.items():
        airflow[r, q] = sector.airflow_intensity

    # Цветовая карта: cool (воздух)
    im = ax.imshow(airflow, cmap='cool', origin='lower', vmin=0, vmax=1)
    plt.colorbar(im, ax=ax, label='Airflow Intensity (0=still, 1=strong intake)')

    # Отметить каверны
    for (q, r), sector in map_data.sectors.items():
        if 'alveolar_vent' in sector.biome_type:
            ax.plot(q, r, 'r*', markersize=10)

def plot_composite_scan(ax, map_data):
    """Комбинированное изображение"""
    # RGB: R=метаболизм, G=лимфа, B=воздух
    image = np.zeros((map_data.height, map_data.width, 3))

    for (q, r), sector in map_data.sectors.items():
        r_val = (sector.metabolic_heat + 20) / 70  # Нормализация temp
        g_val = sector.moisture
        b_val = sector.airflow_intensity

        image[r, q] = [r_val, g_val, b_val]

    ax.imshow(image, origin='lower')
    ax.set_xlabel('Composite: R=Heat, G=Lymph, B=Airflow')
```

**Критерии завершения:**
- ✅ Визуализация создаётся без ошибок
- ✅ Все 5 слоёв читаемы
- ✅ Цветовые палитры анатомические

---

### ФАЗА 5: Конфигурация, тестирование и тюнинг (12-15 часов)

#### Задача 5.1: world_generation.yaml
**Файл:** `config/world_generation.yaml`
**Время:** 1 час

```yaml
global_map:
  default_width: 256
  default_height: 256

  generation:
    default_seed: "Silgarron"

    # === АНАТОМИЧЕСКИЕ ПАРАМЕТРЫ ===

    # Костяной хребет
    spine:
      enabled: true
      center_position: 0.5  # 0-1 (центр карты)
      width_factor: 0.1     # Ширина хребта (% от карты)
      height_multiplier: 1.5  # Насколько выше окружения
      wiggle_amplitude: 10  # Амплитуда изгибов

    # Рёбра
    ribs:
      enabled: true
      count: 8
      prominence: 0.5

    # Лимфатическая система
    lymphatic_system:
      source_density: 0.01  # % гексов = истоки
      flow_threshold: 50    # Минимальный flow для видимого лимфотока

    # Дыхательная система
    respiratory_system:
      cavern_count: 6       # Количество Альвеолярных каверн
      airflow_decay_rate: 0.95  # Затухание потока (0.95 = 5% на гекс)
      desiccation_strength: 1.0  # Сила высушивания

    # Perlin noise (микрорельеф)
    noise:
      scale: 100.0
      octaves: 6
      persistence: 0.5
      lacunarity: 2.0

  # Пороги высот
  elevation_thresholds:
    primordial_fluid: [0.0, 0.3]
    soft_tissue: [0.3, 0.5]
    dense_tissue: [0.5, 0.7]
    chitinous_layer: [0.7, 0.85]
    osseous_structure: [0.85, 1.0]
```

**Критерии завершения:**
- ✅ Конфиг загружается
- ✅ Параметры применяются в генераторе

---

#### Задача 5.2: Тесты на биологическую логичность
**Файл:** `tests/test_world_generator.py`
**Время:** 4-5 часов

```python
import pytest
from core.world_generator import WorldGenerator

class TestAnatomicalGeneration:

    def test_reproducibility(self):
        """Seed воспроизводится детерминированно"""
        gen1 = WorldGenerator(seed="test_seed", width=64, height=64)
        map1 = gen1.generate()

        gen2 = WorldGenerator(seed="test_seed", width=64, height=64)
        map2 = gen2.generate()

        # Проверка нескольких секторов
        for i in range(10):
            q, r = i * 5, i * 3
            s1 = map1.get_sector(q, r)
            s2 = map2.get_sector(q, r)

            assert s1.elevation == s2.elevation
            assert s1.biome_type == s2.biome_type
            assert s1.airflow_intensity == s2.airflow_intensity

    def test_spine_exists(self):
        """Костяной хребет должен существовать"""
        gen = WorldGenerator(seed="spine_test", width=128, height=128)
        map_data = gen.generate()

        # Ищем высокие гексы (хребет)
        high_elevations = [s for s in map_data.sectors.values()
                          if s.elevation > 0.7]

        assert len(high_elevations) > 100, "Хребет должен быть виден"

        # Проверка: хребет должен быть связным
        # (это упрощённая проверка, полноценная требует flood fill)
        assert len(high_elevations) < 5000, "Хребет не должен занимать всю карту"

    def test_spine_is_cold(self):
        """Костяной хребет должен быть холодным"""
        gen = WorldGenerator(seed="cold_spine", width=128, height=128)
        map_data = gen.generate()

        # Фильтруем хребет
        spine_sectors = [s for s in map_data.sectors.values()
                        if s.biome_type == 'osseous_ridge']

        if spine_sectors:
            avg_temp = sum(s.metabolic_heat for s in spine_sectors) / len(spine_sectors)
            assert avg_temp < 15, f"Хребет слишком тёплый: {avg_temp}°C"

    def test_lymph_channels_are_warm(self):
        """Лимфотоки должны быть тёплыми"""
        gen = WorldGenerator(seed="warm_lymph", width=128, height=128)
        map_data = gen.generate()

        lymph_sectors = [s for s in map_data.sectors.values()
                        if s.is_lymph_channel]

        if lymph_sectors:
            avg_temp = sum(s.metabolic_heat for s in lymph_sectors) / len(lymph_sectors)
            assert avg_temp > 20, f"Лимфотоки слишком холодные: {avg_temp}°C"

    def test_caverns_exist(self):
        """Альвеолярные каверны должны быть размещены"""
        gen = WorldGenerator(seed="caverns", width=128, height=128)
        map_data = gen.generate()

        caverns = [s for s in map_data.sectors.values()
                  if s.biome_type == 'alveolar_vent']

        assert len(caverns) >= 3, "Должно быть минимум 3 каверны"
        assert len(caverns) <= 10, "Не должно быть слишком много каверн"

    def test_airflow_near_caverns(self):
        """Airflow должен быть выше рядом с кавернами"""
        gen = WorldGenerator(seed="airflow_test", width=128, height=128)
        map_data = gen.generate()

        caverns = [s for s in map_data.sectors.values()
                  if s.biome_type == 'alveolar_vent']

        if caverns:
            cavern = caverns[0]

            # Найти соседей
            neighbors = map_data.get_neighbors(cavern)

            # У соседей airflow должен быть высоким
            neighbor_airflow = [n.airflow_intensity for n in neighbors]
            avg_airflow = sum(neighbor_airflow) / len(neighbor_airflow)

            assert avg_airflow > 0.5, f"Низкий airflow рядом с каверной: {avg_airflow}"

    def test_no_deserts_in_lymph_zones(self):
        """Пустыни не должны появляться в зонах высокой лимфы"""
        gen = WorldGenerator(seed="logic_test", width=128, height=128)
        map_data = gen.generate()

        for sector in map_data.sectors.values():
            # Если влажность высокая, не должно быть сухой ткани
            if sector.moisture > 0.7:
                assert sector.biome_type != 'desiccated_tissue', \
                    f"Сухая ткань в зоне высокой влажности ({sector.coord})"

    def test_airflow_dries_tissue(self):
        """Высокий airflow должен приводить к низкой влажности"""
        gen = WorldGenerator(seed="dry_wind", width=128, height=128)
        map_data = gen.generate()

        high_airflow_sectors = [s for s in map_data.sectors.values()
                               if s.airflow_intensity > 0.7]

        if high_airflow_sectors:
            # В среднем влажность должна быть низкой
            avg_moisture = sum(s.moisture for s in high_airflow_sectors) / len(high_airflow_sectors)
            assert avg_moisture < 0.4, f"Высокая влажность при сильном airflow: {avg_moisture}"

    def test_generation_performance(self):
        """Генерация занимает <40 секунд"""
        import time

        gen = WorldGenerator(seed="perf_test", width=256, height=256)

        start = time.time()
        map_data = gen.generate()
        duration = time.time() - start

        assert duration < 40.0, f"Генерация заняла {duration:.1f}s"
```

**Критерии завершения:**
- ✅ Все тесты проходят
- ✅ Биологическая логика проверена

---

#### Задача 5.3: Итеративный тюнинг анатомических параметров
**Время:** 4-5 часов

**Концепция:**
В плане присутствует множество "магических чисел", которые напрямую влияют на "биологический" вид карты. Эта задача посвящена целенаправленному подбору оптимальных значений через итеративную визуализацию.

**Параметры для тюнинга:**

```yaml
# 1. СКЕЛЕТНАЯ СТРУКТУРА
spine:
  width_factor: 0.1           # 🔧 Тюнинг: 0.05-0.2 (ширина хребта)
  height_multiplier: 1.5      # 🔧 Тюнинг: 1.2-2.0 (высота хребта)
  wiggle_amplitude: 10        # 🔧 Тюнинг: 5-20 (органичность изгибов)

ribs:
  count: 8                    # 🔧 Тюнинг: 4-12 (количество рёбер)
  prominence: 0.5             # 🔧 Тюнинг: 0.3-0.8 (заметность рёбер)

noise_mixing:
  base_weight: 0.6            # 🔧 Тюнинг: 0.4-0.7
  spine_weight: 0.3           # 🔧 Тюнинг: 0.2-0.4
  rib_weight: 0.1             # 🔧 Тюнинг: 0.05-0.2

# 2. ЛИМФАТИЧЕСКАЯ СИСТЕМА
lymphatic_system:
  source_density: 0.01        # 🔧 Тюнинг: 0.005-0.02 (плотность истоков)
  flow_threshold: 50          # 🔧 Тюнинг: 30-100 (видимость каналов)

# 3. ДЫХАТЕЛЬНАЯ СИСТЕМА
respiratory_system:
  cavern_count: 6             # 🔧 Тюнинг: 4-10 (количество каверн)
  cavern_placement_method: "poisson"  # 🔧 "greedy" | "poisson"
  airflow_decay_rate: 0.95    # 🔧 Тюнинг: 0.90-0.98 (затухание потока)
  desiccation_strength: 1.0   # 🔧 Тюнинг: 0.5-1.5 (сила высушивания)

# 4. МЕТАБОЛИЧЕСКОЕ ТЕПЛО
metabolism:
  bone_penalty_factor: 40     # 🔧 Тюнинг: 30-50 (холод кости)
  lymph_bonus_factor: 15      # 🔧 Тюнинг: 10-20 (тепло лимфы)
  lowland_activity_factor: 10 # 🔧 Тюнинг: 5-15 (активность низин)

# 5. PERLIN NOISE
noise:
  scale: 100.0                # 🔧 Тюнинг: 50-150 (масштаб рельефа)
  octaves: 6                  # 🔧 Тюнинг: 4-8 (детализация)
  persistence: 0.5            # 🔧 Тюнинг: 0.3-0.7 (контраст)
  lacunarity: 2.0             # 🔧 Тюнинг: 1.5-2.5 (частота деталей)
```

**Методология тюнинга:**

```python
# Скрипт для итеративного тюнинга
# tools/tune_parameters.py

def tune_parameters():
    """Итеративный процесс подбора параметров"""

    # 1. Загрузить базовые параметры
    config = load_config('config/world_generation.yaml')

    # 2. Определить диапазоны для тюнинга
    tune_ranges = {
        'spine.width_factor': (0.05, 0.2, 0.01),  # (min, max, step)
        'spine.height_multiplier': (1.2, 2.0, 0.1),
        'respiratory_system.airflow_decay_rate': (0.90, 0.98, 0.01),
        # ... остальные
    }

    # 3. Итерация по параметрам
    seed = "TuneTest_42"

    for param_name, (min_val, max_val, step) in tune_ranges.items():
        current_val = min_val

        while current_val <= max_val:
            # Обновить параметр
            update_config_value(config, param_name, current_val)

            # Сгенерировать мир
            gen = WorldGenerator(seed=seed, config=config)
            map_data = gen.generate()

            # Визуализировать
            output_path = f"tune_results/{param_name}_{current_val:.2f}.png"
            visualize_anatomical_map(map_data, output_path)

            print(f"✅ {param_name} = {current_val:.2f} → {output_path}")

            current_val += step

    print("\n🎯 Тюнинг завершён. Проверьте tune_results/ и выберите лучшие значения.")
```

**Метрики для визуальной валидации:**

При анализе каждого сканирования проверять:

1. **Structural Anatomy (костяная структура):**
   - ✅ Хребет читается как непрерывная структура
   - ✅ Хребет НЕ выглядит как прямая линия (органичные изгибы)
   - ✅ Рёбра видны, но не доминируют
   - ❌ Нет "шума" без крупных структур

2. **Tissue Morphology (типы тканей):**
   - ✅ Тканевые зоны формируют связные кластеры
   - ✅ Переходы между тканями плавные
   - ✅ Лимфатические каналы (золотые) видны и текут от возвышенностей
   - ❌ Нет изолированных пикселей одной ткани среди другой

3. **Metabolic Heatmap (активность):**
   - ✅ Хребет холодный (тёмный)
   - ✅ Лимфотоки тёплые (яркие)
   - ✅ Градиент выглядит естественно
   - ❌ Нет резких скачков температуры

4. **Fluid Saturation (лимфа):**
   - ✅ Лимфотоки насыщены (яркие)
   - ✅ Высокие зоны сухие (тёмные)
   - ✅ Низины умеренно влажные
   - ❌ Нет "пустынь" в зонах активных лимфотоков

5. **Airflow Map (дыхание):**
   - ✅ Каверны видны как яркие точки
   - ✅ Вокруг каверн видны "воронки" притяжения
   - ✅ Затухание плавное (не резкое)
   - ❌ Нет изолированных пятен высокого airflow вдали от каверн

**Процесс тюнинга (пошагово):**

**Шаг 1: Тюнинг скелета (1-1.5 часа)**
- Настроить `spine.width_factor`, `spine.height_multiplier`, `spine.wiggle_amplitude`
- Цель: Хребет выглядит как органичный позвоночник, а не прямая линия
- Критерий: Команда лора одобряет визуал

**Шаг 2: Тюнинг лимфатической системы (1 час)**
- Настроить `source_density`, `flow_threshold`
- Цель: Лимфотоки видны, текут естественно, не слишком густые и не слишком редкие
- Критерий: На карте видно 10-20 крупных "артерий"

**Шаг 3: Тюнинг дыхательной системы (1-1.5 часа)**
- Настроить `cavern_count`, `airflow_decay_rate`, `desiccation_strength`
- Цель: Воронки дыхания видны, но не занимают всю карту
- Критерий: Зоны высушивания логично расположены вокруг каверн

**Шаг 4: Тюнинг метаболизма (0.5 часа)**
- Настроить температурные коэффициенты
- Цель: Тепловая карта соответствует биологии (кость холодная, лимфа тёплая)
- Критерий: Тесты `test_spine_is_cold` и `test_lymph_channels_are_warm` проходят

**Шаг 5: Тюнинг Perlin noise (0.5-1 час)**
- Настроить `scale`, `octaves`, `persistence`
- Цель: Микрорельеф добавляет органичность, но не заглушает крупные структуры
- Критерий: На визуализации видны и хребет, и мелкие детали

**Инструменты:**

```bash
# Генерация с текущими параметрами
python tools/generate_world.py --seed "TuneTest" --visualize

# Автоматический тюнинг по диапазону
python tools/tune_parameters.py --param spine.width_factor --range 0.05:0.2:0.01

# Сравнение нескольких конфигов
python tools/compare_configs.py config1.yaml config2.yaml config3.yaml
```

**Критерии завершения:**
- ✅ Все 5 визуализационных слоёв выглядят "биологично"
- ✅ Команда лора одобряет анатомический вид
- ✅ Все биологические тесты (Задача 5.2) проходят
- ✅ Оптимальные параметры зафиксированы в `world_generation.yaml`
- ✅ Создан отчёт `docs/TUNING_RESULTS.md` с примерами до/после

---

### ФАЗА 6: Документация и CLI (3-4 часа)

#### Задача 6.1: CLI генератор
**Файл:** `tools/generate_world.py`
**Время:** 1.5 часа

```python
#!/usr/bin/env python3
"""
CLI для генерации анатомической карты живого мира.

Использование:
    python tools/generate_world.py --seed "Silgarron" --output world.json.gz
    python tools/generate_world.py --seed "TestWorld" --visualize --output test.png
"""

import argparse
from core.world_generator import WorldGenerator
from tools.visualize_global_map import visualize_anatomical_map

def main():
    parser = argparse.ArgumentParser(
        description='🧬 Генерация анатомической карты живого мира Сильгаррон'
    )

    parser.add_argument('--seed', type=str, required=True,
                       help='Seed для генерации (строка)')

    parser.add_argument('--width', type=int, default=256,
                       help='Ширина карты (по умолчанию 256)')

    parser.add_argument('--height', type=int, default=256,
                       help='Высота карты (по умолчанию 256)')

    parser.add_argument('--output', type=str, default='world.json.gz',
                       help='Путь для сохранения карты')

    parser.add_argument('--visualize', action='store_true',
                       help='Создать медицинское сканирование')

    parser.add_argument('--viz-output', type=str, default='anatomical_scan.png',
                       help='Путь для визуализации')

    args = parser.parse_args()

    # Генерация
    print(f"\n🧬 Генерация живого мира '{args.seed}' ({args.width}×{args.height})...\n")
    gen = WorldGenerator(seed=args.seed, width=args.width, height=args.height)
    map_data = gen.generate()

    # Сохранение
    map_data.save(args.output)

    # Визуализация
    if args.visualize:
        print(f"\n📊 Создание медицинского сканирования...\n")
        visualize_anatomical_map(map_data, args.viz_output)

    print("\n✅ Готово!\n")

if __name__ == "__main__":
    main()
```

**Критерии завершения:**
- ✅ CLI работает
- ✅ Можно сгенерировать и визуализировать мир одной командой

---

#### Задача 6.2: Обновление документации
**Время:** 2 часа

- [ ] Обновить `README.md`
- [ ] Создать `core/README.md`
- [ ] Обновить TDD (статус компонентов)
- [ ] Добавить примеры использования

---

## ✅ Definition of Done

### Обязательные критерии

- [ ] **Генератор работает**
  - ✅ Создаёт анатомическую карту 256×256 за <40 секунд
  - ✅ Seed-based: 100% воспроизводимость (через `hashlib`)
  - ✅ Виден костяной хребет, лимфотоки, каверны

- [ ] **Биологическая логичность**
  - ✅ Хребет = холодный (кость)
  - ✅ Лимфотоки = тёплые (активная циркуляция)
  - ✅ Высокий airflow → низкая влажность
  - ✅ Каверны размещены логично (низины)
  - ✅ Нет пустынь в зонах лимфы

- [ ] **Визуализация**
  - ✅ Медицинское сканирование сохраняет PNG с 5 слоями
  - ✅ Анатомические цветовые палитры
  - ✅ Легенды читаемы

- [ ] **Тесты**
  - ✅ 95%+ тестов проходят
  - ✅ Воспроизводимость seed проверена
  - ✅ Биологическая логика протестирована
  - ✅ Сохранение/загрузка работает

- [ ] **Документация**
  - ✅ Обновлён TDD
  - ✅ README созданы
  - ✅ CLI задокументирован
  - ✅ Комментарии в коде по анатомии

---

## ⚠️ Риски и митигация

### Риск 1: Воспроизводимость seed (КРИТИЧЕСКИЙ)
**Вероятность:** КРИТИЧЕСКАЯ (100% без исправления)
**Митигация:**
- ✅ **ОБЯЗАТЕЛЬНО:** `hashlib.sha256()` вместо `hash()`

### Риск 2: BFS для влажности слишком медленный
**Вероятность:** Средняя
**Митигация:**
- Оптимизация алгоритма
- Возможность отключения через конфиг

### Риск 3: Хребет выглядит искусственно (прямая линия)
**Вероятность:** Средняя (снижена благодаря Задаче 5.3)
**Митигация:**
- ✅ Добавить изгибы (синусоида)
- ✅ Параметр "органичность" в конфиге
- ✅ **Задача 5.3:** Итеративный тюнинг с визуальной валидацией (4-5 часов)

### Риск 4: Недостаточная "биологичность" карты
**Вероятность:** Низкая (снижена благодаря Задаче 5.3)
**Воздействие:** КРИТИЧЕСКОЕ (мир не ощущается живым)

**Митигация:**
1. ✅ **Задача 5.3:** Итеративный тюнинг с метриками биологичности
2. ✅ Сессия визуальной валидации с командой лора (Шаг 1, Задача 5.3)
3. ✅ Параметры "биологичности" в конфиге
4. ✅ Расширение tissue_rules.yaml итеративно

### Риск 5: Производительность генерации >40 секунд
**Вероятность:** Средняя (из-за BFS)
**Митигация:**
- Профилирование
- Numpy vectorization
- Меньшие карты для тестов (64×64)

---

## 📚 Материалы для изучения

### Обязательные

1. **Perlin Noise**
   - https://thebookofshaders.com/11/
   - Время: 1-2 часа

2. **Hex Grid Math**
   - https://www.redblobgames.com/grids/hexagons/
   - Время: 1 час

3. **Flow Accumulation (D8 Algorithm)**
   - https://en.wikipedia.org/wiki/D8_algorithm
   - Время: 1 час

4. **BFS (Breadth-First Search)**
   - Базовый алгоритм графов
   - Время: 30 минут

5. **Poisson Disk Sampling**
   - https://www.cs.ubc.ca/~rbridson/docs/bridson-siggraph07-poissondisk.pdf
   - https://sighack.com/post/poisson-disk-sampling-bridsons-algorithm
   - Время: 1 час

### Дополнительные

6. **Физиология живых систем** (для вдохновения)
   - Кровеносная система
   - Дыхательная система
   - Время: 1-2 часа

---

## 📊 Метрики успеха

| Метрика | Целевое значение |
|---------|------------------|
| Время генерации 256×256 | <40 секунд |
| Размер сжатого мира | <3 MB |
| Размер delta (100 изменений) | <50 KB |
| Тесты проходят | ≥95% |
| Воспроизводимость seed | 100% |
| "Биологичность" (субъективно) | Утверждено командой лора |

---

## 📝 Changelog плана

### v2.1 (21 октября 2025) - Технические уточнения

**Улучшения:**
1. ✅ **Poisson Disk Sampling** для размещения каверн (Задача 1.4)
   - Более органичное распределение альвеолярных каверн
   - Избегание предсказуемых паттернов жадного алгоритма
   - Переключаемый метод через конфиг (`cavern_placement_method: "poisson" | "greedy"`)

2. ✅ **TODO для системы очков** в назначении тканей (Задача 2.2)
   - Документировано будущее улучшение для Sprint 4+
   - Пример реализации для плавных переходов между тканями
   - Текущая система приоритетов остаётся для простоты Sprint 3.5

3. ✅ **Задача 5.3: Итеративный тюнинг** (4-5 часов)
   - Выделены все "магические числа" для тюнинга
   - Методология визуальной валидации с 5 метриками
   - Пошаговый процесс тюнинга (5 шагов)
   - Инструменты для автоматизации
   - Критерии завершения (одобрение команды лора)

**Изменения:**
- Время Фазы 5: 8-10 часов → 12-15 часов (добавлен тюнинг)
- Общее время спринта: 44-50 часов → 48-55 часов
- Риск "биологичности": Высокий → Низкий (благодаря Задаче 5.3)
- Риск "искусственного хребта": Высокий → Средний (благодаря Задаче 5.3)

**Новые материалы для изучения:**
- Poisson Disk Sampling (Bridson's algorithm)

---

### v2.0 (21 октября 2025) - ПОЛНАЯ ПЕРЕРАБОТКА

**Фундаментальные изменения:**
1. ✅ Переход от "геологической" генерации к **анатомической**
2. ✅ Реализация **системы "Дыхания"** (Альвеолярные каверны + BFS)
3. ✅ **Лимфатическая система** вместо рек
4. ✅ **Метаболическое тепло** вместо климата
5. ✅ **Типы тканей** вместо биомов
6. ✅ Визуализация как "медицинское сканирование"

**Новые компоненты:**
- `tissue_rules.yaml` (вместо `biome_rules.yaml`)
- Генерация костяного хребта (ridge-biased noise)
- Система "Дыхания" (airflow, каверны)
- Расширенная модель `GlobalSector` (airflow_intensity, metabolic_heat)

**Изменено:**
- Время оценки: 40-45 часов → 44-50 часов
- Фаза 1: 11-13 часов → 14-16 часов (дыхательная система)

**Обоснование:**
Мир Сильгаррон — это НЕ планета, а живой организм. Стандартная процедурная генерация мира (геология, климат, тектоника) фундаментально не подходит. Требуется симуляция анатомии, метаболизма и физиологии.

### v1.1 (21 октября 2025) - Критические корректировки
Добавлены: hashlib для seed, BFS для влажности, система приоритетов биомов.

### v1.0 (21 октября 2025) - Первоначальный план
Создан базовый план (стандартная процедурная генерация).

---

**Создано:** 21 октября 2025
**Скорректировано:** 21 октября 2025 (v2.0 - ПОЛНАЯ ПЕРЕРАБОТКА)
**Автор:** Команда разработки Silgarron RPG
**Версия:** 2.0
**Статус:** Готов к выполнению ✅

---

## 🎓 Благодарности

Спасибо за критическое замечание о биопанк-специфике мира! Это фундаментально изменило подход к генерации. Вместо симуляции геологии мы теперь симулируем **живой организм** — что полностью соответствует уникальному видению проекта.
