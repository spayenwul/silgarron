"""
Compatibility Service - Математическое ядро системы генерации мира.

Этот сервис отвечает на главный вопрос: "Насколько элемент A совместим с элементом B?"
Он является безмозглым калькулятором, который работает исключительно на основе данных из YAML.
"""

from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class CompatibilityLevel(Enum):
    """Уровни совместимости"""
    INCOMPATIBLE = 0      # Абсолютно несовместимо
    POOR = 1              # Плохая совместимость (0.1 - 0.3)
    WEAK = 2              # Слабая (0.3 - 0.6)
    MODERATE = 3          # Умеренная (0.6 - 1.0)
    GOOD = 4              # Хорошая (1.0 - 1.5)
    EXCELLENT = 5         # Отличная (1.5 - 2.5)
    PERFECT = 6           # Идеальная (> 2.5)


@dataclass
class CompatibilityScore:
    """Результат расчета совместимости"""
    raw_score: float                    # Числовое значение
    level: CompatibilityLevel           # Категория
    breakdown: Dict[str, float]         # Детализация расчета
    blocking_factors: List[str]         # Что блокирует совместимость
    synergy_factors: List[str]          # Что усиливает совместимость
    
    @property
    def is_compatible(self) -> bool:
        """Совместимы ли элементы вообще?"""
        return self.level != CompatibilityLevel.INCOMPATIBLE
    
    @property
    def is_optimal(self) -> bool:
        """В оптимальном ли диапазоне?"""
        return self.level in [CompatibilityLevel.GOOD, CompatibilityLevel.EXCELLENT]


class CompatibilityService:
    """
    Центральный сервис для расчета совместимости между любыми элементами мира.
    
    Работает по принципу:
    1. Извлекает теги из обоих элементов
    2. Применяет локальные правила совместимости
    3. Применяет глобальные модификаторы
    4. Применяет правила синергии/конфликта из tags_registry
    5. Возвращает итоговый score
    """
    
    def __init__(self, 
                 tag_registry: Dict[str, Any],
                 global_rules: Dict[str, Any],
                 world_data_service: Any):
        """
        Args:
            tag_registry: Данные из tags_registry.yaml
            global_rules: Данные из generation_rules.yaml
            world_data_service: Ссылка на WorldDataService
        """
        self.tag_registry = tag_registry
        self.global_rules = global_rules
        self.world_data = world_data_service
        
        # Кэш для оптимизации
        self._compatibility_cache: Dict[Tuple[str, str], CompatibilityScore] = {}
        
        logger.info("CompatibilityService initialized")
    
    # ==========================================================================
    # ГЛАВНЫЕ ПУБЛИЧНЫЕ МЕТОДЫ
    # ==========================================================================
    
    def get_race_biome_compatibility(self, 
                                     race_id: str, 
                                     biome_id: str) -> CompatibilityScore:
        """
        Главный метод: насколько раса совместима с биомом?
        
        Формула:
        score = base_compatibility * tag_synergy_product * global_modifier
        """
        cache_key = (f"race:{race_id}", f"biome:{biome_id}")
        if cache_key in self._compatibility_cache:
            return self._compatibility_cache[cache_key]
        
        race_data = self.world_data.get_race(race_id)
        biome_data = self.world_data.get_biome(biome_id)
        
        if not race_data or not biome_data:
            logger.warning(f"Race {race_id} or biome {biome_id} not found")
            return self._incompatible_score("Element not found")
        
        breakdown = {}
        blocking_factors = []
        synergy_factors = []
        
        # Шаг 1: Проверка абсолютной несовместимости
        incompatible = self._check_absolute_incompatibility(race_data, biome_data)
        if incompatible:
            blocking_factors.append(incompatible)
            score = self._create_score(0.0, breakdown, blocking_factors, synergy_factors)
            self._compatibility_cache[cache_key] = score
            return score
        
        # Шаг 2: Базовая совместимость (из локальных правил расы)
        base_score = self._calculate_base_compatibility(
            race_data.get('environmental_compatibility', {}),
            self._extract_tags(biome_data)
        )
        breakdown['base_compatibility'] = base_score
        
        # Шаг 3: Глобальные модификаторы (из generation_rules.yaml)
        global_mod = self._apply_global_modifiers(race_id, biome_data)
        breakdown['global_modifiers'] = global_mod
        
        # Шаг 4: Синергии тегов (из tags_registry.yaml)
        tag_synergy = self._calculate_tag_synergies(
            self._extract_tags(race_data),
            self._extract_tags(biome_data)
        )
        breakdown['tag_synergies'] = tag_synergy
        if tag_synergy > 1.0:
            synergy_factors.append(f"Tag synergy bonus: +{(tag_synergy - 1.0) * 100:.0f}%")
        
        # Итоговый расчет
        final_score = base_score * global_mod * tag_synergy
        breakdown['final_score'] = final_score
        
        score = self._create_score(final_score, breakdown, blocking_factors, synergy_factors)
        self._compatibility_cache[cache_key] = score
        return score
    
    def get_biome_border_compatibility(self,
                                       biome_a_id: str,
                                       biome_b_id: str) -> CompatibilityScore:
        """
        Могут ли два биома граничить друг с другом?
        
        Проверяет:
        1. Explicit cannot_border rules
        2. Transition zones
        3. Tag compatibility
        """
        cache_key = (f"biome:{biome_a_id}", f"biome:{biome_b_id}")
        if cache_key in self._compatibility_cache:
            return self._compatibility_cache[cache_key]
        
        biome_a = self.world_data.get_biome(biome_a_id)
        biome_b = self.world_data.get_biome(biome_b_id)
        
        breakdown = {}
        blocking_factors = []
        synergy_factors = []
        
        # Проверка explicit правил из биомов
        cannot_border_a = biome_a.get('compatibility', {}).get('cannot_border', [])
        cannot_border_b = biome_b.get('compatibility', {}).get('cannot_border', [])
        
        if biome_b_id in cannot_border_a or biome_a_id in cannot_border_b:
            blocking_factors.append(f"Explicit cannot_border rule")
            score = self._create_score(0.0, breakdown, blocking_factors, synergy_factors)
            self._compatibility_cache[cache_key] = score
            return score
        
        # Проверка can_border (если указано, то только эти)
        can_border_a = biome_a.get('compatibility', {}).get('can_border', [])
        if can_border_a and biome_b_id not in can_border_a:
            blocking_factors.append(f"Not in can_border whitelist")
            score = self._create_score(0.2, breakdown, blocking_factors, synergy_factors)
            self._compatibility_cache[cache_key] = score
            return score
        
        # Проверка специальных правил из generation_rules.yaml
        border_rules = self.global_rules.get('biome_border_rules', {})
        
        # Проверка sharp transitions (резкие границы запрещены)
        sharp_transitions = border_rules.get('sharp_transitions', [])
        for rule in sharp_transitions:
            if (rule['from'] == biome_a_id and rule['to'] == biome_b_id) or \
               (rule['from'] == biome_b_id and rule['to'] == biome_a_id):
                blocking_factors.append(f"Sharp transition: {rule['reason']}")
                score = self._create_score(0.3, breakdown, blocking_factors, synergy_factors)
                self._compatibility_cache[cache_key] = score
                return score
        
        # Проверка smooth transitions (плавные границы усиливают)
        smooth_transitions = border_rules.get('smooth_transitions', [])
        for rule in smooth_transitions:
            if (rule['from'] == biome_a_id and rule['to'] == biome_b_id) or \
               (rule['from'] == biome_b_id and rule['to'] == biome_a_id):
                synergy_factors.append(f"Smooth transition available")
                breakdown['smooth_transition_bonus'] = 1.5
        
        # Базовая совместимость по тегам
        tag_compat = self._calculate_tag_synergies(
            self._extract_tags(biome_a),
            self._extract_tags(biome_b)
        )
        breakdown['tag_compatibility'] = tag_compat
        
        final_score = tag_compat * breakdown.get('smooth_transition_bonus', 1.0)
        breakdown['final_score'] = final_score
        
        score = self._create_score(final_score, breakdown, blocking_factors, synergy_factors)
        self._compatibility_cache[cache_key] = score
        return score
    
    def find_best_match(self,
                       target_tags: Set[str],
                       candidates: List[Dict[str, Any]],
                       candidate_type: str = 'generic') -> Tuple[Optional[str], float]:
        """
        Находит наиболее совместимый элемент из списка кандидатов.
        
        Используется при генерации карты:
        - У нас есть набор тегов от шума Перлина
        - Нужно выбрать лучший биом для этого места
        
        Args:
            target_tags: Набор тегов, с которыми ищем совместимость
            candidates: Список кандидатов (биомы, расы, etc.)
            candidate_type: Тип кандидатов для оптимизации расчета
            
        Returns:
            (id лучшего кандидата, score)
        """
        best_id = None
        best_score = -1.0
        
        for candidate in candidates:
            candidate_id = candidate.get('id')
            candidate_tags = self._extract_tags(candidate)
            
            # Рассчитываем совместимость тегов
            score = self._calculate_tag_match_score(target_tags, candidate_tags)
            
            # Применяем вес появления
            spawn_weight = candidate.get('spawn_weight', 1.0)
            adjusted_score = score * spawn_weight
            
            if adjusted_score > best_score:
                best_score = adjusted_score
                best_id = candidate_id
        
        return best_id, best_score
    
    def get_poi_placement_score(self,
                               poi_type: str,
                               location_tags: Set[str],
                               nearby_pois: List[Dict[str, Any]]) -> CompatibilityScore:
        """
        Может ли точка интереса (POI) появиться в данной локации?
        
        Проверяет:
        1. Required tags
        2. Forbidden tags
        3. Distance rules to other POIs
        4. Special conditions
        """
        poi_rules = self.global_rules.get('poi_placement_rules', {}).get('poi_types', {}).get(poi_type, {})
        
        if not poi_rules:
            logger.warning(f"No placement rules for POI type: {poi_type}")
            return self._incompatible_score("No placement rules defined")
        
        breakdown = {}
        blocking_factors = []
        synergy_factors = []
        
        # Проверка required tags
        required_tags = set(poi_rules.get('required_tags', []))
        if required_tags:
            missing = required_tags - location_tags
            if missing:
                blocking_factors.append(f"Missing required tags: {missing}")
                return self._create_score(0.0, breakdown, blocking_factors, synergy_factors)
            else:
                synergy_factors.append("All required tags present")
                breakdown['required_tags_met'] = 1.5
        
        # Проверка forbidden tags
        forbidden_tags = set(poi_rules.get('forbidden_tags', []))
        if forbidden_tags:
            present = forbidden_tags & location_tags
            if present:
                blocking_factors.append(f"Forbidden tags present: {present}")
                return self._create_score(0.0, breakdown, blocking_factors, synergy_factors)
        
        # Проверка preferred tags (бонус, но не обязательно)
        preferred_tags = set(poi_rules.get('preferred_tags', []))
        if preferred_tags:
            present = preferred_tags & location_tags
            if present:
                bonus = 1.0 + (len(present) * 0.2)
                breakdown['preferred_tags_bonus'] = bonus
                synergy_factors.append(f"Preferred tags: {present}")
        
        # Проверка расстояния до других POI
        min_distance = poi_rules.get('min_distance_from_other_' + poi_type + 's', 0)
        if min_distance > 0:
            for nearby_poi in nearby_pois:
                if nearby_poi['type'] == poi_type:
                    distance = nearby_poi['distance']
                    if distance < min_distance:
                        penalty = distance / min_distance  # Чем ближе, тем больше штраф
                        blocking_factors.append(f"Too close to another {poi_type}: {distance}/{min_distance}")
                        breakdown['distance_penalty'] = penalty
        
        # Итоговый расчет
        base_score = 1.0
        bonus_multiplier = breakdown.get('preferred_tags_bonus', 1.0) * breakdown.get('required_tags_met', 1.0)
        distance_penalty = breakdown.get('distance_penalty', 1.0)
        
        final_score = base_score * bonus_multiplier * distance_penalty
        breakdown['final_score'] = final_score
        
        return self._create_score(final_score, breakdown, blocking_factors, synergy_factors)
    
    # ==========================================================================
    # ВСПОМОГАТЕЛЬНЫЕ ПРИВАТНЫЕ МЕТОДЫ
    # ==========================================================================
    
    def _check_absolute_incompatibility(self,
                                       race_data: Dict[str, Any],
                                       biome_data: Dict[str, Any]) -> Optional[str]:
        """
        Проверяет жесткие ограничения несовместимости.
        
        Returns:
            Причину несовместимости или None
        """
        race_incompatible = race_data.get('environmental_compatibility', {}).get('incompatible', [])
        biome_tags = self._extract_tags(biome_data)
        
        for incompatible_tag in race_incompatible:
            if incompatible_tag in biome_tags:
                return f"Race incompatible with tag: {incompatible_tag}"
        
        # Проверка forbidden_combinations из tags_registry
        forbidden = self.tag_registry.get('validation_rules', {}).get('forbidden_combinations', [])
        race_tags = self._extract_tags(race_data)
        
        for combo in forbidden:
            if all(tag in race_tags or tag in biome_tags for tag in combo):
                return f"Forbidden combination: {combo}"
        
        return None
    
    def _calculate_base_compatibility(self,
                                      race_preferences: Dict[str, Any],
                                      biome_tags: Set[str]) -> float:
        """
        Рассчитывает базовую совместимость на основе локальных правил расы.
        
        Формула:
        score = (сумма весов совпавших preferred тегов) / (сумма весов avoided тегов)
        """
        preferred = race_preferences.get('preferred', {})
        avoided = race_preferences.get('avoided', {})
        
        preferred_score = 1.0
        avoided_penalty = 1.0
        
        # Считаем бонусы от preferred
        for tag, weight in preferred.items():
            if tag in biome_tags:
                preferred_score *= weight
        
        # Считаем штрафы от avoided
        for tag, weight in avoided.items():
            if tag in biome_tags:
                avoided_penalty *= weight
        
        return preferred_score * avoided_penalty
    
    def _apply_global_modifiers(self,
                               race_id: str,
                               biome_data: Dict[str, Any]) -> float:
        """
        Применяет глобальные модификаторы из generation_rules.yaml
        """
        global_mods = self.global_rules.get('global_modifiers', {})
        race_terrain_affinity = global_mods.get('race_terrain_affinity', {}).get(race_id, {})
        
        if not race_terrain_affinity:
            return 1.0  # Нет специальных правил
        
        biome_tags = self._extract_tags(biome_data)
        modifier = 1.0
        
        for tag, weight in race_terrain_affinity.items():
            if tag in biome_tags:
                modifier *= weight
        
        return modifier
    
    def _calculate_tag_synergies(self,
                                 tags_a: Set[str],
                                 tags_b: Set[str]) -> float:
        """
        Рассчитывает синергии и конфликты между наборами тегов
        на основе глобальных правил из tags_registry.yaml
        """
        synergy_rules = self.tag_registry.get('global_compatibility_rules', {}).get('synergies', [])
        conflict_rules = self.tag_registry.get('global_compatibility_rules', {}).get('conflicts', [])
        
        combined_tags = tags_a | tags_b
        multiplier = 1.0
        
        # Проверяем синергии
        for rule in synergy_rules:
            rule_tags = set(rule['tags'])
            if rule_tags.issubset(combined_tags):
                bonus = rule.get('bonus', 1.0)
                multiplier *= bonus
                logger.debug(f"Synergy found: {rule['reason']}, bonus: {bonus}")
        
        # Проверяем конфликты
        for rule in conflict_rules:
            rule_tags = set(rule['tags'])
            if rule_tags.issubset(combined_tags):
                penalty = rule.get('penalty', 1.0)
                multiplier *= penalty
                logger.debug(f"Conflict found: {rule['reason']}, penalty: {penalty}")
        
        return multiplier
    
    def _calculate_tag_match_score(self,
                                   target_tags: Set[str],
                                   candidate_tags: Set[str]) -> float:
        """
        Рассчитывает, насколько хорошо кандидат соответствует целевым тегам.
        
        Используется для find_best_match.
        """
        if not target_tags:
            return 0.5  # Нейтрально
        
        # Пересечение тегов
        matching = target_tags & candidate_tags
        
        # Базовый score - процент совпадения
        base_score = len(matching) / len(target_tags)
        
        # Бонус за полное совпадение
        if matching == target_tags:
            base_score *= 1.5
        
        # Применяем синергии
        synergy_multiplier = self._calculate_tag_synergies(target_tags, candidate_tags)
        
        return base_score * synergy_multiplier
    
    def _extract_tags(self, element_data: Dict[str, Any]) -> Set[str]:
        """
        Извлекает все теги из элемента (расы, биома, etc.)
        
        Ищет в:
        - pillar_tags
        - defining_tags
        - tags (прямой список)
        """
        tags = set()
        
        # Pillar tags (словарь)
        pillar_tags = element_data.get('pillar_tags', {})
        for tag_value in pillar_tags.values():
            tags.add(tag_value)
        
        # Defining tags (список)
        defining_tags = element_data.get('defining_tags', [])
        tags.update(defining_tags)
        
        # Direct tags (список)
        direct_tags = element_data.get('tags', [])
        tags.update(direct_tags)
        
        return tags
    
    def _create_score(self,
                     raw_score: float,
                     breakdown: Dict[str, float],
                     blocking_factors: List[str],
                     synergy_factors: List[str]) -> CompatibilityScore:
        """
        Создает объект CompatibilityScore на основе числового значения
        """
        # Определяем уровень
        if raw_score == 0.0:
            level = CompatibilityLevel.INCOMPATIBLE
        elif raw_score < 0.3:
            level = CompatibilityLevel.POOR
        elif raw_score < 0.6:
            level = CompatibilityLevel.WEAK
        elif raw_score < 1.0:
            level = CompatibilityLevel.MODERATE
        elif raw_score < 1.5:
            level = CompatibilityLevel.GOOD
        elif raw_score < 2.5:
            level = CompatibilityLevel.EXCELLENT
        else:
            level = CompatibilityLevel.PERFECT
        
        return CompatibilityScore(
            raw_score=raw_score,
            level=level,
            breakdown=breakdown,
            blocking_factors=blocking_factors,
            synergy_factors=synergy_factors
        )
    
    def _incompatible_score(self, reason: str) -> CompatibilityScore:
        """Быстрое создание несовместимого score"""
        return CompatibilityScore(
            raw_score=0.0,
            level=CompatibilityLevel.INCOMPATIBLE,
            breakdown={},
            blocking_factors=[reason],
            synergy_factors=[]
        )
    
    # ==========================================================================
    # УТИЛИТЫ ДЛЯ ОТЛАДКИ И ВИЗУАЛИЗАЦИИ
    # ==========================================================================
    
    def explain_compatibility(self,
                             score: CompatibilityScore,
                             verbose: bool = True) -> str:
        """
        Создает человекочитаемое объяснение результата совместимости.
        
        Полезно для отладки и понимания, почему система приняла решение.
        """
        lines = [
            f"=== Compatibility Analysis ===",
            f"Final Score: {score.raw_score:.2f}",
            f"Level: {score.level.name}",
            f"Compatible: {score.is_compatible}",
            f"Optimal: {score.is_optimal}",
            ""
        ]
        
        if score.blocking_factors:
            lines.append("❌ Blocking Factors:")
            for factor in score.blocking_factors:
                lines.append(f"  - {factor}")
            lines.append("")
        
        if score.synergy_factors:
            lines.append("✓ Synergy Factors:")
            for factor in score.synergy_factors:
                lines.append(f"  + {factor}")
            lines.append("")
        
        if verbose and score.breakdown:
            lines.append("📊 Score Breakdown:")
            for component, value in score.breakdown.items():
                lines.append(f"  {component}: {value:.2f}")
        
        return "\n".join(lines)
    
    def generate_compatibility_matrix(self,
                                     race_ids: List[str],
                                     biome_ids: List[str]) -> Dict[str, Dict[str, float]]:
        """
        Генерирует матрицу совместимости для визуализации.
        
        Возвращает:
            {race_id: {biome_id: score}}
            
        Используйте с matplotlib/seaborn для создания heatmap.
        """
        matrix = {}
        
        for race_id in race_ids:
            matrix[race_id] = {}
            for biome_id in biome_ids:
                score = self.get_race_biome_compatibility(race_id, biome_id)
                matrix[race_id][biome_id] = score.raw_score
        
        return matrix
    
    def clear_cache(self):
        """Очищает кэш совместимости (полезно при изменении данных)"""
        self._compatibility_cache.clear()
        logger.info("Compatibility cache cleared")


# =============================================================================
# УТИЛИТАРНЫЕ ФУНКЦИИ
# =============================================================================

def visualize_compatibility_matrix(matrix: Dict[str, Dict[str, float]],
                                   title: str = "Race-Biome Compatibility"):
    """
    Создает heatmap из матрицы совместимости.
    
    Требует: matplotlib, seaborn
    """
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        import pandas as pd
        
        # Преобразуем в DataFrame
        df = pd.DataFrame(matrix).T
        
        # Создаем heatmap
        plt.figure(figsize=(14, 10))
        sns.heatmap(df, annot=True, fmt='.2f', cmap='RdYlGn', 
                   center=1.0, vmin=0, vmax=2.5,
                   cbar_kws={'label': 'Compatibility Score'})
        plt.title(title)
        plt.xlabel('Biomes')
        plt.ylabel('Races')
        plt.tight_layout()
        plt.show()
        
    except ImportError:
        logger.error("matplotlib or seaborn not installed. Cannot visualize.")


def validate_compatibility_rules(compatibility_service: CompatibilityService,
                                 world_data_service: Any) -> List[str]:
    """
    Проверяет валидность правил совместимости.
    
    Возвращает список найденных проблем.
    """
    issues = []
    
    # Получаем все расы и биомы
    all_races = world_data_service.get_all_races()
    all_biomes = world_data_service.get_all_biomes()
    
    # Проверяем, что каждая раса может жить хотя бы где-то
    for race in all_races:
        race_id = race['id']
        compatible_biomes = []
        
        for biome in all_biomes:
            score = compatibility_service.get_race_biome_compatibility(race_id, biome['id'])
            if score.is_compatible:
                compatible_biomes.append(biome['id'])
        
        if not compatible_biomes:
            issues.append(f"⚠️ Race '{race_id}' has NO compatible biomes!")
        elif len(compatible_biomes) < 3:
            issues.append(f"⚠️ Race '{race_id}' has very few compatible biomes: {compatible_biomes}")
    
    # Проверяем, что в каждом биоме может жить хотя бы одна раса
    for biome in all_biomes:
        biome_id = biome['id']
        compatible_races = []
        
        for race in all_races:
            score = compatibility_service.get_race_biome_compatibility(race['id'], biome_id)
            if score.is_compatible:
                compatible_races.append(race['id'])
        
        if not compatible_races:
            issues.append(f"⚠️ Biome '{biome_id}' has NO compatible races!")
    
    return issues