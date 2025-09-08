# models/location.py
from typing import List

class Location:
    def __init__(self, name: str, tags: List[str]):
        self.name = name
        self.tags = tags
        # Это поле оставим пустым. Его в будущем заполнит нейросеть.
        self.description = "Место выглядит неопределенно..."

    def __str__(self):
        tags_str = ", ".join(self.tags)
        return f"--- Локация: {self.name} ---\nТеги: [{tags_str}]\nОписание: {self.description}"