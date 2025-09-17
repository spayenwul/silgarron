# models/inventory.py
from typing import List
from .item import Item

class Inventory:
    def __init__(self):
        self._items: List[Item] = []

    def add_item(self, item: Item):
        self._items.append(item)

    def remove_item(self, item_name: str):
        item_to_remove = next((item for item in self._items if item.name == item_name), None)
        if item_to_remove:
            self._items.remove(item_to_remove)
            
    def __str__(self):
        if not self._items:
            return "Инвентарь пуст."
        item_names = ", ".join(item.name for item in self._items)
        return f"В инвента-ре: {item_names}"

    def to_dict(self) -> dict:
        """
        Превращает инвентарь в словарь.
        Для этого он просит КАЖДЫЙ предмет в списке self._items
        тоже превратиться в словарь.
        """
        return {
            "items": [item.to_dict() for item in self._items]
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """
        Воссоздает объект Inventory из словаря.
        """
        # 1. Создаем новый, пустой объект инвентаря
        inventory = cls()
        
        # 2. Получаем список словарей, описывающих предметы.
        #    data.get("items", []) - безопасный способ, вернет [], если ключа "items" нет.
        item_data_list = data.get("items", [])
        
        # 3. Просим класс Item воссоздать КАЖДЫЙ предмет из его словаря
        #    и наполняем этим списком наш новый инвентарь.
        inventory._items = [Item.from_dict(item_data) for item_data in item_data_list]
        
        # 4. Возвращаем полностью готовый и наполненный объект инвентаря
        return inventory