# ✏️ Technical Design Document - Чек-лист Обновления

**Документ:** Technical_Design_Document.md  
**Текущая версия:** 2.2  
**Требуется обновление до:** 3.0  
**Причина:** Новая трёхуровневая архитектура

---

## 🎯 Цель Обновления

Привести Technical_Design_Document в соответствие с новым архитектурным видением:
- Трёхуровневая маршрутизация команд
- Стратегии обработки (CODE_ONLY/SIMPLE_LLM/COMPLEX_TOOL_CALL)
- Function Calling Pattern
- Обновлённые статусы компонентов

---

## ✅ Чек-лист Изменений

### 1. Executive Summary (Раздел 1)

#### 1.1 Обновить версию
**Текущее:**
```markdown
**Version:** 2.2
**Date:** 2025-01-10
**Status:** Alpha (Phase 1-2 Complete, Production-Ready Skeleton)
```

**Новое:**
```markdown
**Version:** 3.0
**Date:** 2025-10-14
**Status:** Alpha (Phase 1-2 Complete, Sprint 1 In Progress)
```

- [ ] Изменить версию на 3.0
- [ ] Обновить дату
- [ ] Изменить статус

#### 1.2 Обновить таблицу "Текущий статус"
**Добавить строки:**

| Компонент | Статус | Готовность |
|-----------|--------|------------|
| **Command Routing System** | 🟡 В разработке | 60% |
| **Strategy Pattern** | 🟡 Sprint 1 | 40% |
| **Function Calling** | 🔴 Запланировано | 0% |

- [ ] Добавить новые компоненты
- [ ] Обновить процент готовности существующих

---

### 2. Core Concept (Раздел 2)

#### 2.1 Добавить новый подраздел: "P5: Оптимизация по сложности"

**Вставить после P4:**

```markdown
**P5: Оптимизация по сложности**

Не все действия требуют полной мощи LLM:

- Простые действия → код (бесплатно, <10ms)
- Средние → 1 вызов LLM (~0.001₽, 500ms)
- Сложные → Function Calling (~0.002₽, 1500ms)

Трёхуровневая маршрутизация обеспечивает баланс между интеллектом и эффективностью.
```

- [ ] Вставить новый принцип
- [ ] Добавить диаграмму (опционально)

---

### 3. System Architecture (Раздел 3) - КРИТИЧЕСКИЙ

#### 3.1 Заменить диаграмму "Общая структура"

**Текущая диаграмма:** Старая (без маршрутизации)

**Новая диаграмма:**
```
┌─────────────────────────────────────────────────┐
│              FRONTEND (Browser)                 │
└─────────────────┬───────────────────────────────┘
                  │ HTTP/WS
                  ↓
┌─────────────────────────────────────────────────┐
│           API LAYER (FastAPI)                   │
└─────────────────┬───────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────┐
│            GAME LOGIC CORE                      │
│                                                 │
│  ┌──────────────────────────────────────────┐  │
│  │  1. FAST ROUTER (IntentService)          │  │
│  │  all-mini + pymorphy3 (<50ms)            │  │
│  │  "бью мечом" → SIMPLE_LLM                │  │
│  └──────────────┬───────────────────────────┘  │
│                 ↓                               │
│  ┌──────────────────────────────────────────┐  │
│  │  2. DIRECTOR (Orchestrator)              │  │
│  │  Выбор стратегии по complexity_type      │  │
│  └──────┬───────┬───────┬────────────────────┘  │
│         ↓       ↓       ↓                       │
│  ┌──────┴───┐ ┌┴──────┐ ┌┴────────────────┐   │
│  │CODE_ONLY │ │SIMPLE │ │COMPLEX_TOOL_CALL│   │
│  │(no AI)   │ │ LLM   │ │(Function Call)  │   │
│  │<10ms     │ │1 call │ │2 calls          │   │
│  └──────────┘ └───────┘ └─────────────────┘   │
└─────────────────────────────────────────────────┘
```

- [ ] Заменить диаграмму
- [ ] Добавить легенду для трёх стратегий

#### 3.2 Добавить новый подраздел: "3.2 Command Processing Flow"

```markdown
### 3.2 Command Processing Flow

**Жизненный цикл команды игрока:**

```
1. PARSING
   Player: "опрокинуть стол на врага"
      ↓
   IntentService.recognize_intent()
      ↓
   Result: {
     "intent": "COMBAT",
     "complexity_type": "COMPLEX_TOOL_CALL"
   }

2. ROUTING
   Director получает complexity_type
      ↓
   Выбирает Strategy: FunctionCallingStrategy
      ↓
   
3. EXECUTION (для COMPLEX_TOOL_CALL)
   
   Step 3.1: First LLM Call
   ├─ Gemini получает команду + контекст
   └─ Возвращает: JSON с tool_call
      {
        "function": "calculate_physics",
        "args": {"object": "table", "action": "push"}
      }
   
   Step 3.2: Code Execution
   ├─ PhysicalSimulator.calculate_physics()
   └─ Возвращает: результаты расчётов
   
   Step 3.3: Second LLM Call
   ├─ Gemini получает результаты
   └─ Возвращает: красивый нарратив

4. RESPONSE
   Нарратив → Player
```
```

- [ ] Добавить подраздел
- [ ] Добавить диаграмму flow

---

### 4. Implementation Status (Раздел 4)

#### 4.1 Обновить статус logic/director.py

**Текущее:**
```markdown
**Оценка:**
- ✅ Правильно использует `IntentService`
- ✅ Разделяет логику по намерениям
- ❌ НЕТ physical simulation
- ❌ Промпты для "старой" механики
```

**Новое:**
```markdown
**Оценка:**
- ✅ Правильно использует `IntentService`
- 🟡 Рефакторинг на Strategy Pattern (Sprint 1)
- 🟡 Три стратегии обработки в разработке
- ❌ Function Calling ожидает Sprint 2

**Текущий статус:** Рефакторинг в процессе (Sprint 1)
```

- [ ] Обновить оценку
- [ ] Добавить ссылку на CURRENT_SPRINT.md

#### 4.2 Добавить новый подраздел: logic/strategies/

```markdown
#### 🟡 `logic/strategies/` ⭐ НОВЫЙ КОМПОНЕНТ

**Статус:** В разработке (Sprint 1)
**Назначение:** Стратегии обработки команд разной сложности

```python
# Структура
logic/strategies/
├── base_strategy.py           # ABC для всех стратегий
├── code_only_strategy.py      # Без AI (Sprint 1)
├── simple_llm_strategy.py     # 1 вызов (Sprint 1)
└── function_calling_strategy.py # 2 вызова (Sprint 2)
```

**Паттерн:**
```python
class BaseStrategy(ABC):
    @abstractmethod
    def execute(self, game, command, details) -> str:
        pass

# CODE_ONLY: мгновенно, бесплатно
# SIMPLE_LLM: 1 вызов Gemini
# COMPLEX_TOOL_CALL: Function Calling
```

**Оценка:**
- 🟡 В процессе реализации
- ✅ Архитектура спроектирована
- 🔴 Тесты ещё не написаны

**Требуемые изменения:** Завершить реализацию в Sprint 1
```

- [ ] Добавить раздел
- [ ] Указать ссылку на ARCHITECTURE_DECISION.md (ADR-003)

#### 4.3 Обновить services/intent_service.py

**Добавить информацию о новой функциональности:**

```markdown
**Новая функциональность (Sprint 1):**
```python
def recognize_intent(command: str) -> Dict[str, str]:
    """
    Теперь возвращает не только intent, но и complexity_type
    
    Returns:
        {
            "intent": "COMBAT",
            "complexity_type": "SIMPLE_LLM"
        }
    """
```

**Классификация сложности:**
- `CODE_ONLY`: детерминированные действия (инвентарь)
- `SIMPLE_LLM`: простые действия с нарративом (удар мечом)
- `COMPLEX_TOOL_CALL`: сложная физика (опрокинуть стол)

**Текущий статус:** Обновление в Sprint 1
```

- [ ] Добавить информацию
- [ ] Обновить примеры кода

---

### 5. Gap Analysis (Раздел 5)

#### 5.1 Обновить таблицу "Компоненты требующие доработки"

**Добавить строки:**

| Компонент | Текущее состояние | Требуемые изменения | Приоритет |
|-----------|-------------------|---------------------|-----------|
| `logic/director.py` | ~~Старая механика~~ | → Strategy Pattern | 🔴 Sprint 1 |
| `logic/strategies/` | НЕТ | → Три стратегии | 🔴 Sprint 1 |
| `services/intent_service.py` | ~~Только classification~~ | → + complexity_type | 🔴 Sprint 1 |
| `services/tool_registry.py` | НЕТ | → Function registry | 🟡 Sprint 2 |
| `tools/` | НЕТ | → Tool functions | 🟡 Sprint 2 |

- [ ] Добавить новые строки
- [ ] Обновить приоритеты

#### 5.2 Удалить устаревшие пункты

**Удалить (уже реализовано):**
- ~~`combat/body_system.py` - НЕТ~~ → ✅ Skeleton готов
- ~~`services/intent_service.py` - Только classification~~ → ✅ + Detail extraction

- [ ] Очистить устаревшие задачи

---

### 6. Development Roadmap (Раздел 6)

#### 6.1 Обновить статусы фаз

**Изменить:**
```markdown
### Фаза 1: Physical Body System ✅ ЗАВЕРШЕНА
### Фаза 2: Intent Detail Extraction ✅ ЗАВЕРШЕНА
```

**Добавить:**
```markdown
### Фаза 3: Command Routing Architecture 🟡 В ПРОЦЕССЕ (Sprint 1)

**Статус:** 🟡 АКТИВНАЯ РАЗРАБОТКА (Sprint 1: 14-21 октября 2025)

**Цель:** Внедрить трёхуровневую маршрутизацию команд

**Реализуемые компоненты:**

```python
# 3.1 🟡 Обновлён services/intent_service.py
class IntentService:
    def recognize_intent(command) -> Dict:
        # Теперь возвращает {"intent": "...", "complexity_type": "..."}

# 3.2 🟡 Создан logic/strategies/
class CodeOnlyStrategy(BaseStrategy):
    # Мгновенная обработка без AI

class SimpleLLMStrategy(BaseStrategy):
    # 1 вызов к Gemini

class FunctionCallingStrategy(BaseStrategy):
    # 2 вызова (заглушка для Sprint 2)

# 3.3 🟡 Рефакторинг logic/director.py
class Director:
    def process_command(game, command):
        result = self.intent_service.recognize_intent(command)
        strategy = self.strategies[result["complexity_type"]]
        return strategy.execute(game, command)
```

**Результат Фазы 3:** Оптимальное использование LLM ресурсов

**Definition of Done:**
- [ ] IntentService классифицирует по сложности
- [ ] Три стратегии работают
- [ ] Director использует Strategy Pattern
- [ ] 95%+ тестов проходят

**Ссылки:**
- [CURRENT_SPRINT.md](./sprints/CURRENT_SPRINT.md) - Детальный план Sprint 1
- [ARCHITECTURE_DECISION.md](./ARCHITECTURE_DECISION.md) - ADR-003
```

- [ ] Добавить Фазу 3
- [ ] Обновить нумерацию следующих фаз (+1)

#### 6.2 Переименовать старую "Фазу 3"

**Было:**
```markdown
### Фаза 3: Physical Simulation
```

**Стало:**
```markdown
### Фаза 4: Physical Simulation (ожидает команду физики)
```

- [ ] Обновить нумерацию Фазы 3 → 4
- [ ] Обновить нумерацию Фазы 4 → 5
- [ ] И так далее для всех последующих фаз

#### 6.3 Добавить новую фазу между текущими

**Вставить после Фазы 3:**

```markdown
### Фаза 4: Function Calling Implementation 🔴 ЗАПЛАНИРОВАНО (Sprint 2)

**Статус:** Ожидает завершения Sprint 1

**Цель:** Реализовать паттерн вызова инструментов для сложных команд

**Задачи:**
- [ ] Создать ToolRegistry
- [ ] Реализовать tool functions (заглушки для физики)
- [ ] Интеграция с Gemini API (function calling mode)
- [ ] Обновить FunctionCallingStrategy
- [ ] E2E тесты сложных команд

**Результат:** LLM может "вызывать" Python-функции

**Ссылки:**
- [BACKLOG.md](./sprints/BACKLOG.md) - Детальный план Sprint 2
- [ARCHITECTURE_DECISION.md](./ARCHITECTURE_DECISION.md) - ADR-002
```

- [ ] Вставить новую фазу
- [ ] Убедиться, что нумерация последующих фаз обновлена

---

### 7. Technical Specifications (Раздел 7)

#### 7.1 Добавить новый подраздел: "7.4 Command Routing Specification"

```markdown
### 7.4 Command Routing Specification

#### Intent Classification

**Input:**
```python
player_command: str  # "бью мечом по шее гоблина"
```

**Output:**
```python
{
    "intent": "COMBAT",           # Тип намерения
    "complexity_type": "SIMPLE_LLM"  # Уровень сложности
}
```

**Complexity Types:**

| Type | Description | Cost | Latency | Examples |
|------|-------------|------|---------|----------|
| CODE_ONLY | Детерминированные действия | Free | <10ms | инвентарь, статистика |
| SIMPLE_LLM | Простые с нарративом | ~$0.00001 | 500-1000ms | удар мечом, диалог |
| COMPLEX_TOOL_CALL | Сложная физика | ~$0.00002 | 1000-2000ms | опрокинуть стол |

#### Strategy Selection

**Input:**
```python
complexity_type: str
game_instance: Game
command: str
details: Dict  # от extract_action_details()
```

**Process:**
```python
if complexity_type == "CODE_ONLY":
    strategy = CodeOnlyStrategy()
elif complexity_type == "SIMPLE_LLM":
    strategy = SimpleLLMStrategy()
else:  # COMPLEX_TOOL_CALL
    strategy = FunctionCallingStrategy()

result = strategy.execute(game_instance, command, details)
```

**Output:**
```python
result: str  # Нарратив для игрока
```

#### Function Calling Flow (COMPLEX_TOOL_CALL)

**Step 1: Initial LLM Request**
```python
# Промпт
{
    "role": "system",
    "content": "You are a physics simulator. Available tools: calculate_physics"
}
{
    "role": "user",
    "content": "Player wants to: опрокинуть стол на врага"
}
```

**Step 2: LLM Response (tool call)**
```json
{
    "tool_calls": [{
        "name": "calculate_physics",
        "arguments": {
            "action": "push",
            "object": "table",
            "object_mass_kg": 50,
            "force_newtons": 200,
            "target": "enemy"
        }
    }]
}
```

**Step 3: Code Execution**
```python
result = PhysicalSimulator.calculate_physics(
    action="push",
    object_mass_kg=50,
    force_newtons=200
)
# Returns: {
#   "success": true,
#   "object_displaced_m": 2.5,
#   "target_hit": true,
#   "damage_to_target": {...}
# }
```

**Step 4: Final LLM Request**
```python
{
    "role": "tool",
    "content": json.dumps(result)
}
# LLM generates narrative based on results
```

**Step 5: Final Response**
```
"Вы с силой толкаете массивный стол. Он скользит по полу 
на 2.5 метра и врезается в гоблина, сбивая его с ног..."
```
```

- [ ] Добавить подраздел
- [ ] Включить примеры JSON

---

### 8. Appendix (Раздел 8)

#### 8.1 Обновить Glossary

**Добавить термины:**

| Термин | Определение |
|--------|-------------|
| **Command Router** | Компонент, классифицирующий команды по сложности |
| **Complexity Type** | Уровень сложности команды (CODE_ONLY/SIMPLE_LLM/COMPLEX) |
| **Strategy Pattern** | Паттерн проектирования для выбора алгоритма обработки |
| **Function Calling** | Паттерн, где LLM запрашивает выполнение функций кода |
| **Tool Registry** | Реестр доступных инструментов для Function Calling |
| **Tool Call** | Запрос LLM на выполнение конкретной функции |

- [ ] Добавить новые термины
- [ ] Отсортировать по алфавиту

#### 8.2 Обновить File Structure Reference

**Добавить новые директории:**

```markdown
├── logic/
│   ├── director.py                  🟡 Refactoring (Sprint 1)
│   ├── game_states.py               ✅
│   ├── constants.py                 ✅
│   └── strategies/                  🟡 NEW (Sprint 1)
│       ├── __init__.py              
│       ├── base_strategy.py         
│       ├── code_only_strategy.py    
│       ├── simple_llm_strategy.py   
│       └── function_calling_strategy.py
│
├── services/
│   ├── intent_service.py            🟡 Updated (Sprint 1)
│   ├── llm_service.py               ✅
│   ├── tool_registry.py             🔴 Planned (Sprint 2)
│   └── ...
│
├── tools/                            🔴 NEW (Sprint 2)
│   ├── __init__.py
│   ├── physics_tools.py
│   ├── inventory_tools.py
│   └── world_tools.py
```

- [ ] Добавить новые файлы/папки
- [ ] Обновить статусы существующих

#### 8.3 Добавить раздел "8.3 Sprint Links"

```markdown
### 8.3 Sprint & Task Management

**Активная разработка:**
- [CURRENT_SPRINT.md](./sprints/CURRENT_SPRINT.md) - Sprint 1: Director Refactoring
- [MASTER_PLAN.md](./MASTER_PLAN.md) - Общий план проекта

**Планирование:**
- [BACKLOG.md](./sprints/BACKLOG.md) - Очередь задач (Sprint 2-7)
- [DONE.md](./sprints/DONE.md) - История завершённых спринтов

**Архитектурные решения:**
- [ARCHITECTURE_DECISION.md](./ARCHITECTURE_DECISION.md) - ADR-001 до ADR-007
- [architectural_discussion.md](./architectural_discussion.md) - Полная история диалога

**Отчёты:**
- [phase_completion_report.md](./phase_completion_report.md) - Фазы 1-2
- [bugfixes_report.md](./bugfixes_report.md) - История багфиксов
```

- [ ] Добавить раздел с ссылками
- [ ] Проверить корректность путей

---

### 9. Conclusion (Раздел 9)

#### 9.1 Переписать заключение

**Текущее:** Устаревшее

**Новое:**
```markdown
## 9. CONCLUSION

### Текущее Состояние (v3.0)

Проект Silgarron находится в активной фазе развития с чётким архитектурным видением.

**Достигнуто:**
- ✅ Фаза 1-2 завершены (Body System, Intent Extraction)
- ✅ Skeleton боевой системы готов к интеграции
- ✅ Event Sourcing реализован
- ✅ Hex Grid система работает
- ✅ Новая архитектура спроектирована (ADR-001 до ADR-007)

**В Процессе:**
- 🟡 Sprint 1: Трёхуровневая маршрутизация (14-21 октября)
- 🟡 Рефакторинг Director на Strategy Pattern
- 🟡 Реализация трёх стратегий обработки

**Следующие Шаги:**
- 🔴 Sprint 2: Function Calling Implementation
- 🔴 Sprint 3: World Generation Refactoring
- 🔴 Sprint 4: Physics Integration (зависит от команды физики)

### Архитектурное Видение

Ключевое архитектурное решение — **трёхуровневая обработка команд**:

1. **Fast Router** (IntentService) — быстрая классификация
2. **Director** (Orchestrator) — выбор стратегии
3. **Strategies** (Executors) — выполнение с оптимальным использованием ресурсов

Этот подход обеспечивает баланс между:
- 🎯 **Интеллектом** (LLM для сложных задач)
- ⚡ **Скоростью** (код для простых действий)
- 💰 **Стоимостью** (дорогие вызовы только когда нужно)

### Дальнейшее Развитие

Проект следует принципу **итеративной разработки**:
- Каждый спринт добавляет работающий функционал
- Документация обновляется вместе с кодом
- Архитектурные решения фиксируются в ADR

**Система готова к масштабированию:**
- Параллельная работа команд (физика, генерация, AI)
- Чёткие интерфейсы между компонентами
- Comprehensive test coverage

### Ссылки

**Для разработчиков:**
- [MASTER_PLAN.md](./MASTER_PLAN.md) - Начни здесь
- [CURRENT_SPRINT.md](./sprints/CURRENT_SPRINT.md) - Что делать сейчас
- [ARCHITECTURE_DECISION.md](./ARCHITECTURE_DECISION.md) - Почему так

**Для новых участников:**
- [DOCUMENTATION_GUIDE.md](./DOCUMENTATION_GUIDE.md) - Как вести документацию
- [README.md](../README.md) - Быстрый старт

---

**Версия документа:** 3.0  
**Последнее обновление:** 14 октября 2025  
**Следующий пересмотр:** 21 октября 2025 (после Sprint 1)
```

- [ ] Переписать заключение
- [ ] Добавить ссылки на новые документы

---

## ⏱️ Время на Обновление

| Раздел | Задачи | Время |
|--------|--------|-------|
| 1. Executive Summary | 2 задачи | 5 мин |
| 2. Core Concept | 1 задача | 5 мин |
| 3. Architecture | 2 задачи | 20 мин |
| 4. Implementation | 3 задачи | 15 мин |
| 5. Gap Analysis | 2 задачи | 10 мин |
| 6. Roadmap | 3 задачи | 15 мин |
| 7. Specifications | 1 задача | 10 мин |
| 8. Appendix | 3 задачи | 10 мин |
| 9. Conclusion | 1 задача | 10 мин |

**Общее время:** ~1 час 40 минут

---

## 🎯 Приоритеты

### 🔴 Критические (сделать до начала Sprint 1)

- [ ] Раздел 3: Обновить диаграмму архитектуры
- [ ] Раздел 4: Добавить logic/strategies/
- [ ] Раздел 6: Добавить Фазу 3
- [ ] Раздел 8: Обновить File Structure

**Время:** ~45 минут

### 🟡 Важные (сделать в процессе Sprint 1)

- [ ] Раздел 1-2: Обновить метаданные
- [ ] Раздел 5: Обновить Gap Analysis
- [ ] Раздел 7: Добавить спецификации
- [ ] Раздел 9: Переписать заключение

**Время:** ~55 минут

---

## ✅ Финальная Проверка

После завершения обновлений:

- [ ] Все ссылки между документами работают
- [ ] Версия изменена на 3.0
- [ ] Дата обновлена на 14 октября 2025
- [ ] Нет противоречий с другими документами (MASTER_PLAN, ADR)
- [ ] Диаграммы соответствуют описанию
- [ ] Примеры кода актуальны
- [ ] Терминология консистентна

---

## 📝 Шаблон Коммита

После обновления TDD:

```bash
git add docs/Technical_Design_Document.md
git commit -m "docs: Update TDD to v3.0 - Three-tier command routing architecture

- Add new command routing architecture (Section 3)
- Update component statuses (Section 4)
- Add Phase 3: Command Routing (Section 6)
- Update roadmap and priorities
- Add Function Calling specification (Section 7)
- Refresh conclusion with current state

Related: Sprint 1, ADR-003, MASTER_PLAN.md"
```

---

**Документ:** TDD_UPDATE_CHECKLIST.md  
**Создан:** 14 октября 2025  
**Использовать:** Перед началом Sprint 1