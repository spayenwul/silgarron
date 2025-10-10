# combat/physical_simulator.py
from typing import Dict, Any
from dataclasses import dataclass, field
from models.character import Character
from models.item import Item

@dataclass
class PhysicalResult:
    """
    Результат физической симуляции.
    Структура для передачи данных между системами.
    """
    hit: bool
    narrative: str
    damage_points: float = 0.0
    body_part_hit: str = "torso"

    # Дополнительные поля для будущей детальной симуляции
    penetration_depth_cm: float = 0.0
    blood_loss_rate: float = 0.0
    pain_level: int = 0
    effects: list = field(default_factory=list)

class PhysicalSimulator:
    """
    ЗАГЛУШКА: Интерфейс для физической симуляции боя.

    Реализация делегирована команде боевой системы.
    Этот класс определяет только API и возвращает тестовые данные.
    """

    def simulate_attack(
        self,
        attacker: Character,
        target: Character,
        weapon: Item,
        action_details: Dict[str, Any]
    ) -> PhysicalResult:
        """
        Симулировать атаку.

        Args:
            attacker: Персонаж-атакующий
            target: Персонаж-цель
            weapon: Используемое оружие
            action_details: Детали действия из IntentService

        Returns:
            PhysicalResult с результатом симуляции

        TODO: Реализация делегирована команде боевой системы.
        """
        # ЗАГЛУШКА: Возвращаем базовый результат
        weapon_name = weapon.name if weapon else "кулаками"
        body_part = action_details.get("body_part", "torso")

        return PhysicalResult(
            hit=True,
            narrative=f"{attacker.name} наносит удар {weapon_name} по {target.name}.",
            damage_points=10.0,
            body_part_hit=body_part
        )

    def simulate_dodge(
        self,
        character: Character,
        incoming_attack: Dict[str, Any]
    ) -> PhysicalResult:
        """
        Симулировать уклонение.

        TODO: Реализация делегирована команде боевой системы.
        """
        return PhysicalResult(
            hit=False,
            narrative=f"{character.name} уклоняется от атаки."
        )

    def simulate_block(
        self,
        character: Character,
        shield: Item,
        incoming_attack: Dict[str, Any]
    ) -> PhysicalResult:
        """
        Симулировать блок щитом.

        TODO: Реализация делегирована команде боевой системы.
        """
        shield_name = shield.name if shield else "руками"

        return PhysicalResult(
            hit=True,
            narrative=f"{character.name} блокирует атаку {shield_name}.",
            damage_points=2.0  # Частичный урон через блок
        )
