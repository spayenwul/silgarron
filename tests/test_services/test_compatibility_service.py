"""
Unit-тесты для CompatibilityService

Тестируем три основных метода:
1. calculate_biome_compatibility() - совместимость биом-биом
2. find_best_biome_for_region() - выбор лучшего биома
3. calculate_race_biome_score() - совместимость раса-биом
"""

import pytest
from services.compatibility_service import CompatibilityService, CompatibilityLevel


# ============================================================================
# ФИКСТУРЫ
# ============================================================================

@pytest.fixture
def mock_generation_rules():
    """Минимальные generation_rules для тестов"""
    return {
        'global_modifiers': {
            'race_terrain_affinity': {
                'kith': {
                    'terrain:flat': 2.5,
                    'surface:stable': 3.0
                },
                'barophiles': {
                    'terrain:elevated': 3.5,
                    'terrain:flat': 0.2
                }
            }
        }
    }


@pytest.fixture
def mock_tags_registry():
    """Минимальный tags_registry с synergies, conflicts и forbidden_combinations"""
    return {
        'global_compatibility_rules': {
            'synergies': [
                {
                    'tags': ['surface:stable', 'lifestyle:sedentary'],
                    'bonus': 2.0,
                    'reason': 'Стабильная земля идеальна для оседлой жизни'
                },
                {
                    'tags': ['terrain:elevated', 'lifestyle:isolated'],
                    'bonus': 1.5,
                    'reason': 'Горы естественно изолируют'
                },
                {
                    'tags': ['ecology:fertile', 'resource:pure_lymph'],
                    'bonus': 1.8,
                    'reason': 'Чистая лимфа питает богатую экосистему'
                }
            ],
            'conflicts': [
                {
                    'tags': ['surface:unstable', 'lifestyle:sedentary'],
                    'penalty': 0.2,
                    'reason': 'Невозможно строить на нестабильной земле'
                },
                {
                    'tags': ['ecology:barren', 'location:inhabited'],
                    'penalty': 0.4,
                    'reason': 'Трудно жить в бесплодной местности'
                }
            ]
        },
        'validation_rules': {
            'forbidden_combinations': [
                ['terrain:aquatic', 'terrain:subterranean'],
                ['manifestation:numb', 'manifestation:chaotic'],
                ['ecology:barren', 'ecology:fertile']
            ]
        }
    }


@pytest.fixture
def service(mock_generation_rules, mock_tags_registry):
    """Создает CompatibilityService с моками"""
    return CompatibilityService(mock_generation_rules, mock_tags_registry)


# ============================================================================
# ТЕСТЫ ДЛЯ calculate_biome_compatibility()
# ============================================================================

def test_forbidden_combination_returns_incompatible(service):
    """Тест: forbidden combination возвращает score = 0"""
    candidate_tags = {'terrain:aquatic', 'ecology:fertile'}
    neighbor_tags = [{'terrain:subterranean', 'surface:stable'}]

    result = service.calculate_biome_compatibility(candidate_tags, neighbor_tags)

    assert result.raw_score == 0.0
    assert result.level == CompatibilityLevel.INCOMPATIBLE
    assert len(result.blocking_factors) > 0
    assert 'Forbidden combination' in result.blocking_factors[0]


def test_synergy_increases_score(service):
    """Тест: синергия увеличивает score"""
    # Кандидат имеет surface:stable, сосед - lifestyle:sedentary
    # Synergy bonus = 2.0
    candidate_tags = {'surface:stable', 'terrain:flat'}
    neighbor_tags = [{'lifestyle:sedentary', 'ecology:fertile'}]

    result = service.calculate_biome_compatibility(candidate_tags, neighbor_tags)

    # base_score = 1.0, synergy_bonus = 2.0 - 1.0 = 1.0
    # final_score = 1.0 + 1.0 = 2.0
    assert result.raw_score > 1.5  # Ожидаем значительный рост
    assert result.breakdown['synergy_count'] == 1
    assert result.is_compatible


def test_conflict_decreases_score(service):
    """Тест: конфликт уменьшает score"""
    candidate_tags = {'surface:unstable', 'terrain:dynamic'}
    neighbor_tags = [{'lifestyle:sedentary', 'ecology:moderate'}]

    result = service.calculate_biome_compatibility(candidate_tags, neighbor_tags)

    # base_score = 1.0, conflict_penalty = 1.0 - 0.2 = 0.8
    # final_score = 1.0 - 0.8 = 0.2
    assert result.raw_score < 1.0  # Ожидаем снижение
    assert result.breakdown['conflict_count'] == 1


def test_no_neighbors_returns_base_score(service):
    """Тест: без соседей возвращается базовый score"""
    candidate_tags = {'terrain:flat', 'ecology:fertile'}
    neighbor_tags = []

    result = service.calculate_biome_compatibility(candidate_tags, neighbor_tags)

    assert result.raw_score == 1.0
    assert result.breakdown['base_score'] == 1.0
    assert result.breakdown.get('synergy_count', 0) == 0


def test_multiple_synergies_stack(service):
    """Тест: множественные синергии складываются"""
    candidate_tags = {'surface:stable', 'ecology:fertile'}
    neighbor_tags = [
        {'lifestyle:sedentary'},  # Synergy 1
        {'resource:pure_lymph'}   # Synergy 2
    ]

    result = service.calculate_biome_compatibility(candidate_tags, neighbor_tags)

    assert result.breakdown['synergy_count'] == 2
    assert result.raw_score > 2.0  # Два бонуса должны сильно поднять score


def test_synergy_and_conflict_both_apply(service):
    """Тест: синергия и конфликт применяются одновременно"""
    candidate_tags = {'surface:stable', 'ecology:barren'}
    neighbor_tags = [
        {'lifestyle:sedentary'},  # Synergy
        {'location:inhabited'}    # Conflict
    ]

    result = service.calculate_biome_compatibility(candidate_tags, neighbor_tags)

    assert result.breakdown['synergy_count'] == 1
    assert result.breakdown['conflict_count'] == 1
    # Итоговый score зависит от того, что сильнее


# ============================================================================
# ТЕСТЫ ДЛЯ find_best_biome_for_region()
# ============================================================================

def test_find_best_biome_prefers_synergistic(service):
    """Тест: выбирается биом с лучшей синергией"""
    candidates = [
        {'id': 'biome_a', 'tags': ['terrain:flat', 'ecology:moderate']},
        {'id': 'biome_b', 'tags': ['surface:stable', 'ecology:fertile']},  # Лучше!
    ]
    neighbors = [
        {'tags': ['lifestyle:sedentary']}  # Синергия с surface:stable
    ]

    result = service.find_best_biome_for_region(candidates, neighbors)

    assert result is not None
    assert result['id'] == 'biome_b'


def test_find_best_biome_all_incompatible_returns_none(service):
    """Тест: если все несовместимы, возвращается None"""
    candidates = [
        {'id': 'biome_a', 'tags': ['terrain:aquatic']},
        {'id': 'biome_b', 'tags': ['terrain:aquatic']},
    ]
    neighbors = [
        {'tags': ['terrain:subterranean']}  # Forbidden combination!
    ]

    result = service.find_best_biome_for_region(candidates, neighbors)

    assert result is None


def test_find_best_biome_no_neighbors_returns_random(service):
    """Тест: без соседей возвращается случайный биом"""
    candidates = [
        {'id': 'biome_a', 'tags': ['terrain:flat']},
        {'id': 'biome_b', 'tags': ['terrain:elevated']},
    ]
    neighbors = []

    result = service.find_best_biome_for_region(candidates, neighbors)

    assert result is not None
    assert result['id'] in ['biome_a', 'biome_b']


def test_find_best_biome_no_candidates_returns_none(service):
    """Тест: без кандидатов возвращается None"""
    candidates = []
    neighbors = [{'tags': ['terrain:flat']}]

    result = service.find_best_biome_for_region(candidates, neighbors)

    assert result is None


def test_find_best_biome_sorts_by_score(service):
    """Тест: биомы сортируются по score, выбирается лучший"""
    candidates = [
        {'id': 'biome_weak', 'tags': ['terrain:flat']},  # score = 1.0
        {'id': 'biome_strong', 'tags': ['surface:stable']},  # score > 1.0 (synergy)
    ]
    neighbors = [{'tags': ['lifestyle:sedentary']}]

    result = service.find_best_biome_for_region(candidates, neighbors)

    assert result['id'] == 'biome_strong'


# ============================================================================
# ТЕСТЫ ДЛЯ calculate_race_biome_score()
# ============================================================================

def test_race_biome_incompatible_tag(service):
    """Тест: несовместимый тег расы блокирует биом"""
    race_data = {
        'id': 'test_race',
        'tags': ['lifestyle:nomadic'],
        'environmental_compatibility': {
            'incompatible': ['terrain:subterranean']
        }
    }
    biome_data = {
        'id': 'test_biome',
        'tags': ['terrain:subterranean', 'ecology:unique']
    }

    result = service.calculate_race_biome_score(race_data, biome_data)

    assert result.raw_score == 0.0
    assert result.level == CompatibilityLevel.INCOMPATIBLE


def test_race_biome_preferred_tag_increases_score(service):
    """Тест: предпочитаемый тег увеличивает score"""
    race_data = {
        'id': 'kith',
        'tags': [],
        'environmental_compatibility': {
            'preferred': {
                'terrain': {'flat': 2.0}
            }
        }
    }
    biome_data = {
        'id': 'plains',
        'tags': ['terrain:flat', 'ecology:fertile']
    }

    result = service.calculate_race_biome_score(race_data, biome_data)

    assert result.raw_score > 1.0
    assert result.breakdown['local_preference_score'] == 2.0


def test_race_biome_global_modifier_applies(service):
    """Тест: глобальный модификатор применяется"""
    race_data = {
        'id': 'kith',  # В mock_generation_rules есть правила для kith
        'tags': [],
        'environmental_compatibility': {}
    }
    biome_data = {
        'id': 'stable_plains',
        'tags': ['terrain:flat', 'surface:stable']
    }

    result = service.calculate_race_biome_score(race_data, biome_data)

    # global_modifier должен быть > 1.0
    assert result.breakdown.get('global_modifier', 0) > 1.0


def test_race_biome_synergy_with_race_tags(service):
    """Тест: синергия между тегами расы и биома"""
    race_data = {
        'id': 'settlers',
        'tags': ['lifestyle:sedentary'],
        'environmental_compatibility': {}
    }
    biome_data = {
        'id': 'stable_land',
        'tags': ['surface:stable', 'ecology:fertile']
    }

    result = service.calculate_race_biome_score(race_data, biome_data)

    assert result.breakdown.get('synergy_count', 0) >= 1


def test_race_biome_forbidden_combination(service):
    """Тест: forbidden combination между расой и биомом"""
    race_data = {
        'id': 'aquatic_race',
        'tags': ['terrain:aquatic'],
        'environmental_compatibility': {}
    }
    biome_data = {
        'id': 'underground',
        'tags': ['terrain:subterranean']
    }

    result = service.calculate_race_biome_score(race_data, biome_data)

    assert result.raw_score == 0.0
    assert 'Forbidden combination' in result.blocking_factors[0]


# ============================================================================
# INTEGRATION ТЕСТЫ
# ============================================================================

def test_integration_hex_world_uses_compatibility(service):
    """Интеграционный тест: проверка работы в реальном сценарии"""
    # Симуляция генерации региона с 3 биомами
    all_candidates = [
        {'id': 'plains', 'tags': ['terrain:flat', 'surface:stable']},
        {'id': 'hills', 'tags': ['terrain:elevated']},
        {'id': 'swamp', 'tags': ['terrain:flat', 'ecology:toxic']},
    ]

    # Первый биом (нет соседей)
    biome1 = service.find_best_biome_for_region(all_candidates, [])
    assert biome1 is not None

    # Второй биом (с учетом первого)
    biome2 = service.find_best_biome_for_region(
        [c for c in all_candidates if c['id'] != biome1['id']],
        [biome1]
    )
    assert biome2 is not None


def test_real_data_from_yaml():
    """Тест: загрузка реальных данных из YAML"""
    from pathlib import Path
    import yaml

    project_root = Path(__file__).parent.parent.parent
    generation_rules_path = project_root / "data" / "generation_rules.yaml"
    tags_registry_path = project_root / "data" / "tags_registry.yaml"

    with open(generation_rules_path, 'r', encoding='utf-8') as f:
        generation_rules = yaml.safe_load(f)

    with open(tags_registry_path, 'r', encoding='utf-8') as f:
        tags_registry = yaml.safe_load(f)

    service = CompatibilityService(generation_rules, tags_registry)

    # Проверяем, что сервис корректно инициализирован
    assert len(service.synergies) > 0
    assert len(service.conflicts) > 0
    assert len(service.forbidden_combinations) > 0


def test_caching_works(service):
    """Тест: проверка кэширования"""
    race_data = {
        'id': 'kith',
        'tags': [],
        'environmental_compatibility': {}
    }
    biome_data = {
        'id': 'plains',
        'tags': ['terrain:flat']
    }

    # Первый вызов
    result1 = service.calculate_race_biome_score(race_data, biome_data)

    # Второй вызов (должен использовать кэш)
    result2 = service.calculate_race_biome_score(race_data, biome_data)

    assert result1.raw_score == result2.raw_score
    assert len(service._compatibility_cache) > 0
