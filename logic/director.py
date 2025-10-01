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
    """Инициализирует Director и его подсистемы, такие как сервис распознавания намерений."""
    def __init__(self):
        self.intent_service = IntentService()

    def decide_llm_action(self, game_instance: 'game.Game', player_command: str) -> str:
        """
        Главный метод-маршрутизатор. Распознает намерение, определяет стратегию
        и делегирует выполнение соответствующему обработчику.
        """
        
        # --- ШАГ 1: Распознавание намерения ---
        intent = self.intent_service.recognize_intent(player_command)
        
        # --- ШАГ 2: Принятие решения на основе намерения и состояния ---
        
        # Если атака и мы НЕ в бою, используем "промпт начала боя"
        if intent == "COMBAT" and game_instance.state != GameState.COMBAT:
            game_instance.change_state(GameState.COMBAT)
            return self._handle_combat_start(game_instance, player_command)

        # Обычная обработка боя
        if game_instance.state == GameState.COMBAT:
            return self._handle_combat(game_instance, player_command, recognized_intent=intent)
                       
        # (Здесь будет логика для DIALOGUE и других методов)

        if intent == "UNKNOWN":
            # Если мы не поняли, считаем, что это простое исследование
            intent = "EXPLORATION" 
            print("⚠️ Намерение не распознано, используется EXPLORATION по умолчанию.")

        # По умолчанию (или если намерение не распознано) используется режим исследования
        return self._handle_exploration(game_instance, player_command, recognized_intent=intent)

    def _handle_combat_start(self, game_instance: 'game.Game', command: str) -> str:
        """
        Собирает контекст и промпт для самого НАЧАЛА БОЯ.
        Этот метод используется один раз при переходе из EXPLORATION в COMBAT.
        """
        print("🎬 Режиссёр: Сцена 'Начало Боя'.")

        # 1. Сборка контекста. В начале боя лог еще почти пуст.
        log_str = "\n".join(game_instance.short_term_memory) # Будет содержать "Начало боя в локации..."
        
        # Ищем информацию о возможных врагах в этой локации
        search_query = f"описание врагов или опасностей в {' '.join(game_instance.current_location.tags)}"
        lore_list = game_instance.memory_service.retrieve_relevant_memories(
            search_query, n_results=1, filter_metadata={META_TYPE: TYPE_LORE}
        )
        lore_str = "\n".join(lore_list) if lore_list else "Нет особых данных о врагах."
        
        # Получаем общую информацию об игроке и локации
        context_dict = game_instance.get_context_for_llm()
        context_json_str = json.dumps(context_dict, ensure_ascii=False, indent=2)

        # 2. Сборка промпта (предполагается, что у вас есть или будет промпт 'combat_start')
        # Если его нет, можно временно использовать 'combat_action'.
        prompt_template_name = 'combat_start' # Используем специальный промпт
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
        
        # 3. Формирование и отправка пакета в LLM-сервис
        llm_request = {
            "prompt": prompt,
            "prompt_template_name": prompt_template_name,
            "game_state": game_instance.state.name
        }
        return llm._send_prompt_to_gemini(llm_request)

    def _handle_exploration(self, game_instance: 'game.Game', command: str, recognized_intent: str) -> str:
        """Собирает контекст и промпт для режима ИССЛЕДОВАНИЯ."""
        print("🎬 Режиссёр: Сцена 'Исследование'.")
       
        if recognized_intent == "UNKNOWN":
            print("⚠️ Намерение не распознано, используется EXPLORATION по умолчанию.")
        
        # 1. Сборка долгосрочной памяти
        search_query = f"{' '.join(game_instance.current_location.tags)} {command}"
        memories_list = game_instance._get_layered_context(search_query)
        memories_str = "\n".join(f"- {item}" for item in memories_list) if memories_list else "Нет особых воспоминаний."

        # 2. Сборка краткосрочной памяти
        context_dict = game_instance.get_context_for_llm()
        context_json_str = json.dumps(context_dict, ensure_ascii=False, indent=2)
        
        # 3. Сборка промпта
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
        
        # 4. Формирование и отправка пакета в LLM-сервис
        llm_request = {
            "prompt": prompt,
            "prompt_template_name": prompt_template_name,
            "game_state": game_instance.state.name
        }
        return llm._send_prompt_to_gemini(llm_request)

    def _handle_combat(self, game_instance: 'game.Game', command: str, recognized_intent: str) -> str:
        """Собирает контекст и промпт для режима БОЯ."""
        print("🎬 Режиссёр: Сцена 'Бой'.")

        if recognized_intent == "UNKNOWN":
            print("⚠️ Намерение не распознано, используется EXPLORATION по умолчанию.")

        # 1. Сборка контекста
        log_str = "\n".join(game_instance.short_term_memory)
        
        search_query = f"уязвимости или тактика против {' '.join(game_instance.current_location.tags)}"
        lore_list = game_instance.memory_service.retrieve_relevant_memories(
            search_query, n_results=1, filter_metadata={META_TYPE: TYPE_LORE}
        )
        lore_str = "\n".join(lore_list) if lore_list else "Нет особых данных."
        
        # 2. Сборка промпта
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
        
        # 3. Формирование и отправка пакета в LLM-сервис
        llm_request = {
            "prompt": prompt,
            "prompt_template_name": prompt_template_name,
            "game_state": game_instance.state.name
        }
        return llm._send_prompt_to_gemini(llm_request)