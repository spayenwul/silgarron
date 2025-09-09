# game.py
from models.character import Character
from models.item import Item
from models.location import Location
from generators.location_generator import generate_random_location

class Game:
    """
    Управляет всем состоянием игры.
    Хранит игрока и текущую локацию.
    """
    def __init__(self):
        self.player: Character | None = None
        self.current_location: Location | None = None

    def start_new_game(self, player_name: str):
        """Инициализирует новую игру."""
        self.player = Character(name=player_name)

        # Даем стартовые предметы
        healing_potion = Item(name="Зелье лечения", description="Восстанавливает немного здоровья.")
        old_sword = Item(name="Старый меч", description="Простой, но надежный меч.")
        self.player.inventory.add_item(healing_potion)
        self.player.inventory.add_item(old_sword)

        # Генерируем первую локацию
        self.current_location = generate_random_location()

        print("--- Новая игра началась! ---")