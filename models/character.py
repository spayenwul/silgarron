# models/character.py
from .inventory import Inventory

class Character:
    def __init__(self, name: str):
        self.name = name
        self.stats = {
            "сила": 10,
            "ловкость": 10,
            "интеллект": 10,
        }
        self.inventory = Inventory()

    def __str__(self):
        stats_str = ", ".join(f"{key}: {value}" for key, value in self.stats.items())
        return f"=== Персонаж: {self.name} ===\nСтаты: {stats_str}\n{self.inventory}"