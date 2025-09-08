# models/inventory.py
from typing import List
from .item import Item  # Точка означает "из этой же папки"

class Inventory:
    def __init__(self):
        self._items: List[Item] = []

    def add_item(self, item: Item):
        print(f"В инвентарь добавлен предмет: {item.name}")
        self._items.append(item)

    def remove_item(self, item_name: str):
        item_to_remove = next((item for item in self._items if item.name == item_name), None)
        if item_to_remove:
            self._items.remove(item_to_remove)
            print(f"Из инвентаря удален предмет: {item_name}")
        else:
            print(f"Предмет '{item_name}' не найден в инвентаре.")

    def __str__(self):
        if not self._items:
            return "Инвентарь пуст."
        item_names = ", ".join(item.name for item in self._items)
        return f"В инвентаре: {item_names}"