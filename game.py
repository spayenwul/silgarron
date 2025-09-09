# game.py
import re
import json
import random 
from models.character import Character
from models.item import Item
from models.location import Location
from generators.location_generator import generate_random_location  # Отсюда берем ТОЛЬКО генератор локаций
from services.llm_service import generate_action_result          # обработчик действий берем из СЕРВИСА
from services.memory_service import MemoryService

class Game:
    def __init__(self):
        self.player: Character | None = None
        self.current_location: Location | None = None
        
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
        self.current_location = generate_random_location(self.memory_service)
        print("--- Новая игра началась! ---")

    def process_player_command(self, command: str) -> str:
        """
        Обрабатывает команду игрока, обращаясь к LLM для генерации результата.
        """
        print("...Обдумывание действия...")

        context = {
            "location_tags": self.current_location.tags,
            "location_description": self.current_location.description,
            "player_stats": self.player.stats,
            "player_inventory": [item.name for item in self.player.inventory._items]
        }

        # Получаем структурированный ответ
        raw_response = generate_action_result(context, command)

        try:
            # ПАРСЕР

            # 1. Ищем паттерн: всё от первого '{' до последнего '}' включительно.
            # re.DOTALL позволяет символу '.' соответствовать также и переносам строк.
            match = re.search(r'\{.*\}', raw_response, re.DOTALL)

            # 2. Проверяем, был ли JSON вообще найден
            if not match:
                print(f"⚠️ Не удалось найти JSON в ответе LLM.")
                return raw_response

            # 3. Извлекаем найденную часть
            json_string = match.group(0)

            # 4. Парсим только извлеченную, чистую строку JSON
            response_data = json.loads(json_string)
            
            narrative = response_data.get("narrative", "Произошло что-то странное...")
            changes = response_data.get("state_changes", {})
            feedback_lines = [] # Собираем сюда сообщения о механических изменениях

            if "add_item" in changes:
                new_item_name = changes["add_item"]
                self.player.inventory.add_item(Item(name=new_item_name, description="Неизвестный предмет"))
                narrative += f"\n(В инвентарь добавлен: {new_item_name})"

            if "damage_player" in changes:
                damage = int(changes["damage_player"])
                if damage > 0:
                    self.player.take_damage(damage)
                    feedback_lines.append(f"(Вы получили {damage} ед. урона!)")

            if "new_event" in changes:
                event_text = changes["new_event"]
                event_id = f"event_{random.randint(1000, 9999)}" 
                self.memory_service.add_memory(event_text, event_id)

            # Собираем финальный ответ для игрока
            full_response = narrative
            if feedback_lines:
                # Добавляем все сообщения о механике в конце
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