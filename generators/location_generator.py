# generators/location_generator.py
import random
from typing import List
from models.location import Location # Импортируем наш класс Location

# Базы для генерации. В будущем их можно вынести в отдельные файлы.
BIOMES = ["Пещера", "Лес", "Болото", "Руины", "Подземелье"]
INHABITANTS = ["Пауки", "Гоблины", "Скелеты", "Слизи", "Крысы"]
FEATURES = ["Сокровища", "Древний алтарь", "Загадочный туман", "Странные грибы", "Логово"]

def generate_random_location() -> Location:
    """Создает случайную локацию с набором тегов."""
    biome = random.choice(BIOMES)
    inhabitant = random.choice(INHABITANTS)
    feature = random.choice(FEATURES)

    name = f"{biome} | {inhabitant} | {feature}"
    tags = [biome.lower(), inhabitant.lower(), feature.lower()]

    print(f"\n...Генерация новой локации с тегами: {tags}...")

    return Location(name=name, tags=tags)