# 🗺️ Global Map Implementation Guide

**Проект:** Silgarron RPG
**Документ:** Полное руководство по реализации глобальной карты 256×256
**Статус:** Активный рабочий документ
**Целевая аудитория:** Разработчики, работающие над Sprint 2-3

---

## 📋 Table of Contents

1. [Философия и видение](#философия-и-видение)
2. [Архитектурное решение](#архитектурное-решение)
3. [Технические детали](#технические-детали)
4. [Долгосрочная перспектива](#долгосрочная-перспектива)
5. [Дополнительные материалы](#дополнительные-материалы)
6. [Визуализация: До vs После](#визуализация-до-vs-после)
7. [Структуры данных](#структуры-данных)
8. [Финальный чеклист](#финальный-чеклист)

---

## 🎯 Философия и видение

### "Нарративная плотность важнее физического размера"

Мир Сильгаррона проектируется не как бесконечная процедурная карта, а как **компактное пространство с максимальной плотностью историй**. Каждая локация - это не пустой тайл, а уникальное место с контекстом, конфликтами и возможностями.

**Принципы:**
- ✅ **Компактность**: 256×256 гексов (~65 км²) вместо 10000×10000
- ✅ **Нарративный вес**: Каждая локация имеет причину существования
- ✅ **Воспроизводимость**: Один seed = один и тот же мир
- ✅ **Эффективность**: Delta-saves экономят 95% места

### ⚠️ ВАЖНО: О легаси коде

**Игра в разработке - НЕ релизнута!**

Это означает:
- ❌ **Старые сохранения НЕ валидны** - можно тупо удалять
- ❌ **Легаси куски кода** - удаляем без сожаления
- ❌ **Обратная совместимость** - НЕ требуется на этом этапе
- ✅ **Чистая архитектура** - приоритет над "не сломать старое"

**Правило:**
> Если старый код мешает новой архитектуре - удаляй. Если старая структура данных не подходит - переписывай. Никаких костылей для поддержки legacy.

---

## 🏗️ Архитектурное решение

### Текущая система (УСТАРЕЛА - удалить)

```
КОНТИНЕНТ "Торакс"
    ↓
РЕГИОН "Склеритовый хребет" (абстрактный контейнер)
    ↓
БИОМЫ внутри региона:
    - Кит Поселение (в центре)
    - Горная тундра (случайное место)
    - Альвеольные пещеры (случайное место)
    - Лимфатическая долина (случайное место)
```

**Проблемы:**
- ❌ "Горы" не выглядят как горы (просто узлы графа)
- ❌ Нет естественных форм
- ❌ Невозможно проложить маршрут
- ❌ AI не может описать "хребет тянется на север"

**Что удалить:**
```python
# services/hex_world_service.py
class HexWorldService:
    def generate_continent(self, ...):  # ❌ УДАЛИТЬ
        pass

    def _generate_local_biome_layout(self, ...):  # ❌ УДАЛИТЬ
        pass

# models/ (где-то)
@dataclass
class RegionData:  # ❌ УДАЛИТЬ ВЕСЬ КЛАСС
    id: str
    biome_ids: List[str]  # ❌ Концепция устарела
    parent_region_id: str  # ❌ Больше не нужно
```

### Новая система (РЕАЛИЗУЕМ)

```
ГЛОБАЛЬНАЯ КАРТА 256×256
    ↓
Сектор [100, 50]: elevation=0.85, temp=-5°C, moisture=0.2
    → biome = "mountain_tundra"
    → part_of_cluster = "Sclerite Ridge" (мета-информация)

Сектор [101, 50]: elevation=0.87, temp=-6°C, moisture=0.2
    → biome = "mountain_tundra"
    → part_of_cluster = "Sclerite Ridge"

Сектор [102, 50]: elevation=0.91, temp=-8°C, moisture=0.1
    → biome = "high_peaks"
    → part_of_cluster = "Sclerite Ridge"

... (непрерывная цепь горных хексов) ...

Сектор [120, 60]: elevation=0.82, temp=-4°C, moisture=0.3
    → biome = "mountain_tundra"
    → poi_type = "kith_settlement" (деревня в горах)
    → part_of_cluster = "Sclerite Ridge"
```

**Преимущества:**
- ✅ Горы = непрерывная цепь высоких хексов
- ✅ Естественные формы (из Perlin noise)
- ✅ Можно проложить маршрут вдоль хребта
- ✅ AI: "Склеритовый хребет тянется с юга на север"
- ✅ Деревня логично расположена в седловине между пиками

---

## 🔧 Технические детали

### Структуры данных

**Создать файл:** `models/global_map.py`

```python
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json
import gzip

@dataclass
class GlobalSector:
    """Атомарная единица глобальной карты"""
    coord: HexCoord

    # Физические свойства (генерируются из seed, не меняются)
    elevation: float        # 0.0 (глубокий океан) - 1.0 (высокая гора)
    temperature: float      # -50°C - +50°C
    moisture: float         # 0.0 (пустыня) - 1.0 (болото)
    biome_type: str        # "plains", "forest", "mountains", etc.
    has_river: bool = False
    is_river_navigable: bool = False

    # Динамические свойства (меняются во время игры)
    poi_type: Optional[str] = None       # "village", "dungeon", None
    poi_name: Optional[str] = None       # "Речная Долина", etc.
    faction_id: Optional[str] = None     # Кто контролирует территорию
    is_burned: bool = False              # Последствие пожара
    is_explored: bool = False            # Fog of war

    # Мета-информация (для UI/нарратива)
    cluster_id: Optional[str] = None     # "Sclerite_Ridge_001"
    tags: List[str] = field(default_factory=list)  # ["dangerous", "sacred"]

    def to_dict(self) -> dict:
        return {
            "coord": self.coord.to_tuple(),
            "elevation": self.elevation,
            "temperature": self.temperature,
            "moisture": self.moisture,
            "biome_type": self.biome_type,
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
        data['coord'] = HexCoord.from_tuple(data['coord'])
        return cls(**data)


@dataclass
class GlobalMapData:
    """Полная глобальная карта мира"""
    seed: str
    width: int
    height: int
    sectors: Dict[Tuple[int, int], GlobalSector]  # {(q, r): sector}
    generation_timestamp: datetime

    # Кэши для производительности
    _path_cache: Dict[Tuple[HexCoord, HexCoord], List[HexCoord]] = field(default_factory=dict, repr=False)
    _cluster_cache: Dict[str, List[HexCoord]] = field(default_factory=dict, repr=False)

    def get_sector(self, q: int, r: int) -> Optional[GlobalSector]:
        """Получить сектор по координатам"""
        return self.sectors.get((q, r))

    def get_neighbors(self, sector: GlobalSector) -> List[GlobalSector]:
        """Получить соседние сектора"""
        neighbors = []
        for neighbor_coord in sector.coord.neighbors():
            neighbor = self.get_sector(neighbor_coord.q, neighbor_coord.r)
            if neighbor:
                neighbors.append(neighbor)
        return neighbors

    def is_passable(self, sector: GlobalSector) -> bool:
        """Проверить, можно ли пройти через сектор"""
        if sector.biome_type == 'ocean':
            return False  # Пока нет кораблей
        if sector.elevation > 0.95:
            return False  # Слишком высокие горы
        return True

    def find_path(self, start: HexCoord, end: HexCoord) -> Optional[List[HexCoord]]:
        """A* pathfinding с кэшированием"""
        cache_key = (start, end)
        if cache_key in self._path_cache:
            return self._path_cache[cache_key]

        path = self._a_star_pathfinding(start, end)

        # Кэшируем только если кэш не переполнен
        if len(self._path_cache) < 1000:
            self._path_cache[cache_key] = path

        return path

    def _a_star_pathfinding(self, start: HexCoord, end: HexCoord) -> Optional[List[HexCoord]]:
        """Реализация A* (детали в Sprint 2)"""
        # TODO: Реализовать в Sprint 2
        pass

    def find_sectors_by_biome(self, biome_type: str) -> List[GlobalSector]:
        """Найти все сектора определённого биома"""
        return [s for s in self.sectors.values() if s.biome_type == biome_type]

    def find_biome_clusters(self, biome_type: str) -> List[List[HexCoord]]:
        """Найти связные кластеры биома (для определения регионов)"""
        cache_key = f"cluster_{biome_type}"
        if cache_key in self._cluster_cache:
            return self._cluster_cache[cache_key]

        # Flood fill для поиска кластеров
        clusters = self._flood_fill_clusters(biome_type)
        self._cluster_cache[cache_key] = clusters
        return clusters

    def _flood_fill_clusters(self, biome_type: str) -> List[List[HexCoord]]:
        """Flood fill для поиска связных областей (детали в Sprint 3)"""
        # TODO: Реализовать в Sprint 3
        pass

    def to_json(self, compress: bool = True) -> bytes:
        """Сохранить в JSON (с опциональным сжатием)"""
        data = {
            "seed": self.seed,
            "width": self.width,
            "height": self.height,
            "generation_timestamp": self.generation_timestamp.isoformat(),
            "sectors": [s.to_dict() for s in self.sectors.values()]
        }

        json_str = json.dumps(data, indent=2)

        if compress:
            return gzip.compress(json_str.encode('utf-8'))
        else:
            return json_str.encode('utf-8')

    @classmethod
    def from_json(cls, data: bytes, compressed: bool = True) -> 'GlobalMapData':
        """Загрузить из JSON"""
        if compressed:
            data = gzip.decompress(data)

        json_data = json.loads(data.decode('utf-8'))

        sectors = {}
        for sector_data in json_data['sectors']:
            sector = GlobalSector.from_dict(sector_data)
            sectors[(sector.coord.q, sector.coord.r)] = sector

        return cls(
            seed=json_data['seed'],
            width=json_data['width'],
            height=json_data['height'],
            sectors=sectors,
            generation_timestamp=datetime.fromisoformat(json_data['generation_timestamp'])
        )

    def save(self, filepath: str):
        """Сохранить в файл"""
        compressed_data = self.to_json(compress=True)
        with open(filepath, 'wb') as f:
            f.write(compressed_data)
        print(f"✅ Мир сохранён: {filepath} ({len(compressed_data) / 1024:.1f} KB)")

    @classmethod
    def load(cls, filepath: str) -> 'GlobalMapData':
        """Загрузить из файла"""
        with open(filepath, 'rb') as f:
            compressed_data = f.read()
        print(f"✅ Мир загружен: {filepath} ({len(compressed_data) / 1024:.1f} KB)")
        return cls.from_json(compressed_data, compressed=True)


@dataclass
class DeltaTracker:
    """Отслеживает изменения от исходного состояния мира"""
    changes: Dict[Tuple[int, int], Dict[str, any]] = field(default_factory=dict)

    def mark_changed(self, sector: GlobalSector, field: str, new_value):
        """Зафиксировать изменение поля сектора"""
        coord_key = (sector.coord.q, sector.coord.r)

        if coord_key not in self.changes:
            self.changes[coord_key] = {}

        self.changes[coord_key][field] = new_value

    def apply_to(self, map_data: GlobalMapData) -> GlobalMapData:
        """Применить изменения к карте"""
        for (q, r), fields in self.changes.items():
            sector = map_data.get_sector(q, r)
            if sector:
                for field, value in fields.items():
                    setattr(sector, field, value)

        return map_data

    def to_json(self, compress: bool = True) -> bytes:
        """Сохранить delta в JSON"""
        # Конвертируем tuple keys в строки для JSON
        serializable_changes = {
            f"{q},{r}": fields
            for (q, r), fields in self.changes.items()
        }

        json_str = json.dumps(serializable_changes, indent=2)

        if compress:
            return gzip.compress(json_str.encode('utf-8'))
        else:
            return json_str.encode('utf-8')

    @classmethod
    def from_json(cls, data: bytes, compressed: bool = True) -> 'DeltaTracker':
        """Загрузить delta из JSON"""
        if compressed:
            data = gzip.decompress(data)

        json_data = json.loads(data.decode('utf-8'))

        # Конвертируем строковые keys обратно в tuples
        changes = {}
        for coord_str, fields in json_data.items():
            q, r = map(int, coord_str.split(','))
            changes[(q, r)] = fields

        return cls(changes=changes)

    def save(self, filepath: str):
        """Сохранить delta в файл"""
        compressed_data = self.to_json(compress=True)
        with open(filepath, 'wb') as f:
            f.write(compressed_data)
        print(f"✅ Delta сохранена: {filepath} ({len(compressed_data) / 1024:.1f} KB)")

    @classmethod
    def load(cls, filepath: str) -> 'DeltaTracker':
        """Загрузить delta из файла"""
        with open(filepath, 'rb') as f:
            compressed_data = f.read()
        return cls.from_json(compressed_data, compressed=True)
```

---

## 🔮 Долгосрочная перспектива

### После Sprint 2-3 (глобальная карта готова)

Откроются новые возможности для AI-нарратора:

#### 1. События распространяются естественно

```python
# Пример: Лесной пожар
fire_origin = sector[100, 50]
fire_origin.is_burned = True

# Распространение на соседей (с вероятностью)
for neighbor in fire_origin.neighbors():
    if neighbor.biome_type == "forest" and random() < 0.6:
        neighbor.is_burned = True
        # Рекурсивно распространяется дальше
```

**AI может описать:**
> "Дым лесного пожара виден на горизонте. Ветер дует в вашу сторону - пламя распространяется на восток."

#### 2. Миграция животных

```python
# Стадо оленей мигрирует вдоль границы леса и равнин
deer_herd_path = find_biome_border("forest", "plains")
```

**AI может создать событие:**
> "Вдалеке вы видите мигрирующее стадо оленей, движущееся на юг вдоль опушки леса."

#### 3. Караванные маршруты

```python
# Торговый караван из деревни A в деревню B
route = global_map.find_path(village_a, village_b)
```

**AI может создать случайную встречу:**
> "На дороге вы встречаете караван торговцев, везущих шелк из Речной Долины в Горное Поселение."

#### 4. Распространение эпидемий

```python
# Чума начинается в порту
plague_origin = coastal_village
infected_settlements = spread_disease(
    origin=plague_origin,
    transmission_rate=0.3,
    via_trade_routes=True
)
```

**AI может генерировать нарратив:**
> "В городе объявлен карантин из-за чумы, пришедшей с кораблями с побережья. Торговцы боятся въезжать."

#### 5. Территориальные конфликты

```python
# Две фракции имеют общую границу
border_sectors = find_border("kingdom_A", "kingdom_B")
```

**AI может генерировать приграничные конфликты:**
> "Патруль Королевства Когтей останавливает вас на границе. Напряжение между королевствами растёт после недавней стычки."

---

## 📚 Дополнительные материалы для изучения

### Перед началом Sprint 2 рекомендуется изучить:

#### 1. Perlin/Simplex Noise

**Учебный ресурс:**
- https://thebookofshaders.com/11/

**Библиотека:**
- https://pypi.org/project/noise/

**Пример кода:**
```python
from noise import pnoise2

for y in range(height):
    for x in range(width):
        elevation = pnoise2(
            x / scale,
            y / scale,
            octaves=4,
            persistence=0.5,
            lacunarity=2.0,
            base=seed
        )
```

#### 2. Flow Accumulation (для рек)

**Алгоритм D8 (8 направлений стока):**
- https://en.wikipedia.org/wiki/D8_algorithm

**Псевдокод:**
```
1. Отсортировать все сектора по убыванию высоты
2. Для каждого сектора:
   - Найти самого низкого соседа
   - Направить поток к нему
   - Накопить flow
3. Сектора с flow > threshold = реки
```

#### 3. Hex Grid Math

**Cube coordinates (используем в проекте):**
- https://www.redblobgames.com/grids/hexagons/

**Полезные функции:**
- `hex_distance(a, b)`
- `hex_neighbors(coord)`
- `hex_to_pixel(q, r)`

#### 4. A* Pathfinding

**Для караванов и миграции:**
- https://www.redblobgames.com/pathfinding/a-star/

**С учётом стоимости terrain:**
```python
terrain_costs = {
    "plains": 1.0,
    "forest": 1.5,
    "mountains": 2.0,
    "river_crossing": 1.5
}
```

---

## 🎨 Визуализация: До vs После

### ДО (Старая система) - УДАЛЯЕМ

```
КОНТИНЕНТ "Торакс"
    ↓
РЕГИОН "Склеритовый хребет" (абстрактный контейнер)
    ↓
БИОМЫ внутри региона:
    - Кит Поселение (в центре)
    - Горная тундра (случайное место)
    - Альвеольные пещеры (случайное место)
    - Лимфатическая долина (случайное место)

Проблемы:
❌ "Горы" не выглядят как горы (просто узлы графа)
❌ Нет естественных форм
❌ Невозможно проложить маршрут
❌ AI не может описать "хребет тянется на север"
```

### ПОСЛЕ (Новая система) - РЕАЛИЗУЕМ

```
ГЛОБАЛЬНАЯ КАРТА 256x256
    ↓
Сектор [100, 50]: elevation=0.85, temp=-5°C, moisture=0.2
    → biome = "mountain_tundra"
    → part_of_cluster = "Sclerite Ridge" (мета-информация)

Сектор [101, 50]: elevation=0.87, temp=-6°C, moisture=0.2
    → biome = "mountain_tundra"
    → part_of_cluster = "Sclerite Ridge"

Сектор [102, 50]: elevation=0.91, temp=-8°C, moisture=0.1
    → biome = "high_peaks"
    → part_of_cluster = "Sclerite Ridge"

... (непрерывная цепь горных хексов) ...

Сектор [120, 60]: elevation=0.82, temp=-4°C, moisture=0.3
    → biome = "mountain_tundra"
    → poi_type = "kith_settlement" (деревня в горах)
    → part_of_cluster = "Sclerite Ridge"

Преимущества:
✅ Горы = непрерывная цепь высоких хексов
✅ Естественные формы (из Perlin noise)
✅ Можно проложить маршрут вдоль хребта
✅ AI: "Склеритовый хребет тянется с юга на север"
✅ Деревня логично расположена в седловине между пиками
```

---

## 🎯 Финальный чеклист

### Перед началом работы:

- [ ] Sprint 1 завершён (или близок к завершению)
- [ ] Понято новое архитектурное видение
- [ ] Прочитаны примеры из этого документа
- [ ] Есть ~40 часов для Sprint 2-3

### Документы для создания/обновления:

#### Приоритет 1 (Critical)

- [x] `docs/GLOBAL_MAP_IMPLEMENTATION_GUIDE.md` - этот документ ✅
- [x] `docs/architecture_decision.md` - добавить ADR-011, ADR-012, ADR-013 ✅
- [x] `docs/Technical_Design_Document.md` - уже обновлён ✅

#### Приоритет 2 (High)

- [ ] `docs/sprints/SPRINT_3.5_PLAN.md` - детальный план Sprint 2-3
- [ ] `models/global_map.py` - создать структуры данных
- [ ] `core/world_generator.py` - seed-based генератор

#### Приоритет 3 (Medium)

- [ ] `services/poi_placement_service.py` - размещение POI
- [ ] `services/delta_tracker.py` - отслеживание изменений
- [ ] Рефакторинг `HexWorldService` (удалить legacy методы)

#### Приоритет 4 (Post-Sprint 3 - Расширения)

- [ ] **Narrative Anchors**: Дополнить `GlobalSector` нарративными тегами
- [ ] **Meta Regions**: Создать систему именованных регионов
- [ ] **Path System**: Реализовать генерацию путей между POI (`services/path_generator.py`)
- [ ] **World Events**: Создать `models/world_events.py` и обновить `DeltaTracker`

### Что удалить СРАЗУ (не откладывать):

```bash
# Удалить deprecated методы из HexWorldService
# services/hex_world_service.py

class HexWorldService:
    # ❌ УДАЛИТЬ
    def generate_continent(self, continent_id: str, radius: int):
        pass

    # ❌ УДАЛИТЬ
    def _generate_local_biome_layout(self, count: int) -> List[HexCoord]:
        pass
```

```bash
# Удалить модель RegionData (если есть отдельный файл)
# models/region_data.py - УДАЛИТЬ ВЕСЬ ФАЙЛ

# Или удалить класс из существующего файла
@dataclass
class RegionData:  # ❌ УДАЛИТЬ ВЕСЬ КЛАСС
    id: str
    biome_ids: List[str]
    parent_region_id: str
```

```bash
# Удалить старые файлы сохранений (если есть)
rm -rf saves/*.json  # Старые сохранения больше не нужны
```

### После завершения Sprint 2-3:

- [ ] Создать коммит: `feat: Implement global map 256x256 with seed-based generation`
- [ ] Написать ретроспективу Sprint 2-3
- [ ] Обновить прогресс в `docs/sprints/DONE.md`
- [ ] Начать Sprint 4 или 2 (Function Calling)

---

## 🚀 Расширенные возможности (Post-Sprint 3)

### Введение

После реализации базовой системы Global Map (Sprint 2-3), открываются возможности для создания по-настоящему живого мира с глубоким AI-нарративом. Ниже представлены четыре ключевых расширения системы, которые превратят карту из набора гексов в осмысленный мир с историей.

---

### 1. Нарративные Якоря (Narrative Anchors)

#### Проблема
`GlobalSector` содержит числовые данные (`elevation: 0.85`, `temperature: -5.0`). LLM может испытывать трудности с прямой интерпретацией этих цифр для генерации богатого описания. Ей проще работать с готовыми концептами.

#### Решение
Добавить слой "Нарративных Якорей" — предварительно сгенерированных тегов и описательных фраз, которые напрямую подаются AI.

#### Реализация

**Дополнить структуру `GlobalSector`:**

```python
@dataclass
class GlobalSector:
    # ... существующие поля (elevation, temperature, etc.)

    # НОВЫЕ ПОЛЯ: Нарративные Якоря
    # Генерируются один раз вместе с биомом
    narrative_tags: List[str] = field(default_factory=list)
    # Пример: ["high-altitude", "bitter-wind", "sparse-vegetation", "rocky-ground"]

    ambient_sound: Optional[str] = None  # "howling-wind", "bird-song", "river-flow"
    visibility: str = "clear"  # "clear", "foggy", "snow-storm"

    def get_narrative_context(self) -> str:
        """Генерирует краткую сводку для LLM"""
        tags_str = ", ".join(self.narrative_tags)
        return (f"Местность: {self.biome_type}. "
                f"Ключевые особенности: {tags_str}. "
                f"Высота над уровнем моря: {self.get_elevation_description()}. "
                f"Окружающие звуки: {self.ambient_sound}. "
                f"Видимость: {self.visibility}. "
                f"Реки: {'есть' if self.has_river else 'нет'}.")

    def get_elevation_description(self) -> str:
        """Человекочитаемое описание высоты"""
        if self.elevation > 0.9: return "высокогорный пик"
        elif self.elevation > 0.7: return "горы"
        elif self.elevation > 0.55: return "холмистая местность"
        elif self.elevation > 0.45: return "равнина"
        elif self.elevation > 0.3: return "низина"
        else: return "впадина или долина"

    def get_temperature_description(self) -> str:
        """Человекочитаемое описание температуры"""
        if self.temperature < -20: return "леденящий холод"
        elif self.temperature < 0: return "холодно"
        elif self.temperature < 15: return "прохладно"
        elif self.temperature < 25: return "тепло"
        else: return "жарко"
```

**Процесс генерации якорей:**

```python
# core/world_generator.py
class WorldGenerator:
    def _assign_narrative_tags(self, sector: GlobalSector):
        """Генерирует нарративные якоря на основе физических свойств"""
        tags = []

        # Высота
        if sector.elevation > 0.8:
            tags.extend(["high-altitude", "rocky-ground", "thin-air"])
        elif sector.elevation < 0.35:
            tags.extend(["low-lying", "sheltered"])

        # Температура
        if sector.temperature < -10:
            tags.extend(["freezing", "bitter-wind", "frost-covered"])
        elif sector.temperature > 30:
            tags.extend(["scorching", "heat-shimmer", "dry-air"])

        # Влажность
        if sector.moisture > 0.7:
            tags.extend(["damp", "moss-covered", "humid"])
        elif sector.moisture < 0.3:
            tags.extend(["arid", "cracked-earth", "dust"])

        # Биом-специфичные теги
        if sector.biome_type == "forest":
            tags.extend(["dense-canopy", "bird-song", "rustling-leaves"])
        elif sector.biome_type == "mountains":
            tags.extend(["jagged-peaks", "echoing-valleys", "avalanche-prone"])
        elif sector.biome_type == "desert":
            tags.extend(["sand-dunes", "shimmering-heat", "endless-horizon"])

        sector.narrative_tags = tags

        # Окружающие звуки
        if sector.has_river:
            sector.ambient_sound = "river-flow"
        elif sector.biome_type == "forest":
            sector.ambient_sound = "bird-song"
        elif sector.elevation > 0.8:
            sector.ambient_sound = "howling-wind"
        else:
            sector.ambient_sound = "silence"
```

**Использование в промптах:**

```python
# Пример использования для генерации описания
def generate_location_description(sector: GlobalSector) -> str:
    narrative_context = sector.get_narrative_context()

    prompt = f"""
    Ты - мастер игры в текстовой RPG. Опиши локацию игрока.

    Контекст местности:
    {narrative_context}

    Создай атмосферное описание (2-3 предложения), используя эти детали.
    """

    return llm_service.generate(prompt)
```

**Преимущества:**
- ✅ **AI-Friendly**: LLM получает готовые концепты вместо цифр
- ✅ **Консистентность**: Одинаковые описания для одного и того же места
- ✅ **Богатство**: AI может комбинировать якоря для разнообразных описаний
- ✅ **Performance**: Якоря генерируются один раз при создании мира

---

### 2. Мета-Регионы и Именованные Кластеры

#### Проблема
`cluster_id: "Sclerite_Ridge_001"` — это хорошо, но ID сам по себе не несет нарративной нагрузки. Как AI узнает, что это "Склеритовый Хребет", а не "Великая Равнина"?

#### Решение
Ввести сущность `MetaRegion` — именованный географический объект с нарративным контекстом.

#### Реализация

**Создать новую структуру:**

```python
# models/global_map.py

@dataclass
class MetaRegion:
    """Именованный географический регион (горная цепь, лес, пустыня)"""
    id: str  # "sclerite_ridge_001"
    name: str  # "Склеритовый Хребет"
    region_type: str  # "mountain_chain", "great_forest", "desert", "river_basin"
    hex_coords: Set[Tuple[int, int]]  # Все хексы в регионе

    # Нарративная информация
    description: str  # "Великая горная цепь, простирающаяся с севера на юг"
    notable_features: List[str]  # ["highest_peak_in_world", "ancient_ruins"]
    faction_control: Optional[str] = None  # Кто контролирует регион
    danger_level: int = 1  # 1-10

    # Статистика (для AI)
    size_km2: float = 0.0  # Площадь региона
    avg_elevation: float = 0.0
    dominant_biome: str = ""

    def get_narrative_summary(self) -> str:
        """Краткое описание для AI"""
        features_str = ", ".join(self.notable_features) if self.notable_features else "нет особых примет"
        control = f"Контролируется фракцией {self.faction_control}" if self.faction_control else "Нейтральная территория"

        return (f"{self.name} — {self.description}. "
                f"Тип: {self.region_type}. "
                f"Особенности: {features_str}. "
                f"{control}. "
                f"Уровень опасности: {self.danger_level}/10.")

    def contains_coord(self, q: int, r: int) -> bool:
        """Проверяет, входит ли координата в регион"""
        return (q, r) in self.hex_coords
```

**Дополнить `GlobalMapData`:**

```python
@dataclass
class GlobalMapData:
    # ... существующие поля
    meta_regions: Dict[str, MetaRegion] = field(default_factory=dict)

    def get_region_at(self, q: int, r: int) -> Optional[MetaRegion]:
        """Найти мета-регион по координатам"""
        for region in self.meta_regions.values():
            if region.contains_coord(q, r):
                return region
        return None

    def get_regions_by_type(self, region_type: str) -> List[MetaRegion]:
        """Найти все регионы определенного типа"""
        return [r for r in self.meta_regions.values() if r.region_type == region_type]
```

**Процесс генерации (финальный шаг в `WorldGenerator`):**

```python
# core/world_generator.py

class WorldGenerator:
    def generate_meta_regions(self, global_map: GlobalMapData):
        """Определяет и именует крупные географические регионы"""
        print("Поиск мета-регионов...")

        # 1. Находим кластеры каждого биома (flood fill)
        for biome_type in ["mountains", "forest", "desert", "plains"]:
            clusters = self._find_biome_clusters(global_map, biome_type)

            # 2. Для каждого достаточно крупного кластера создаем MetaRegion
            for i, cluster_coords in enumerate(clusters):
                if len(cluster_coords) < 20:  # Игнорируем мелкие кластеры
                    continue

                # Генерируем имя на основе seed и типа биома
                region_name = self._generate_region_name(biome_type, i)

                # Вычисляем статистику
                avg_elevation = np.mean([global_map.get_sector(*c).elevation
                                       for c in cluster_coords])
                size_km2 = len(cluster_coords) * 1.0  # Каждый гекс = 1 км²

                # Создаем объект MetaRegion
                meta_region = MetaRegion(
                    id=f"{biome_type}_{i:03d}",
                    name=region_name,
                    region_type=self._get_region_type(biome_type),
                    hex_coords=set(cluster_coords),
                    description=self._generate_region_description(biome_type, region_name),
                    notable_features=[],  # TODO: процедурная генерация
                    size_km2=size_km2,
                    avg_elevation=avg_elevation,
                    dominant_biome=biome_type,
                    danger_level=self._calculate_danger_level(biome_type, avg_elevation)
                )

                global_map.meta_regions[meta_region.id] = meta_region

                # 3. Записываем cluster_id в каждый гекс
                for q, r in cluster_coords:
                    sector = global_map.get_sector(q, r)
                    if sector:
                        sector.cluster_id = meta_region.id

        print(f"✅ Создано {len(global_map.meta_regions)} мета-регионов")

    def _generate_region_name(self, biome_type: str, index: int) -> str:
        """Процедурная генерация имени региона"""
        # Используем seed для детерминированной генерации
        rng = np.random.default_rng(hash((self.seed, biome_type, index)))

        # Словари для генерации имен (можно расширить)
        prefixes = {
            "mountains": ["Склеритовый", "Костяной", "Железный", "Драконий"],
            "forest": ["Лимфатический", "Спящий", "Древний", "Шепчущий"],
            "desert": ["Огненная", "Мертвая", "Забытая", "Кровавая"]
        }

        suffixes = {
            "mountains": ["Хребет", "Пики", "Горы", "Массив"],
            "forest": ["Лес", "Чаща", "Роща", "Дебри"],
            "desert": ["Пустыня", "Пески", "Пустошь", "Бесплодье"]
        }

        prefix = rng.choice(prefixes.get(biome_type, ["Неизвестный"]))
        suffix = rng.choice(suffixes.get(biome_type, ["Регион"]))

        return f"{prefix} {suffix}"
```

**Использование в игре:**

```python
# Пример: квест, привязанный к мета-региону
def generate_quest_find_artifact():
    # Выбираем случайный мета-регион типа "ancient_forest"
    ancient_forests = global_map.get_regions_by_type("great_forest")
    target_region = random.choice(ancient_forests)

    quest_description = f"""
    Древний артефакт скрыт где-то в {target_region.name}.
    {target_region.get_narrative_summary()}

    Найдите артефакт и принесите его мне.
    """

    # Игра может подсветить весь регион на карте!
    return Quest(
        title=f"Поиски в {target_region.name}",
        description=quest_description,
        target_region_id=target_region.id
    )
```

**Преимущества:**
- ✅ **Географическая осознанность**: AI может ссылаться на именованные регионы
- ✅ **Улучшение квестов**: "Найти что-то в Лесу Забвения" вместо "в хексе [50, 100]"
- ✅ **Узнаваемость**: Мир становится набором запоминающихся мест
- ✅ **Стратегия**: Фракции могут контролировать целые регионы

---

### 3. Система Путей и Маршрутов (Path System)

#### Проблема
A* pathfinding находит кратчайший путь. Но в реальном мире существуют дороги, торговые тракты, миграционные тропы — пути с историей и контекстом.

#### Решение
После размещения POI генерировать "именованные пути" между ключевыми точками как полноценные объекты.

#### Реализация

**Создать структуру `Path`:**

```python
# models/global_map.py

@dataclass
class Path:
    """Именованный путь между двумя точками"""
    id: str
    name: str  # "Королевский Тракт", "Соляной Путь", "Тропа Мигрантов"
    path_type: str  # "trade_route", "patrol_route", "migration_trail", "pilgrimage"

    # Начало и конец пути
    start_poi_id: str
    end_poi_id: str

    # Гексы, через которые проходит путь (упорядоченные)
    hex_coords: List[Tuple[int, int]]

    # Игровые параметры
    danger_level: int = 1  # 1-10
    travel_speed_modifier: float = 1.5  # Путешествие по дороге быстрее
    patrol_frequency: float = 0.3  # Вероятность встретить патруль
    random_encounter_table_id: Optional[str] = None

    # Нарративная информация
    description: str = ""
    notable_landmarks: List[str] = field(default_factory=list)
    # ["old_bridge", "abandoned_watchtower", "merchant_inn"]

    # Динамическое состояние
    is_blocked: bool = False  # Заблокирован (обвал, набег)
    condition: float = 1.0  # 0.0 (разрушен) - 1.0 (отличное состояние)

    def get_travel_time_days(self) -> float:
        """Время в пути в днях"""
        base_time = len(self.hex_coords) * 0.1  # 0.1 дня на гекс
        return base_time / self.travel_speed_modifier

    def get_narrative_summary(self) -> str:
        condition_str = "в отличном состоянии" if self.condition > 0.8 else "в плохом состоянии"
        blocked_str = " (ПЕРЕКРЫТ!)" if self.is_blocked else ""

        return (f"{self.name} ({self.path_type}) — {self.description}. "
                f"Состояние: {condition_str}{blocked_str}. "
                f"Время в пути: {self.get_travel_time_days():.1f} дней. "
                f"Опасность: {self.danger_level}/10.")
```

**Дополнить `GlobalMapData`:**

```python
@dataclass
class GlobalMapData:
    # ...
    paths: Dict[str, Path] = field(default_factory=dict)

    def get_path_at_coord(self, q: int, r: int) -> Optional[Path]:
        """Найти путь, проходящий через координату"""
        for path in self.paths.values():
            if (q, r) in path.hex_coords:
                return path
        return None

    def get_paths_between(self, start_poi: str, end_poi: str) -> List[Path]:
        """Найти все пути между двумя POI"""
        return [p for p in self.paths.values()
                if (p.start_poi_id == start_poi and p.end_poi_id == end_poi) or
                   (p.start_poi_id == end_poi and p.end_poi_id == start_poi)]
```

**Процесс генерации (конец Sprint 3, после размещения POI):**

```python
# services/path_generator.py (НОВЫЙ ФАЙЛ)

class PathGenerator:
    def __init__(self, world_gen: WorldGenerator):
        self.world_gen = world_gen

    def generate_paths(self, global_map: GlobalMapData):
        """Генерирует пути между POI"""
        print("Генерация путей...")

        # 1. Найти все POI типа "village", "city", "fortress"
        settlements = [s for s in global_map.sectors.values()
                      if s.poi_type in ["village", "city", "fortress"]]

        path_count = 0

        # 2. Для пар поселений в пределах MAX_DISTANCE создать пути
        MAX_DISTANCE = 50  # гексов
        for i, poi_a in enumerate(settlements):
            for poi_b in settlements[i+1:]:
                distance = hex_distance(poi_a.coord, poi_b.coord)

                if distance > MAX_DISTANCE:
                    continue  # Слишком далеко

                # 3. Проложить A* pathfinding
                raw_path = global_map.find_path(poi_a.coord, poi_b.coord)

                if not raw_path:
                    continue  # Нет пути

                # 4. "Искривить" путь для естественности
                smoothed_path = self._smooth_path(raw_path, global_map)

                # 5. Определить тип пути
                path_type = self._determine_path_type(poi_a, poi_b)

                # 6. Сгенерировать имя
                path_name = self._generate_path_name(poi_a, poi_b, path_type)

                # 7. Создать объект Path
                path = Path(
                    id=f"path_{path_count:04d}",
                    name=path_name,
                    path_type=path_type,
                    start_poi_id=poi_a.id,
                    end_poi_id=poi_b.id,
                    hex_coords=[(c.q, c.r) for c in smoothed_path],
                    description=self._generate_path_description(path_type),
                    danger_level=self._calculate_path_danger(smoothed_path, global_map),
                    travel_speed_modifier=1.5 if path_type == "trade_route" else 1.2
                )

                global_map.paths[path.id] = path
                path_count += 1

        print(f"✅ Создано {path_count} путей")

    def _smooth_path(self, raw_path: List[HexCoord], global_map: GlobalMapData) -> List[HexCoord]:
        """Делает путь более естественным (следует вдоль рек, по долинам)"""
        # TODO: Реализовать алгоритм сглаживания
        # Идея: если путь проходит через горы, попробовать найти проход между пиками
        return raw_path

    def _determine_path_type(self, poi_a: GlobalSector, poi_b: GlobalSector) -> str:
        """Определяет тип пути на основе POI"""
        if poi_a.poi_type == "city" or poi_b.poi_type == "city":
            return "trade_route"
        elif poi_a.poi_type == "fortress" or poi_b.poi_type == "fortress":
            return "patrol_route"
        else:
            return "village_trail"

    def _generate_path_name(self, poi_a: GlobalSector, poi_b: GlobalSector, path_type: str) -> str:
        """Генерирует имя пути"""
        if path_type == "trade_route":
            return f"Торговый путь {poi_a.poi_name} — {poi_b.poi_name}"
        elif path_type == "patrol_route":
            return f"Патрульный маршрут {poi_a.poi_name}"
        else:
            return f"Тропа между {poi_a.poi_name} и {poi_b.poi_name}"
```

**Использование в игре:**

```python
# Пример: случайная встреча на дороге
def check_random_encounter(player_coord: HexCoord, global_map: GlobalMapData):
    # Проверяем, находится ли игрок на каком-то пути
    path = global_map.get_path_at_coord(player_coord.q, player_coord.r)

    if not path:
        return None  # Игрок не на дороге, обычная встреча

    # На дороге встречи более вероятны и специфичны
    if random.random() < path.patrol_frequency:
        if path.path_type == "trade_route":
            return generate_caravan_encounter(path)
        elif path.path_type == "patrol_route":
            return generate_patrol_encounter(path)

    return None
```

**Преимущества:**
- ✅ **Живой мир**: Караваны движутся по реальным путям
- ✅ **Стратегия**: Быстрее по дороге, но она может быть перекрыта
- ✅ **Логичные события**: Бандиты на торговых путях, патрули на военных маршрутах
- ✅ **Нарратив**: "Вы идете по древнему Королевскому Тракту..."

---

### 4. Система Мировых Событий (World Event System)

#### Проблема
`DeltaTracker` фиксирует изменения (`is_burned: true`), но не хранит *причину*. Пожар от игрока и пожар от молнии — разные события с разными нарративными последствиями.

#### Решение
Сохранять не конечные изменения, а список объектов `WorldEvent`, которые привели к ним.

#### Реализация

**Создать структуру `WorldEvent`:**

```python
# models/world_events.py (НОВЫЙ ФАЙЛ)

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Tuple

@dataclass
class WorldEvent:
    """Событие, изменившее состояние мира"""
    id: str
    event_type: str  # "ForestFire", "PlagueSpread", "BanditRaid", "PlayerAction"
    timestamp: datetime
    turn_number: int  # Номер хода, когда событие произошло

    # География
    origin_coord: Tuple[int, int]  # Где началось событие
    affected_coords: List[Tuple[int, int]] = field(default_factory=list)  # Куда распространилось

    # Параметры события (специфичны для каждого типа)
    params: Dict[str, Any] = field(default_factory=dict)
    # Например: {"cause": "dragon_attack", "radius": 5, "intensity": 0.8}

    # Нарративная информация
    description: str = ""  # "Великий пожар, устроенный драконом Шкаром"
    witnesses: List[str] = field(default_factory=list)  # ID NPC, видевших событие

    # Последствия (для AI)
    consequences: List[str] = field(default_factory=list)
    # ["forest_destroyed", "village_evacuated", "trade_route_blocked"]

    def get_narrative_summary(self) -> str:
        """Краткое описание для AI"""
        affected_count = len(self.affected_coords)
        return (f"{self.description} "
                f"(тип: {self.event_type}, "
                f"затронуто гексов: {affected_count}). "
                f"Последствия: {', '.join(self.consequences)}.")


# Специфичные типы событий

@dataclass
class ForestFireEvent(WorldEvent):
    """Лесной пожар"""
    event_type: str = "ForestFire"
    intensity: float = 0.5  # 0.0-1.0
    spread_rate: float = 0.6  # Вероятность распространения на соседей

    def apply(self, global_map: 'GlobalMapData'):
        """Применяет последствия пожара к карте"""
        # Помечаем все затронутые гексы как сгоревшие
        for q, r in self.affected_coords:
            sector = global_map.get_sector(q, r)
            if sector and sector.biome_type in ["forest", "plains"]:
                sector.is_burned = True
                sector.narrative_tags.append("fire-scarred")


@dataclass
class PlagueEvent(WorldEvent):
    """Эпидемия"""
    event_type: str = "Plague"
    disease_type: str = "unknown"  # "cholera", "black_death"
    transmission_rate: float = 0.3
    mortality_rate: float = 0.4

    def apply(self, global_map: 'GlobalMapData'):
        """Применяет последствия эпидемии"""
        for q, r in self.affected_coords:
            sector = global_map.get_sector(q, r)
            if sector and sector.poi_type in ["village", "city"]:
                sector.tags.append("plague-stricken")
                # TODO: Уменьшить население в POI


@dataclass
class TerritorialConflictEvent(WorldEvent):
    """Территориальный конфликт"""
    event_type: str = "TerritorialConflict"
    attacker_faction: str
    defender_faction: str
    victor: Optional[str] = None

    def apply(self, global_map: 'GlobalMapData'):
        """Меняет контроль над территорией"""
        if self.victor:
            for q, r in self.affected_coords:
                sector = global_map.get_sector(q, r)
                if sector:
                    sector.faction_id = self.victor
```

**Обновить `DeltaTracker`:**

```python
# models/global_map.py

@dataclass
class DeltaTracker:
    """Отслеживает изменения через систему событий"""
    events: List[WorldEvent] = field(default_factory=list)
    next_event_id: int = 0

    def add_event(self, event: WorldEvent):
        """Добавляет событие в историю мира"""
        if not event.id:
            event.id = f"event_{self.next_event_id:06d}"
            self.next_event_id += 1

        self.events.append(event)
        print(f"[WorldEvent] {event.get_narrative_summary()}")

    def apply_to(self, map_data: GlobalMapData) -> GlobalMapData:
        """При загрузке "проигрываем" все события по очереди"""
        print(f"Применение {len(self.events)} мировых событий...")

        for event in self.events:
            # Каждое событие знает, как себя применить
            event.apply(map_data)

        return map_data

    def get_events_at_coord(self, q: int, r: int) -> List[WorldEvent]:
        """Получить все события, затронувшие координату"""
        return [e for e in self.events if (q, r) in e.affected_coords]

    def get_events_by_type(self, event_type: str) -> List[WorldEvent]:
        """Получить все события определенного типа"""
        return [e for e in self.events if e.event_type == event_type]

    def get_recent_events(self, n: int = 10) -> List[WorldEvent]:
        """Получить N последних событий"""
        return sorted(self.events, key=lambda e: e.turn_number, reverse=True)[:n]
```

**Использование в игре:**

```python
# Пример 1: Игрок устраивает пожар
def player_sets_fire(coord: HexCoord, global_map: GlobalMapData, delta: DeltaTracker):
    # Создаем событие
    fire_event = ForestFireEvent(
        timestamp=datetime.now(),
        turn_number=game.current_turn,
        origin_coord=(coord.q, coord.r),
        description="Пожар, устроенный путешественником",
        params={"cause": "player_action", "intentional": True},
        intensity=0.8,
        spread_rate=0.6
    )

    # Симулируем распространение огня
    affected = simulate_fire_spread(coord, global_map, fire_event.spread_rate, radius=5)
    fire_event.affected_coords = [(c.q, c.r) for c in affected]
    fire_event.consequences = ["forest_destroyed", "wildlife_fled", "smoke_visible"]

    # Применяем событие
    fire_event.apply(global_map)

    # Сохраняем в историю
    delta.add_event(fire_event)


# Пример 2: AI использует историю для нарратива
def generate_location_description_with_history(sector: GlobalSector, delta: DeltaTracker):
    # Получаем события, затронувшие эту локацию
    local_events = delta.get_events_at_coord(sector.coord.q, sector.coord.r)

    # Строим контекст для AI
    history_context = ""
    if local_events:
        recent_event = local_events[-1]  # Последнее событие
        history_context = f"\nИстория этого места: {recent_event.description}"

    narrative_context = sector.get_narrative_context()

    prompt = f"""
    Опиши локацию игрока.

    Текущее состояние:
    {narrative_context}

    {history_context}

    Создай атмосферное описание, учитывая историю.
    """

    return llm_service.generate(prompt)
```

**Преимущества:**
- ✅ **Полная история мира**: Можно "отмотать" и увидеть развитие событий
- ✅ **Нарративная глубина**: AI знает *почему* лес сгорел, не только *что* он сгорел
- ✅ **Системный геймплей**: События запускают цепочки (набег → голод → миграция)
- ✅ **Debugging**: Легко отследить, какое событие вызвало изменение

---

## 💬 Заключение

Это **фундаментальное архитектурное изменение**, которое превращает игру из "текстового квеста с абстрактными локациями" в "живой мир с географией, которая определяет повествование".

### Ключевые преимущества:

**Для нарратива:**
- AI может создавать истории, связанные с географией
- События распространяются естественно
- Фракции имеют реальные территории и границы

**Для геймплея:**
- Осмысленное исследование (не телепортация между точками)
- Стратегическое планирование маршрутов
- Последствия действий видны на карте

**Для разработки:**
- Чистая, понятная архитектура
- Легко расширяемая (новые биомы, POI)
- Seed-based генерация упрощает отладку

### Цена изменений:

- ✅ 2-3 недели разработки (Sprint 2-3)
- ✅ Переработка части кодовой базы
- ✅ **БЕЗ** необходимости поддерживать legacy (игра в разработке!)

---

**Последнее обновление:** 20 октября 2025
**Автор:** Команда разработки Silgarron RPG
**Версия:** 1.0

**Следующие шаги:** Приступить к реализации `WorldGenerator` и `GlobalMapData`
