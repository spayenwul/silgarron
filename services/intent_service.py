import json
import chromadb
from pathlib import Path

INTENTS_FILE = Path(__file__).parent.parent / "data/intents.json"
COLLECTION_NAME = "intent_recognition_collection"

class IntentService:
    def __init__(self):
        print("⚙️ Инициализация Сервиса Распознавания Намерений...")
        client = chromadb.Client()
        # 1. Получаем список ВСЕХ существующих коллекций
        existing_collections = [c.name for c in client.list_collections()]
        
        # 2. Проверяем, есть ли НАША коллекция в этом списке
        if COLLECTION_NAME in existing_collections:
            # 3. И удаляем ее, только если она была найдена
            print(f"Очистка старой базы намерений ('{COLLECTION_NAME}')...")
            client.delete_collection(name=COLLECTION_NAME)
        
        # 4. Теперь мы можем безопасно создавать новую, чистую коллекцию
        self.collection = client.get_or_create_collection(name=COLLECTION_NAME)
        self._load_intents_into_chroma()

    def _load_intents_into_chroma(self):
        """Загружает все примеры из JSON в векторную базу."""
        with open(INTENTS_FILE, "r", encoding="utf-8") as f:
            intents_data = json.load(f)
        
        # Готовим данные для ChromaDB
        documents = [item['text'] for item in intents_data]
        metadatas = [item['metadata'] for item in intents_data]
        ids = [f"intent_{i}" for i in range(len(documents))]

        self.collection.add(documents=documents, metadatas=metadatas, ids=ids)
        print(f"✅ Векторная база намерений успешно загружена ({len(documents)} примеров).")

    def recognize_intent(self, player_command: str) -> str:
        """
        Находит наиболее близкое намерение к команде игрока.
        """
        results = self.collection.query(
            query_texts=[player_command],
            n_results=1 # Нам нужен только один, самый похожий результат
        )
        
        if not results['metadatas'][0]:
            return "UNKNOWN" # На случай, если ничего не найдено
        
        # Извлекаем намерение из метаданных самого похожего примера
        recognized_intent = results['metadatas'][0][0]['intent']
        print(f"🔍 Распознано намерение: '{player_command}' -> {recognized_intent}")
        return recognized_intent