# 📊 Руководство по визуализации Sprint 3.6

Полное руководство по использованию инструментов визуализации и работе с конфигурацией для генератора мира v2.0 (ADR-020).

---

## 📋 Содержание

1. [Быстрый старт](#быстрый-старт)
2. [Phase 1: Визуализация инфраструктуры](#phase-1-визуализация-инфраструктуры)
3. [Работа с конфиг-менеджером](#работа-с-конфиг-менеджером)
4. [Примеры использования](#примеры-использования)
5. [Troubleshooting](#troubleshooting)

---

## 🚀 Быстрый старт

### Запуск визуализации Phase 1

```bash
# Из корня проекта
python scripts/visualize_phase1.py
```

**Что это делает:**
- Загружает конфигурацию из `config/world_generation_v2.yaml`
- Демонстрирует создание моделей данных (Organ, Region, ContinentData, World)
- Показывает работу валидации
- Создает визуализацию в `output/phase1_visualization.png`

**Ожидаемый результат:**
```
====================================================================
📋 ДЕМОНСТРАЦИЯ: Менеджер конфигурации
====================================================================
✅ Конфиг загружен из config/world_generation_v2.yaml

============================================================
📋 World Generation Config v2.0
============================================================

🌍 Global Settings:
   Map size: (512, 512)
   Phase: EXHALE
   Age: LATE_EXHALE

🏔️ Continent:
   Sea level: 0.35
   Perlin: scale=150, octaves=2

🫀 Organs (4 types):
   - metabolic_organ: count=1, radius=30
   - digestive: count=1, radius=25
   - neural_cluster: count=2, radius=15
   - immune_node: count=1, radius=10

🗺️ Regions (4 types):
   - THORAX
   - DIAPHRAGM
   - ORGANOID
   - GRASPING_LIMB
============================================================

✅ Конфигурация валидна

...

✅ Визуализация сохранена: E:\neuro_rpg\output\phase1_visualization.png
```

---

## 📐 Phase 1: Визуализация инфраструктуры

### Что визуализируется

Phase 1 демонстрирует **структуры данных** перед началом реальной генерации:

1. **Континент (Mask)** — бинарная маска суши/океана
2. **Континент (Heightmap)** — карта высот (0.0-1.0)
3. **Регион** — маска региона с характеристиками
4. **Орган** — визуализация органа на континенте

### Структура визуализации

```
┌─────────────────────────────────────────────────────────┐
│ Sprint 3.6 Phase 1: Модели данных                       │
│ Seed: demo_seed_123 | Phase: EXHALE                     │
├────────────────────────┬────────────────────────────────┤
│ Континент (Mask)       │ Континент (Heightmap)          │
│ - Черное = океан       │ - Цветовая карта высот         │
│ - Белое = суша         │ - Terrain colormap             │
│ - Красный X = центр    │ - Colorbar справа              │
│ - Синяя линия = ось    │                                │
├────────────────────────┼────────────────────────────────┤
│ Регион: THORAX         │ Орган: heart                   │
│ - Синяя маска          │ - Красный круг                 │
│ - Покрытие: 50%        │ - Параметры справа             │
│ - Характеристики       │ - На фоне континента           │
└────────────────────────┴────────────────────────────────┘
```

### Что проверяется

Скрипт автоматически проверяет:

- ✅ Загрузка конфигурации
- ✅ Валидация параметров
- ✅ Создание валидных моделей
- ✅ Отклонение невалидных данных (отрицательный radius, неправильный размер маски)

---

## ⚙️ Работа с конфиг-менеджером

### Базовое использование

```python
from services.world_config_v2 import WorldGenerationConfigV2

# Загрузка конфига
config = WorldGenerationConfigV2.from_yaml('config/world_generation_v2.yaml')

# Валидация
if config.validate():
    print("Config is valid!")

# Вывод сводки
config.print_summary()
```

### Чтение параметров

```python
# Глобальные настройки
size = config.get_global_size()  # (512, 512)
phase = config.get_world_phase()  # 'EXHALE'
age = config.get_world_age()  # 'LATE_EXHALE'

# Континент
sea_level = config.get_sea_level()  # 0.35
perlin_params = config.get_perlin_params()
# {'scale': 150, 'octaves': 2, 'persistence': 0.6, 'lacunarity': 2.0}

# Органы
metabolic = config.get_organ_config('metabolic_organ')
# {'count': 1, 'radius': 30, 'temperature': 0.95, ...}

# Регионы
thorax = config.get_region_config('THORAX')
# {'detection_method': 'skeletal_density', 'characteristics': {...}}
```

### Изменение параметров

```python
# Изменение уровня моря
config.set_sea_level(0.40)  # Теперь 40% карты будет океаном

# Изменение параметров Perlin Noise
config.set_perlin_scale(180)  # Более крупные фичи
config.set_perlin_octaves(3)  # Больше детализации

# Изменение параметров органов
config.set_organ_count('neural_cluster', 3)  # Теперь 3 ганглия
config.set_organ_radius('metabolic_organ', 35)  # Увеличили радиус

# Сохранение изменений
config.save_to_yaml('config/world_generation_v2.yaml')
```

### Валидация изменений

Конфиг-менеджер **автоматически валидирует** все изменения:

```python
# Попытка установить невалидное значение
try:
    config.set_sea_level(0.8)  # ОШИБКА: должно быть 0.2-0.5
except ValueError as e:
    print(f"Validation error: {e}")
    # "sea_level должен быть 0.2-0.5, получено: 0.8"

# Попытка установить отрицательный радиус
try:
    config.set_organ_radius('digestive', -10)  # ОШИБКА
except ValueError as e:
    print(f"Validation error: {e}")
    # "radius должен быть > 0, получено: -10"
```

### Валидационные правила

| Параметр | Диапазон | Описание |
|----------|----------|----------|
| `global_width/height` | 512×512 | Фиксированный размер глобальной карты |
| `detail_width/height` | 4096×4096 | Фиксированный размер детализации |
| `scale_factor` | 8 | 1 global hex = 8×8 detail hexes |
| `world_phase` | EXHALE/INHALE | Фаза мира |
| `perlin.scale` | 50-300 | Масштаб шума (больше = крупнее) |
| `perlin.octaves` | 1-5 | Количество слоёв детализации |
| `perlin.persistence` | 0.0-1.0 | Затухание амплитуды октав |
| `perlin.lacunarity` | 1.5-4.0 | Рост частоты октав |
| `sea_level` | 0.2-0.5 | Порог океана (0.35 = 35% океана) |
| `organ.count` | ≥ 0 | Количество органов типа |
| `organ.radius` | > 0 | Радиус влияния органа |

---

## 💡 Примеры использования

### Пример 1: Тюнинг параметров континента

```python
from services.world_config_v2 import WorldGenerationConfigV2

# Загрузка
config = WorldGenerationConfigV2.from_yaml('config/world_generation_v2.yaml')

# Хотим больше воды и более плавные континенты
config.set_sea_level(0.40)  # 40% океана вместо 35%
config.set_perlin_scale(200)  # Более крупные формы
config.set_perlin_octaves(2)  # Меньше мелких деталей

# Сохраняем
config.save_to_yaml('config/world_generation_v2.yaml')

print("Конфигурация обновлена!")
print("Теперь запустите генератор для проверки результата")
```

### Пример 2: Создание тестового конфига

```python
from services.world_config_v2 import WorldGenerationConfigV2

# Создаем дефолтный конфиг
config = WorldGenerationConfigV2()

# Настраиваем для быстрого тестирования
config.set_perlin_octaves(1)  # Минимум деталей
config.set_organ_count('neural_cluster', 1)  # Упрощаем

# Сохраняем как тестовый
config.save_to_yaml('config/world_generation_v2_test.yaml')
```

### Пример 3: Автоматизация экспериментов

```python
from services.world_config_v2 import WorldGenerationConfigV2
from core.world_generator_v2 import WorldGeneratorV2

# Тестируем разные уровни моря
for sea_level in [0.30, 0.35, 0.40, 0.45]:
    # Загружаем и изменяем
    config = WorldGenerationConfigV2.from_yaml('config/world_generation_v2.yaml')
    config.set_sea_level(sea_level)
    config.save_to_yaml('config/world_generation_v2.yaml')

    # Генерируем мир
    gen = WorldGeneratorV2()
    world = gen.generate(f"test_sea_{sea_level}")

    # Сохраняем результат
    # ... визуализация и анализ ...

    print(f"Sea level {sea_level}: Land coverage = ...")
```

---

## 🎨 Запуск тестов моделей

```bash
# Тесты моделей данных
python -m pytest tests/models/test_world.py -v

# Тесты генератора
python -m pytest tests/core/test_world_generator_v2.py -v

# Все тесты Phase 1
python -m pytest tests/models/ tests/core/test_world_generator_v2.py -v
```

**Ожидаемый результат:**
```
tests/models/test_world.py::TestOrgan::test_organ_creation PASSED
tests/models/test_world.py::TestOrgan::test_organ_validation_negative_radius PASSED
tests/models/test_world.py::TestOrgan::test_organ_validation_zero_radius PASSED
...
tests/core/test_world_generator_v2.py::TestWorldGeneratorV2::test_generator_initialization PASSED
tests/core/test_world_generator_v2.py::TestWorldGeneratorV2::test_config_loaded_correctly PASSED
...

============================== 22 passed ==============================
```

---

## 🛠️ Troubleshooting

### Ошибка: "Config file not found"

```
FileNotFoundError: Config file not found: config/world_generation_v2.yaml
```

**Решение:**
```bash
# Проверьте, что вы в корне проекта
ls config/world_generation_v2.yaml

# Если файла нет, создайте его (он должен был быть создан в Phase 1)
# Проверьте файлы в config/
ls config/
```

### Ошибка: "Validation failed"

```
❌ Ошибки валидации конфигурации:
   - sea_level должен быть 0.2-0.5, получено: 0.8
```

**Решение:**
Откройте `config/world_generation_v2.yaml` и исправьте невалидные значения согласно таблице валидационных правил выше.

### Визуализация не отображается

**Решение:**
```python
# В конце visualize_phase1.py замените plt.show() на:
plt.savefig('output/phase1_visualization.png', dpi=150)
print("Saved to output/phase1_visualization.png")
# Затем откройте файл вручную
```

### ModuleNotFoundError

```
ModuleNotFoundError: No module named 'core.models.world'
```

**Решение:**
```bash
# Убедитесь, что запускаете из корня проекта
cd E:\neuro_rpg

# Проверьте PYTHONPATH
echo $PYTHONPATH  # Linux/Mac
echo %PYTHONPATH%  # Windows

# Запускайте скрипты через python -m или убедитесь что path добавлен в sys.path
```

---

## 📁 Структура файлов

```
neuro_rpg/
├── config/
│   ├── world_generation_v2.yaml          # Основная конфигурация
│   └── world_generation_v2_modified.yaml # Модифицированные версии
│
├── core/
│   ├── models/
│   │   ├── __init__.py
│   │   └── world.py                      # Organ, Region, ContinentData, World
│   ├── world_generator_v2.py             # WorldGeneratorV2
│   └── perlin_noise.py                   # Perlin Noise
│
├── services/
│   └── world_config_v2.py                # WorldGenerationConfigV2
│
├── scripts/
│   └── visualize_phase1.py               # Визуализатор Phase 1
│
├── tests/
│   ├── models/
│   │   └── test_world.py                 # Тесты моделей
│   └── core/
│       └── test_world_generator_v2.py    # Тесты генератора
│
├── output/
│   └── phase1_visualization.png          # Результат визуализации
│
└── docs/
    └── sprint_3.6_implementation/
        ├── SPRINT_3.6_PLAN.md            # План спринта
        └── VISUALIZATION_GUIDE.md        # Этот файл
```

---

## 📝 Следующие шаги

После завершения Phase 1 переходите к:

**Phase 2: Генерация континента (СЛОЙ 0.5)**
- Задача 2.1: Генерация макро-рельефа континента
- Задача 2.2: Итеративный тюнинг параметров
- Визуализатор: `scripts/visualize_continent.py` (будет создан)

**Планируемые визуализаторы:**
- `scripts/visualize_continent.py` - визуализация континента
- `scripts/visualize_organs.py` - визуализация размещения органов
- `scripts/visualize_regions.py` - визуализация регионов
- `scripts/tune_continent_parameters.py` - grid search параметров

---

## ✅ Чеклист Phase 1

- [x] Модели данных созданы (`core/models/world.py`)
- [x] Конфигурация создана (`config/world_generation_v2.yaml`)
- [x] Конфиг-менеджер создан (`services/world_config_v2.py`)
- [x] Генератор v2 создан (`core/world_generator_v2.py`)
- [x] Тесты написаны (22 теста)
- [x] Визуализатор создан (`scripts/visualize_phase1.py`)
- [x] Документация создана (этот файл)

**Phase 1 завершена! 🎉**

Теперь можно безопасно приступать к Phase 2.

---

**Авторы:** Claude Code (Sprint 3.6)
**Дата:** 2025-10-25
**Версия:** 1.0
