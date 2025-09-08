# main.py
from models.character import Character
from models.item import Item
from generators.location_generator import generate_random_location

def main():
    """Главная функция игры."""
    print("Запуск текстовой RPG с AI...")

    # 1. Создаем персонажа
    player = Character(name="Авантюрист")

    # 2. Даем ему стартовые предметы
    healing_potion = Item(name="Зелье лечения", description="Восстанавливает немного здоровья.")
    old_sword = Item(name="Старый меч", description="Простой, но надежный меч.")
    player.inventory.add_item(healing_potion)
    player.inventory.add_item(old_sword)

    # 3. Выводим информацию о персонаже
    print(player)

    # 4. Генерируем и выводим первую локацию
    current_location = generate_random_location()
    print(current_location)


if __name__ == "__main__":
    main()