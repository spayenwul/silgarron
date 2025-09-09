# services/memory_service.py
import chromadb
from typing import List

# Инициализируем клиент ChromaDB. 
# Он создаст файлы для хранения данных в папке проекта.
client = chromadb.Client()

# Создаем "коллекцию" (аналог таблицы в SQL). 
# Если она уже есть, просто подключаемся к ней.
# embedding_function - это то, как Chroma будет превращать текст в векторы.
# Мы оставляем значение по умолчанию, которое отлично работает.
collection = client.get_or_create_collection(name="game_world_lore")

class MemoryService:
    def add_memory(self, text: str, memory_id: str):
        """
        Добавляет фрагмент текста (воспоминание/лор) в базу данных.
        """
        try:
            collection.add(
                documents=[text],
                ids=[memory_id]
            )
            print(f"✅ Добавлено воспоминание с ID: {memory_id}")
        except Exception as e:
            # Например, если ID уже существует
            print(f"⚠️ Не удалось добавить воспоминание: {e}")

    def retrieve_relevant_memories(self, query_text: str, n_results: int = 2) -> List[str]:
        """
        Ищет в базе несколько самых релевантных воспоминаний.
        """
        print(f"🧠 Поиск воспоминаний, связанных с: '{query_text}'...")
        results = collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        
        # results['documents'][0] содержит список найденных текстов
        retrieved = results['documents'][0]
        if retrieved:
            print(f"📚 Найдено: {retrieved}")
        else:
            print("📚 Ничего релевантного не найдено.")
            
        return retrieved