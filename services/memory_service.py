# services/memory_service.py
import chromadb
from pathlib import Path
from typing import List, Dict, Any
from config import settings
from logic.constants import META_TYPE, TYPE_EVENT, TYPE_LORE

# Путь к базе данных из конфигурации или дефолтный
DB_PATH = settings.chromadb_persist_directory or str(Path(__file__).parent.parent / "db")

class MemoryService:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=DB_PATH)
        self.collection = self.client.get_or_create_collection(name="game_world_lore")

    def add_memory(self, text: str, memory_id: str, metadata: Dict[str, Any]):
        """
        Добавляет фрагмент текста с метаданными.
        """
        try:
            self.collection.add(
                documents=[text],
                ids=[memory_id],
                metadatas=[metadata]
            )
            print(f"✅ Добавлено воспоминание типа '{metadata.get(META_TYPE)}' с ID: {memory_id}")
        except Exception as e:
            print(f"⚠️ Не удалось добавить воспоминание: {e}")

    def retrieve_relevant_memories(self, query_text: str, n_results: int = 2, filter_metadata: Dict[str, Any] = None) -> List[str]:
        """
        Ищет релевантные воспоминания, опционально фильтруя по метаданным
        с корректным формированием фильтра для ChromaDB.
        """
        query_options = {
            "query_texts": [query_text],
            "n_results": n_results
        }

        if filter_metadata:
            log_message = ", ".join(f"{k}: {v}" for k, v in filter_metadata.items())
            print(f"🧠 Поиск воспоминаний ({log_message}), связанных с: '{query_text}'...")

            # --- КОНВЕРТЕР ФИЛЬТРА ---
            # Преобразуем простой словарь в формат, понятный ChromaDB
            conditions = []
            for key, value in filter_metadata.items():
                conditions.append({key: {"$eq": value}})
            
            if len(conditions) > 1:
                chroma_where_filter = {"$and": conditions}
            elif len(conditions) == 1:
                chroma_where_filter = conditions[0]
            else:
                chroma_where_filter = {} # Пустой фильтр, если словарь был пуст

            if chroma_where_filter:
                query_options["where"] = chroma_where_filter
        else:
            print(f"🧠 Поиск общих воспоминаний, связанных с: '{query_text}'...")

        results = self.collection.query(**query_options)

        retrieved = results['documents'][0]
        if retrieved:
            print(f"📚 Найдено: {retrieved}")
        else:
            print("📚 Ничего релевантного не найдено.")

        return retrieved