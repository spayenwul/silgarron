# services/llm_service.py
import os
from typing import List
import google.generativeai as genai
from dotenv import load_dotenv

# Загружаем переменные окружения (включая наш API ключ) из файла .env
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-pro") 


try:
    if not API_KEY:
        raise ValueError("Ключ API Gemini не найден. Проверьте файл .env и переменную GEMINI_API_KEY.")
    
    genai.configure(api_key=API_KEY)
    print(f"Сервис Gemini успешно сконфигурирован. Используется модель: {MODEL_NAME}")

except Exception as e:
    print(f"Ошибка конфигурации Gemini: {e}")


def generate_location_description(tags: List[str]) -> str:
    """
    Генерирует описание локации с помощью Gemini на основе тегов.
    """
    try:
        # 1. Выбираем модель из нашей переменной
        model = genai.GenerativeModel(MODEL_NAME)

        # 2. Создаем "промпт" - инструкцию для нейросети
        tags_str = ", ".join(tags)
        prompt = f"""
        Ты — мастер подземелий для текстовой ролевой игры в жанре тёмного фэнтези. 
        Твоя задача — сгенерировать короткое, атмосферное и яркое описание локации (3-4 предложения).
        Не используй приветствия или лишние фразы, только сам текст описания.
        
        Ключевые теги для генерации: [{tags_str}]
        """

        print(f"...Отправка запроса в Gemini с тегами: {tags}...")

        # 3. Отправляем запрос
        response = model.generate_content(prompt)
        # 4. Возвращаем сгенерированный текст
        return response.text.strip()
    
    except Exception as e:
        print(f"Произошла ошибка при обращении к API Gemini: {e}")
        return "Таинственный туман скрывает это место от ваших глаз..."