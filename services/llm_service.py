# services/llm_service.py
import os
from typing import List
import google.generativeai as genai
from dotenv import load_dotenv
from typing import List, Optional
import json
from utils.logger import log_llm_trace
from utils.prompt_manager import load_and_format_prompt
from logic.constants import *

# --- Конфигурация ---
# Загружаем переменные окружения один раз при запуске
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


# --- Основная точка входа в API ---
def _send_prompt_to_gemini(request_package: dict) -> str:
    """
    Единая, централизованная функция для отправки любого промпта в Gemini.
    Принимает "пакет запроса", отправляет его и логирует полный след.
    """
    # 1. Распаковываем данные из пакета
    prompt = request_package.get("prompt", "")
    
    raw_response = ""
    # 2. Создаем "скелет" для лога, копируя данные из пакета
    trace = request_package.copy()
    trace["error"] = None
    
    try:
        # 3. Вызываем API
        model = genai.GenerativeModel(MODEL_NAME)
        print("...Отправка запроса в Gemini...")
        response = model.generate_content(prompt)
        raw_response = response.text.strip()
        
        trace["raw_response"] = raw_response
        return raw_response
        
    except Exception as e:
        # 4. Обрабатываем любые ошибки
        error_message = f"КРИТИЧЕСКАЯ ОШИБКА API Gemini: {e}"
        print(f"🔴 {error_message}")
        
        # Формируем "аварийный" JSON-ответ
        raw_response = """
        {
          "narrative": "В мироздании произошел сбой. На мгновение реальность треснула, не в силах обработать ваше действие. Попробуйте еще раз.",
          "state_changes": {}
        }
        """
        trace["error"] = error_message
        trace["raw_response"] = raw_response
        return raw_response
        
    finally:
        # 5. Логируем результат, неважно, успешный он или нет
        log_llm_trace(trace)

# --- Вспомогательная функция (пока что) ---
def generate_location_description(tags: List[str], context: Optional[List[str]] = None) -> str:
    """
    Генерирует описание для НОВОЙ локации.
    Это одна из немногих функций, которая сама формирует промпт.
    """
    tags_str = ", ".join(tags)

    context_block = ""
    if context:
        context_items_str = "\n".join(f"- {item}" for item in context)
        context_block = (
            "\nУчти следующую информацию из истории мира (это может быть слух, факт или прошлое событие):"
            f"\n{context_items_str}"
        )

    prompt = load_and_format_prompt(
        'location_description',
        tags_str=tags_str,
        context_block=context_block
    )
    
    # Собираем "пакет" для отправки и логирования
    llm_request = {
        "prompt": prompt,
        "prompt_template_name": "location_description",
        "game_state": "GENERATION" # Специальное состояние для лога
    }
    
    return _send_prompt_to_gemini(llm_request)