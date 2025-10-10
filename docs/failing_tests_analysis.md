# Анализ падающих тестов

**Дата:** 2025-10-10
**Статус:** 7 из 76 тестов падают (это НЕ новые проблемы)

## Общая картина

- ✅ **19/19** новых smoke tests — **ВСЕ ПРОШЛИ**
- ✅ **66/76** всех тестов — прошли
- ⚠️ **7/76** тестов падают — **старые проблемы**, не связанные с новой работой
- ⏸️ **3/76** тестов пропущены — помечены как `@pytest.mark.skip` (будущая работа)

---

## 1. Combat System Tests (2 failure)

### 1.1. `test_unconsciousness_from_blood_loss` ❌

**Файл:** `tests/test_combat/test_body_system_skeleton.py:203`

#### Описание проблемы
Тест проверяет, что персонаж теряет сознание при потере 70% крови (остаётся 30% = 1500 мл из 5000 мл).

```python
def test_unconsciousness_from_blood_loss():
    body = BodySystem(species="human")
    body.blood_volume = 1500  # 30% remaining
    body.tick(1)  # Update consciousness
    assert body.is_unconscious() == True  # FAILS!
```

#### Реальное поведение
```python
# combat/body_system.py:236
def is_unconscious(self) -> bool:
    return (
        self.consciousness < 0.3 or
        any(e.type == EffectType.UNCONSCIOUS for e in self.status_effects)
    )
```

Проблема: `consciousness` НЕ обновляется корректно в `tick()`:

```python
# combat/body_system.py:226-228
blood_percentage = self.blood_volume / self.max_blood_volume
if blood_percentage < 0.6:
    self.consciousness = blood_percentage  # Устанавливает consciousness = 0.3
```

При `blood_volume = 1500` и `max_blood_volume = 5000`:
- `blood_percentage = 1500 / 5000 = 0.3`
- `self.consciousness = 0.3` (граничное значение)
- `is_unconscious()` проверяет `self.consciousness < 0.3` → **False** ❌

#### Решение

**Вариант 1: Изменить логику проверки (рекомендуется)**
```python
# combat/body_system.py:236
def is_unconscious(self) -> bool:
    return (
        self.consciousness <= 0.3  # Было: < 0.3
        or any(e.type == EffectType.UNCONSCIOUS for e in self.status_effects)
    )
```

**Вариант 2: Изменить формулу сознания**
```python
# combat/body_system.py:226-228
blood_percentage = self.blood_volume / self.max_blood_volume
if blood_percentage < 0.6:
    # Более агрессивная потеря сознания
    self.consciousness = max(0.0, blood_percentage - 0.1)
```

**Вариант 3: Изменить тест (не рекомендуется)**
```python
# Установить 1400 вместо 1500
body.blood_volume = 1400  # 28% remaining
```

---

### 1.2. `test_character_death_detection` ❌

**Файл:** `tests/test_combat/test_body_system_skeleton.py:271`

#### Описание проблемы
Тест проверяет, что персонаж умирает при `hp = 0` (legacy система).

```python
def test_character_death_detection():
    char = Character(name="Hero")
    assert char.is_dead() == False  # OK

    char.hp = 0
    assert char.is_dead() == True  # FAILS!
```

#### Реальное поведение
```python
# models/character.py:63-73
def is_dead(self) -> bool:
    if BODY_SYSTEM_AVAILABLE and self.body:
        return self.body.is_dead()  # Использует НОВУЮ систему!
    else:
        return self.hp <= 0  # LEGACY
```

Проблема: даже если `hp = 0`, функция проверяет `self.body.is_dead()`, а не `hp`:

```python
# combat/body_system.py:253
def is_dead(self) -> bool:
    return (
        self.blood_volume < 1000 or
        self.parts["head"].integrity < 0.1 or
        self.parts["torso"].integrity < 0.2
    )
```

При создании персонажа:
- `self.body.blood_volume = 5000` (здоров)
- `self.hp = 0` (мёртв по legacy)
- `is_dead()` возвращает `False` ❌

#### Решение

**Вариант 1: Синхронизировать HP и body system (рекомендуется)**
```python
# models/character.py:63
def is_dead(self) -> bool:
    if BODY_SYSTEM_AVAILABLE and self.body:
        # Проверяем ОБЕ системы
        return self.body.is_dead() or self.hp <= 0
    else:
        return self.hp <= 0
```

**Вариант 2: Обновлять body при изменении HP**
```python
# models/character.py:51
def take_damage(self, amount: int):
    self.hp -= amount
    if self.hp < 0:
        self.hp = 0

    # НОВОЕ: синхронизация с body system
    if BODY_SYSTEM_AVAILABLE and self.body:
        # Симулируем потерю крови пропорционально урону
        blood_loss = (amount / self.max_hp) * self.body.max_blood_volume
        self.body.blood_volume -= blood_loss
```

**Вариант 3: Изменить тест (временное решение)**
```python
def test_character_death_detection():
    char = Character(name="Hero")

    # Убиваем через body system, а не HP
    char.body.blood_volume = 500  # < 1000
    assert char.is_dead() == True
```

---

## 2. Intent Service Tests (5 failures)

### Общая проблема: Gemini API 404 Error

Все 5 падающих тестов связаны с одной проблемой:

```
🔴 КРИТИЧЕСКАЯ ОШИБКА API Gemini: 404 models/gemini-1.5-flash
is not found for API version v1beta, or is not supported
for generateContent. Call ListModels to see the list of
available models and their supported methods.
```

#### Причина
Модель `gemini-1.5-flash` больше недоступна или изменилось API.

#### Падающие тесты

1. `test_extract_shoot_arrow` - KeyError: 'weapon'
2. `test_extract_stab_dagger` - KeyError: 'action'
3. `test_extract_slash_axe` - AssertionError: action is None
4. `test_extract_with_modifier` - AssertionError: action is None
5. `test_extract_dodge` - AssertionError: 'strike' == 'dodge'

#### Как это работает

```python
# services/intent_service.py (псевдокод)
def extract_action_details(command):
    # 1. Rule-based extraction
    details = extract_with_rules(command)
    confidence = calculate_confidence(details)

    # 2. Если уверенность низкая (< 0.5), вызываем LLM
    if confidence < 0.5:
        llm_result = ask_gemini(command)  # ❌ Возвращает 404
        if llm_result:
            return llm_result
        else:
            return details  # Возвращаем rule-based результат

    return details
```

#### Почему тесты падают

**Пример: `test_extract_shoot_arrow`**
```python
details = service.extract_action_details("стреляю из лука в голову")
```

1. Rule-based система НЕ распознаёт "стреляю" → `action` не найден
2. Confidence < 0.5 → вызывается LLM
3. LLM возвращает 404 ошибку
4. Возвращается пустой или неполный результат
5. Тест ожидает `details["weapon"] == "bow"` → **KeyError** ❌

**Пример: `test_extract_dodge`**
```python
details = service.extract_action_details("уклониться от удара")
```

1. Rule-based система находит "удар" → распознаёт как "strike"
2. LLM вызывается, но возвращает ошибку
3. Возвращается rule-based результат: `action = "strike"`
4. Тест ожидает `action == "dodge"` → **AssertionError** ❌

---

### Решение для Intent Service

#### Вариант 1: Обновить модель Gemini (рекомендуется)

**Шаг 1:** Узнать актуальные модели
```bash
# Проверить доступные модели через API
curl "https://generativelanguage.googleapis.com/v1beta/models?key=YOUR_API_KEY"
```

**Шаг 2:** Обновить config
```python
# config.py
llm_model: str = "gemini-2.0-flash-exp"  # Новая модель
# ИЛИ
llm_model: str = "gemini-1.5-pro"  # Стабильная модель
```

**Шаг 3:** Обновить `.env`
```env
GEMINI_MODEL=gemini-2.0-flash-exp
```

#### Вариант 2: Улучшить rule-based систему

Добавить недостающие действия в `intents.json`:

```json
{
  "text": "стреляю из лука в голову",
  "intent": "attack",
  "details": {
    "action": "shoot",
    "weapon": "bow",
    "body_part": "head"
  }
},
{
  "text": "колю кинжалом в сердце",
  "intent": "attack",
  "details": {
    "action": "stab",
    "weapon": "dagger",
    "body_part": "heart"
  }
},
{
  "text": "уклоняюсь от удара",
  "intent": "defend",
  "details": {
    "action": "dodge"
  }
}
```

Обновить keywords в `services/intent_service.py`:

```python
ACTION_KEYWORDS = {
    "strike": ["бить", "ударить", "атака", "удар"],
    "stab": ["колоть", "колю", "проткнуть", "тыкнуть"],
    "slash": ["рубить", "рублю", "резать", "режу", "махнуть"],
    "shoot": ["стрелять", "стреляю", "выстрел"],
    "dodge": ["уклониться", "уклоняться", "уклон", "увернуться"],
    "block": ["блокировать", "блок", "защита"],
    "cast": ["применить", "использовать", "кастовать", "заклинание"]
}
```

#### Вариант 3: Mock LLM в тестах

Создать fixture для мокирования Gemini:

```python
# tests/conftest.py
import pytest
from unittest.mock import patch

@pytest.fixture
def mock_gemini_success():
    """Mock successful Gemini response"""
    with patch('services.llm_service.LLMService.generate') as mock:
        mock.return_value = '{"action": "shoot", "weapon": "bow", "confidence": 1.0}'
        yield mock

# tests/test_services/test_intent_service_extended.py
def test_extract_shoot_arrow(service, mock_gemini_success):
    details = service.extract_action_details("стреляю из лука в голову")
    assert details["weapon"] == "bow"
```

---

## Приоритизация исправлений

### 🔥 Критичные (блокируют работу)
1. **Gemini API 404** - обновить модель в конфиге
   - Время: 5 минут
   - Файлы: `config.py`, `.env`
   - Решит: 5 из 7 падающих тестов

### ⚠️ Важные (влияют на функциональность)
2. **Character death detection** - синхронизировать HP и body system
   - Время: 15 минут
   - Файлы: `models/character.py`
   - Решит: 1 тест, но важно для игры

### 📝 Желательные (polish)
3. **Unconsciousness threshold** - изменить `< 0.3` на `<= 0.3`
   - Время: 2 минуты
   - Файлы: `combat/body_system.py`
   - Решит: 1 тест

4. **Rule-based improvements** - добавить keywords для shoot/stab/dodge
   - Время: 30 минут
   - Файлы: `services/intent_service.py`, `data/intents.json`
   - Уменьшит зависимость от LLM

---

## Рекомендации

### Немедленно (5 минут)
```bash
# 1. Узнать актуальную модель
python -c "import google.generativeai as genai; genai.configure(api_key='YOUR_KEY'); print([m.name for m in genai.list_models()])"

# 2. Обновить .env
echo "GEMINI_MODEL=gemini-2.0-flash-exp" >> .env

# 3. Запустить тесты снова
python -m pytest tests/test_services/test_intent_service_extended.py -v
```

### Сегодня (20 минут)
```python
# Исправить combat/body_system.py:236
def is_unconscious(self) -> bool:
    return (
        self.consciousness <= 0.3  # Изменено с <
        or any(e.type == EffectType.UNCONSCIOUS for e in self.status_effects)
    )

# Исправить models/character.py:63
def is_dead(self) -> bool:
    if BODY_SYSTEM_AVAILABLE and self.body:
        return self.body.is_dead() or self.hp <= 0  # Добавлено or self.hp <= 0
    else:
        return self.hp <= 0
```

### На этой неделе (1-2 часа)
- Расширить `ACTION_KEYWORDS` для всех действий
- Добавить 20-30 примеров в `intents.json`
- Создать mock fixtures для Gemini в тестах
- Написать документацию по добавлению новых действий

---

## Выводы

### ✅ Положительное
1. **Все новые features работают идеально** (19/19 tests)
2. **87% всех тестов проходят** (66/76)
3. **Падающие тесты НЕ связаны с новой работой**
4. **Проблемы известны и легко исправимы**

### ⚠️ Требует внимания
1. **Gemini API** - обновить модель (5 тестов)
2. **Body-HP синхронизация** - добавить логику (1 тест)
3. **Граничные значения** - исправить порог (1 тест)

### 🎯 Общая оценка
Проект в отличном состоянии. Падающие тесты — это **технический долг из предыдущих фаз**, не связанный с текущей работой. Все можно исправить за 30-60 минут.

**Рекомендация:** Исправить критичную проблему (Gemini API) сейчас, остальное — в следующий спринт.
