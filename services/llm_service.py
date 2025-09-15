# services/llm_service.py
import os
from typing import List
import google.generativeai as genai
from dotenv import load_dotenv
from typing import List, Optional
import json
from utils.logger import log_llm_interaction 
from logic.constants import *

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
    # Если нам передали контекст, добавляем его в промпт
    if context:
        context_str = "\n".join(f"- {item}" for item in context)
        prompt_parts.append(
            "\nУчти следующую информацию из истории мира (это может быть слух, факт или прошлое событие):"
            f"\n{context_str}"
        )

    prompt = "\n".join(prompt_parts)

    response_text = _send_prompt_to_gemini(prompt)
    # Проверяем, не является ли ответ JSON-ошибкой
    # Так как _send_prompt_to_gemini может вернуть JSON, а нам нужен простой текст,
    # мы делаем простую проверку.
    if response_text.strip().startswith('{'):
        # Это, скорее всего, аварийный JSON. Возвращаем запасной текст.
        return "Таинственный туман скрывает это место от ваших глаз..."
    else:
        return response_text
        
def generate_action_result(context: dict, memories: List[str], player_action: str) -> str:
    """Генерирует JSON-ответ для режима ИССЛЕДОВАНИЯ."""
    prompt = f"""
    Ты — Мастер Подземелий в режиме исследования. Твоя задача — отреагировать на действие игрока.
    Твой ответ ДОЛЖЕН БЫТЬ строго в формате JSON с ключами "narrative" и "state_changes".

    # V-- ЭТА ИНСТРУКЦИЯ КРИТИЧЕСКИ ВАЖНА --V
    КЛЮЧЕВОЕ ПРАВИЛО: Если действие игрока является явной атакой, агрессией или провокацией, которая НЕИЗБЕЖНО ведет к началу боя, ты ОБЯЗАН добавить в "state_changes" ключ "new_game_state" со значением "COMBAT". В остальных случаях этот ключ добавлять не нужно.

    Пример начала боя:
    - Игрок: "Я атакую слизь мечом"
    - Твой JSON: {{
        "{NARRATIVE}": "Вы бросаетесь на слизь, которая враждебно раздувается в ответ. Бой начался!",
        "{STATE_CHANGES}": {{
            "{NEW_GAME_STATE}": "COMBAT",
            "{NEW_EVENT}": "Игрок спровоцировал бой со слизью"
        }}
    }}
    # ------------------------------------
    
    КОНТЕКСТ ИЗ ИСТОРИИ МИРА:
    {json.dumps(memories, ensure_ascii=False, indent=2) if memories else "Нет релевантных воспоминаний."}

    ТЕКУЩАЯ СИТУАЦИЯ:
    {json.dumps(context, ensure_ascii=False, indent=2)}

    ДЕЙСТВИЕ ИГРОКА:
    > {player_action}

    ТВОЙ JSON ОТВЕТ:
    """
    return _send_prompt_to_gemini(prompt)


def generate_combat_action_result(combat_log: List[str], lore: List[str], player_action: str) -> str:
    """
    Генерирует результат боевого хода, используя лог боя.
    """
    model = genai.GenerativeModel(MODEL_NAME)
    
    log_str = "\n".join(combat_log)
    lore_str = "\n".join(lore) if lore else "Нет особых данных."

    prompt = f"""
    Ты — Мастер Подземелий, ведущий напряженную боевую сцену в текстовой RPG.
    Твой ответ ДОЛЖЕН БЫТЬ строго в формате JSON с ключами "narrative" и "state_changes".

    КЛЮЧЕВОЕ ПРАВИЛО: Если бой окончился делаем "state_changes" ключ "new_game_state" со значением "EXPLORATION".

    ПРИМЕР ОТВЕТА ДЛЯ БОЕВОГО ХОДА:
    {{
      "{NARRATIVE}": "Вы уворачиваетесь от замаха гоблина и наносите ответный удар мечом ему в бок. Враг отшатывается, но его союзник бьет вас дубинкой по спине.",
      "{STATE_CHANGES}": {{
        "{DAMAGE_PLAYER}": 3,
        "{NEW_EVENT}": "Игрок ранил гоблина, но получил ответный удар"
      }}
    }}

    Опирайся на ПОЛНЫЙ лог боя, чтобы сохранить преемственность. Опиши не только действие игрока, но и ответный ход противника. Бой должен ощущаться динамичным.

    ПОЛЕЗНАЯ ИНФОРМАЦИЯ ИЗ ИСТОРИИ МИРА (уязвимости, тактика):
    {lore_str}

    ПОЛНЫЙ ЛОГ ТЕКУЩЕГО БОЯ:
    ---
    {log_str}
    ---

    ДЕЙСТВИЕ ИГРОКА В ЭТОМ ХОДЕ:
    > {player_action}

    ТВОЙ JSON ОТВЕТ (опиши яркий результат и ответный ход врага):
    """
    return _send_prompt_to_gemini(prompt)

def _send_prompt_to_gemini(prompt: str) -> str:
    """
    Единая функция для отправки любого промпта в Gemini.
    Обрабатывает сам вызов API, извлечение текста и базовые ошибки.
    """
    raw_response = "" # Инициализируем переменную для логгера
    try:
        # 1. Выбираем модель.
        model = genai.GenerativeModel(MODEL_NAME)
        
        # 2. Отправляем запрос
        print("...Отправка запроса в Gemini...")
        response = model.generate_content(prompt)
        raw_response = response.text.strip()
        
        return raw_response

    except Exception as e:
        print(f"🔴 КРИТИЧЕСКАЯ ОШИБКА API Gemini: {e}")
        raw_response = """
        {
          "{NARRATIVE}": "В мироздании произошел сбой...",
          "{STATE_CHANGES}": {}
        }
        """
        return raw_response
    # Логирование    
    finally:
        if prompt and raw_response:
             log_llm_interaction(prompt, raw_response)