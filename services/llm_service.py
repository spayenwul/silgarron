# services/llm_service.py
import os
from typing import List
import google.generativeai as genai
from dotenv import load_dotenv
from typing import List, Optional
import json
from utils.logger import log_llm_interaction 
from logic.constants import *
from utils.prompt_manager import load_and_format_prompt
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
    Генерирует описание локации, используя шаблон из файла и динамически
    формируя блок контекста.
    """
    # --- Шаг 1: Подготовка переменных для шаблона ---

    # 1.1. Обязательная переменная: строка с тегами
    tags_str = ", ".join(tags)

    # 1.2. Динамическая переменная: блок контекста
    context_block = "" # По умолчанию - пустая строка
    if context:
        # Если контекст есть, формируем целый абзац текста
        context_items_str = "\n".join(f"- {item}" for item in context)
        context_block = (
            "\nУчти следующую информацию из истории мира (это может быть слух, факт или прошлое событие):"
            f"\n{context_items_str}"
        )

    # --- Шаг 2: Вызов менеджера промптов ---
    # Передаем ему все подготовленные переменные
    prompt = load_and_format_prompt(
        'location_description',
        tags_str=tags_str,
        context_block=context_block
    )

    # --- Шаг 3: Отправка готового промпта в API ---
    return _send_prompt_to_gemini(prompt)

def generate_combat_action_result(combat_log: List[str], lore: List[str], player_action: str) -> str:
    log_str = "\n".join(combat_log)
    lore_str = "\n".join(lore) if lore else "Нет особых данных."
    
    prompt = load_and_format_prompt(
        'combat_action',
        narrative_key=NARRATIVE,
        state_changes_key=STATE_CHANGES,
        damage_player_key=DAMAGE_PLAYER,
        combat_log=log_str,
        lore=lore_str,
        player_action=player_action
    )
    
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