# game.py
import re
import json
from pathlib import Path 
import random 
from typing import List
from logic.constants import *
from models.character import Character
from models.item import Item
from models.location import Location
from services.llm_service import _send_prompt_to_gemini
from services.memory_service import MemoryService
from logic.director import Director
from logic.game_states import GameState
from utils.prompt_manager import load_and_format_prompt
from utils.logger import log_player_input
from services.world_data_service import WorldDataService
from services.tag_registry_service import TagRegistry
import generators.region_generator as region_gen
import generators.location_generator as loc_gen

SAVE_DIR = Path(__file__).parent / "saves"

class Game:
    def __init__(self, world_data_service, tag_registry_service, memory_service):
        """
        Конструктор теперь ТОЛЬКО ПРИНИМАЕТ и СОХРАНЯЕТ глобальные сервисы.
        Он больше не создает их сам и не выводит ничего в консоль.
        """
        self.player: Character | None = None
        self.current_location: Location | None = None
        self.state = GameState.EXPLORATION
        self.short_term_memory: List[str] = []
        
        # Сохраняем ссылки на УЖЕ СУЩЕСТВУЮЩИЕ, переданные нам сервисы
        self.world_data = world_data_service
        self.tag_registry = tag_registry_service
        self.memory_service = memory_service
        
        # Director легковесный, его можно создавать здесь
        self.director = Director()

    def start_new_game(self, player_name: str):
        """Инициализирует новую игру с использованием иерархической генерации."""
        self.player = Character(name=player_name)

        # Даем стартовые предметы
        healing_potion = Item(name="Зелье лечения", description="Восстанавливает немного здоровья.")
        old_sword = Item(name="Старый меч", description="Простой, но надежный меч.")
        self.player.inventory.add_item(healing_potion)
        self.player.inventory.add_item(old_sword)
        print("\n--- Запуск иерархической генерации мира ---")
        
        # 1. Выбираем "континент" для старта. Пока что можно захардкодить.
        # В будущем здесь может быть выбор игрока или случайный выбор.
        start_continent_id = "torax" 
        
        # 2. Генерируем паспорт РЕГИОНА в контексте этого континента.
        # Передаем сервисы как зависимости, чтобы генератор имел доступ к данным.
        region_passport = region_gen.generate_region_passport_in_context(
            world_data_service=self.world_data,
            tag_registry=self.tag_registry, # Передаем, чтобы генератор мог использовать теги
            continent_id=start_continent_id
        )

        # 3. На основе региона генерируем паспорт стартовой ЛОКАЦИИ.
        location_passport = loc_gen.generate_location_passport(
            region_passport=region_passport,
            tag_registry=self.tag_registry,
            world_data_service=self.world_data

        )

        # 4. Создаем объект Location, передавая ему паспорт.
        # Класс Location должен быть обновлен, чтобы принимать 'passport' в __init__.
        self.current_location = Location(passport=location_passport)

        # 5. Просим LLM сгенерировать художественное описание
        # на основе ПОЛНОГО и богатого паспорта локации.
        # Это потребует создания нового, специализированного промпта.
        # description = llm.generate_artistic_description(self.current_location.passport)
        # self.current_location.description = description
        # ПОКА ЧТО для теста можно использовать заглушку:
        self.current_location.description = f"Вы находитесь в локации '{self.current_location.name}'.\n" \
                                            f"Сгенерированные теги: {self.current_location.tags}"
        
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

    def _apply_state_changes(self, changes: dict, narrative: str, command: str) -> str:
        """
        Применяет все механические изменения из объекта state_changes
        и формирует финальный ответ для игрока.
        """
        feedback_lines = [] # Собираем сюда сообщения о механических изменениях для игрока

        # --- Применение изменений ---

        # 1. Обновление Краткосрочной Памяти (если мы в бою)
        if self.state == GameState.COMBAT:
            self.short_term_memory.append(f"Игрок: '{command}'")
            self.short_term_memory.append(f"Результат: {narrative}")

        # 2. Обработка добавления предметов
        if ADD_ITEM in changes:
            new_item_name = changes[ADD_ITEM]
            self.player.inventory.add_item(Item(name=new_item_name, description="Неизвестный предмет"))
            feedback_lines.append(f"(В инвентарь добавлен: {new_item_name})")

        # 3. Обработка урона игроку
        if DAMAGE_PLAYER in changes:
            damage = int(changes[DAMAGE_PLAYER])
            if damage > 0:
                self.player.take_damage(damage)
                feedback_lines.append(f"(Вы получили {damage} ед. урона!)")

        # 4. Обновление Долгосрочной Памяти (создание событий)
        if NEW_EVENT in changes:
            event_text = changes[NEW_EVENT]
            event_id = f"event_{random.randint(1000, 9999)}"
            event_metadata = {META_TYPE: TYPE_EVENT, META_LOCATION: self.current_location.name}
            self.memory_service.add_memory(event_text, event_id, event_metadata)
        
        # 5. Проверка на смену состояния игры (триггер от LLM)
        if NEW_GAME_STATE in changes:
            new_state_str = changes[NEW_GAME_STATE]
            # Этот блок можно будет улучшить, используя Enum, но пока оставим так
            if new_state_str == "COMBAT" and self.state != GameState.COMBAT:
                self.change_state(GameState.COMBAT)
            elif new_state_str == "EXPLORATION" and self.state != GameState.COMBAT:
                self.change_state(GameState.EXPLORATION)

        # --- Формирование финального ответа ---
        full_response = narrative
        if feedback_lines:
            full_response += "\n" + "\n".join(feedback_lines)

        return full_response

    def _extract_json_from_text(self, text: str) -> str:
        """
        Ищет и извлекает первую корректную JSON-строку из текста с помощью regex.
        Поддерживает вложенные структуры.
        """
        # Ищем JSON с помощью regex (поддерживает вложенность)
        pattern = r'\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}'
        match = re.search(pattern, text)
        
        if match:
            return match.group(0) # Возвращаем найденную строку
        
        raise ValueError("JSON-объект не найден в тексте ответа LLM.")

    def _validate_llm_response(self, data: dict):
        """
        Проверяет, что распарсенный JSON от LLM имеет правильную структуру и типы данных.
        Выбрасывает ValueError, если проверка не пройдена.
        """
        if not isinstance(data, dict):
            raise ValueError(f"Ответ LLM должен быть словарем (dict), а не {type(data).__name__}.")
        
        if NARRATIVE not in data:
            raise ValueError(f"В ответе LLM отсутствует обязательное поле '{NARRATIVE}'.")
        
        if not isinstance(data[NARRATIVE], str):
             raise ValueError(f"Поле '{NARRATIVE}' должно быть строкой, а не {type(data[NARRATIVE]).__name__}.")

        if STATE_CHANGES not in data:
            raise ValueError(f"В ответе LLM отсутствует обязательное поле '{STATE_CHANGES}'.")

        if not isinstance(data[STATE_CHANGES], dict):
            raise ValueError(f"Поле '{STATE_CHANGES}' должно быть словарем, а не {type(data[STATE_CHANGES]).__name__}.")
        
    @log_player_input
    def process_player_command(self, command: str) -> str:
        """
        Делегирует команду Режиссёру, парсит ответ с помощью regex,
        валидирует его структуру и передает изменения в _apply_state_changes.
        """
        # 1. Получаем сырой ответ от LLM через Режиссёра
        raw_response = self.director.decide_llm_action(self, command)
        
        try:          
            # Шаг 1: Используем надежный парсер для извлечения JSON
            json_string = self._extract_json_from_text(raw_response)
            
            # Шаг 2: Декодируем JSON
            response_data = json.loads(json_string)
            
            # Шаг 3: Валидируем структуру и типы данных
            self._validate_llm_response(response_data)
            
            # Если все проверки пройдены, мы можем безопасно извлекать данные
            narrative = response_data[NARRATIVE]
            changes = response_data[STATE_CHANGES]
            
            return self._apply_state_changes(changes, narrative, command)
            
        except (json.JSONDecodeError, ValueError) as e:
            # Ловим ошибки парсинга (JSONDecodeError) и валидации (ValueError)
            print(f"⚠️ Ошибка обработки ответа LLM: {e}")
            print(f"⚠️ Возвращаем сырой ответ как есть.")
            return raw_response
        except Exception as e:
            print(f"⚠️ Произошла непредвиденная ошибка при обработке ответа: {e}")
            return raw_response

    # --- СИСТЕМА SAVE/LOAD ---

    def to_dict(self) -> dict:
        """Собирает полное состояние игры в один словарь."""
        print("DEBUG: Собираем состояние игры для сохранения...")
        return {
            "player": self.player.to_dict() if self.player else None,
            "current_location": self.current_location.to_dict() if self.current_location else None,
            "game_state": self.state.name, # Сохраняем имя Enum, например 'EXPLORATION'
            "short_term_memory": self.short_term_memory,
            # Долгосрочную память (ChromaDB) мы не сохраняем, она живет отдельно в своей папке.
            # Мы доверяем, что она будет на месте при следующей загрузке.
        }

    def load_from_dict(self, data: dict):
        """Восстанавливает состояние игры из словаря. Этот метод вызывается на уже существующем объекте."""
        print("DEBUG: Восстанавливаем состояние игры из словаря...")
        # Воссоздаем объекты, делегируя это их классам
        self.player = Character.from_dict(data["player"]) if data.get("player") else None
        self.current_location = Location.from_dict(data["current_location"]) if data.get("current_location") else None
        
        # Восстанавливаем Enum по его имени
        self.state = GameState[data.get("game_state", "EXPLORATION")]
        
        # Восстанавливаем простые данные
        self.short_term_memory = data.get("short_term_memory", [])
        
        print("--- Игра успешно загружена ---")

    def save_to_file(self, filename: str):
        """Сохраняет игру в JSON файл."""
        # Создаем папку 'saves', если ее еще нет. `exist_ok=True` предотвращает ошибку, если папка уже есть.
        SAVE_DIR.mkdir(exist_ok=True) 
        filepath = SAVE_DIR / f"{filename}.json"
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                # json.dump элегантно записывает наш словарь в файл
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=4)
            print(f"✅ Игра сохранена в файл: {filepath.name}")
        except Exception as e:
            print(f"🔴 Не удалось сохранить игру: {e}")

    @classmethod
    def load_from_file(cls, filename: str):
        """Создает НОВЫЙ объект Game и загружает в него данные из файла."""
        filepath = SAVE_DIR / f"{filename}.json"
        
        if not filepath.exists():
            print(f"🔴 Файл сохранения не найден: {filepath}")
            return None

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Создаем новый "чистый" экземпляр игры
            game_instance = cls() 
            # Наполняем его данными из файла
            game_instance.load_from_dict(data)
            return game_instance
        except Exception as e:
            print(f"🔴 Не удалось загрузить игру из файла: {e}")
            return None