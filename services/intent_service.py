from typing import Dict
import chromadb
import json
from pathlib import Path

class IntentService:
    """
    IntentService - Быстрый Маршрутизатор Команд (Fast Router).

    Архитектура (согласно ADR-004):
    Роль этого сервиса - НЕ извлекать детали из команды, а максимально быстро
    классифицировать ее ТИП СЛОЖНОСТИ. Это позволяет Director'у выбрать
    правильную стратегию обработки (мгновенный код, один вызов LLM или
    сложный вызов с симуляцией).

    - Использует локальную векторную базу данных (ChromaDB) для мгновенной
      классификации (<50ms).
    - Не использует ресурсоемкие парсеры (pymorphy3, re) и не вникает
      в синтаксис команды.
    - Его главная задача - ответить на вопрос: "Эта команда простая (нарратив)
      или сложная (физика)?"
    """

    def __init__(self):
        """
        Инициализирует ChromaDB и загружает в нее обучающие примеры из intents.json.
        """
        print("[INIT] Initializing Player Intent Engine...")

        # ChromaDB для быстрой классификации намерений
        self.chroma_client = chromadb.Client()
        self.intent_collection = self.chroma_client.get_or_create_collection(
            name="intent_recognition",
            metadata={"hnsw:space": "cosine"}
        )

        # Загружаем intents.json и заполняем ChromaDB
        self._load_intents_into_chroma()

        # Валидные типы сложности, которые может вернуть сервис
        self.VALID_COMPLEXITY_TYPES = {"SIMPLE_LLM", "COMPLEX_TOOL_CALL"}


    def _load_intents_into_chroma(self):
        """
        Загружает примеры из data/intents.json в ChromaDB для векторного поиска.
        """
        intents_path = Path(__file__).parent.parent / "data" / "intents.json"

        # Проверяем, не загружены ли уже данные, чтобы избежать дублирования
        try:
            count = self.intent_collection.count()
            if count > 0:
                print(f"[INIT] Intent collection already populated with {count} examples")
                return
        except Exception:
            # Коллекция может еще не существовать, это нормально
            pass

        # Загружаем данные и добавляем их в ChromaDB
        with open(intents_path, "r", encoding="utf-8") as f:
            intents_data = json.load(f)

        documents = [item["text"] for item in intents_data]
        metadatas = [item["metadata"] for item in intents_data]
        ids = [f"intent_{i}" for i, _ in enumerate(intents_data)]

        if documents:
            self.intent_collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            print(f"[INIT] Loaded {len(documents)} intent examples into ChromaDB")


    def recognize_intent(self, player_command: str) -> Dict[str, str]:
        """
        Распознаёт намерение игрока и уровень сложности команды.

        Args:
            player_command: Команда игрока на естественном языке.

        Returns:
            Словарь с полями:
            - intent: Тип намерения (e.g., "DIRECT_COMBAT_LLM").
            - complexity_type: Уровень сложности (e.g., "COMPLEX_TOOL_CALL").
        """
        if not player_command:
            return {"intent": "UNKNOWN", "complexity_type": "SIMPLE_LLM"}

        # 1. Векторный поиск ближайшего примера в ChromaDB
        try:
            results = self.intent_collection.query(
                query_texts=[player_command.lower()],
                n_results=1
            )
        except Exception as e:
            print(f"[ERROR] ChromaDB query failed: {e}")
            return {"intent": "UNKNOWN", "complexity_type": "SIMPLE_LLM"}

        if not results or not results.get('metadatas') or not results['metadatas'][0]:
            print(f"[WARN] No intent found for command: '{player_command}', using fallback")
            return {"intent": "UNKNOWN", "complexity_type": "SIMPLE_LLM"}

        metadata = results['metadatas'][0][0]
        intent = metadata.get("intent", "UNKNOWN")
        complexity_type = metadata.get("complexity_type", "SIMPLE_LLM")

        # 2. Валидация, чтобы гарантировать возврат корректного типа
        if complexity_type not in self.VALID_COMPLEXITY_TYPES:
            print(f"[WARN] Unknown complexity_type '{complexity_type}' in intents.json, falling back to SIMPLE_LLM")
            complexity_type = "SIMPLE_LLM"

        return {
            "intent": intent,
            "complexity_type": complexity_type
        }