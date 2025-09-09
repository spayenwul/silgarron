from enum import Enum, auto

class GameState(Enum):
    EXPLORATION = auto() # Режим исследования мира
    COMBAT = auto()      # Режим пошагового боя