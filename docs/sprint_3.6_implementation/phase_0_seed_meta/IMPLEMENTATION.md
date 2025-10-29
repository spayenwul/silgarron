# Phase 0: Seed и Meta-параметры

**Статус:** ✅ Реализовано (Sprint 3.6)

## Задачи реализации

1. Инициализация объекта World с детерминированными параметрами
2. Загрузка конфигурации из YAML (world_phase, world_age)
3. Хеширование seed для всех последующих генераторов
4. Установка глобального размера карты (512×512)

## Инструменты

- **Python stdlib**: `hashlib` для seed hashing
- **PyYAML**: загрузка конфигурации
- **Dataclass**: структура World

## Входные данные

```yaml
# config/world_generation_v2.yaml
global_settings:
  world_phase: "EXHALE"  # EXHALE | INHALE
  world_age: "LATE_EXHALE"  # EARLY_EXHALE | LATE_EXHALE | EXHALE_PEAK
  map_size: [512, 512]
```

## Выходные данные

```python
World(
    seed="silgarron_alpha_01",
    world_phase="EXHALE",
    age="LATE_EXHALE",
    global_size=(512, 512)
)
```

## Пошаговый план

### 1. Создать структуру данных World

```python
from dataclasses import dataclass
from typing import Tuple

@dataclass
class World:
    seed: str
    world_phase: str  # "EXHALE" | "INHALE"
    age: str
    global_size: Tuple[int, int]
```

### 2. Реализовать метод инициализации

```python
def _initialize_world(self, seed: str) -> World:
    """
    Инициализация мира с параметрами из конфигурации
    """
    return World(
        seed=seed,
        world_phase=self.config['global_settings']['world_phase'],
        age=self.config['global_settings']['world_age'],
        global_size=tuple(self.config['global_settings']['map_size'])
    )
```

### 3. Создать hash-функцию для детерминизма

```python
import hashlib

def _hash_seed(self, base_seed: str, suffix: str) -> int:
    """
    Создаёт детерминированный int seed для генератора

    Args:
        base_seed: Базовый seed мира
        suffix: Суффикс для разделения генераторов ("continent", "spine", и т.д.)

    Returns:
        int seed в диапазоне [0, 2^31)
    """
    combined = f"{base_seed}_{suffix}"
    hash_bytes = hashlib.sha256(combined.encode()).digest()
    return int.from_bytes(hash_bytes[:4], 'big') % (2**31)
```

### 4. Интегрировать с генератором

```python
class WorldGeneratorV2:
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.global_size = tuple(self.config['global_settings']['map_size'])

    def generate(self, seed: str) -> World:
        # Phase 0: Инициализация
        world = self._initialize_world(seed)

        # Генерация хеша для каждой последующей фазы
        continent_seed = self._hash_seed(seed, "continent")
        spine_seed = self._hash_seed(seed, "spine")

        return world
```

## Тестирование

**Рабочий пакет:** WP1 (Основа мира)
**Файл тестов:** `tests/core/test_world_initialization.py`

### Unit тесты для реализации

#### ✅ test_seed_determinism
```python
def test_seed_determinism():
    """
    Проверка детерминизма hash_seed

    Критерий: Одинаковые seed + suffix → одинаковый hash
              Разные suffix → разные hash
    """
    generator = WorldGeneratorV2("config/world_generation_v2.yaml")

    # Одинаковые seed + suffix дают одинаковый hash
    hash1 = generator._hash_seed("test", "continent")
    hash2 = generator._hash_seed("test", "continent")
    assert hash1 == hash2

    # Разные suffix дают разные hash
    hash3 = generator._hash_seed("test", "spine")
    assert hash1 != hash3

    # Диапазон
    assert 0 <= hash1 < (2**31)
```

#### ✅ test_world_initialization
```python
def test_world_initialization():
    """
    Проверка корректной инициализации World объекта

    Критерий: Все поля заполнены из конфига + seed
    """
    generator = WorldGeneratorV2("config/world_generation_v2.yaml")
    world = generator._initialize_world("test_seed")

    assert world.seed == "test_seed"
    assert world.world_phase == "EXHALE"
    assert world.age == "LATE_EXHALE"
    assert world.global_size == (512, 512)
```

#### ✅ test_config_loading
```python
def test_config_loading():
    """
    Проверка успешной загрузки YAML конфигурации

    Критерий: Все ожидаемые параметры присутствуют
    """
    generator = WorldGeneratorV2("config/world_generation_v2.yaml")

    assert 'global_settings' in generator.config
    assert 'world_phase' in generator.config['global_settings']
    assert 'world_age' in generator.config['global_settings']
    assert 'map_size' in generator.config['global_settings']

    # Валидация значений
    assert generator.config['global_settings']['world_phase'] in ['EXHALE', 'INHALE']
    assert generator.config['global_settings']['map_size'] == [512, 512]
```

#### ✅ test_world_data_types
```python
def test_world_data_types():
    """
    Валидация типов данных World объекта

    Критерий: Схема данных соответствует спецификации WP1
    """
    generator = WorldGeneratorV2("config/world_generation_v2.yaml")
    world = generator._initialize_world("test_seed")

    assert isinstance(world.seed, str)
    assert isinstance(world.world_phase, str)
    assert isinstance(world.age, str)
    assert isinstance(world.global_size, tuple)
    assert len(world.global_size) == 2
    assert isinstance(world.global_size[0], int)
    assert isinstance(world.global_size[1], int)
```

### Критерии валидации WP1

#### Функциональная валидация
- ✅ `_hash_seed` возвращает одинаковый int для одинаковых входов
- ✅ Разные suffix дают разные hash
- ✅ YAML конфигурация загружается без ошибок
- ✅ Все параметры конфига корректны

#### Валидация схемы данных
- ✅ World имеет поля: seed, world_phase, age, global_size
- ✅ Типы данных корректны (str, str, str, tuple)
- ✅ global_size = (512, 512)

## Метрики

- **Время выполнения**: <0.001 секунды
- **Память**: ~100 байт

## Зависимости

**Зависит от:**
- Конфигурационный файл YAML

**Используется в:**
- Phase 1a (Spine)
- Phase 1b (Continent)
- Все последующие фазы (через hash_seed)
