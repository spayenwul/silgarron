"""
Базовый абстрактный класс для всех стратегий обработки команд.

Определяет общий интерфейс для паттерна Strategy.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseStrategy(ABC):
    """
    Абстрактный базовый класс для стратегий обработки команд игрока.

    Все стратегии должны реализовать метод execute(), который принимает:
    - game_instance: экземпляр класса Game с текущим состоянием игры
    - command: строка команды игрока
    - details: словарь с извлечёнными деталями команды (action, target, instrument и т.д.)

    И возвращают:
    - Строку с результатом выполнения команды для отображения игроку
    """

    @abstractmethod
    def execute(self, game_instance: Any, command: str, details: Dict[str, Any]) -> str:
        """
        Выполнить команду игрока и вернуть результат.

        Args:
            game_instance: Экземпляр Game с текущим состоянием мира
            command: Оригинальная команда игрока
            details: Извлечённые детали (action, target_entity, instrument_entity, и т.д.)

        Returns:
            Строка с описанием результата для отображения игроку

        Raises:
            NotImplementedError: Если метод не реализован в подклассе
        """
        pass
