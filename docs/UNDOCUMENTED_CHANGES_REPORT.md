# Отчет о недокументированных изменениях

**Дата аудита:** 2025-10-19
**Версия проекта:** 3.0 (после Sprint 3)

## Резюме

Обнаружено **6 критических недокументированных изменений** в проекте после Sprint 3. Документация отстает от реального состояния кода.

---

## 1. CompatibilityService получил HYBRID FORMULA

### Текущее состояние кода
`services/compatibility_service.py:133-260`

**Новая гибридная формула:**
```python
Formula = (base_affinity + situational_bonus + penalty + synergy - conflict) * multiplier
```

**Компоненты:**
- `base_affinity`: Аддитивная база из локальных правил расы
- `situational_bonus`: Контекстные бонусы (аддитивно)
- `penalty`: Штрафы (аддитивно, отрицательные)
- `multiplier`: Мультипликативный модификатор для синергий
- `synergy_bonus`: Глобальные синергии из tags_registry
- `conflict_penalty`: Глобальные конфликты из tags_registry

**Legacy support:** Если новые ключи отсутствуют, использует старую мультипликативную формулу

### Что было документировано
TDD.md:626-741 описывает только базовую логику без упоминания HYBRID FORMULA

### Статус
✅ Обновлено в TDD.md (строки 626-714)

---

## 2. Добавлен CompatibilityLevel Enum и CompatibilityScore dataclass

### Текущее состояние кода
`services/compatibility_service.py:23-38`

```python
class CompatibilityLevel(Enum):
    INCOMPATIBLE = 0      # Абсолютно несовместимо
    POOR = 1              # Плохая совместимость (0.1 - 0.4)
    MODERATE = 2          # Умеренная (0.4 - 0.8)
    GOOD = 3              # Хорошая (0.8 - 1.5)
    EXCELLENT = 4         # Отличная (> 1.5)

@dataclass
class CompatibilityScore:
    raw_score: float
    level: CompatibilityLevel
    breakdown: Dict[str, float]
    blocking_factors: List[str]

    @property
    def is_compatible(self) -> bool:
        return self.raw_score > 0.1
```

### Что было документировано
TDD.md возвращал простой `Dict` или `float`, не упоминал структурированный ответ

### Статус
✅ Обновлено в TDD.md (строки 632-713)

---

## 3. location_compatibility.yaml переименован в generation_rules.yaml

### Текущее состояние файлов
- ❌ `data/location_compatibility.yaml` - не существует
- ✅ `data/generation_rules.yaml` - существует (660 строк, 10 разделов)

**Новая структура:**
```yaml
meta:
  schema_version: "2.0.0"
  last_updated: "2025-10-05"

global_modifiers:
  race_terrain_affinity: {...}
  resource_settlement_bonus: {...}

biome_border_rules:
  smooth_transitions: [...]
  sharp_transitions: [...]
  mandatory_buffers: [...]

poi_placement_rules: {...}
compatibility_formulas: {...}
dynamic_rules: {...}
balance_params: {...}
region_presets: {...}
validation_rules: {...}
debug_params: {...}
evolution_rules: {...}
```

### Что было документировано
- TDD.md:595: `self._location_compatibility = self._load_yaml("location_compatibility.yaml")`
- TDD.md:932-950: Описание `location_compatibility.yaml`
- DONE.md:161, 171: Ссылки на старый файл

### Статус
✅ Обновлено в TDD.md (строки 955-994)

---

## 4. validate_data.py перенесен в validators/world_gen_validator.py

### Текущее состояние файлов
- ❌ `validate_data.py` (корневая директория) - удален
- ✅ `validators/world_gen_validator.py` - создан (101 строка)

**Новая архитектура:**
```python
def validate_compatibility_rules(
    comp_service: CompatibilityService,
    world_data: WorldDataService
) -> list[str]:
    """
    Углубленная валидация:
    - Проверка жизнеспособности рас
    - Проверка заселяемости биомов
    - Использует CompatibilityScore.is_compatible
    """
```

### Что было документировано
- TDD.md:1136-1139: Ссылка на `utils/validate_data.py`
- DONE.md:161: `validate_data.py`

### Статус
⚠️ Требует обновления (не смог найти строку в TDD.md)

---

## 5. HexWorldService получил двухуровневую архитектуру

### Текущее состояние кода
`services/hex_world_service.py:1-389`

**Ключевые изменения:**
1. Биомы теперь имеют `hex_coord: HexCoord` вместо `pixel_position` (строка 105)
2. Раздельные методы для UI:
   - `get_world_map_for_ui()` - граф регионов
   - `get_local_map_for_ui()` - граф биомов внутри региона
3. Компактный кластерный алгоритм размещения биомов `_generate_local_biome_layout()` (строки 207-237)
4. Интеграция с CompatibilityService:
   - `find_best_biome_for_region()` для выбора оптимального биома (строка 182)
   - Проверка `biome is not None` перед размещением (строка 193)

### Что было документировано
Документация не отражает эти изменения

### Статус
⚠️ Требует добавления в TDD.md

---

## 6. Папка analysis/ не отслеживается git (untracked)

### Текущее состояние
- ✅ `analysis/` - директория существует (11 файлов)
- ✅ Все инструменты анализа присутствуют:
  - `compatibility_visualizer.py` (7,695 bytes)
  - `compatibility_analyzer.py` (15,329 bytes)
  - `generation_analyzer.py` (15,679 bytes)
  - `world_analysis.ipynb` (780,687 bytes)
  - `README.md` (13,311 bytes)
  - `HYBRID_FORMULA_IMPLEMENTATION_REPORT.md` (8,405 bytes)
  - `baseline_analysis.md` (20,580 bytes)
- ⚠️ **ПРОБЛЕМА**: Папка не добавлена в git (`?? analysis/` в git status)

### Что было документировано
DONE.md:160-205 детально описывает все инструменты анализа:
- `print_synergies_table()` - таблица всех синергий
- `print_conflicts_table()` - таблица всех конфликтов
- `plot_compatibility_distribution()` - гистограмма распределения
- `analyze_race_specialization()` - box plots для рас
- `run_frequency_analysis()` - частотный анализ биомов
- `analyze_adjacency_matrix()` - heatmap матрицы смежности
- `visualize_world_graph()` - сетевой граф через NetworkX

### Статус
⚠️ **ВАЖНО** - инструменты существуют и функциональны, но не отслеживаются git. Рекомендуется добавить в репозиторий.

---

## Рекомендации

### Приоритет 1 (Критический)
1. ✅ **Обновить TDD.md** с информацией о HYBRID FORMULA и CompatibilityScore
2. ⚠️ **Добавить папку analysis/ в git** - инструменты существуют, но не отслеживаются (`git add analysis/`)
3. ⚠️ **Обновить DONE.md** с реальным состоянием валидаторов

### Приоритет 2 (Высокий)
4. Документировать двухуровневую архитектуру HexWorldService
5. Обновить все ссылки на `location_compatibility.yaml` → `generation_rules.yaml`
6. Добавить недокументированные изменения в CHANGELOG

### Приоритет 3 (Средний)
7. Создать автоматическую проверку согласованности кода и документации
8. Добавить pre-commit hook для проверки документации при изменении ключевых файлов

---

## Статистика изменений

| Категория | Количество |
|-----------|------------|
| Недокументированные изменения API | 3 |
| Переименованные файлы | 2 |
| Неотслеживаемые папки в git | 1 |
| Новые структуры данных | 2 |
| **Итого** | **8** |

---

**Последнее обновление отчета:** 2025-10-19
