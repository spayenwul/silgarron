from typing import List
# В будущем здесь могут понадобиться импорты NPC, Enemy и т.д.
# from .enemy import Enemy 

class Location:
    def __init__(self, name: str, tags: List[str]):
        self.name = name
        self.tags = tags
        # Это поле заполняется нейросетью. Его важно сохранять.
        self.description = "Место выглядит неопределенно..."

        # --- Задел на будущее ---
        # Здесь мы будем хранить "паспорт" локации: кто и что в ней находится.
        # Пока эти списки будут пустыми.
        # self.enemies: List[Enemy] = [] 
        # self.npcs: List[NPC] = []
        # self.objects: List[InteractiveObject] = []

    def __str__(self):
        # Метод для отображения не меняется
        tags_str = ", ".join(self.tags)
        # В будущем можно будет добавить вывод врагов и NPC
        return f"--- Локация: {self.name} ---\nТеги: [{tags_str}]\nОписание: {self.description}"

    # --- Новая логика Save/Load ---

    def to_dict(self) -> dict:
        """
        Превращает объект Location в словарь для сохранения.
        """
        return {
            "name": self.name,
            "tags": self.tags,
            "description": self.description
            # Когда мы добавим врагов, здесь появится строка:
            # "enemies": [enemy.to_dict() for enemy in self.enemies]
        }

    @classmethod
    def from_dict(cls, data: dict):
        """
        Воссоздает объект Location из словаря.
        """
        # 1. Создаем базовый объект Location, используя конструктор
        location = cls(
            name=data.get("name", "Неизвестная локация"),
            tags=data.get("tags", [])
        )
        
        # 2. Восстанавливаем сгенерированное описание. Это важно,
        #    чтобы при загрузке не пришлось заново его генерировать,
        #    что экономит время и деньги, а также сохраняет консистентность.
        location.description = data.get("description", "Таинственный туман скрывает это место...")

        # Когда мы добавим врагов, здесь появится блок для их воссоздания:
        # enemy_data_list = data.get("enemies", [])
        # location.enemies = [Enemy.from_dict(enemy_data) for enemy_data in enemy_data_list]

        # 3. Возвращаем полностью готовый объект
        return location