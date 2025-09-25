from typing import List, Dict, Any

class Location:
    def __init__(self, passport: Dict[str, Any]):
        self.name: str = passport.get("name", "Неизвестное место")
        self.tags: List[str] = passport.get("tags", [])
        # Описание тоже может быть в паспорте, либо генерироваться позже
        self.description: str = passport.get("description", "Место выглядит неопределенно...")
        self.passport = passport # Сохраняем весь паспорт на всякий случай

    def __str__(self):
        # Метод для отображения не меняется
        tags_str = ", ".join(self.tags)
        # В будущем можно будет добавить вывод врагов и NPC
        return f"--- Локация: {self.name} ---\nТеги: [{tags_str}]\nОписание: {self.description}"

    # --- Save/Load ---
    def __str__(self):
        tags_str = ", ".join(self.tags)
        return f"--- Локация: {self.name} ---\nТеги: [{tags_str}]\nОписание: {self.description}"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "tags": self.tags,
            "description": self.description,
            "passport": self.passport # Сохраняем и паспорт
        }

    @classmethod
    def from_dict(cls, data: dict):
        # Если в сохранении есть паспорт, используем его для воссоздания
        if "passport" in data:
            return cls(passport=data["passport"])
        else: # Обратная совместимость со старыми сохранениями
            location = cls(passport={}) # Создаем с пустым паспортом
            location.name = data.get("name", "Неизвестная локация")
            location.tags = data.get("tags", [])
            location.description = data.get("description", "Таинственный туман...")
            return location