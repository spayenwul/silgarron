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
import random

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
    def __init__(self, generation_rules: Dict[str, Any], tags_registry: Optional[Dict[str, Any]] = None):
        self.rules = generation_rules
        self.tags_registry = tags_registry or {}
        self._compatibility_cache: Dict[Tuple[str, str], CompatibilityScore] = {}

        # Извлекаем глобальные правила совместимости из tags_registry
        compat_rules = self.tags_registry.get('global_compatibility_rules', {})
        self.synergies = compat_rules.get('synergies', [])
        self.conflicts = compat_rules.get('conflicts', [])

        # Извлекаем forbidden_combinations из validation_rules
        validation = self.tags_registry.get('validation_rules', {})
        self.forbidden_combinations = validation.get('forbidden_combinations', [])

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
        """
        Рассчитывает совместимость расы с биомом.

        Args:
            race_data: Словарь с данными расы (должен содержать 'id', 'tags', 'environmental_compatibility')
            biome_data: Словарь с данными биома (должен содержать 'id', 'tags')

        Returns:
            CompatibilityScore с детальной информацией о совместимости
        """
        race_id = race_data.get('id')
        biome_id = biome_data.get('id')
        cache_key = (f"race_biome:{race_id}", biome_id)

        if cache_key in self._compatibility_cache:
            return self._compatibility_cache[cache_key]

        breakdown = {}
        blocking_factors = []

        # Извлекаем теги
        race_tags = set(race_data.get('tags', []))
        biome_tags = set(biome_data.get('tags', []))
        local_rules = race_data.get('environmental_compatibility', {})

        # Шаг 1: Проверка несовместимых тегов (локальные правила расы)
        incompatible_tags = self._normalize_tag_list(local_rules.get('incompatible', []))
        if any(tag in biome_tags for tag in incompatible_tags):
            offending_tag = next(tag for tag in incompatible_tags if tag in biome_tags)
            blocking_factors.append(f"Биом имеет несовместимый тег: '{offending_tag}'")
            return self._create_score(0.0, {}, blocking_factors)

        # Шаг 2: Проверка forbidden_combinations из tags_registry
        for forbidden_combo in self.forbidden_combinations:
            if len(forbidden_combo) != 2:
                continue
            tag1, tag2 = forbidden_combo
            # Проверяем, есть ли конфликт между расой и биомом
            if (tag1 in race_tags and tag2 in biome_tags) or \
               (tag2 in race_tags and tag1 in biome_tags):
                blocking_factors.append(
                    f"Forbidden combination между расой и биомом: {tag1} + {tag2}"
                )
                return self._create_score(0.0, {}, blocking_factors)

        # Шаг 3: Базовый score на основе локальных предпочтений расы
        base_score = 1.0
        preferred_rules = self._flatten_rules(local_rules.get('preferred', {}))
        avoided_rules = self._flatten_rules(local_rules.get('avoided', {}))

        for tag, weight in preferred_rules.items():
            if tag in biome_tags:
                base_score *= weight
        for tag, weight in avoided_rules.items():
            if tag in biome_tags:
                base_score *= weight
        breakdown['local_preference_score'] = base_score

        # Шаг 4: Глобальные модификаторы из generation_rules
        global_modifier = 1.0
        race_global_rules = self.rules.get('global_modifiers', {}).get('race_terrain_affinity', {}).get(race_id, {})
        flat_global_rules = self._flatten_rules(race_global_rules)
        for tag, weight in flat_global_rules.items():
            if tag in biome_tags:
                global_modifier *= weight
        breakdown['global_modifier'] = global_modifier

        # Шаг 5: Применение synergies из tags_registry
        synergy_bonus = 0.0
        synergy_count = 0
        for synergy in self.synergies:
            required_tags = set(synergy.get('tags', []))
            bonus = synergy.get('bonus', 1.0)

            # Синергия срабатывает, если часть тегов есть у расы, часть у биома
            race_match = required_tags & race_tags
            biome_match = required_tags & biome_tags

            if race_match and biome_match and (race_match | biome_match) == required_tags:
                synergy_bonus += (bonus - 1.0)
                synergy_count += 1
                logger.debug(
                    f"Race-Biome synergy: {synergy.get('reason', 'Unknown')} (bonus: {bonus})"
                )
        breakdown['synergy_bonus'] = synergy_bonus
        breakdown['synergy_count'] = synergy_count

        # Шаг 6: Применение conflicts из tags_registry
        conflict_penalty = 0.0
        conflict_count = 0
        for conflict in self.conflicts:
            required_tags = set(conflict.get('tags', []))
            penalty = conflict.get('penalty', 1.0)

            race_match = required_tags & race_tags
            biome_match = required_tags & biome_tags

            if race_match and biome_match and (race_match | biome_match) == required_tags:
                conflict_penalty += (1.0 - penalty)
                conflict_count += 1
                logger.debug(
                    f"Race-Biome conflict: {conflict.get('reason', 'Unknown')} (penalty: {penalty})"
                )
        breakdown['conflict_penalty'] = conflict_penalty
        breakdown['conflict_count'] = conflict_count

        # Шаг 7: Финальный расчет
        final_score = (base_score * global_modifier) + synergy_bonus - conflict_penalty
        final_score = max(0.0, final_score)

        score = self._create_score(final_score, breakdown, blocking_factors)
        self._compatibility_cache[cache_key] = score
        return score

    def calculate_biome_compatibility(
        self,
        candidate_biome_tags: Set[str],
        neighbor_biomes_tags: List[Set[str]]
    ) -> CompatibilityScore:
        """
        Рассчитывает совместимость биома-кандидата с соседними биомами.

        Args:
            candidate_biome_tags: Множество тегов биома-кандидата
            neighbor_biomes_tags: Список множеств тегов соседних биомов

        Returns:
            CompatibilityScore с детальной информацией о совместимости

        Логика:
            1. Проверка forbidden_combinations (если нарушено -> score = 0.0)
            2. Базовый score = 1.0
            3. Применение synergies (увеличивают score)
            4. Применение conflicts (уменьшают score)
            5. Возврат результата
        """
        breakdown = {}
        blocking_factors = []

        # Шаг 1: Проверка forbidden_combinations
        for forbidden_combo in self.forbidden_combinations:
            # forbidden_combo это список из 2 тегов, которые не могут быть вместе
            if len(forbidden_combo) != 2:
                continue

            tag1, tag2 = forbidden_combo
            # Проверяем, есть ли оба запрещенных тега в кандидате
            if tag1 in candidate_biome_tags and tag2 in candidate_biome_tags:
                blocking_factors.append(
                    f"Forbidden combination в самом биоме: {tag1} + {tag2}"
                )
                return self._create_score(0.0, {}, blocking_factors)

            # Проверяем, есть ли конфликт между кандидатом и соседями
            for neighbor_tags in neighbor_biomes_tags:
                if (tag1 in candidate_biome_tags and tag2 in neighbor_tags) or \
                   (tag2 in candidate_biome_tags and tag1 in neighbor_tags):
                    blocking_factors.append(
                        f"Forbidden combination с соседом: {tag1} + {tag2}"
                    )
                    return self._create_score(0.0, {}, blocking_factors)

        # Шаг 2: Базовый score
        base_score = 1.0
        breakdown['base_score'] = base_score

        # Шаг 3: Применение synergies
        synergy_bonus = 0.0
        synergy_count = 0

        for synergy in self.synergies:
            required_tags = set(synergy.get('tags', []))
            bonus = synergy.get('bonus', 1.0)

            # Проверяем, есть ли синергия с соседями
            for neighbor_tags in neighbor_biomes_tags:
                # Синергия срабатывает, если часть тегов в кандидате, часть в соседе
                candidate_match = required_tags & candidate_biome_tags
                neighbor_match = required_tags & neighbor_tags

                # Если оба набора непустые и вместе покрывают все required_tags
                if candidate_match and neighbor_match and \
                   (candidate_match | neighbor_match) == required_tags:
                    synergy_bonus += (bonus - 1.0)  # bonus обычно > 1.0, сохраняем прирост
                    synergy_count += 1
                    logger.debug(
                        f"Synergy detected: {synergy.get('reason', 'Unknown')} "
                        f"(bonus: {bonus})"
                    )

        breakdown['synergy_bonus'] = synergy_bonus
        breakdown['synergy_count'] = synergy_count

        # Шаг 4: Применение conflicts
        conflict_penalty = 0.0
        conflict_count = 0

        for conflict in self.conflicts:
            required_tags = set(conflict.get('tags', []))
            penalty = conflict.get('penalty', 1.0)  # penalty обычно < 1.0

            # Проверяем, есть ли конфликт с соседями
            for neighbor_tags in neighbor_biomes_tags:
                candidate_match = required_tags & candidate_biome_tags
                neighbor_match = required_tags & neighbor_tags

                # Конфликт срабатывает аналогично синергии
                if candidate_match and neighbor_match and \
                   (candidate_match | neighbor_match) == required_tags:
                    conflict_penalty += (1.0 - penalty)  # penalty < 1.0, сохраняем штраф
                    conflict_count += 1
                    logger.debug(
                        f"Conflict detected: {conflict.get('reason', 'Unknown')} "
                        f"(penalty: {penalty})"
                    )

        breakdown['conflict_penalty'] = conflict_penalty
        breakdown['conflict_count'] = conflict_count

        # Шаг 5: Финальный расчет
        final_score = base_score + synergy_bonus - conflict_penalty

        # Гарантируем, что score не отрицательный
        final_score = max(0.0, final_score)

        return self._create_score(final_score, breakdown, blocking_factors)

    def find_best_biome_for_region(
        self,
        candidate_biomes: List[Dict[str, Any]],
        placed_neighbors: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Находит наилучший биом из списка кандидатов на основе совместимости с соседями.

        Args:
            candidate_biomes: Список словарей с данными биомов-кандидатов
            placed_neighbors: Список словарей с данными уже размещенных соседних биомов

        Returns:
            Словарь с данными лучшего биома или None, если все несовместимы

        Логика:
            1. Если нет кандидатов -> None
            2. Если нет соседей -> случайный биом
            3. Для каждого кандидата рассчитываем совместимость с соседями
            4. Сортируем по score
            5. Возвращаем лучший
        """
        # Шаг 1: Проверка на пустой список кандидатов
        if not candidate_biomes:
            logger.warning("find_best_biome_for_region: нет кандидатов")
            return None

        # Шаг 2: Если нет соседей, возвращаем случайный биом
        if not placed_neighbors:
            chosen = random.choice(candidate_biomes)
            logger.debug(f"Нет соседей, выбран случайный биом: {chosen.get('id', 'Unknown')}")
            return chosen

        # Шаг 3: Извлекаем теги соседей
        neighbor_tags_list = []
        for neighbor in placed_neighbors:
            tags = neighbor.get('tags', [])
            neighbor_tags_list.append(set(tags))

        # Шаг 4: Рассчитываем совместимость для каждого кандидата
        scored_candidates = []
        for candidate in candidate_biomes:
            candidate_tags = set(candidate.get('tags', []))

            # Используем calculate_biome_compatibility
            score_obj = self.calculate_biome_compatibility(
                candidate_tags,
                neighbor_tags_list
            )

            scored_candidates.append({
                'biome_data': candidate,
                'score': score_obj.raw_score,
                'score_obj': score_obj
            })

            logger.debug(
                f"Биом '{candidate.get('id', 'Unknown')}': score={score_obj.raw_score:.2f}, "
                f"level={score_obj.level.name}, "
                f"breakdown={score_obj.breakdown}"
            )

        # Шаг 5: Фильтруем несовместимые (score <= 0.1)
        compatible_candidates = [c for c in scored_candidates if c['score_obj'].is_compatible]

        if not compatible_candidates:
            logger.warning(
                f"Все {len(candidate_biomes)} кандидатов несовместимы с соседями. "
                f"Возвращаем None."
            )
            return None

        # Шаг 6: Сортируем по убыванию score
        compatible_candidates.sort(key=lambda x: x['score'], reverse=True)

        # Шаг 7: Возвращаем лучший
        best = compatible_candidates[0]
        logger.info(
            f"Лучший биом: '{best['biome_data'].get('id', 'Unknown')}' "
            f"(score={best['score']:.2f}, level={best['score_obj'].level.name})"
        )

        return best['biome_data']