"""
SIMPLE_LLM Strategy - простые действия с одним вызовом AI.

Обрабатывает команды, требующие LLM для генерации ответа, но без сложной
физической симуляции или функциональных вызовов.

Примеры:
- Простые атаки ("ударить мечом")
- Исследование ("осмотреться", "изучить статую")
- Простые диалоги ("поговорить с торговцем")

Характеристики:
- Скорость: 500-1000ms
- Стоимость: ~0.001₽ за вызов
- Качество: Хорошая генерация нарратива
"""

from typing import Dict, Any
import json
from logic.strategies.base_strategy import BaseStrategy
from logic.game_states import GameState
from logic.constants import *
from utils.prompt_manager import load_and_format_prompt
import services.llm_service as llm


class SimpleLLMStrategy(BaseStrategy):
    """
    Стратегия для обработки простых команд с помощью LLM (1 вызов).

    Использует разные промпты в зависимости от состояния игры и интента:
    - combat_action: Для боевых действий
    - combat_start: Для начала боя
    - exploration_action: Для исследования
    """

    def execute(self, game_instance: Any, command: str, details: Dict[str, Any]) -> str:
        """
        Выполнить простое действие с помощью LLM.

        Args:
            game_instance: Экземпляр Game
            command: Оригинальная команда игрока
            details: Dict с полями 'intent' и 'complexity_type'

        Returns:
            Строка с результатом от LLM
        """
        intent = details.get("intent", "UNKNOWN")

        # Определяем состояние игры для выбора стратегии
        game_state = game_instance.state

        # --- Логика начала боя ---
        # Если команда связана с боем и мы НЕ в бою, начинаем бой
        if "COMBAT" in intent and game_state != GameState.COMBAT:
            game_instance.change_state(GameState.COMBAT)
            return self._handle_combat_start(game_instance, command)

        # --- Обработка текущего состояния ---
        if game_state == GameState.COMBAT:
            return self._handle_combat(game_instance, command, intent)
        else:
            # По умолчанию используем exploration
            return self._handle_exploration(game_instance, command, intent)

    def _handle_combat_start(self, game_instance: Any, command: str) -> str:
        """
        Обработка начала боя.

        Используется один раз при переходе из EXPLORATION в COMBAT.
        """
        print("🎬 SimpleLLMStrategy: Начало боя")

        # 1. Сборка контекста
        log_str = "\n".join(game_instance.short_term_memory)

        # Ищем информацию о врагах в этой локации
        search_query = f"описание врагов или опасностей в {' '.join(game_instance.current_location.tags)}"
        lore_list = game_instance.memory_service.retrieve_relevant_memories(
            search_query, n_results=1, filter_metadata={META_TYPE: TYPE_LORE}
        )
        lore_str = "\n".join(lore_list) if lore_list else "Нет особых данных о врагах."

        context_dict = game_instance.get_context_for_llm()
        context_json_str = json.dumps(context_dict, ensure_ascii=False, indent=2)

        # 2. Загрузка и форматирование промпта
        prompt_template_name = 'combat_start'
        prompt = load_and_format_prompt(
            prompt_template_name,
            narrative_key=NARRATIVE,
            state_changes_key=STATE_CHANGES,
            damage_player_key=DAMAGE_PLAYER,
            new_event_key=NEW_EVENT,
            add_item_key=ADD_ITEM,
            lore=lore_str,
            combat_log=log_str,
            context_json=context_json_str,
            player_action=command
        )

        # 3. Отправка в LLM
        llm_request = {
            "prompt": prompt,
            "prompt_template_name": prompt_template_name,
            "game_state": game_instance.state.name
        }
        return llm._send_prompt_to_gemini(llm_request)

    def _handle_combat(self, game_instance: Any, command: str, intent: str) -> str:
        """
        Обработка боевых действий в режиме COMBAT.
        """
        print("🎬 SimpleLLMStrategy: Бой")

        # 1. Сборка контекста
        log_str = "\n".join(game_instance.short_term_memory)

        search_query = f"уязвимости или тактика против {' '.join(game_instance.current_location.tags)}"
        lore_list = game_instance.memory_service.retrieve_relevant_memories(
            search_query, n_results=1, filter_metadata={META_TYPE: TYPE_LORE}
        )
        lore_str = "\n".join(lore_list) if lore_list else "Нет особых данных."

        # 2. Загрузка и форматирование промпта
        prompt_template_name = 'combat_action'
        prompt = load_and_format_prompt(
            prompt_template_name,
            narrative_key=NARRATIVE,
            state_changes_key=STATE_CHANGES,
            damage_player_key=DAMAGE_PLAYER,
            new_event_key=NEW_EVENT,
            add_item_key=ADD_ITEM,
            new_game_state_key=NEW_GAME_STATE,
            lore=lore_str,
            combat_log=log_str,
            player_action=command
        )

        # 3. Отправка в LLM
        llm_request = {
            "prompt": prompt,
            "prompt_template_name": prompt_template_name,
            "game_state": game_instance.state.name
        }
        return llm._send_prompt_to_gemini(llm_request)

    def _handle_exploration(self, game_instance: Any, command: str, intent: str) -> str:
        """
        Обработка действий в режиме EXPLORATION.
        """
        print("🎬 SimpleLLMStrategy: Исследование")

        # 1. Сборка долгосрочной памяти
        search_query = f"{' '.join(game_instance.current_location.tags)} {command}"
        memories_list = game_instance._get_layered_context(search_query)
        memories_str = "\n".join(f"- {item}" for item in memories_list) if memories_list else "Нет особых воспоминаний."

        # 2. Сборка краткосрочной памяти
        context_dict = game_instance.get_context_for_llm()
        context_json_str = json.dumps(context_dict, ensure_ascii=False, indent=2)

        # 3. Загрузка и форматирование промпта
        prompt_template_name = 'exploration_action'
        prompt = load_and_format_prompt(
            prompt_template_name,
            narrative_key=NARRATIVE,
            state_changes_key=STATE_CHANGES,
            new_game_state_key=NEW_GAME_STATE,
            memories=memories_str,
            context_json=context_json_str,
            player_action=command
        )

        # 4. Отправка в LLM
        llm_request = {
            "prompt": prompt,
            "prompt_template_name": prompt_template_name,
            "game_state": game_instance.state.name
        }
        return llm._send_prompt_to_gemini(llm_request)
