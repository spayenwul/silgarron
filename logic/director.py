# logic/director.py
from typing import List
from logic.game_states import GameState
# Важно: используем 'import game' чтобы избежать циклических импортов
# и используем type hint в кавычках: 'game.Game'
import game 
import services.llm_service as llm

class Director:
    def decide_llm_action(self, game_instance: 'game.Game', player_command: str) -> str:
        """
        Главный метод, который анализирует состояние игры и выбирает стратегию.
        """
        if game_instance.state == GameState.EXPLORATION:
            return self._handle_exploration(game_instance, player_command)
        elif game_instance.state == GameState.COMBAT:
            return self._handle_combat(game_instance, player_command)
        
        return "Режиссёр в замешательстве и не знает, что делать."

    def _handle_exploration(self, game_instance: 'game.Game', command: str) -> str:
        print("🎬 Режиссёр: Сцена 'Исследование'.")
        # --- Стратегия для исследования ---
        # 1. Собираем контекст как раньше (LTM)
        search_query = f"{' '.join(game_instance.current_location.tags)} {command}"
        memories = game_instance._get_layered_context(search_query)

        # 2. Собираем текущую ситуацию
        context = game_instance.get_context_for_llm()

        # 3. Используем ОБЫЧНЫЙ промпт
        return llm.generate_action_result(context, memories, command)

    def _handle_combat(self, game_instance: 'game.Game', command: str) -> str:
        print("🎬 Режиссёр: Сцена 'Бой'.")
        # --- Стратегия для боя ---
        # 1. Собираем ВЕСЬ лог боя из Краткосрочной Памяти (STM)
        combat_log = game_instance.short_term_memory

        # 2. Ищем в Долгосрочной Памяти (LTM) только полезные факты (например, уязвимости)
        search_query = f"уязвимости или тактика против {' '.join(game_instance.current_location.tags)}"
        lore = game_instance.memory_service.retrieve_relevant_memories(
            search_query, n_results=1, filter_metadata={"type": "lore"}
        )

        # 3. Используем СПЕЦИАЛЬНЫЙ боевой промпт
        return llm.generate_combat_action_result(combat_log, lore, command)