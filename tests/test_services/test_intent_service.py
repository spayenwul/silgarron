import pytest
from services.intent_service import IntentService

@pytest.fixture
def service():
    return IntentService()

# ===============================================================
# ======== БАЗОВЫЕ ТЕСТЫ (ОДНО ДЕЙСТВИЕ) ========
# ===============================================================

def test_simple_strike_with_instrument(service):
    result = service.parse_command_sequence("бью гоблина мечом")
    
    assert len(result) == 1
    action = result[0]
    assert action["action"] == "strike"
    assert action["target_entity"] == "гоблин"  # ИСПРАВЛЕНО
    assert action["instrument_entity"] == "меч" # ИСПРАВЛЕНО

def test_full_command_with_all_parts(service):
    result = service.parse_command_sequence("осторожно рублю огромного орка секирой по голове")
    
    assert len(result) == 1
    action = result[0]
    assert action["action"] == "slash"
    assert action["target_entity"] == "орк"      # ИСПРАВЛЕНО
    assert action["instrument_entity"] == "секира" # ИСПРАВЛЕНО
    assert action["body_part_entity"] == "голова" # ИСПРАВЛЕНО
    assert action["modifier"] == "carefully"

def test_unarmed_strike(service):
    result = service.parse_command_sequence("ударь скелета")
    
    assert len(result) == 1
    action = result[0]
    assert action["action"] == "strike"
    assert action["target_entity"] == "скелет" # ИСПРАВЛЕНО
    assert "instrument_entity" not in action

# ===============================================================
# ======== ТЕСТЫ ПОСЛЕДОВАТЕЛЬНОСТЕЙ (НЕСКОЛЬКО ДЕЙСТВИЙ) ========
# ===============================================================

def test_simple_sequence_two_actions(service):
    result = service.parse_command_sequence("подойди к троллю и ударь его")
    
    assert len(result) == 2
    
    action1 = result[0]
    assert action1["action"] == "move"
    assert action1["target_entity"] == "тролль" # ИСПРАВЛЕНО

    action2 = result[1]
    assert action2["action"] == "strike"

def test_sequence_with_different_instruments(service):
    result = service.parse_command_sequence("атакую гоблина мечом, а затем кидаю в него камень")
    
    assert len(result) == 2

    action1 = result[0]
    assert action1["instrument_entity"] == "меч" # ИСПРАВЛЕНО

    action2 = result[1]
    assert action2["action"] == "throw"
    assert action2["instrument_entity"] == "камень" # ИСПРАВЛЕНО
    
def test_long_sequence_four_actions(service):
    result = service.parse_command_sequence("подбеги к скелету, ударь его щитом, потом рубани мечом и отскочи")
    
    assert len(result) == 4
    
    assert result[0]["action"] == "move"
    assert result[1]["action"] == "strike"
    assert result[1]["instrument_entity"] == "щит" # ИСПРАВЛЕНО
    assert result[2]["action"] == "slash"
    assert result[2]["instrument_entity"] == "меч" # ИСПРАВЛЕНО
    assert result[3]["action"] == "dodge"

# ===============================================================
# ======== ТЕСТЫ ПРОБРОСА КОНТЕКСТА ========
# ===============================================================

def test_context_propagation_target(service):
    result = service.parse_command_sequence("атакую злобного орка топором, а затем просто рублю")
    
    assert len(result) == 2
    
    action1 = result[0]
    assert action1["target_entity"] == "орк" # ИСПРАВЛЕНО

    action2 = result[1]
    assert "target_entity" in action2
    assert action2["target_entity"] == "орк" # Ключевая проверка

def test_context_override(service):
    result = service.parse_command_sequence("бью гоблина мечом, а затем рублю скелета топором")
    
    assert len(result) == 2
    
    action1 = result[0]
    assert action1["target_entity"] == "гоблин" # ИСПРАВЛЕНО

    action2 = result[1]
    assert action2["target_entity"] == "скелет" # ИСПРАВЛЕНО

# ===============================================================
# ======== ТЕСТЫ УНИВЕРСАЛЬНОГО ИНСТРУМЕНТА ========
# ===============================================================

def test_using_mundane_object_as_instrument(service):
    result = service.parse_command_sequence("кидаю в стражника тяжелой книгой")
    
    assert len(result) == 1
    action = result[0]
    assert action["action"] == "throw"
    assert action["target_entity"] == "стражник" # ИСПРАВЛЕНО
    assert action["instrument_entity"] == "книга" # ИСПРАВЛЕНО

def test_using_environment_as_instrument(service):
    result = service.parse_command_sequence("бью паука горящей веткой")
    
    assert len(result) == 1
    action = result[0]
    assert action["action"] == "strike"
    assert action["target_entity"] == "паук" # ИСПРАВЛЕНО
    assert action["instrument_entity"] == "ветка" # ИСПРАВЛЕНО

def test_defend_with_any_object(service):
    result = service.parse_command_sequence("блокирую удар столом")
    
    assert len(result) == 1
    action = result[0]
    assert action["action"] == "block"
    assert action["instrument_entity"] == "стол" # ИСПРАВЛЕНО

# ===============================================================
# ======== EDGE CASES И ОСОБЫЕ СЛУЧАИ ========
# ===============================================================

# Эти тесты уже проходили, так как в них не было сущностей для нормализации
# Но я оставляю их для полноты картины

def test_empty_command(service):
    result = service.parse_command_sequence("")
    assert result == []

def test_command_without_action(service):
    result = service.parse_command_sequence("просто большой гоблин")
    assert result == []

def test_command_with_only_action(service):
    result = service.parse_command_sequence("увернуться")
    assert len(result) == 1
    action = result[0]
    assert action["action"] == "dodge"
    assert "target_entity" not in action
    assert "instrument_entity" not in action

def test_command_with_pronoun_target(service):
    result = service.parse_command_sequence("ударь его")
    assert len(result) == 1
    action = result[0]
    assert action["action"] == "strike"
    assert "target_entity" not in action

# ===============================================================
# ======== ТЕСТЫ RECOGNIZE_INTENT() (TASK 1.3) ========
# ===============================================================

def test_recognize_intent_returns_complexity_type(service):
    """Проверяет, что recognize_intent возвращает оба поля: intent и complexity_type"""
    result = service.recognize_intent("Посмотреть инвентарь")

    assert "intent" in result
    assert "complexity_type" in result
    assert isinstance(result["intent"], str)
    assert isinstance(result["complexity_type"], str)

def test_recognize_intent_code_only_type(service):
    """Тест классификации CODE_ONLY команд"""
    test_cases = [
        "Посмотреть инвентарь",
        "Что у меня в сумке?",
        "Проверить свои раны",
        "Сохранить игру",
        "Открыть меню настроек",
        "Покажи мне карту"
    ]

    for command in test_cases:
        result = service.recognize_intent(command)
        assert result["complexity_type"] == "CODE_ONLY", \
            f"Command '{command}' should be CODE_ONLY, got {result['complexity_type']}"

def test_recognize_intent_simple_llm_type(service):
    """Тест классификации SIMPLE_LLM команд"""
    test_cases = [
        "Атаковать врага мечом",
        "Бью мечом по шее гоблина",
        "Выстрелить из лука в скелета",
        "Осмотреться вокруг",
        "Поговорить с торговцем",
        "Уклоняюсь от удара"
    ]

    for command in test_cases:
        result = service.recognize_intent(command)
        assert result["complexity_type"] == "SIMPLE_LLM", \
            f"Command '{command}' should be SIMPLE_LLM, got {result['complexity_type']}"

def test_recognize_intent_complex_tool_call_type(service):
    """Тест классификации COMPLEX_TOOL_CALL команд"""
    test_cases = [
        "Попробовать подпереть дверь столом, чтобы ее не выломали",
        "Кинуть свой факел в лужу масла на полу, чтобы поджечь ее",
        "Перерубить веревку, на которой висит люстра, чтобы она упала на врагов",
        "Опрокинуть котел с кипящей похлебкой на приближающегося волка",
        "Толкнуть шаткую колонну, чтобы она обрушилась на противников"
    ]

    for command in test_cases:
        result = service.recognize_intent(command)
        assert result["complexity_type"] == "COMPLEX_TOOL_CALL", \
            f"Command '{command}' should be COMPLEX_TOOL_CALL, got {result['complexity_type']}"

def test_recognize_intent_unknown_command_fallback(service):
    """Тест что ChromaDB возвращает результаты даже для необычных команд

    Примечание: ChromaDB всегда возвращает ближайшее совпадение даже для
    полностью незнакомых команд. Этот тест проверяет, что система корректно
    обрабатывает такие случаи через эвристики и не падает.
    """
    # Реалистичные команды, которых нет в обучающей выборке
    unusual_commands = [
        "почитать книгу",  # Действие не из боевой системы
        "станцевать танец",  # Совсем не игровая команда
        "спеть песню"  # Еще одна необычная команда
    ]

    for command in unusual_commands:
        result = service.recognize_intent(command)
        # Проверяем что система не падает и возвращает валидный результат
        assert "intent" in result
        assert "complexity_type" in result
        assert result["complexity_type"] in service.VALID_COMPLEXITY_TYPES, \
            f"Command '{command}' returned invalid complexity_type: {result['complexity_type']}'"

def test_recognize_intent_heuristics_override_code_only(service):
    """Тест эвристических правил для CODE_ONLY"""
    # Команды с ключевыми словами CODE_ONLY должны классифицироваться правильно
    # даже если векторный поиск ошибается
    heuristic_commands = [
        "покажи инвентарь",
        "мои характеристики",
        "открыть журнал",
        "статистика персонажа"
    ]

    for command in heuristic_commands:
        result = service.recognize_intent(command)
        assert result["complexity_type"] == "CODE_ONLY", \
            f"Heuristic should classify '{command}' as CODE_ONLY"

def test_recognize_intent_heuristics_override_complex(service):
    """Тест эвристических правил для COMPLEX_TOOL_CALL"""
    # Команды с ключевыми словами COMPLEX должны классифицироваться правильно
    complex_keywords_commands = [
        "опрокинуть стол на врага",
        "бросить факел на землю, чтобы поджечь масло",
        "подпереть дверь стулом",
        "перерубить веревку мечом"
    ]

    for command in complex_keywords_commands:
        result = service.recognize_intent(command)
        assert result["complexity_type"] == "COMPLEX_TOOL_CALL", \
            f"Heuristic should classify '{command}' as COMPLEX_TOOL_CALL"

def test_recognize_intent_validation_invalid_type(service):
    """Тест валидации: неизвестные complexity_type должны fallback на SIMPLE_LLM"""
    # Этот тест проверяет внутреннюю логику валидации
    # В нормальной ситуации такого не должно происходить, но защита должна быть

    # Мы не можем напрямую протестировать это без моков,
    # но можем проверить, что VALID_COMPLEXITY_TYPES установлены правильно
    assert hasattr(service, 'VALID_COMPLEXITY_TYPES')
    assert service.VALID_COMPLEXITY_TYPES == {"CODE_ONLY", "SIMPLE_LLM", "COMPLEX_TOOL_CALL"}

def test_recognize_intent_returns_correct_intent_metadata(service):
    """Тест что intent метаданные возвращаются правильно"""
    result = service.recognize_intent("Посмотреть инвентарь")

    # Проверяем что intent соответствует ожидаемому формату
    assert result["intent"] in [
        "SELF_ACTION_CODE_ONLY",
        "META_ACTION_CODE_ONLY",
        "SIMPLE_INTERACTION_LLM",
        "DIRECT_COMBAT_LLM",
        "COMPLEX_INTERACTION_TOOL_CALL",
        "UNKNOWN"
    ]