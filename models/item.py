class Item:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def __str__(self):
        return f"{self.name}: {self.description}"

    def to_dict(self) -> dict:
        """
        Превращает объект Item в словарь.
        """
        return {
            "name": self.name,
            "description": self.description
            # Если в будущем у предмета появятся новые свойства
            # (например, 'damage', 'is_usable'), их нужно будет добавить сюда.
        }

    @classmethod
    def from_dict(cls, data: dict):
        """
        Воссоздает (инстанцирует) объект Item из словаря.
        """
        # Мы просто берем значения из словаря и передаем их
        # в обычный конструктор __init__ нашего класса.
        return cls(
            name=data.get("name", "Неизвестный предмет"), 
            description=data.get("description", "")
        )