# services/llm_service.py
import os
from typing import List
import google.generativeai as genai
from dotenv import load_dotenv
from typing import List, Optional
import json

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


def generate_location_description(tags: List[str], context: Optional[List[str]] = None) -> str:
    """
    Генерирует описание локации, используя опциональный контекст из памяти.
    """
    model = genai.GenerativeModel(MODEL_NAME)
    tags_str = ", ".join(tags)

    # Динамически создаем промпт
    prompt_parts = [
        "Ты — мастер подземелий для текстовой ролевой игры в жанре тёмного фэнтези.",
        "Твоя задача — сгенерировать короткое, атмосферное и яркое описание локации (3-4 предложения).",
        "Не используй приветствия или лишние фразы, только сам текст описания.",
        f"Ключевые теги для генерации: [{tags_str}]"
    ]

    # Если нам передали контекст, добавляем его в промпт!
    if context:
        context_str = "\n".join(f"- {item}" for item in context)
        prompt_parts.append(
            "\nУчти следующую информацию из истории мира (это может быть слух, факт или прошлое событие):"
            f"\n{context_str}"
        )

    prompt = "\n".join(prompt_parts)

    print(f"...Отправка запроса в Gemini...")
    # Для отладки можно распечатать весь промпт:
    # print("--- PROMPT ---\n", prompt, "\n--------------")

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Произошла ошибка при обращении к API Gemini: {e}")
        return "Таинственный туман скрывает это место от ваших глаз..."

def generate_action_result(context: dict, player_action: str) -> str:
    """
    Генерирует нарративный результат действия игрока.
    """
    model = genai.GenerativeModel(MODEL_NAME)

    # Создаем максимально подробный промпт для ГМ
    prompt = f"""
    Ты — Мастер Подземелий и игровой движок для текстовой RPG. Твоя задача — отреагировать на действие игрока.
    Твой ответ ДОЛЖЕН БЫТЬ строго в формате JSON.

    JSON должен содержать два ключа:
    1. "narrative": (string) Атмосферное описание результата действия игрока (2-3 предложения).
    2. "state_changes": (object) Объект, описывающий механические изменения в игре. Возможные ключи: "add_item" (string, название предмета), "remove_item" (string), "damage_player" (integer), "new_event" (string, краткое описание события для записи в память). Если изменений нет, оставь объект пустым {{}}.

    ПРИМЕР ОТВЕТА:
    {{
      "narrative": "Вы шарите рукой по холодному алтарю и нащупываете небольшой бронзовый ключ. Кажется, он может подойти к какому-нибудь замку поблизости.",
      "state_changes": {{
        "add_item": "Бронзовый ключ"
      }}
    }}

    ТЕКУЩАЯ СИТУАЦИЯ:
    {json.dumps(context, ensure_ascii=False, indent=2)}

    ДЕЙСТВИЕ ИГРОКА:
    > {player_action}

    ТВОЙ JSON ОТВЕТ:
    """

    print("...Отправка действия игрока в Gemini...")
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Произошла ошибка при обработке действия: {e}")
        return "Мир на мгновение замер, не в силах отреагировать на ваше действие..."