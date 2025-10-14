from typing import List, Dict, Any, TYPE_CHECKING
from logic.game_states import GameState

# Используем TYPE_CHECKING для избежания циклических импортов
# Type hints в кавычках проверяются только статическими анализаторами
if TYPE_CHECKING:
    import game

import services.llm_service as llm
from logic.constants import *
from services.intent_service import IntentService
from combat.physical_simulator import PhysicalSimulator, PhysicalResult
from combat.context_builder import PhysicalContextBuilder
import json
from utils.prompt_manager import load_and_format_prompt

# Импорт стратегий
from logic.strategies import CodeOnlyStrategy, SimpleLLMStrategy, FunctionCallingStrategy

class Director:
    """
    Режиссёр игры - маршрутизатор команд игрока к соответствующим обработчикам.

    Использует Pattern Strategy для выбора метода обработки команды на основе
    её сложности (complexity_type), определённой IntentService.

    Два уровня сложности:
    - SIMPLE_LLM: Простые действия с 1 вызовом LLM (500-1000ms)
    - COMPLEX_TOOL_CALL: Сложные действия с Function Calling (1000-2000ms, STUB)
    """

    def __init__(self):
        # Сервис распознавания намерений
        self.intent_service = IntentService()

        # НОВОЕ: Заглушки боевой системы (для будущего использования)
        self.physics_simulator = PhysicalSimulator()
        self.context_builder = PhysicalContextBuilder()

        # НОВОЕ: Strategy Pattern - словарь стратегий по complexity_type
        self.strategies = {
            "SIMPLE_LLM": SimpleLLMStrategy(),
            "COMPLEX_TOOL_CALL": FunctionCallingStrategy()
        }

        print("[Director] Initialized with Strategy Pattern")

    def process_command(self, game_instance: 'game.Game', command: str) -> str:
        """
        НОВЫЙ МЕТОД: Обрабатывает команду игрока с использованием Strategy Pattern.

        Алгоритм:
        1. Распознать intent и complexity_type через IntentService
        2. Валидировать complexity_type (с fallback)
        3. Извлечь детали команды (если нужно)
        4. Выбрать стратегию по complexity_type
        5. Выполнить стратегию

        Args:
            game_instance: Экземпляр Game с текущим состоянием
            command: Команда игрока

        Returns:
            Строка с результатом для отображения игроку
        """
        print(f"[Director] Processing command: '{command}'")

        # 1. Распознать тип команды и её сложность
        result = self.intent_service.recognize_intent(command)
        intent = result["intent"]
        complexity_type = result["complexity_type"]

        print(f"[Director] Intent: {intent}, Complexity: {complexity_type}")

        # 2. Валидация complexity_type
        if complexity_type not in self.strategies:
            print(f"[Director] ⚠️ Unknown complexity_type '{complexity_type}', falling back to SIMPLE_LLM")
            complexity_type = "SIMPLE_LLM"

        # 3. Извлечь детали
        details = {"intent": intent, "complexity_type": complexity_type}

        # 4. Выбрать стратегию
        strategy = self.strategies[complexity_type]

        # 5. Выполнить стратегию
        return strategy.execute(game_instance, command, details)

    def decide_llm_action(self, game_instance: 'game.Game', player_command: str) -> str:
        """
        УСТАРЕВШИЙ МЕТОД: Для обратной совместимости.

        Теперь просто делегирует вызов в process_command().

        TODO: Удалить после обновления всех вызовов в game.py (Task 3.3)
        """
        print("[Director] ⚠️ Using deprecated decide_llm_action(), forwarding to process_command()")
        return self.process_command(game_instance, player_command)

    # СТАРЫЕ МЕТОДЫ УДАЛЕНЫ (Task 3.2)
    # Логика перенесена в:
    # - SimpleLLMStrategy._handle_combat_start()
    # - SimpleLLMStrategy._handle_exploration()
    # - SimpleLLMStrategy._handle_combat()
    #
    # См. logic/strategies/simple_llm_strategy.py