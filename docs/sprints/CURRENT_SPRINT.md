# 🎯 SPRINT 1: Director Refactoring

**Спринт:** #1  
**Период:** 14 октября - 21 октября 2025 (7 дней)  
**Цель:** Внедрить трёхуровневую архитектуру маршрутизации команд

---

## 🎯 Цель Спринта

Реализовать новую архитектуру обработки команд с тремя уровнями сложности:
- **CODE_ONLY** - мгновенные действия без AI
- **SIMPLE_LLM** - простые действия с 1 вызовом AI
- **COMPLEX_TOOL_CALL** - сложные действия с Function Calling

---

## 📋 Задачи

### 1. Обновление IntentService
**Приоритет:** 🔴 Критический  
**Статус:** ⏳ Not Started  
**Владелец:** Ты

**Подзадачи:**
- [ ] **1.1** Обновить `data/intents.json` - добавить поле `complexity_type`
  ```json
  {
    "text": "посмотреть инвентарь",
    "metadata": {
      "intent": "INVENTORY",
      "complexity_type": "CODE_ONLY"
    }
  }
  ```
  **Время:** 30 минут

- [ ] **1.2** Изменить `IntentService.recognize_intent()` 
  - Возвращать не только `intent`, но и `complexity_type`
  - Сигнатура: `recognize_intent(command) -> Dict[str, str]`
  - Возвращает: `{"intent": "COMBAT", "complexity_type": "SIMPLE_LLM"}`
  - **ВАЖНО:** Добавить эвристические правила как второй слой
  - **ВАЖНО:** Добавить валидацию известных типов
  **Время:** 30 минут

- [ ] **1.3** Обновить тесты `test_intent_service.py`
  - Проверить возврат `complexity_type`
  - Добавить тесты для всех трёх типов
  - Тест на неизвестный тип (fallback)
  - Тест эвристических правил
  **Время:** 30 минут

**Общее время:** ~3.5 часа  
**Результат:** Три работающие стратегии обработки с защитой от ошибок

---

### 3. Рефакторинг Director
**Приоритет:** 🔴 Критический  
**Статус:** ⏳ Not Started  
**Владелец:** Ты

**Подзадачи:**

- [ ] **3.1** Обновить `logic/director.py` - паттерн Strategy
  ```python
  class Director:
      def __init__(self):
          self.intent_service = IntentService()
          self.strategies = {
              "CODE_ONLY": CodeOnlyStrategy(),
              "SIMPLE_LLM": SimpleLLMStrategy(),
              "COMPLEX_TOOL_CALL": FunctionCallingStrategy()
          }
      
      def process_command(self, game, command):
          # 1. Распознать тип сложности
          result = self.intent_service.recognize_intent(command)
          intent = result["intent"]
          complexity = result["complexity_type"]
          
          # 2. Валидация complexity_type
          if complexity not in self.strategies:
              logger.error(f"Unknown complexity: {complexity}")
              complexity = "SIMPLE_LLM"  # Fallback
              logger.info(f"Falling back to: {complexity}")
          
          # 3. Извлечь детали (если нужно)
          details = {}
          if complexity != "CODE_ONLY":
              details = self.intent_service.extract_action_details(command)
          
          # 4. Выбрать стратегию
          strategy = self.strategies[complexity]
          
          # 5. Выполнить
          return strategy.execute(game, command, details)
  ```
  **Время:** 2 часа

- [ ] **3.2** Удалить старые методы
  - Удалить `_handle_combat()`, `_handle_exploration()` 
  - Переместить логику в стратегии
  **Время:** 30 минут

- [ ] **3.3** Обновить вызовы в `game.py`
  - Изменить `director.decide_llm_action()` → `director.process_command()`
  **Время:** 15 минут

**Общее время:** ~2.5 часа  
**Результат:** Director использует Strategy Pattern

---

### 4. Интеграционное Тестирование
**Приоритет:** 🟡 Высокий  
**Статус:** ⏳ Not Started  
**Владелец:** Ты

**Подзадачи:**

- [ ] **4.1** Создать `tests/test_director_strategies.py`
  ```python
  def test_code_only_path():
      """Тест: посмотреть инвентарь → CODE_ONLY → мгновенный ответ"""
      
  def test_simple_llm_path():
      """Тест: ударить мечом → SIMPLE_LLM → 1 вызов"""
      
  def test_complex_path_stub():
      """Тест: опрокинуть стол → COMPLEX → TODO сообщение"""
  ```
  **Время:** 1.5 часа

- [ ] **4.2** End-to-End тест
  ```python
  def test_full_flow():
      game = Game()
      game.start_new_game()
      
      # CODE_ONLY
      result = game.process_player_input("посмотреть инвентарь")
      assert "Инвентарь" in result
      assert llm_calls == 0
      
      # SIMPLE_LLM
      result = game.process_player_input("ударить гоблина")
      assert llm_calls == 1
  ```
  **Время:** 1 час

- [ ] **4.3** Запустить все тесты
  - Проверить, что 95%+ тестов проходят
  - Исправить найденные баги
  **Время:** 1 час

**Общее время:** ~3.5 часа  
**Результат:** Все пути работают и протестированы

---

### 5. Документация
**Приоритет:** 🟢 Средний  
**Статус:** ⏳ Not Started  
**Владелец:** Ты

**Подзадачи:**

- [ ] **5.1** Обновить `Technical_Design_Document.md`
  - Раздел 3: Architecture Overview - новая диаграмма
  - Раздел 4: Статус компонентов
  **Время:** 45 минут

- [ ] **5.2** Создать `logic/strategies/README.md`
  ```markdown
  # Command Processing Strategies
  
  ## CODE_ONLY
  For: инвентарь, статистика
  Cost: Free
  Time: <10ms
  
  ## SIMPLE_LLM
  For: простые атаки, диалог
  Cost: ~0.001₽
  Time: 500-1000ms
  
  ## COMPLEX_TOOL_CALL
  For: сложная физика
  Cost: ~0.002₽
  Time: 1000-2000ms
  ```
  **Время:** 20 минут

- [ ] **5.3** Обновить `MASTER_PLAN.md`
  - Отметить Sprint 1 как завершённый
  - Обновить метрики прогресса
  **Время:** 10 минут

**Общее время:** ~1 час  
**Результат:** Актуальная документация

---

## 📊 Прогресс Спринта

```
┌─────────────────────────────────────────┐
│ SPRINT 1 PROGRESS                       │
├─────────────────────────────────────────┤
│ [░░░░░░░░░░░░░░░░░░░░] 0/5 completed   │
│                                         │
│ ⏳ IntentService Refactoring      0/3   │
│ ⏳ Strategy Implementation        0/5   │
│ ⏳ Director Refactoring           0/3   │
│ ⏳ Integration Testing            0/3   │
│ ⏳ Documentation                  0/3   │
└─────────────────────────────────────────┘
```

**Общее время:** ~12 часов работы  
**Прогресс:** 0% (0/17 подзадач)

---

## 🎯 Definition of Done (Sprint 1)

Спринт считается завершённым, когда:

- [x] ✅ IntentService возвращает `complexity_type`
- [x] ✅ Три стратегии работают (CODE_ONLY, SIMPLE_LLM, COMPLEX stub)
- [x] ✅ Director использует Strategy Pattern
- [x] ✅ 95%+ тестов проходят
- [x] ✅ Написаны интеграционные тесты
- [x] ✅ Документация обновлена
- [x] ✅ Нет критических багов

---

## 🚀 Следующий Sprint

**Sprint 2:** Function Calling Implementation  
**Дата старта:** 22 октября 2025  
**Цель:** Реализовать полноценный паттерн вызова инструментов для сложных команд

---

## 📝 Дневник Разработки

### День 1 (14 октября)
- Создана документационная система
- Написаны MASTER_PLAN, ARCHITECTURE_DECISION, CURRENT_SPRINT
- Готовимся к началу кодирования

### День 2 (15 октября)
_Запланировано: Задачи 1.1-1.3 (IntentService)_

### День 3 (16 октября)
_Запланировано: Задачи 2.1-2.3 (Стратегии: base, code_only)_

### День 4 (17 октября)
_Запланировано: Задачи 2.4-2.5, 3.1 (SimpleLLM, заглушка, начало Director)_

### День 5 (18 октября)
_Запланировано: Задачи 3.2-3.3, 4.1 (Завершение Director, начало тестов)_

### День 6 (19 октября)
_Запланировано: Задачи 4.2-4.3 (Интеграционные тесты, баг-фиксы)_

### День 7 (20-21 октября)
_Запланировано: Задача 5 (Документация), финальная проверка_

---

## 🔗 Связанные Документы

- [Master Plan](../MASTER_PLAN.md) - Общий план проекта
- [Architecture Decision Records](../ARCHITECTURE_DECISION.md) - История решений
- [Technical Design Document](../Technical_Design_Document.md) - Полная архитектура
- [Backlog](./BACKLOG.md) - Следующие спринты

---

## 💡 Заметки

### Риски и Митигации

#### Риск 1: Неверная классификация сложности
**Проблема:** IntentService может неправильно классифицировать команду  
**Последствие:** Простая команда идёт через дорогой COMPLEX путь, или сложная - через неадекватный CODE_ONLY

**Митигация:**
- [ ] Расширить `intents.json` примерами для всех типов (минимум 20 примеров на тип)
- [ ] Добавить эвристические правила как второй слой защиты
  ```python
  def _apply_heuristics(self, command: str, base_classification: str) -> str:
      """Дополнительная проверка классификации по ключевым словам"""
      # Ключевые слова для COMPLEX
      if any(word in command.lower() for word in 
             ['опрокинуть', 'бросить на', 'использовать окружение', 'сложная комбинация']):
          return "COMPLEX_TOOL_CALL"
      
      # Ключевые слова для CODE_ONLY
      if any(word in command.lower() for word in 
             ['инвентарь', 'статистика', 'посмотреть на себя']):
          return "CODE_ONLY"
      
      return base_classification  # Используем базовую классификацию
  ```
- [ ] Логировать все классификации для анализа
- [ ] После Sprint 1: провести анализ ошибок классификации

#### Риск 2: Неизвестный complexity_type
**Проблема:** Опечатка в `intents.json` или новый неизвестный тип  
**Последствие:** Программа падает с KeyError

**Митигация:**
- [ ] Добавить обработку неизвестных типов в Director
  ```python
  def process_command(self, game, command):
      result = self.intent_service.recognize_intent(command)
      complexity = result["complexity_type"]
      
      # Валидация
      if complexity not in self.strategies:
          logger.error(f"Unknown complexity type: {complexity}")
          # Fallback на SIMPLE_LLM как наиболее универсальный
          complexity = "SIMPLE_LLM"
          logger.info(f"Falling back to: {complexity}")
      
      strategy = self.strategies[complexity]
      return strategy.execute(game, command, details)
  ```
- [ ] Добавить валидацию `intents.json` при загрузке
  ```python
  def _validate_intents(self):
      """Проверяет, что все complexity_type известны"""
      valid_types = {"CODE_ONLY", "SIMPLE_LLM", "COMPLEX_TOOL_CALL"}
      for item in self.intents_data:
          complexity = item['metadata'].get('complexity_type')
          if complexity not in valid_types:
              raise ValueError(f"Invalid complexity_type: {complexity}")
  ```

#### Риск 3: Старые промпты несовместимы
**Проблема:** Промпты для старой архитектуры могут не работать  
**Последствие:** LLM возвращает неадекватные ответы

**Митигация:**
- [ ] Протестировать каждый промпт после миграции
- [ ] Обновить промпты для новой архитектуры
- [ ] Создать тесты для валидации промптов

### Идеи для будущего
- 💡 Кэш для частых команд (например, "посмотреть инвентарь")
- 💡 Метрики времени выполнения для каждой стратегии
- 💡 A/B тестирование разных промптов

---

**Статус:** 🏗️ В разработке  
**Последнее обновление:** 14 октября 2025:** ~1 час  
**Результат:** IntentService классифицирует команды по сложности

---

### 2. Создание Стратегий Обработки
**Приоритет:** 🔴 Критический  
**Статус:** ⏳ Not Started  
**Владелец:** Ты

**Подзадачи:**

- [ ] **2.1** Создать директорию `logic/strategies/`
  ```
  logic/strategies/
  ├── __init__.py
  ├── base_strategy.py        # Абстрактный класс
  ├── code_only_strategy.py   # Без AI
  ├── simple_llm_strategy.py  # 1 вызов
  └── function_calling_strategy.py  # 2 вызова (заглушка)
  ```
  **Время:** 10 минут

- [ ] **2.2** Реализовать `base_strategy.py`
  ```python
  from abc import ABC, abstractmethod
  
  class BaseStrategy(ABC):
      @abstractmethod
      def execute(self, game_instance, command: str, details: Dict) -> str:
          """Выполнить команду и вернуть результат."""
          pass
  ```
  **Время:** 5 минут

- [ ] **2.3** Реализовать `CodeOnlyStrategy`
  - Обрабатывать: инвентарь, статистика, простые действия
  - БЕЗ вызовов LLM
  - Возвращать шаблонный текст
  **Время:** 1 час

- [ ] **2.4** Реализовать `SimpleLLMStrategy`
  - Делать 1 вызов к Gemini с контекстом
  - Использовать существующие промпты из `prompts/`
  **Время:** 1.5 часа

- [ ] **2.5** Создать заглушку `FunctionCallingStrategy`
  - Пока возвращать TODO-сообщение
  - Полная реализация в Sprint 2
  **Время:** 15 минут

**Общее время