# Analysis Toolkit

Набор инструментов для анализа системы генерации мира Neuro RPG.

## Содержание

### 1. `compatibility_analyzer.py`
Статистический анализ системы совместимости биомов и рас.

**Основные функции:**
- `plot_compatibility_distribution()` - Гистограмма распределения очков совместимости между всеми биомами
- `analyze_race_specialization()` - Box plots для анализа специализации рас

**Вопросы, на которые отвечает:**
- Создаёт ли моя система осмысленный контраст между биомами?
- Есть ли у меня расы-специалисты и расы-универсалы?
- Правильно ли настроены синергии и конфликты?

**Использование:**
```python
from analysis.compatibility_analyzer import CompatibilityAnalyzer

analyzer = CompatibilityAnalyzer()
analyzer.plot_compatibility_distribution(save_path="distribution.png")
analyzer.analyze_race_specialization(save_path="specialization.png")
```

### 2. `generation_analyzer.py`
Анализ результатов процедурной генерации мира.

**ВНИМАНИЕ:** Работает в DEMO-режиме с mock-данными до реализации `SpatialLocationGenerator`.

**Основные функции:**
- `run_frequency_analysis()` - Частотный анализ появления биомов
- `analyze_adjacency_matrix()` - Матрица смежности биомов (heatmap)
- `visualize_world_graph()` - Сетевой граф мира через NetworkX

**Вопросы, на которые отвечает:**
- Работает ли случайность так, как ожидается?
- Какие биомы часто граничат друг с другом?
- Есть ли изолированные зоны или центральные хабы?

**Использование:**
```python
from analysis.generation_analyzer import GenerationAnalyzer

# DEMO режим (без генератора)
analyzer = GenerationAnalyzer(generator=None)
analyzer.run_frequency_analysis()
analyzer.analyze_adjacency_matrix(world_graph=None)
analyzer.visualize_world_graph(world_graph=None)

# Реальное использование (после реализации генератора)
from services.spatial_location_generator import SpatialLocationGenerator
generator = SpatialLocationGenerator()
analyzer = GenerationAnalyzer(generator=generator)
analyzer.run_frequency_analysis(n_iterations=1000, region_type="dermal_plateau")
```

### 3. `compatibility_visualizer.py`
Табличные визуализации правил совместимости.

**Основные функции:**
- `print_synergies_table()` - Таблица всех синергий тегов
- `print_conflicts_table()` - Таблица всех конфликтов тегов
- `print_forbidden_combinations()` - Список запрещённых комбинаций
- `print_biome_compatibility_matrix()` - Статистика из generation_rules.yaml
- `analyze_race_affinity(race_name)` - Детальный анализ расовых предпочтений

**Использование:**
```python
from analysis.compatibility_visualizer import *

print_synergies_table()
print_conflicts_table()
analyze_race_affinity("humans")
```

### 4. `world_analysis.ipynb`
Jupyter Notebook для интерактивного анализа.

**Содержит:**
- Полный pipeline анализа от загрузки данных до интерпретации
- Markdown-документацию для каждого инструмента
- Примеры использования всех анализаторов
- Автоматическую интерпретацию результатов
- Экспорт данных в CSV

**Запуск:**
```bash
jupyter notebook analysis/world_analysis.ipynb
```

## Быстрый старт

### Вариант 1: Python скрипт
```bash
# Анализ совместимости
python -m analysis.compatibility_analyzer

# Анализ генерации (DEMO режим)
python -m analysis.generation_analyzer
```

### Вариант 2: Jupyter Notebook (рекомендуется)
```bash
cd analysis
jupyter notebook world_analysis.ipynb
```

### Вариант 3: Интерактивный Python
```python
from analysis.compatibility_analyzer import CompatibilityAnalyzer
from analysis.generation_analyzer import GenerationAnalyzer

# Быстрый анализ
compat = CompatibilityAnalyzer()
compat.plot_compatibility_distribution()
compat.analyze_race_specialization()

gen = GenerationAnalyzer()
gen.run_frequency_analysis()
```

## Интерпретация результатов

### Распределение совместимости

**Хорошие признаки:**
- Стандартное отклонение (std) > 0.5 → Система создаёт контраст
- Несколько пиков на гистограмме → Чёткие группы совместимых/несовместимых биомов
- Forbidden combinations (score = 0.0) присутствуют → Жёсткие ограничения работают

**Проблемы:**
- std < 0.3 → Правила слишком слабые, все биомы одинаково совместимы
- Все scores около 1.0 → Синергии и конфликты не работают
- Один пик около среднего → Недостаточно вариативности

**Решения:**
- Увеличить bonus в синергиях (tags_registry.yaml)
- Уменьшить penalty в конфликтах (сделать штрафы жёстче)
- Добавить больше тегов для контрастных биомов

### Специализация рас (Box Plot)

**Раса-универсал:**
- Короткий box (узкий диапазон)
- Медиана около 1.0
- Мало выбросов
- Пример: Люди (humans) адаптивны везде

**Раса-специалист:**
- Длинный box (широкий диапазон)
- Медиана далеко от 1.0
- Много выбросов вверх/вниз
- Пример: Дроу (drow) идеальны в пещерах, страдают на поверхности

**Как изменить:**
- Универсал → Специалист: Добавить специфичные теги, создать синергии
- Специалист → Универсал: Добавить универсальные теги, уменьшить конфликты

### Частотный анализ биомов

**Хорошие признаки:**
- Распределение близко к ожидаемому (из spawn_weight)
- Редкие биомы (spawn_weight=0.1) появляются ~10% времени
- Нет доминирующих биомов (>60%)

**Проблемы:**
- Один биом доминирует → Проверить spawn_weight
- Редкий биом почти не появляется → Проверить правила совместимости
- Коэффициент вариации (CV) > 1.5 → Слишком неравномерное распределение

### Матрица смежности

**Интерпретация:**
- Высокие значения (>30) → Биомы часто граничат (возможно, синергия)
- Низкие значения (<5) → Биомы редко граничат (возможно, конфликт)
- Асимметрия → Направленные правила (A может граничить с B, но не наоборот)
- Диагональ нулевая → Биом не может граничить сам с собой

**Примеры паттернов:**
- "Остров плодородия в пустыне" → Оазис имеет высокие значения с desert, но низкие с другими
- "Градиент биомов" → Plains-Forest-Mountains показывают последовательное снижение значений

### Сетевой граф

**Что искать:**
- **Изолированные узлы** → Биом без соседей (ПРОБЛЕМА!)
- **Центральные хабы** → Биомы с высокой степенью (универсальные)
- **Кластеры** → Группы тесно связанных биомов (тематические зоны)
- **Диаметр графа** → Максимальное расстояние между локациями

**Статистика:**
- Средняя степень < 2 → Граф слишком разрежённый
- Диаметр > 10 → Мир слишком вытянутый
- Несколько компонент связности → Изолированные регионы (может быть задумкой)

## Структура директории

```
analysis/
├── README.md                       # Эта документация
├── compatibility_analyzer.py       # Статистический анализ совместимости
├── generation_analyzer.py          # Анализ генерации мира
├── compatibility_visualizer.py     # Табличные визуализации
├── world_analysis.ipynb           # Jupyter notebook (интерактивный)
└── results/                       # Автоматически создаваемая директория
    ├── compatibility_distribution.png
    ├── race_specialization.png
    ├── biome_frequency_demo.png
    ├── adjacency_matrix_demo.png
    ├── world_graph_demo.png
    ├── compatibility_scores.csv
    └── race_biome_scores.csv
```

## Зависимости

Все зависимости уже в requirements.txt проекта:
- matplotlib >= 3.5.0
- seaborn >= 0.11.0
- numpy >= 1.21.0
- networkx >= 2.6.0
- pandas >= 1.3.0 (для экспорта CSV)
- jupyter >= 1.0.0 (для notebook)

## Workflow рекомендаций

1. **Начальная балансировка** (до реализации генератора):
   ```bash
   python -m analysis.compatibility_analyzer
   ```
   Проверить распределение и специализацию рас.

2. **Итерация правил**:
   - Изменить tags_registry.yaml (синергии/конфликты)
   - Запустить анализ заново
   - Сравнить результаты

3. **Тестирование генерации** (после реализации генератора):
   ```bash
   jupyter notebook analysis/world_analysis.ipynb
   ```
   Запустить все анализы и проверить реальные паттерны.

4. **Экспорт и документация**:
   - Сохранить графики в results/
   - Экспортировать CSV для внешнего анализа
   - Документировать найденные паттерны в ADR

## Известные ограничения

- **generation_analyzer.py** работает в DEMO-режиме до реализации `SpatialLocationGenerator`
- Анализ использует только теги из `tags_registry.yaml` (не учитывает race_modifiers)
- Box plots не показывают уверенность оценок (confidence intervals)
- Матрица смежности строится только для реальных графов (mock-данные не полные)

## TODO

- [ ] Добавить анализ кластеризации биомов (k-means)
- [ ] Реализовать сравнение нескольких генераций (A/B testing)
- [ ] Добавить экспорт в HTML report
- [ ] Интеграция с validation pipeline (автоматические тесты балансировки)
- [ ] Добавить анализ event distribution (когда реализуем события)

## Обратная связь

Если найдёте проблемы или нужны дополнительные анализы:
1. Создать issue в репозитории
2. Документировать в ADR, если это архитектурное решение
3. Расширить этот README с примерами

---

**Версия:** 1.0.0
**Дата создания:** 2025-10-15
**Автор:** Claude Code (Sprint 3, Task 5)
