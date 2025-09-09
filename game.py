# game.py
import re
import json
import random 
from typing import List 
from models.character import Character
from models.item import Item
from models.location import Location
from generators.location_generator import generate_random_location  # Отсюда берем ТОЛЬКО генератор локаций
from services.llm_service import generate_action_result          # обработчик действий берем из СЕРВИСА
from services.memory_service import MemoryService
from logic.director import Director
from logic.game_states import GameState

class Game:
    def __init__(self):
        self.player: Character | None = None
        self.current_location: Location | None = None
        # Проверяем какое состояние выбрал Режиссёр
        self.state = GameState.EXPLORATION
        self.short_term_memory: List[str] = []
        self.director = Director()
        # Game создает и хранит сервисы
        self.memory_service = MemoryService()

    def start_new_game(self, player_name: str):
        """Инициализирует новую игру."""
        self.player = Character(name=player_name)

        # Даем стартовые предметы
        healing_potion = Item(name="Зелье лечения", description="Восстанавливает немного здоровья.")
        old_sword = Item(name="Старый меч", description="Простой, но надежный меч.")
        self.player.inventory.add_item(healing_potion)
        self.player.inventory.add_item(old_sword)

        # Передаем сервис как зависимость
        self.current_location = generate_random_location(self)
        print("--- Новая игра началась! ---")

    def get_context_for_llm(self) -> dict:
        """Собирает словарь с текущей ситуацией для передачи в LLM."""
        return {
            "location_tags": self.current_location.tags,
            "location_description": self.current_location.description,
            "player_hp": f"{self.player.hp}/{self.player.max_hp}",
            "player_stats": self.player.stats,
            "player_inventory": [item.name for item in self.player.inventory._items]
        }

    def change_state(self, new_state: GameState):
        """Меняет состояние игры и обрабатывает логику перехода."""
        print(f"--- Смена состояния: {self.state.name} -> {new_state.name} ---")
        self.state = new_state
        if new_state == GameState.COMBAT:
            # Начиная бой, очищаем лог и добавляем первую запись
            self.short_term_memory.clear()
            self.short_term_memory.append(f"Начало боя в локации: {self.current_location.name}.")
        elif new_state == GameState.EXPLORATION:
            # Заканчивая бой, очищаем лог
            self.short_term_memory.clear()

    def _get_layered_context(self, search_query: str) -> List[str]:
        """Собирает многослойный контекст для LLM."""
        
        all_context = []
        
        # Слой 1: Ищем 1-2 самых свежих СОБЫТИЯ, произошедших в ЭТОЙ ЖЕ локации
        location_events = self.memory_service.retrieve_relevant_memories(
            query_text=search_query,
            n_results=2,
            filter_metadata={"type": "event", "location": self.current_location.name}
        )
        if location_events:
            all_context.extend(location_events)
        
        # Слой 2: Ищем 1 самый релевантный фрагмент глобального ЛОРА
        global_lore = self.memory_service.retrieve_relevant_memories(
            query_text=search_query,
            n_results=1,
            filter_metadata={"type": "lore"}
        )
        if global_lore:
            all_context.extend(global_lore)

        # Убираем дубликаты, если они есть
        unique_context = list(dict.fromkeys(all_context))
        
        return unique_context

    def process_player_command(self, command: str) -> str:
        """
        Делегирует обработку команды Режиссёру, а затем парсит
        и применяет механические изменения, полученные от LLM.
        """
        # --- Шаг 1: Делегирование ---
        # Вместо того чтобы самим собирать контекст и вызывать LLM,
        # мы просим Режиссёра сделать это за нас. Он сам выберет
        # нужный промпт и нужную память в зависимости от состояния игры.
        raw_response = self.director.decide_llm_action(self, command)

        # --- Шаг 2: Парсинг ответа ---
        # Эта часть остается такой же надежной, как и была.
        try:
            match = re.search(r'\{.*\}', raw_response, re.DOTALL)
            if not match:
                print(f"⚠️ Не удалось найти JSON в ответе LLM.")
                return raw_response

            json_string = match.group(0)
            response_data = json.loads(json_string)
            
            # --- Шаг 3: Применение изменений ---
            # Это - главная ответственность этой функции сейчас.
            narrative = response_data.get("narrative", "Мир погрузился в тишину...")
            changes = response_data.get("state_changes", {})
            feedback_lines = []

            # 3.1 Обновление Краткосрочной Памяти (если мы в бою)
            if self.state == GameState.COMBAT:
                self.short_term_memory.append(f"Игрок: '{command}'")
                self.short_term_memory.append(f"Результат: {narrative}")

            # 3.2 Применение механических изменений
            if "add_item" in changes:
                new_item_name = changes["add_item"]
                self.player.inventory.add_item(Item(name=new_item_name, description="Неизвестный предмет"))
                feedback_lines.append(f"(В инвентарь добавлен: {new_item_name})")

            if "damage_player" in changes:
                damage = int(changes["damage_player"])
                if damage > 0:
                    self.player.take_damage(damage)
                    feedback_lines.append(f"(Вы получили {damage} ед. урона!)")

            # 3.3 Обновление Долгосрочной Памяти (создание событий)
            if "new_event" in changes:
                event_text = changes["new_event"]
                event_id = f"event_{random.randint(1000, 9999)}"
                event_metadata = { "type": "event", "location": self.current_location.name }
                self.memory_service.add_memory(event_text, event_id, event_metadata)
            
            # 3.4 Проверка на смену состояния игры (триггер от LLM)
            if "new_game_state" in changes:
                new_state_str = changes["new_game_state"]
                if new_state_str == "COMBAT" and self.state != GameState.COMBAT:
                    self.change_state(GameState.COMBAT)
                elif new_state_str == "EXPLORATION" and self.state != GameState.COMBAT:
                    self.change_state(GameState.EXPLORATION)

            # --- Шаг 4: Формирование финального ответа для игрока ---
            full_response = narrative
            if feedback_lines:
                full_response += "\n" + "\n".join(feedback_lines)

            return full_response
            
        except json.JSONDecodeError:
            print(f"⚠️ Найденный текст похож на JSON, но содержит ошибку: {json_string}")
            return raw_response
        except Exception as e:
            print(f"⚠️ Произошла непредвиденная ошибка при обработке ответа: {e}")
            return raw_response

    # Сохранение состояния
    def get_state(self) -> dict:
        """Собирает все данные игры в словарь, готовый для сериализации."""
        state = {
            "player": {
                "name": self.player.name,
                "stats": self.player.stats,
                "inventory": [item.name for item in self.player.inventory._items]
            },
            "location": {
                "name": self.current_location.name,
                "tags": self.current_location.tags,
                "description": self.current_location.description
            }
        }
        return state
    
    def save_to_file(self, filename: str):
        """Сохраняет текущее состояние игры в JSON файл."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.get_state(), f, ensure_ascii=False, indent=4)
        print(f"Игра сохранена в {filename}")