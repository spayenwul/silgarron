from pathlib import Path
from config import settings

# Указываем путь к папке с промптами из конфигурации
PROMPT_DIR = Path(settings.prompts_dir)

def load_and_format_prompt(prompt_name: str, **kwargs) -> str:
    """
    Загружает промпт из файла и форматирует его, подставляя значения.
    
    :param prompt_name: Имя файла без .txt (например, 'combat_action')
    :param kwargs: Словарь с переменными для подстановки
    """
    try:
        filepath = PROMPT_DIR / f"{prompt_name}.txt"
        with open(filepath, "r", encoding="utf-8") as f:
            prompt_template = f.read()
        
        return prompt_template.format(**kwargs)
    except FileNotFoundError:
        print(f"🔴 ОШИБКА: Файл промпта не найден: {filepath}")
        return "Ошибка: промпт не найден."
    except KeyError as e:
        print(f"🔴 ОШИБКА: В промпте '{prompt_name}' не хватает переменной: {e}")
        return "Ошибка: неверная переменная в промпте."