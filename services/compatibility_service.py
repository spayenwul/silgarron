"""
Compatibility Service - Математическое ядро системы генерации мира.

Этот сервис отвечает на главный вопрос: "Насколько элемент A совместим с элементом B?"
Он является калькулятором, который работает исключительно на основе данных из YAML.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class CompatibilityLevel(Enum):
    """Уровни совместимости"""
    INCOMPATIBLE = 0      # Абсолютно несовместимо
    POOR = 1              # Плохая совместимость (0.1 - 0.4)    
    MODERATE = 2          # Умеренная (0.4 - 0.8)
    GOOD = 3              # Хорошая (0.8 - 1.5)
    EXCELLENT = 4         # Отличная (> 1.5)


@dataclass
class CompatibilityScore:
    raw_score: float; level: CompatibilityLevel
    breakdown: Dict[str, float] = field(default_factory=dict)
    blocking_factors: List[str] = field(default_factory=list)
    @property
    def is_compatible(self) -> bool: return self.raw_score > 0.1 # Порог совместимости

class CompatibilityService:
    def __init__(self, generation_rules: Dict[str, Any]):
        self.rules = generation_rules
        self._compatibility_cache: Dict[Tuple[str, str], CompatibilityScore] = {}
        logger.info("CompatibilityService initialized.")

    def _create_score(self, raw_score: float, breakdown: Dict, blocking: List) -> CompatibilityScore:
        level = CompatibilityLevel.INCOMPATIBLE
        if raw_score > 0.001:
            if raw_score <= 0.4: level = CompatibilityLevel.POOR
            elif raw_score <= 0.8: level = CompatibilityLevel.MODERATE
            elif raw_score <= 1.5: level = CompatibilityLevel.GOOD
            else: level = CompatibilityLevel.EXCELLENT
        return CompatibilityScore(raw_score, level, breakdown, blocking)

    def _normalize_tag_list(self, tags_list: List[Any]) -> List[str]:
        if not tags_list: return []
        normalized = []
        for item in tags_list:
            if isinstance(item, str): normalized.append(item)
            elif isinstance(item, dict):
                key, value = next(iter(item.items()))
                normalized.append(f"{key}:{value}")
        return normalized

    def _flatten_rules(self, rules: Dict[str, Any]) -> Dict[str, float]:
        """Превращает {'terrain': {'flat': 2.5}} в {'terrain:flat': 2.5}."""
        flat_rules = {}
        for key, value in rules.items():
            if isinstance(value, dict):
                for sub_key, weight in value.items():
                    flat_rules[f"{key}:{sub_key}"] = weight
            else:
                flat_rules[key] = value
        return flat_rules

    def calculate_race_biome_score(self, race_data: Dict[str, Any], biome_data: Dict[str, Any]) -> CompatibilityScore:
        race_id = race_data.get('id'); biome_id = biome_data.get('id')
        cache_key = (f"race_biome:{race_id}", biome_id)
        if cache_key in self._compatibility_cache: return self._compatibility_cache[cache_key]

        breakdown = {}; blocking_factors = []
        
        # Теперь мы уверены, что 'tags' существует и содержит все теги
        biome_tags = set(biome_data.get('tags', []))
        local_rules = race_data.get('environmental_compatibility', {})

        incompatible_tags = self._normalize_tag_list(local_rules.get('incompatible', []))
        if any(tag in biome_tags for tag in incompatible_tags):
            offending_tag = next(tag for tag in incompatible_tags if tag in biome_tags)
            blocking_factors.append(f"Биом имеет несовместимый тег: '{offending_tag}'")
            return self._create_score(0.0, {}, blocking_factors)

        base_score = 1.0
        # "Распрямляем" правила для удобной проверки
        preferred_rules = self._flatten_rules(local_rules.get('preferred', {}))
        avoided_rules = self._flatten_rules(local_rules.get('avoided', {}))

        for tag, weight in preferred_rules.items():
            if tag in biome_tags: base_score *= weight
        for tag, weight in avoided_rules.items():
            if tag in biome_tags: base_score *= weight
        breakdown['local_preference_score'] = base_score

        global_modifier = 1.0
        race_global_rules = self.rules.get('global_modifiers', {}).get('race_terrain_affinity', {}).get(race_id, {})
        flat_global_rules = self._flatten_rules(race_global_rules)
        for tag, weight in flat_global_rules.items():
            if tag in biome_tags: global_modifier *= weight
        breakdown['global_modifier'] = global_modifier

        final_score = base_score * global_modifier
        score = self._create_score(final_score, breakdown, blocking_factors)
        self._compatibility_cache[cache_key] = score
        return score