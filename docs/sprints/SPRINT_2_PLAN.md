# 🎯 SPRINT 2: Function Calling Implementation

**Спринт:** #2  
**Период:** 22 октября - 1 ноября 2025 (10 дней)  
**Цель:** Реализовать паттерн вызова инструментов для сложных команд

---

## 🎯 Цель Спринта

Реализовать полноценный **Function Calling Pattern**, чтобы LLM могла активно запрашивать данные из кода для принятия физически обоснованных решений.

**Что это даёт:**
- LLM не галлюцинирует данные ("стол весит 50кг" основано на реальном расчёте)
- Код остаётся главным по части физики
- Нарратив основан на фактических результатах

---

## 📋 Задачи

### 1. Спроектировать Tool Registry
**Приоритет:** 🔴 Критический  
**Статус:** ⏳ Not Started  
**Зависимости:** Sprint 1 завершён

**Подзадачи:**

- [ ] **1.1** Создать `services/tool_registry.py`
  ```python
  class ToolRegistry:
      """
      Реестр всех доступных инструментов для Function Calling.
      Каждый инструмент описывается для LLM в формате JSON Schema.
      """
      def __init__(self):
          self.tools = {}
      
      def register(self, name: str, func: Callable, schema: Dict):
          """Зарегистрировать новый инструмент"""
          
      def get_tool_descriptions(self) -> List[Dict]:
          """Получить описания всех инструментов для Gemini"""
          
      def execute_tool(self, name: str, arguments: Dict) -> Dict:
          """Выполнить инструмент и вернуть результат"""
  ```
  **Время:** 1 час

- [ ] **1.2** Определить JSON Schema для инструментов
  ```python
  # Пример схемы для calculate_physics
  {
      "name": "calculate_physics",
      "description": "Calculate physical results of an action",
      "parameters": {
          "type": "object",
          "properties": {
              "action": {
                  "type": "string",
                  "enum": ["push", "pull", "throw", "strike"],
                  "description": "Type of physical action"
              },
              "object_mass_kg": {
                  "type": "number",
                  "description": "Mass of object in kilograms"
              },
              "force_newtons": {
                  "type": "number",
                  "description": "Applied force in Newtons"
              }
          },
          "required": ["action", "object_mass_kg", "force_newtons"]
      }
  }
  ```
  **Время:** 2 часа

- [ ] **1.3** Написать тесты для ToolRegistry
  ```python
  def test_register_tool():
      registry = ToolRegistry()
      registry.register("test_tool", lambda x: x*2, {...})
      assert "test_tool" in registry.tools
  
  def test_execute_tool():
      registry = ToolRegistry()
      registry.register("calc", lambda a, b: a + b, {...})
      result = registry.execute_tool("calc", {"a": 2, "b": 3})
      assert result == 5
  ```
  **Время:** 1 час

**Общее время:** ~4 часа  
**Результат:** ToolRegistry готов к регистрации инструментов

---

### 2. Реализовать Tool Functions
**Приоритет:** 🔴 Критический  
**Статус:** ⏳ Not Started

**Подзадачи:**

- [ ] **2.1** Создать директорию `tools/`
  ```
  tools/
  ├── __init__.py
  ├── physics_tools.py      # Физические расчёты
  ├── inventory_tools.py    # Работа с инвентарём
  ├── world_tools.py        # Информация о мире
  └── combat_tools.py       # Боевые расчёты
  ```
  **Время:** 10 минут

- [ ] **2.2** Реализовать `physics_tools.py`
  ```python
  def calculate_physics(action: str, object_mass_kg: float, 
                       force_newtons: float, **kwargs) -> Dict:
      """
      ЗАГЛУШКА для физических расчётов.
      Полная реализация будет от команды физики.
      
      Returns:
          {
              "success": bool,
              "object_displaced_m": float,
              "damage": Dict,
              "narrative_hints": List[str]
          }
      """
      # Простые формулы для демонстрации
      acceleration = force_newtons / object_mass_kg
      displacement = 0.5 * acceleration * (1.0 ** 2)  # t=1 sec
      
      return {
          "success": True,
          "object_displaced_m": displacement,
          "damage": {"type": "blunt", "severity": "moderate"},
          "narrative_hints": [
              f"Object moves {displacement:.1f} meters",
              "Impact creates loud crash"
          ]
      }
  ```
  **Время:** 2 часа

- [ ] **2.3** Реализовать `inventory_tools.py`
  ```python
  def get_item_properties(item_name: str, character) -> Dict:
      """Получить свойства предмета из инвентаря"""
      
  def check_item_availability(item_name: str, character) -> bool:
      """Проверить, есть ли предмет"""
  ```
  **Время:** 1 час

- [ ] **2.4** Реализовать `world_tools.py`
  ```python
  def get_location_objects(location) -> List[Dict]:
      """Получить список объектов в локации"""
      
  def get_object_properties(object_name: str, location) -> Dict:
      """Получить физические свойства объекта мира"""
  ```
  **Время:** 1 час

- [ ] **2.5** Реализовать `combat_tools.py`
  ```python
  def get_enemy_stats(enemy_name: str, game) -> Dict:
      """Получить характеристики врага"""
      
  def calculate_damage_potential(weapon: str, target: str) -> Dict:
      """Оценить потенциальный урон"""
  ```
  **Время:** 1.5 часа

- [ ] **2.6** Написать тесты для всех tools
  **Время:** 2 часа

**Общее время:** ~7.5 часа  
**Результат:** Библиотека инструментов готова

---

### 3. Интеграция с Gemini API
**Приоритет:** 🔴 Критический  
**Статус:** ⏳ Not Started

**Подзадачи:**

- [ ] **3.1** Обновить `services/llm_service.py`
  ```python
  class LLMService:
      def call_with_tools(self, 
                         messages: List[Dict],
                         tools: List[Dict],
                         max_iterations: int = 3) -> str:
          """
          Вызов LLM с поддержкой function calling.
          
          Process:
          1. Отправить запрос с tool descriptions
          2. Если LLM возвращает tool_calls → выполнить
          3. Отправить результаты обратно
          4. Получить финальный ответ
          
          Args:
              messages: История диалога
              tools: Описания доступных инструментов
              max_iterations: Макс число tool calls
          """
          iteration = 0
          
          while iteration < max_iterations:
              response = self.gemini.generate_content(
                  messages,
                  tools=tools,
                  tool_config={"function_calling_config": "AUTO"}
              )
              
              # Проверяем, вернула ли LLM tool_call
              if response.candidates[0].content.parts[0].function_call:
                  # Выполняем инструмент
                  tool_result = self._execute_tool_call(response)
                  # Добавляем результат в messages
                  messages.append(tool_result)
                  iteration += 1
              else:
                  # Финальный ответ
                  return response.text
          
          raise Exception("Max tool call iterations exceeded")
  ```
  **Время:** 3 часа

- [ ] **3.2** Реализовать обработку tool_calls
  ```python
  def _execute_tool_call(self, response) -> Dict:
      """
      Извлекает tool_call из ответа LLM,
      выполняет через ToolRegistry,
      форматирует результат для следующего запроса.
      """
      function_call = response.candidates[0].content.parts[0].function_call
      tool_name = function_call.name
      arguments = dict(function_call.args)
      
      # Выполнить через registry
      result = tool_registry.execute_tool(tool_name, arguments)
      
      # Форматировать для LLM
      return {
          "role": "function",
          "name": tool_name,
          "content": json.dumps(result)
      }
  ```
  **Время:** 2 часа

- [ ] **3.3** Добавить логирование tool calls
  ```python
  # Логировать каждый вызов для отладки
  logger.info(f"Tool call: {tool_name}")
  logger.info(f"Arguments: {arguments}")
  logger.info(f"Result: {result}")
  ```
  **Время:** 30 минут

- [ ] **3.4** Тесты интеграции с Gemini
  **Время:** 2 часа

**Общее время:** ~7.5 часа  
**Результат:** LLM может вызывать инструменты

---

### 4. Обновить FunctionCallingStrategy
**Приоритет:** 🔴 Критический  
**Статус:** ⏳ Not Started

**Подзадачи:**

- [ ] **4.1** Заменить заглушку реальной реализацией
  ```python
  class FunctionCallingStrategy(BaseStrategy):
      def __init__(self):
          self.llm_service = LLMService()
          self.tool_registry = ToolRegistry()
          self._register_all_tools()
      
      def execute(self, game, command: str, details: Dict) -> str:
          # 1. Собрать контекст
          context = self._build_context(game, details)
          
          # 2. Подготовить messages
          messages = [
              {"role": "system", "content": SYSTEM_PROMPT},
              {"role": "user", "content": self._format_command(command, context)}
          ]
          
          # 3. Получить tool descriptions
          tools = self.tool_registry.get_tool_descriptions()
          
          # 4. Вызвать LLM с tools
          narrative = self.llm_service.call_with_tools(messages, tools)
          
          return narrative
  ```
  **Время:** 2 часа

- [ ] **4.2** Реализовать `_register_all_tools()`
  ```python
  def _register_all_tools(self):
      from tools.physics_tools import calculate_physics
      from tools.inventory_tools import get_item_properties
      from tools.world_tools import get_location_objects
      
      self.tool_registry.register("calculate_physics", 
                                  calculate_physics, 
                                  PHYSICS_TOOL_SCHEMA)
      # ... остальные инструменты
  ```
  **Время:** 1 час

- [ ] **4.3** Написать промпт для function calling режима
  ```python
  SYSTEM_PROMPT = """
  You are a physics simulator for a text RPG.
  
  When player takes an action, you must:
  1. Use available tools to get actual data
  2. Never make up physical properties
  3. Base narrative on tool results
  
  Available tools:
  - calculate_physics: for physical interactions
  - get_item_properties: for inventory items
  - get_location_objects: for world objects
  
  Process:
  1. Analyze player's command
  2. Call necessary tools to gather data
  3. Generate realistic narrative based on results
  """
  ```
  **Время:** 1 час

**Общее время:** ~4 часа  
**Результат:** FunctionCallingStrategy полностью работает

---

### 5. Тестирование
**Приоритет:** 🟡 Высокий  
**Статус:** ⏳ Not Started

**Подзадачи:**

- [ ] **5.1** E2E тест: "опрокинуть стол на врага"
  ```python
  def test_complex_action_with_function_calling():
      game = Game()
      game.start_new_game()
      
      # Сложное действие
      result = game.process_player_input("опрокинуть стол на гоблина")
      
      # Проверяем, что:
      # 1. Были вызваны tools
      assert len(tool_call_log) > 0
      # 2. calculate_physics был вызван
      assert "calculate_physics" in [call.name for call in tool_call_log]
      # 3. Нарратив основан на результатах
      assert "стол" in result.lower()
      # 4. Враг получил урон
      assert game.current_location.enemies[0].body.has_wounds()
  ```
  **Время:** 2 часа

- [ ] **5.2** Тест валидации tool call arguments
  ```python
  def test_tool_call_validation():
      # LLM должна передавать корректные аргументы
      # Проверяем обработку ошибок
  ```
  **Время:** 1 час

- [ ] **5.3** Тест max_iterations
  ```python
  def test_max_iterations_protection():
      # Защита от бесконечного цикла tool calls
  ```
  **Время:** 30 минут

- [ ] **5.4** Performance тесты
  ```python
  def test_function_calling_latency():
      # Измерить время на сложное действие
      # Ожидаемое: 1-2 секунды
  ```
  **Время:** 1 час

**Общее время:** ~4.5 часа  
**Результат:** Всё протестировано и работает

---

### 6. Документация
**Приоритет:** 🟢 Средний  
**Статус:** ⏳ Not Started

**Подзадачи:**

- [ ] **6.1** Создать `tools/README.md`
  - Список всех инструментов
  - Как добавить новый инструмент
  - Примеры использования
  **Время:** 30 минут

- [ ] **6.2** Обновить `services/README.md`
  - Добавить ToolRegistry
  - Обновить LLMService
  **Время:** 20 минут

- [ ] **6.3** Обновить `Technical_Design_Document.md`
  - Раздел "Function Calling Specification"
  - Диаграммы flow
  **Время:** 1 час

- [ ] **6.4** Создать ADR-008: Tool Design Decisions
  - Почему выбрали такую архитектуру tools
  - Альтернативы
  **Время:** 30 минут

**Общее время:** ~2 часа  
**Результат:** Документация актуальна

---

## 📊 Прогресс Спринта

```
┌─────────────────────────────────────────┐
│ SPRINT 2 PROGRESS                       │
├─────────────────────────────────────────┤
│ [░░░░░░░░░░░░░░░░░░░░] 0/6 completed   │
│                                         │
│ ⏳ Tool Registry              0/3       │
│ ⏳ Tool Functions             0/6       │
│ ⏳ Gemini Integration         0/4       │
│ ⏳ Strategy Update            0/3       │
│ ⏳ Testing                    0/4       │
│ ⏳ Documentation              0/4       │
└─────────────────────────────────────────┘
```

**Общее время:** ~30 часов работы  
**Прогресс:** 0% (0/24 подзадач)

---

## 🎯 Definition of Done (Sprint 2)

Спринт считается завершённым, когда:

- [ ] ✅ ToolRegistry работает и протестирован
- [ ] ✅ Минимум 4 tool functions реализованы
- [ ] ✅ Gemini API интеграция работает
- [ ] ✅ FunctionCallingStrategy использует реальные tools
- [ ] ✅ E2E тест "опрокинуть стол" проходит
- [ ] ✅ Документация обновлена
- [ ] ✅ 95%+ тестов проходят
- [ ] ✅ Нет критических багов

---

## 🚀 Следующий Sprint

**Sprint 3:** World Generation Refactoring  
**Дата старта:** 2 ноября 2025  
**Цель:** Улучшить процедурную генерацию на основе тегов

---

## 📝 Дневник Разработки

_Будет заполняться в процессе спринта..._

---

**Статус:** 🏗️ Готов к началу (после завершения Sprint 1)  
**Последнее обновление:** 14 октября 2025