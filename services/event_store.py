# services/event_store.py
import json
from pathlib import Path
from typing import List
from datetime import datetime
from config import settings
from models.events import GameEvent

class EventStore:
    """
    Хранилище событий для Event Sourcing.
    Записывает все события в файл для персистентности.
    """

    def __init__(self, storage_path: str = None):
        if storage_path is None:
            storage_path = str(Path(settings.saves_dir) / "events")
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def append(self, session_id: str, event: GameEvent) -> None:
        """Добавить событие в лог."""
        event_file = self.storage_path / f"{session_id}.jsonl"

        event_dict = {
            "event_type": event.__class__.__name__,
            "event_id": event.event_id,
            "timestamp": event.timestamp.isoformat(),
            "session_id": event.session_id,
            "data": self._serialize_event(event)
        }

        with open(event_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event_dict, ensure_ascii=False) + '\n')

    def get_events(self, session_id: str) -> List[GameEvent]:
        """Получить все события для сессии."""
        event_file = self.storage_path / f"{session_id}.jsonl"

        if not event_file.exists():
            return []

        events = []
        with open(event_file, 'r', encoding='utf-8') as f:
            for line in f:
                event_dict = json.loads(line)
                event = self._deserialize_event(event_dict)
                if event:
                    events.append(event)

        return events

    def _serialize_event(self, event: GameEvent) -> dict:
        """Сериализация события в словарь."""
        data = event.__dict__.copy()
        # Удаляем базовые поля, они уже в корне
        data.pop('event_id', None)
        data.pop('timestamp', None)
        data.pop('session_id', None)
        return data

    def _deserialize_event(self, event_dict: dict) -> GameEvent:
        """Десериализация события из словаря."""
        from models import events  # Динамический импорт

        event_type = event_dict['event_type']

        # Получаем класс события по имени
        if not hasattr(events, event_type):
            print(f"⚠️ Unknown event type: {event_type}")
            return None

        event_class = getattr(events, event_type)

        return event_class(
            event_id=event_dict['event_id'],
            timestamp=datetime.fromisoformat(event_dict['timestamp']),
            session_id=event_dict['session_id'],
            **event_dict['data']
        )
