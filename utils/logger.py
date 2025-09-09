# utils/logger.py
import datetime

LOG_FILENAME = "llm_debug_log.txt"

def log_llm_interaction(prompt: str, raw_response: str):
    """
    Записывает полный текст промпта и ответа от LLM в лог-файл.
    """
    try:
        with open(LOG_FILENAME, "a", encoding="utf-8") as f:
            # 'a' означает 'append' - дописывать в конец файла
            
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            f.write("="*80 + "\n")
            f.write(f"TIMESTAMP: {timestamp}\n")
            f.write("="*80 + "\n\n")
            
            f.write("--- PROMPT SENT TO LLM --->\n")
            f.write(prompt)
            f.write("\n\n")
            
            f.write("<--- RAW RESPONSE FROM LLM ---\n")
            f.write(raw_response)
            f.write("\n\n")

        print(f"📝 Запись в лог '{LOG_FILENAME}' добавлена.")
    except Exception as e:
        print(f"🔴 Не удалось записать в лог-файл: {e}")