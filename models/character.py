# models/character.py
from .inventory import Inventory

class Character:
    def __init__(self, name: str):
        self.name = name
        self.max_hp = 20
        self.hp = self.max_hp
        self.stats = {
            "сила": 10,
            "ловкость": 10,
            "интеллект": 10,
        }
        self.inventory = Inventory()

    def take_damage(self, amount: int):
        """Уменьшает здоровье персонажа."""
        self.hp -= amount
        if self.hp < 0:
            self.hp = 0 # Здоровье не может быть отрицательным
        print(f"DEBUG: Персонаж {self.name} получил {amount} урона. Осталось HP: {self.hp}")

    def is_dead(self) -> bool:
        """Проверяет, жив ли персонаж."""
        return self.hp <= 0

    def __str__(self):
        # Отображение
        stats_str = ", ".join(f"{key}: {value}" for key, value in self.stats.items())
        status_line = f"Здоровье: {self.hp}/{self.max_hp}"
        return f"=== Персонаж: {self.name} ===\n{status_line}\nСтаты: {stats_str}\n{self.inventory}"
        
    def to_dict(self) -> dict:
        # 1. Берем все "простые" атрибуты (имя, hp, статы) автоматически
        state = self.__dict__.copy() 
        
        # 2. Сложные, вложенные объекты обрабатываем вручную
        # Мы не можем просто сохранить объект Inventory, нам нужно его тоже превратить в словарь
        state['inventory'] = self.inventory.to_dict()
        
        return state

    @classmethod
    def from_dict(cls, data: dict):
        # Создаем пустой объект, не вызывая __init__
        obj = cls.__new__(cls)
        
        # 1. Загружаем все "простые" атрибуты
        obj.__dict__.update(data)
        
        # 2. Сложные объекты воссоздаем из их словарей
        obj.inventory = Inventory.from_dict(data['inventory'])
        
        return obj