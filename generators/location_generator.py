# generators/location_generator.py
import random
from typing import List
from models.location import Location
from services.llm_service import generate_location_description
from services.memory_service import MemoryService

# Базы для генерации. В будущем их можно вынести в отдельные файлы.
BIOMES = ["Пещера", "Лес", "Болото", "Руины", "Подземелье"]
INHABITANTS = ["Пауки", "Гоблины", "Скелеты", "Слизи", "Крысы"]
FEATURES = ["Сокровища", "Древний алтарь", "Загадочный туман", "Странные грибы", "Логово"]

def generate_random_location(game) -> Location:
    """Создает случайную локацию с набором тегов."""
    biome = random.choice(BIOMES)
    inhabitant = random.choice(INHABITANTS)
    feature = random.choice(FEATURES)

    name = f"{biome} | {inhabitant} | {feature}"
    tags = [biome.lower(), inhabitant.lower(), feature.lower()]

    print(f"\n...Генерация новой локации с тегами: {tags}...")

    # Шаг 2: Создаем объект локации
    location = Location(name=name, tags=tags)

    # Шаг 3: Используем данные из созданного объекта для поиска в памяти
    query_for_memory = " ".join(location.tags)
    # Ищем только релевантный лор для описания НОВОГО места
    relevant_context = game.memory_service.retrieve_relevant_memories(
        query_text=query_for_memory,
        n_results=2,
        filter_metadata={"type": "lore"}
    )

    description_from_ai = generate_location_description(location.tags, relevant_context)
    location.description = description_from_ai

    return location