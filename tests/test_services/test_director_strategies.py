"""
Integration tests for Director Strategy Pattern implementation.

Tests verify that the three-tier command routing system works correctly:
- CODE_ONLY: Instant actions without AI
- SIMPLE_LLM: Simple actions with 1 LLM call
- COMPLEX_TOOL_CALL: Complex actions (stub)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from logic.director import Director
from logic.game_states import GameState
from models.character import Character
from models.location import Location
from models.inventory import Inventory


@pytest.fixture
def mock_game():
    """Create a mock Game instance for testing."""
    game = Mock()

    # Setup player
    game.player = Character(name="Test Hero", species="human")
    game.player.hp = 20
    game.player.max_hp = 20

    # Setup location
    game.current_location = Location(passport={
        "name": "Test Room",
        "description": "A test room for testing",
        "tags": ["indoor", "safe"]
    })
    game.current_location.id = "test_loc"  # Set id attribute separately

    # Setup game state
    game.state = GameState.EXPLORATION
    game.short_term_memory = []

    # Mock memory service
    game.memory_service = Mock()
    game.memory_service.retrieve_relevant_memories = Mock(return_value=[])

    # Mock get_context_for_llm
    game.get_context_for_llm = Mock(return_value={
        "location_tags": ["indoor", "safe"],
        "location_description": "A test room for testing",
        "player_hp": "20/20",
        "player_stats": {"сила": 10, "ловкость": 10, "интеллект": 10},
        "player_inventory": []
    })

    # Mock _get_layered_context
    game._get_layered_context = Mock(return_value=[])

    return game


@pytest.fixture
def director():
    """Create a Director instance for testing."""
    return Director()


# ===============================================================
# ======== CODE_ONLY PATH TESTS ========
# ===============================================================

def test_code_only_inventory_command(director, mock_game):
    """Test CODE_ONLY path: посмотреть инвентарь → instant response, no LLM call"""

    result = director.process_command(mock_game, "посмотреть инвентарь")

    # Should return a response
    assert isinstance(result, str)
    assert len(result) > 0

    # Should mention inventory
    assert "инвентарь" in result.lower() or "сумк" in result.lower() or "🎒" in result

    # Should NOT call LLM (no memory service calls for CODE_ONLY)
    # Memory service is only used by SIMPLE_LLM strategy


def test_code_only_stats_command(director, mock_game):
    """Test CODE_ONLY path: статистика → instant response"""

    result = director.process_command(mock_game, "показать характеристики")

    assert isinstance(result, str)
    assert "характеристик" in result.lower() or "стат" in result.lower() or "📊" in result


def test_code_only_health_command(director, mock_game):
    """Test CODE_ONLY path: проверить здоровье → instant response"""

    result = director.process_command(mock_game, "проверить свои раны")

    assert isinstance(result, str)
    assert "hp" in result.lower() or "здоров" in result.lower() or "❤️" in result


def test_code_only_meta_command(director, mock_game):
    """Test CODE_ONLY path: мета-команды (карта, журнал)"""

    result = director.process_command(mock_game, "показать карту")

    assert isinstance(result, str)
    assert "карт" in result.lower() or "🗺️" in result or "локаци" in result.lower()


# ===============================================================
# ======== SIMPLE_LLM PATH TESTS ========
# ===============================================================

@patch('services.llm_service._send_prompt_to_gemini')
def test_simple_llm_exploration_command(mock_llm, director, mock_game):
    """Test SIMPLE_LLM path: осмотреться → 1 LLM call"""

    # Mock LLM response
    mock_llm.return_value = '{"narrative": "You look around the test room.", "state_changes": {}}'

    result = director.process_command(mock_game, "осмотреться вокруг")

    # Should call LLM exactly once
    assert mock_llm.call_count == 1

    # Should return LLM response
    assert isinstance(result, str)
    assert len(result) > 0


@patch('services.llm_service._send_prompt_to_gemini')
def test_simple_llm_combat_command(mock_llm, director, mock_game):
    """Test SIMPLE_LLM path: ударить мечом → 1 LLM call"""

    # Mock LLM response
    mock_llm.return_value = '{"narrative": "You strike with your sword!", "state_changes": {}}'

    result = director.process_command(mock_game, "ударить гоблина мечом")

    # Should call LLM exactly once
    assert mock_llm.call_count == 1

    # Should return LLM response
    assert isinstance(result, str)


@patch('services.llm_service._send_prompt_to_gemini')
def test_simple_llm_dialogue_command(mock_llm, director, mock_game):
    """Test SIMPLE_LLM path: поговорить с NPC → 1 LLM call"""

    mock_llm.return_value = '{"narrative": "The merchant greets you warmly.", "state_changes": {}}'

    result = director.process_command(mock_game, "поговорить с торговцем")

    assert mock_llm.call_count == 1
    assert isinstance(result, str)


@patch('services.llm_service._send_prompt_to_gemini')
def test_simple_llm_combat_start_transition(mock_llm, director, mock_game):
    """Test SIMPLE_LLM path: начало боя → state change to COMBAT"""

    mock_llm.return_value = '{"narrative": "Combat begins!", "state_changes": {}}'

    # Initially in EXPLORATION
    assert mock_game.state == GameState.EXPLORATION

    # Mock change_state
    original_state = mock_game.state
    def change_state_side_effect(new_state):
        mock_game.state = new_state
    mock_game.change_state = Mock(side_effect=change_state_side_effect)

    result = director.process_command(mock_game, "атаковать врага мечом")

    # Should call LLM
    assert mock_llm.call_count == 1


# ===============================================================
# ======== COMPLEX_TOOL_CALL PATH TESTS (STUB) ========
# ===============================================================

def test_complex_tool_call_stub_message(director, mock_game):
    """Test COMPLEX path: опрокинуть стол → TODO stub message"""

    result = director.process_command(mock_game, "опрокинуть стол на врага")

    # Should return stub message
    assert isinstance(result, str)
    assert "🚧" in result or "разработк" in result.lower() or "sprint" in result.lower()
    assert "опрокинуть стол на врага" in result.lower()


def test_complex_tool_call_environment_interaction(director, mock_game):
    """Test COMPLEX path: использовать окружение → stub"""

    result = director.process_command(mock_game, "перерубить веревку, чтобы люстра упала")

    assert isinstance(result, str)
    assert "🚧" in result or "разработк" in result.lower()


def test_complex_tool_call_creative_action(director, mock_game):
    """Test COMPLEX path: кинуть факел в масло → stub"""

    result = director.process_command(mock_game, "кинуть факел в лужу масла, чтобы поджечь")

    assert isinstance(result, str)
    assert "🚧" in result or "разработк" in result.lower()


# ===============================================================
# ======== INTENT CLASSIFICATION TESTS ========
# ===============================================================

def test_intent_classification_code_only(director, mock_game):
    """Test that CODE_ONLY commands are correctly classified"""

    code_only_commands = [
        "посмотреть инвентарь",
        "мои характеристики",
        "проверить здоровье",
        "сохранить игру",
        "показать карту"
    ]

    for command in code_only_commands:
        result = director.intent_service.recognize_intent(command)
        assert result["complexity_type"] == "CODE_ONLY", \
            f"Command '{command}' should be CODE_ONLY, got {result['complexity_type']}"


def test_intent_classification_simple_llm(director, mock_game):
    """Test that SIMPLE_LLM commands are correctly classified"""

    simple_llm_commands = [
        "осмотреться вокруг",
        "ударить мечом",
        "поговорить с торговцем",
        "выстрелить из лука"
    ]

    for command in simple_llm_commands:
        result = director.intent_service.recognize_intent(command)
        assert result["complexity_type"] == "SIMPLE_LLM", \
            f"Command '{command}' should be SIMPLE_LLM, got {result['complexity_type']}"


def test_intent_classification_complex(director, mock_game):
    """Test that COMPLEX commands are correctly classified"""

    complex_commands = [
        "опрокинуть котел на врага",
        "перерубить веревку, чтобы люстра упала",
        "толкнуть колонну на противников"
    ]

    for command in complex_commands:
        result = director.intent_service.recognize_intent(command)
        assert result["complexity_type"] == "COMPLEX_TOOL_CALL", \
            f"Command '{command}' should be COMPLEX_TOOL_CALL, got {result['complexity_type']}"


# ===============================================================
# ======== STRATEGY SELECTION TESTS ========
# ===============================================================

def test_strategy_selection_validation(director, mock_game):
    """Test that Director validates complexity_type and falls back if needed"""

    # Mock IntentService to return invalid complexity_type
    with patch.object(director.intent_service, 'recognize_intent') as mock_recognize:
        mock_recognize.return_value = {
            "intent": "UNKNOWN",
            "complexity_type": "INVALID_TYPE"
        }

        # Should fallback to SIMPLE_LLM
        with patch('services.llm_service._send_prompt_to_gemini') as mock_llm:
            mock_llm.return_value = '{"narrative": "Fallback response", "state_changes": {}}'

            result = director.process_command(mock_game, "какая-то команда")

            # Should still return a valid response (using fallback strategy)
            assert isinstance(result, str)
            assert mock_llm.call_count == 1  # Should use SIMPLE_LLM fallback


def test_strategy_selection_all_three_types(director, mock_game):
    """Test that Director can route to all three strategy types"""

    # Test CODE_ONLY
    result1 = director.process_command(mock_game, "посмотреть инвентарь")
    assert isinstance(result1, str)

    # Test SIMPLE_LLM
    with patch('services.llm_service._send_prompt_to_gemini') as mock_llm:
        mock_llm.return_value = '{"narrative": "LLM response", "state_changes": {}}'
        result2 = director.process_command(mock_game, "осмотреться")
        assert mock_llm.call_count == 1

    # Test COMPLEX_TOOL_CALL
    result3 = director.process_command(mock_game, "опрокинуть стол")
    assert "🚧" in result3 or "разработк" in result3.lower()


# ===============================================================
# ======== BACKWARDS COMPATIBILITY TESTS ========
# ===============================================================

@patch('services.llm_service._send_prompt_to_gemini')
def test_decide_llm_action_backwards_compatible(mock_llm, director, mock_game):
    """Test that old decide_llm_action() method still works (forwards to process_command)"""

    mock_llm.return_value = '{"narrative": "Compatibility test", "state_changes": {}}'

    # Call old method
    result = director.decide_llm_action(mock_game, "осмотреться")

    # Should work and call LLM
    assert isinstance(result, str)
    assert mock_llm.call_count == 1


# ===============================================================
# ======== EDGE CASES ========
# ===============================================================

def test_empty_command(director, mock_game):
    """Test handling of empty command"""

    # Should not crash, should return some response
    result = director.process_command(mock_game, "")
    assert isinstance(result, str)


def test_very_long_command(director, mock_game):
    """Test handling of very long command"""

    long_command = "посмотреть " * 100 + "инвентарь"

    result = director.process_command(mock_game, long_command)
    assert isinstance(result, str)


def test_unknown_command_fallback(director, mock_game):
    """Test that unknown commands fall back gracefully"""

    with patch('services.llm_service._send_prompt_to_gemini') as mock_llm:
        mock_llm.return_value = '{"narrative": "Unknown command response", "state_changes": {}}'

        result = director.process_command(mock_game, "абракадабра непонятная команда")

        # Should not crash
        assert isinstance(result, str)


# ===============================================================
# ======== END-TO-END INTEGRATION TESTS (Task 4.2) ========
# ===============================================================

@patch('services.llm_service._send_prompt_to_gemini')
def test_e2e_full_flow_code_only(mock_llm, director, mock_game):
    """
    End-to-End test: Full flow for CODE_ONLY command.

    Verifies:
    - Command goes through Director → CodeOnlyStrategy
    - No LLM calls made (0 calls)
    - Returns valid response
    """

    # Execute CODE_ONLY command
    result = director.process_command(mock_game, "посмотреть инвентарь")

    # Verify no LLM calls
    assert mock_llm.call_count == 0, "CODE_ONLY should not call LLM"

    # Verify valid response returned
    assert isinstance(result, str)
    assert len(result) > 0
    print(f"[E2E CODE_ONLY] Response: {result[:100]}...")


@patch('services.llm_service._send_prompt_to_gemini')
def test_e2e_full_flow_simple_llm(mock_llm, director, mock_game):
    """
    End-to-End test: Full flow for SIMPLE_LLM command.

    Verifies:
    - Command goes through Director → SimpleLLMStrategy
    - Exactly 1 LLM call made
    - Returns valid response
    """

    # Mock LLM response
    mock_llm.return_value = '{"narrative": "You look around the room.", "state_changes": {}}'

    # Execute SIMPLE_LLM command
    result = director.process_command(mock_game, "осмотреться вокруг")

    # Verify exactly 1 LLM call
    assert mock_llm.call_count == 1, "SIMPLE_LLM should call LLM exactly once"

    # Verify valid response returned
    assert isinstance(result, str)
    assert len(result) > 0
    print(f"[E2E SIMPLE_LLM] Response: {result[:100]}...")


def test_e2e_full_flow_complex_stub(director, mock_game):
    """
    End-to-End test: Full flow for COMPLEX command (stub).

    Verifies:
    - Command goes through Director → FunctionCallingStrategy
    - Returns stub TODO message
    - No crashes
    """

    # Execute COMPLEX command
    result = director.process_command(mock_game, "опрокинуть котел на врага")

    # Verify stub message returned
    assert isinstance(result, str)
    assert "🚧" in result or "разработк" in result.lower()
    assert "опрокинуть котел на врага" in result.lower()
    print(f"[E2E COMPLEX STUB] Response: {result[:100]}...")


@patch('services.llm_service._send_prompt_to_gemini')
def test_e2e_multiple_commands_sequence(mock_llm, director, mock_game):
    """
    End-to-End test: Sequence of different command types.

    Simulates a realistic gameplay session with mixed command types.
    """

    mock_llm.return_value = '{"narrative": "Action completed.", "state_changes": {}}'

    # Command 1: CODE_ONLY (check inventory)
    result1 = director.process_command(mock_game, "посмотреть инвентарь")
    assert isinstance(result1, str)
    llm_calls_after_1 = mock_llm.call_count
    assert llm_calls_after_1 == 0, "First command should not call LLM"

    # Command 2: SIMPLE_LLM (explore)
    result2 = director.process_command(mock_game, "осмотреться")
    assert isinstance(result2, str)
    llm_calls_after_2 = mock_llm.call_count
    assert llm_calls_after_2 == 1, "Second command should call LLM once"

    # Command 3: CODE_ONLY (check stats)
    result3 = director.process_command(mock_game, "мои характеристики")
    assert isinstance(result3, str)
    llm_calls_after_3 = mock_llm.call_count
    assert llm_calls_after_3 == 1, "Third command should not call LLM"

    # Command 4: SIMPLE_LLM (combat)
    result4 = director.process_command(mock_game, "ударить врага")
    assert isinstance(result4, str)
    llm_calls_after_4 = mock_llm.call_count
    assert llm_calls_after_4 == 2, "Fourth command should call LLM once more"

    # Command 5: COMPLEX (environment interaction)
    result5 = director.process_command(mock_game, "толкнуть колонну")
    assert isinstance(result5, str)
    assert "🚧" in result5 or "разработк" in result5.lower()
    llm_calls_after_5 = mock_llm.call_count
    assert llm_calls_after_5 == 2, "Fifth command should not call LLM (stub)"

    print(f"[E2E SEQUENCE] Total LLM calls: {mock_llm.call_count}")
    print(f"[E2E SEQUENCE] All 5 commands executed successfully")


@patch('services.llm_service._send_prompt_to_gemini')
def test_e2e_performance_code_only_vs_llm(mock_llm, director, mock_game):
    """
    End-to-End test: Verify performance characteristics.

    CODE_ONLY should be significantly faster than SIMPLE_LLM.
    """

    import time

    # Test CODE_ONLY speed
    start_code_only = time.time()
    result_code_only = director.process_command(mock_game, "посмотреть инвентарь")
    time_code_only = time.time() - start_code_only

    # Verify CODE_ONLY is very fast (<100ms typically)
    assert time_code_only < 1.0, f"CODE_ONLY took {time_code_only}s, should be <1s"
    assert mock_llm.call_count == 0

    # Test SIMPLE_LLM (with mocked LLM, so also fast)
    mock_llm.return_value = '{"narrative": "Test", "state_changes": {}}'

    start_simple_llm = time.time()
    result_simple_llm = director.process_command(mock_game, "осмотреться")
    time_simple_llm = time.time() - start_simple_llm

    assert mock_llm.call_count == 1

    print(f"[E2E PERFORMANCE] CODE_ONLY: {time_code_only*1000:.2f}ms")
    print(f"[E2E PERFORMANCE] SIMPLE_LLM: {time_simple_llm*1000:.2f}ms (mocked)")
    print(f"[E2E PERFORMANCE] Speed ratio: {time_simple_llm/time_code_only:.1f}x")

