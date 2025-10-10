# config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """
    Централизованная конфигурация проекта.
    Значения загружаются из .env файла или переменных окружения.
    """

    # ==================== API KEYS ====================
    gemini_api_key: str

    # ==================== GAME SETTINGS ====================
    max_turn_memory: int = 50
    max_short_term_memory: int = 10

    # ==================== LLM SETTINGS ====================
    llm_model: str = "gemini-2.0-flash-exp"  # Обновлено: gemini-1.5-flash deprecated
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2000

    # ==================== PATHS ====================
    saves_dir: str = "saves"
    data_dir: str = "data"
    prompts_dir: str = "prompts"

    # ==================== MEMORY SERVICE ====================
    chromadb_persist_directory: Optional[str] = None
    embedding_model: str = "all-MiniLM-L6-v2"

    # ==================== HEX GRID (для будущего) ====================
    hex_grid_radius: int = 15
    hex_grid_default_size: int = 20

    # ==================== DEBUG ====================
    debug_mode: bool = False
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Игнорировать дополнительные поля из .env

# Глобальный экземпляр настроек
settings = Settings()
