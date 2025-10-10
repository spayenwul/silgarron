# combat/context_builder.py
from typing import Dict, Any
from models.character import Character
from models.item import Item
from models.location import Location

class PhysicalContextBuilder:
    """
    ЗАГЛУШКА: Сборщик контекста для физической симуляции.

    Реализация делегирована команде боевой системы.
    """

    def build(
        self,
        attacker: Character,
        target: Character,
        weapon: Item,
        action_details: Dict[str, Any],
        location: Location
    ) -> Dict[str, Any]:
        """
        Собрать физический контекст для симуляции.

        Args:
            attacker: Атакующий персонаж
            target: Персонаж-цель
            weapon: Используемое оружие
            action_details: Детали действия из IntentService
            location: Текущая локация

        Returns:
            Словарь с контекстом для симуляции

        TODO: Реализация делегирована команде боевой системы.
        """
        # ЗАГЛУШКА: Возвращаем базовый контекст
        return {
            "attacker_name": attacker.name,
            "target_name": target.name,
            "weapon_name": weapon.name if weapon else "fists",
            "location_tags": location.tags if location else [],
            "action": action_details.get("action", "strike"),
            "body_part": action_details.get("body_part", "torso"),
            "modifier": action_details.get("modifier"),

            # Дополнительные поля для будущей детальной симуляции
            "attacker_stats": attacker.stats if hasattr(attacker, 'stats') else {},
            "target_stats": target.stats if hasattr(target, 'stats') else {},
            "environmental_factors": self._get_environmental_factors(location)
        }

    def _get_environmental_factors(self, location: Location) -> Dict[str, Any]:
        """
        Извлечь факторы окружения из локации.

        TODO: Реализация делегирована команде боевой системы.
        """
        if not location:
            return {}

        # ЗАГЛУШКА: Базовый анализ тегов
        factors = {
            "lighting": "normal",
            "terrain": "flat",
            "weather": "clear"
        }

        # Простой анализ тегов локации
        if location.tags:
            if any(tag in ["dark", "cave", "night"] for tag in location.tags):
                factors["lighting"] = "poor"
            if any(tag in ["forest", "swamp", "mountain"] for tag in location.tags):
                factors["terrain"] = "difficult"

        return factors
