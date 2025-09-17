from typing import List
from logic.game_states import GameState
# Важно: используем 'import game' чтобы избежать циклических импортов
# и используем type hint в кавычках: 'game.Game'
import game
import services.llm_service as llm
from logic.constants import *
from services.intent_service import IntentService
import json
from utils.prompt_manager import load_and_format_prompt 

class Director:
    # Первым идёт анализ от all-MiniLM-L6-v2 по data\intents.json
    def __init__(self):
        self.intent_service = IntentService()

    def decide_llm_action(self, game_instance: 'game.Game', player_command: str) -> str:
        """
        Главный метод, который анализирует состояние игры и выбирает стратегию.
        """
        
        # --- ШАГ 1: Распознавание намерения ---
        intent = self.intent_service.recognize_intent(player_command)
        
        # --- ШАГ 2: Принятие решения на основе намерения и состояния ---
        
        # Триггер для начала боя
        if intent == "COMBAT" and game_instance.state != GameState.COMBAT:
            game_instance.change_state(GameState.COMBAT)

        # Выбор обработчика в зависимости от ТЕКУЩЕГО состояния игры
        if game_instance.state == GameState.COMBAT:
            return self._handle_combat(game_instance, player_command)
                
        # (Здесь будет логика для DIALOGUE и других методов)

        if intent == "UNKNOWN":
            # Если мы не поняли, считаем, что это простое исследование
            intent = "EXPLORATION" 
            print("⚠️ Намерение не распознано, используется EXPLORATION по умолчанию.")

        # Если ничего особенного, остаемся в исследовании
        return self._handle_exploration(game_instance, player_command)

    def _handle_exploration(self, game_instance: 'game.Game', command: str) -> str:
        print("🎬 Режиссёр: Сцена 'Исследование'.")
        # --- Стратегия для исследования ---

        # 1. Собираем Долгосрочную Память (LTM)
        search_query = f"{' '.join(game_instance.current_location.tags)} {command}"
        memories_list = game_instance._get_layered_context(search_query)
        memories_str = "\n".join(f"- {item}" for item in memories_list) if memories_list else "Нет особых воспоминаний."

        # 2. Собираем текущую ситуацию в виде строки JSON
        context_dict = game_instance.get_context_for_llm()
        context_json_str = json.dumps(context_dict, ensure_ascii=False, indent=2)
        
        # 3. Используем ОБЫЧНЫЙ промпт для исследования
        prompt = load_and_format_prompt(
            'exploration_action',
            # Передаем константы для ключей JSON
            narrative_key=NARRATIVE,
            state_changes_key=STATE_CHANGES,
            new_game_state_key=NEW_GAME_STATE,
            # Передаем динамические данные
            memories=memories_str,
            context_json=context_json_str,
            player_action=command
        )
        
        # 4. Отправляем в API
        return llm._send_prompt_to_gemini(prompt)

# logic/director.py -> внутри класса Director

    def _handle_combat(self, game_instance: 'game.Game', command: str) -> str:
        print("🎬 Режиссёр: Сцена 'Бой'.")
        # --- Стратегия для боя ---
        # 1. Собираем ВЕСЬ лог боя из Краткосрочной Памяти (STM)
        combat_log = game_instance.short_term_memory
        log_str = "\n".join(combat_log)

        # 2. Ищем в Долгосрочной Памяти (LTM) только полезные факты (например, уязвимости)
        search_query = f"уязвимости или тактика против {' '.join(game_instance.current_location.tags)}"
        lore_list = game_instance.memory_service.retrieve_relevant_memories(
            search_query, n_results=1, filter_metadata={META_TYPE: TYPE_LORE}
        )
        lore_str = "\n".join(lore_list) if lore_list else "Нет особых данных."
        
        # 3. Используем СПЕЦИАЛЬНЫЙ боевой промпт
        prompt = load_and_format_prompt(
            'combat_action',
            # Передаем константы для ключей JSON
            narrative_key=NARRATIVE,
            state_changes_key=STATE_CHANGES,
            damage_player_key=DAMAGE_PLAYER,
            new_event_key=NEW_EVENT,
            add_item_key=ADD_ITEM,
            new_game_state_key=NEW_GAME_STATE,
            # Передаем динамические данные
            lore=lore_str,
            combat_log=log_str,
            player_action=command
        )
        return llm._send_prompt_to_gemini(prompt)