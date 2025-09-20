import datetime
import json
from pathlib import Path
import functools

# --- Конфигурация ---
LOG_DIR = Path(__file__).parent.parent / "logs"
GAME_LOG_FILE = LOG_DIR / "game_events.log"
LLM_TRACE_FILE = LOG_DIR / "llm_trace.jsonl"


def setup_logging():
    """Создает папку для логов, если ее нет."""
    LOG_DIR.mkdir(exist_ok=True)


# --- "Человеческий" лог ---
def log_game_event(tag: str, message: str):
    """
    Записывает человекочитаемое событие в игровой лог.
    Пример: log_game_event("STATE_CHANGE", "EXPLORATION -> COMBAT")
    """
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{tag.upper()}] {message}\n"
        
        with open(GAME_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
            
    except Exception as e:
        print(f"🔴 Не удалось записать в игровой лог: {e}")


# --- Технический лог "Черный ящик" ---
def log_llm_trace(trace_data: dict):
    """
    Записывает полный технический след вызова LLM в JSONL файл.
    """
    try:
        trace_data["timestamp"] = datetime.datetime.now().isoformat()
        log_entry = json.dumps(trace_data, ensure_ascii=False) + "\n"
        
        with open(LLM_TRACE_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
            
    except Exception as e:
        print(f"🔴 Не удалось записать в LLM trace лог: {e}")


# --- Декоратор для логирования ввода ---
def log_player_input(func):
    """Декоратор, который логирует первый аргумент (команду) функции."""
    @functools.wraps(func)
    def wrapper(game_instance, command: str, *args, **kwargs):
        log_game_event("PLAYER_INPUT", command)
        result = func(game_instance, command, *args, **kwargs)
        return result
    return wrapper

# --- Инициализация ---
# Вызываем setup один раз при импорте модуля, чтобы папка 'logs' была создана
setup_logging()