# Быстрый старт - Sprint 3.6 Phase 1

## Что было создано

### 1. Модели данных
- `core/models/world.py` - Organ, Region, ContinentData, World
- Полная валидация всех параметров
- 18 unit-тестов

### 2. Менеджер конфигурации
- `services/world_config_v2.py` - WorldGenerationConfigV2
- Загрузка/сохранение YAML
- Валидация параметров
- Удобные геттеры и сеттеры

### 3. Генератор v2.0
- `core/world_generator_v2.py` - WorldGeneratorV2
- Интегрирован с конфиг-менеджером
- Готов к Phase 2 (генерация континента)

### 4. Визуализатор
- `scripts/visualize_phase1.py` - демонстрация всех компонентов

### 5. Документация
- `docs/sprint_3.6_implementation/VISUALIZATION_GUIDE.md` - полное руководство
- `docs/sprint_3.6_implementation/QUICKSTART.md` - этот файл

---

## Как запустить

### Визуализация Phase 1

```bash
# Из корня проекта
python scripts/visualize_phase1.py
```

**Результат:** Файл `output/phase1_visualization.png` (584 KB)

### Тестирование конфиг-менеджера

```bash
python services/world_config_v2.py
```

**Вывод:**
```
World Generation Config v2.0
Global Settings:
   Map size: (512, 512)
   Phase: EXHALE
   Age: LATE_EXHALE

Continent:
   Sea level: 0.35
   Perlin: scale=150, octaves=2

Organs (4 types):
   - metabolic_organ: count=1, radius=30
   - digestive: count=1, radius=25
   - neural_cluster: count=2, radius=15
   - immune_node: count=1, radius=10

...
```

### Запуск тестов

```bash
# Все тесты Phase 1
python -m pytest tests/models/ tests/core/test_world_generator_v2.py -v

# Ожидаемый результат: 22 passed
```

---

## Изменение конфигурации

### Через Python API

```python
from services.world_config_v2 import WorldGenerationConfigV2

# Загрузка
config = WorldGenerationConfigV2.from_yaml('config/world_generation_v2.yaml')

# Изменение параметров
config.set_sea_level(0.40)  # Больше океана
config.set_perlin_scale(180)  # Более крупные континенты
config.set_perlin_octaves(3)  # Больше деталей

# Сохранение
config.save_to_yaml('config/world_generation_v2.yaml')
```

### Напрямую в YAML

Откройте `config/world_generation_v2.yaml` и отредактируйте:

```yaml
continent:
  perlin_noise:
    scale: 180  # Было 150
    octaves: 3  # Было 2
  sea_level: 0.40  # Было 0.35
```

После изменения конфиг будет автоматически валидирован при следующей загрузке.

---

## Структура файлов

```
neuro_rpg/
├── config/
│   └── world_generation_v2.yaml  # Конфигурация
│
├── core/
│   ├── models/
│   │   └── world.py  # Модели данных
│   └── world_generator_v2.py  # Генератор
│
├── services/
│   └── world_config_v2.py  # Менеджер конфигов
│
├── scripts/
│   └── visualize_phase1.py  # Визуализатор
│
├── tests/
│   ├── models/
│   │   └── test_world.py  # 18 тестов
│   └── core/
│       └── test_world_generator_v2.py  # 4 теста
│
├── output/
│   └── phase1_visualization.png  # Результат
│
└── docs/
    └── sprint_3.6_implementation/
        ├── SPRINT_3.6_PLAN.md  # Полный план
        ├── VISUALIZATION_GUIDE.md  # Руководство
        └── QUICKSTART.md  # Этот файл
```

---

## Phase 2: Генерация континента

### Визуализация континента

```bash
# Визуализация одного seed
python scripts/visualize_continent.py --seed silgarron_alpha_01

# Сравнение нескольких seeds
python scripts/visualize_continent.py --compare seed_A seed_B seed_C
```

**Результат:**
- `output/continent_silgarron_alpha_01.png` (4.8 MB)
- `output/continent_comparison.png` (5.6 MB)

### Тестирование

```bash
# Тесты генерации континента
python -m pytest tests/core/test_continent_generation.py -v

# Все тесты (Phase 1 + Phase 2)
python -m pytest tests/models/ tests/core/ -v

# Ожидаемый результат: 37 passed
```

### Что реализовано

✅ **Perlin Noise генерация континента**
- Органичные формы вместо геометрических примитивов
- Уникальный континент для каждого seed
- Сглаживание береговой линии

✅ **Геометрический анализ**
- Расчет центра масс (для размещения органов)
- Расчет главной оси через PCA (для "позвоночника")

✅ **15 новых тестов**
- Детерминированность, уникальность
- Валидация геометрии
- Edge cases

**Детали:** См. `docs/sprint_3.6_implementation/PHASE2_RESULTS.md`

---

## Следующие шаги

**Phase 2 завершена!**

**Готово к Phase 3:**
- Размещение органов на континенте
- Определение регионов
- Визуализация анатомии

Для продолжения см. `docs/sprint_3.6_implementation/SPRINT_3.6_PLAN.md` - раздел "ФАЗА 3".

---

**Дата:** 2025-10-25
**Статус:** Phase 2 Complete ✅
**Тестов:** 37/37 passing
