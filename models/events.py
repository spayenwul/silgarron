# models/events.py
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime

@dataclass
class GameEvent:
    """Базовый класс для всех игровых событий."""
    event_id: str
    timestamp: datetime
    session_id: str

@dataclass
class GameStarted(GameEvent):
    """Игра началась."""
    player_name: str
    starting_location_id: str

@dataclass
class PlayerMoved(GameEvent):
    """Игрок переместился."""
    from_location_id: str
    to_location_id: str

@dataclass
class PlayerActionExecuted(GameEvent):
    """Игрок выполнил действие."""
    command: str
    intent: str
    action_details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ItemPickedUp(GameEvent):
    """Игрок подобрал предмет."""
    item_id: str
    item_name: str
    location_id: str

@dataclass
class ItemDropped(GameEvent):
    """Игрок выбросил предмет."""
    item_id: str
    item_name: str
    location_id: str

@dataclass
class CombatStarted(GameEvent):
    """Начался бой."""
    location_id: str
    enemy_ids: List[str] = field(default_factory=list)

@dataclass
class CombatEnded(GameEvent):
    """Бой закончился."""
    victory: bool
    location_id: str

@dataclass
class CharacterDamaged(GameEvent):
    """Персонаж получил урон."""
    character_id: str
    damage_amount: float
    damage_type: str
    body_part: Optional[str] = None

@dataclass
class MemoryAdded(GameEvent):
    """Добавлена запись в долгосрочную память."""
    memory_id: str
    memory_text: str
    memory_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GameStateSaved(GameEvent):
    """Состояние игры сохранено."""
    save_path: str

@dataclass
class GameStateChanged(GameEvent):
    """Состояние игры изменилось (EXPLORATION -> COMBAT и т.д.)."""
    from_state: str
    to_state: str
