# Этот файл собирает все ключевые таблицы данных из модулей для удобного импорта.
# Он отражает текущую, заполненную структуру наших YAML-файлов.

# --- Раздел I: Анатомия Мира ---
from .anatomy import REGION_TYPES, BIOMES, LANDMARKS
# Примечание: METABOLIC_MODES, ATMOSPHERIC_PHENOMENA и т.д.
# пока не созданы как таблицы, поэтому их не импортируем.

# --- Раздел II: Экосистема ---
from .ecosystem import *
# Примечание: FLORA, FAUNA, ECOLOGICAL_THREATS будут добавлены позже.

# --- Раздел III: Проявления Мира ---
from .manifestations import CONDUCTIVITY_LEVELS, SCEPKA_TYPES, ANOMALIES, DIVINE_INFLUENCE

# --- Раздел IV: Обитатели и Культура ---
from .inhabitants import RACES, FACTIONS, GOVERNANCE_FORMS, SETTLEMENT_TYPES, ARCHITECTURE_STYLES
# Остальные пункты (TECH_LEVEL, LANGUAGES, ALIGNMENTS, SOCIAL_STRUCTURES, CUISINE)

# --- Раздел V: Экономика и Ресурсы ---
from .inhabitants import RESOURCES, economy_branches, currencies

# --- Раздел VI: Память Мира ---
from .history import ANCIENT_CIVS, RUIN_TYPES, HISTORICAL_EVENTS, CONFLICT_TYPES, MYTHS
# Остальные пункты (PERSONALITIES, TREASURES, SECRETS, EXPLORATION_LEVEL, MOODS)
