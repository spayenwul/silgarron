"""
Strategy Pattern для обработки команд игрока.

Модуль содержит различные стратегии обработки команд в зависимости от сложности:
- CodeOnlyStrategy: Мгновенные действия без AI (<10ms, бесплатно)
- SimpleLLMStrategy: Простые действия с 1 вызовом LLM (500-1000ms, ~0.001₽)
- FunctionCallingStrategy: Сложные действия с Function Calling (1000-2000ms, ~0.002₽)
"""

from logic.strategies.base_strategy import BaseStrategy
from logic.strategies.code_only_strategy import CodeOnlyStrategy
from logic.strategies.simple_llm_strategy import SimpleLLMStrategy
from logic.strategies.function_calling_strategy import FunctionCallingStrategy

__all__ = [
    "BaseStrategy",
    "CodeOnlyStrategy",
    "SimpleLLMStrategy",
    "FunctionCallingStrategy"
]
