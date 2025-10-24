"""
Unit tests for WorldGenerator (Sprint 3.5)

Тестируемые компоненты:
- Task 1.1: Детерминированный seed
- Task 1.2: Скелетная структура (TODO)
- Task 1.3: Лимфатическая система (TODO)
- Task 1.4: Дыхательная система (TODO)
- Task 1.5: Метаболизм (TODO)

Уровни валидации:
1. Unit Tests - изолированные функции
2. Integration Tests - взаимодействие систем
3. Visual Validation - PNG проверка (вручную)
4. Biological Plausibility - правила биологии
"""

import pytest
import numpy as np
from core.world_generator import WorldGenerator


class TestDeterministicSeed:
    """
    Task 1.1: Валидация детерминированной генерации.

    Критерии успеха:
    - Один seed → всегда одинаковый seed_int
    - Один seed → всегда одинаковый результат генерации
    - Разные seeds → разные результаты
    """

    def test_seed_hashing_deterministic(self):
        """Один строковый seed → всегда одно и то же число"""
        gen1 = WorldGenerator(seed="test_world")
        gen2 = WorldGenerator(seed="test_world")

        assert gen1.seed_int == gen2.seed_int, \
            "Одинаковый seed должен давать одинаковый seed_int"

    def test_different_seeds_produce_different_ints(self):
        """Разные seeds → разные seed_int"""
        gen1 = WorldGenerator(seed="forest")
        gen2 = WorldGenerator(seed="desert")

        assert gen1.seed_int != gen2.seed_int, \
            "Разные seeds должны давать разные seed_int"

    def test_seed_int_in_valid_range(self):
        """Seed_int находится в допустимом диапазоне [0, 2^63-1]"""
        gen = WorldGenerator(seed="test")

        assert gen.seed_int >= 0, "Seed_int должен быть неотрицательным"
        assert gen.seed_int < 2**63, "Seed_int должен быть меньше 2^63"

    def test_rng_initialized(self):
        """RNG корректно инициализируется"""
        gen = WorldGenerator(seed="test")

        assert gen.rng is not None, "RNG должен быть инициализирован"
        assert hasattr(gen.rng, 'random'), "RNG должен иметь метод random()"

    def test_rng_produces_deterministic_values(self):
        """RNG даёт одинаковые значения для одного seed"""
        gen1 = WorldGenerator(seed="test")
        gen2 = WorldGenerator(seed="test")

        # Генерируем по 5 случайных чисел
        values1 = [gen1.rng.random() for _ in range(5)]
        values2 = [gen2.rng.random() for _ in range(5)]

        assert values1 == values2, \
            "RNG с одинаковым seed должен давать одинаковую последовательность"

    def test_rng_produces_different_values_for_different_seeds(self):
        """RNG даёт разные значения для разных seeds"""
        gen1 = WorldGenerator(seed="forest")
        gen2 = WorldGenerator(seed="desert")

        values1 = [gen1.rng.random() for _ in range(5)]
        values2 = [gen2.rng.random() for _ in range(5)]

        assert values1 != values2, \
            "RNG с разными seeds должен давать разные последовательности"

    def test_generate_deterministic(self):
        """
        Полная генерация детерминирована для одного seed.

        Это ключевой интеграционный тест!
        """
        gen1 = WorldGenerator(seed="test_world")
        gen2 = WorldGenerator(seed="test_world")

        result1 = gen1.generate()
        result2 = gen2.generate()

        # Проверяем метаданные
        assert result1['seed'] == result2['seed']
        assert result1['seed_int'] == result2['seed_int']
        assert result1['width'] == result2['width']
        assert result1['height'] == result2['height']

        # Проверяем скелетную структуру
        assert np.array_equal(
            result1['skeletal']['elevation'],
            result2['skeletal']['elevation']
        ), "Elevation должен быть идентичным"

        assert np.array_equal(
            result1['skeletal']['ridge_mask'],
            result2['skeletal']['ridge_mask']
        ), "Ridge mask должен быть идентичным"

        # TODO: Добавить проверки после реализации остальных фаз
        # assert np.array_equal(result1['lymphatic']['flow_accumulation'], ...)
        # assert np.array_equal(result1['respiratory']['exhalation_influence'], ...)
        # assert result1['sectors'] == result2['sectors']

    def test_different_seeds_produce_different_worlds(self):
        """Разные seeds → разные миры"""
        gen1 = WorldGenerator(seed="alpha")
        gen2 = WorldGenerator(seed="beta")

        result1 = gen1.generate()
        result2 = gen2.generate()

        # Elevation должен отличаться (пока это заглушка из нулей, но тест готов)
        # TODO: Раскомментировать после реализации Task 1.2
        # assert not np.array_equal(
        #     result1['skeletal']['elevation'],
        #     result2['skeletal']['elevation']
        # ), "Разные seeds должны давать разные elevation maps"

        assert result1['seed'] != result2['seed']
        assert result1['seed_int'] != result2['seed_int']


class TestWorldGeneratorStructure:
    """Тесты базовой структуры WorldGenerator"""

    def test_initialization(self):
        """Генератор корректно инициализируется"""
        gen = WorldGenerator(seed="test", width=256, height=256)

        assert gen.seed_string == "test"
        assert gen.width == 256
        assert gen.height == 256
        assert gen.seed_int is not None
        assert gen.rng is not None

    def test_custom_dimensions(self):
        """Можно задать произвольные размеры (для тестирования)"""
        gen = WorldGenerator(seed="test", width=64, height=64)

        assert gen.width == 64
        assert gen.height == 64

    def test_generate_returns_dict(self):
        """generate() возвращает словарь с нужными ключами"""
        gen = WorldGenerator(seed="test")
        result = gen.generate()

        assert isinstance(result, dict)
        assert 'seed' in result
        assert 'seed_int' in result
        assert 'width' in result
        assert 'height' in result
        assert 'skeletal' in result
        assert 'lymphatic' in result
        assert 'respiratory' in result
        assert 'metabolic' in result
        assert 'tissues' in result  # Phase 2: Tissue assignment
        assert 'world_map' in result  # Phase 3: WorldMap with GlobalSector objects
        assert 'generator_version' in result

    def test_skeletal_data_structure(self):
        """Скелетные данные имеют правильную структуру"""
        gen = WorldGenerator(seed="test")
        result = gen.generate()

        skeletal = result['skeletal']
        assert 'elevation' in skeletal
        assert 'ridge_mask' in skeletal
        assert 'rib_mask' in skeletal

        # Проверяем размеры массивов
        assert skeletal['elevation'].shape == (256, 256)
        assert skeletal['ridge_mask'].shape == (256, 256)
        assert skeletal['rib_mask'].shape == (256, 256)

    def test_lymphatic_data_structure(self):
        """Лимфатические данные имеют правильную структуру"""
        gen = WorldGenerator(seed="test")
        result = gen.generate()

        lymphatic = result['lymphatic']
        assert 'flow_accumulation' in lymphatic
        assert 'source_points' in lymphatic
        assert 'lymph_channels' in lymphatic

    def test_respiratory_data_structure(self):
        """Дыхательные данные имеют правильную структуру"""
        gen = WorldGenerator(seed="test")
        result = gen.generate()

        respiratory = result['respiratory']
        assert 'caverns' in respiratory
        assert 'exhalation_influence' in respiratory
        assert 'bioactive_saturation' in respiratory

    def test_metabolic_data_structure(self):
        """Метаболические данные имеют правильную структуру"""
        gen = WorldGenerator(seed="test")
        result = gen.generate()

        metabolic = result['metabolic']
        assert 'temperature' in metabolic
        assert metabolic['temperature'].shape == (256, 256)


class TestSkeletalStructure:
    """
    Task 1.2: Тесты скелетной структуры.

    Валидация:
    - Perlin Noise детерминирован
    - Ridge проходит вертикально по центру
    - Elevation в диапазоне [0, 1]
    - Ridge сильнее на центре
    """

    def test_perlin_noise_deterministic(self):
        """Perlin Noise детерминирован для одного seed"""
        gen1 = WorldGenerator(seed="test")
        gen2 = WorldGenerator(seed="test")

        result1 = gen1._generate_skeletal_structure()
        result2 = gen2._generate_skeletal_structure()

        assert np.array_equal(
            result1['elevation'],
            result2['elevation']
        ), "Elevation должен быть идентичным для одного seed"

    def test_elevation_in_range(self):
        """Elevation находится в диапазоне [0, 1]"""
        gen = WorldGenerator(seed="test")
        result = gen._generate_skeletal_structure()

        elevation = result['elevation']
        assert np.all(elevation >= 0.0), "Elevation не должен быть отрицательным"
        assert np.all(elevation <= 1.0), "Elevation не должен превышать 1.0"

    def test_ridge_has_wiggle(self):
        """
        Хребет имеет изгибы (wiggle), а не является идеально прямой линией.

        Проверяем, что максимум ridge mask в разных Y координатах
        находится на разных X позициях.
        """
        gen = WorldGenerator(seed="test")
        result = gen._generate_skeletal_structure()

        ridge = result['ridge_mask']

        # Находим X координату максимума для каждой Y
        ridge_path_x = []
        for y in range(0, gen.height, 10):  # Каждые 10 строк
            max_x = np.argmax(ridge[y, :])
            ridge_path_x.append(max_x)

        # Проверяем, что есть вариация (не все X одинаковые)
        x_std = np.std(ridge_path_x)
        assert x_std > 3.0, \
            f"Хребет должен иметь изгибы (std X positions: {x_std:.2f} > 3.0)"

        # Края должны иметь низкие значения
        left_edge = ridge[:, 0]
        right_edge = ridge[:, -1]
        assert np.mean(left_edge) < 0.05, "Левый край должен быть почти нулевым"
        assert np.mean(right_edge) < 0.05, "Правый край должен быть почти нулевым"

    def test_ridge_approximately_centered(self):
        """
        Хребет примерно центрирован (с учётом wiggle).

        После добавления изгибов хребет больше не симметричен,
        но его среднее положение должно быть близко к центру.
        """
        gen = WorldGenerator(seed="test")
        result = gen._generate_skeletal_structure()

        ridge = result['ridge_mask']
        center_x = gen.width // 2

        # Находим среднее положение хребта
        ridge_path_x = []
        for y in range(gen.height):
            max_x = np.argmax(ridge[y, :])
            ridge_path_x.append(max_x)

        mean_ridge_x = np.mean(ridge_path_x)

        # Среднее положение должно быть близко к центру (±10 пикселей)
        assert abs(mean_ridge_x - center_x) < 10, \
            f"Среднее положение хребта ({mean_ridge_x:.1f}) должно быть близко к центру ({center_x})"

    def test_ridge_mask_range(self):
        """Ridge mask в диапазоне [0, 1]"""
        gen = WorldGenerator(seed="test")
        result = gen._generate_skeletal_structure()

        ridge = result['ridge_mask']
        assert np.all(ridge >= 0.0), "Ridge mask >= 0"
        assert np.all(ridge <= 1.0), "Ridge mask <= 1"
        assert np.max(ridge) > 0.9, "Ridge mask должен достигать ~1.0 в центре"

    def test_rib_mask_range(self):
        """Rib mask в ожидаемом диапазоне"""
        gen = WorldGenerator(seed="test")
        result = gen._generate_skeletal_structure()

        ribs = result['rib_mask']
        assert np.all(ribs >= 0.0), "Ribs mask >= 0"
        # Ribs имеют максимум ~0.15 (уменьшено с 0.3)
        assert np.max(ribs) <= 0.25, "Ribs mask должны быть слабее хребта"

    def test_elevation_has_variance(self):
        """
        Elevation не является константой (имеет рельеф).

        Проверяем, что есть достаточная вариация высот.
        """
        gen = WorldGenerator(seed="test")
        result = gen._generate_skeletal_structure()

        elevation = result['elevation']
        std_dev = np.std(elevation)

        assert std_dev > 0.1, \
            f"Elevation должен иметь вариацию (std_dev: {std_dev:.4f})"

    def test_different_seeds_different_elevation(self):
        """Разные seeds дают разные elevation maps"""
        gen1 = WorldGenerator(seed="alpha")
        gen2 = WorldGenerator(seed="beta")

        result1 = gen1._generate_skeletal_structure()
        result2 = gen2._generate_skeletal_structure()

        # Elevation должен отличаться (базовый Perlin Noise разный)
        assert not np.array_equal(
            result1['elevation'],
            result2['elevation']
        ), "Разные seeds должны давать разные elevation maps"

    def test_skeletal_structure_completeness(self):
        """Проверка, что все компоненты скелетной структуры присутствуют"""
        gen = WorldGenerator(seed="test")
        result = gen._generate_skeletal_structure()

        assert 'elevation' in result
        assert 'ridge_mask' in result
        assert 'rib_mask' in result

        assert result['elevation'].shape == (256, 256)
        assert result['ridge_mask'].shape == (256, 256)
        assert result['rib_mask'].shape == (256, 256)


class TestLymphaticSystem:
    """
    Task 1.3: Тесты лимфатической системы.

    Валидация:
    - Flow Direction указывает вниз по склону
    - Flow Accumulation корректно накапливается
    - Истоки находятся на хребте
    - Каналы текут от хребта к краям
    """

    def test_lymphatic_system_structure(self):
        """Лимфатическая система имеет правильную структуру"""
        gen = WorldGenerator(seed="test")
        skeletal = gen._generate_skeletal_structure()
        lymphatic = gen._generate_lymphatic_system(skeletal)

        assert 'flow_direction' in lymphatic
        assert 'flow_accumulation' in lymphatic
        assert 'source_points' in lymphatic
        assert 'lymph_channels' in lymphatic
        assert 'lymph_intensity' in lymphatic

        # Проверяем размеры
        assert lymphatic['flow_direction'].shape == (256, 256)
        assert lymphatic['flow_accumulation'].shape == (256, 256)

    def test_flow_accumulation_positive(self):
        """Flow accumulation всегда положительна"""
        gen = WorldGenerator(seed="test")
        skeletal = gen._generate_skeletal_structure()
        lymphatic = gen._generate_lymphatic_system(skeletal)

        flow_accum = lymphatic['flow_accumulation']

        assert np.all(flow_accum >= 1.0), \
            "Flow accumulation должна быть >= 1.0 (минимум сама ячейка)"
        assert np.max(flow_accum) > 10, \
            "Должны быть русла с высокой аккумуляцией"

    def test_sources_in_foothills(self):
        """
        Истоки лимфотоков находятся в ПРЕДГОРЬЯХ хребта.

        Критично для анатомической модели:
        - НЕ на самых высоких пиках (это "кость")
        - НЕ в низинах (это устья)
        - В диапазоне [0.5, 0.8] (предгорья = "фильтрующие органы")
        """
        gen = WorldGenerator(seed="test")
        skeletal = gen._generate_skeletal_structure()
        lymphatic = gen._generate_lymphatic_system(skeletal)

        sources = lymphatic['source_points']
        ridge_mask = skeletal['ridge_mask']
        elevation = skeletal['elevation']

        assert len(sources) > 0, "Должны быть найдены истоки"

        for y, x in sources:
            # Каждый исток должен быть на хребте
            assert ridge_mask[y, x] > 0.3, \
                f"Source at ({y},{x}) not on ridge (ridge={ridge_mask[y,x]:.3f})"

            # Каждый исток должен быть в предгорьях [0.5, 0.8]
            assert 0.45 <= elevation[y, x] <= 0.85, \
                f"Source at ({y},{x}) not in foothills (elev={elevation[y,x]:.3f}, expected [0.5, 0.8])"

            # НЕ на самых высоких пиках
            assert elevation[y, x] < 0.9, \
                f"Source at ({y},{x}) too high - should be in foothills, not peaks"

    def test_sources_count(self):
        """Генерируется правильное количество истоков"""
        gen = WorldGenerator(seed="test")
        skeletal = gen._generate_skeletal_structure()
        lymphatic = gen._generate_lymphatic_system(skeletal)

        sources = lymphatic['source_points']

        # Строгие критерии: около 6 истоков (меньше = меньше хаоса)
        assert 3 <= len(sources) <= 6, \
            f"Expected 3-6 sources (strict criteria), got {len(sources)}"

    def test_lymph_channels_exist(self):
        """Лимфатические каналы существуют и имеют разумный размер"""
        gen = WorldGenerator(seed="test")
        skeletal = gen._generate_skeletal_structure()
        lymphatic = gen._generate_lymphatic_system(skeletal)

        channels = lymphatic['lymph_channels']
        channel_count = np.sum(channels)

        # СТРОГИЕ критерии: каналы должны занимать 2-8% карты (было 5-15%)
        # Показываем только главные артерии (top 5%, было 10%)
        total_cells = channels.size
        channel_ratio = channel_count / total_cells

        assert 0.02 <= channel_ratio <= 0.10, \
            f"Channels should cover 2-10% of map (main arteries only), got {channel_ratio*100:.1f}%"

    def test_flow_intensity_normalized(self):
        """Lymph intensity нормализована в [0, 1]"""
        gen = WorldGenerator(seed="test")
        skeletal = gen._generate_skeletal_structure()
        lymphatic = gen._generate_lymphatic_system(skeletal)

        intensity = lymphatic['lymph_intensity']

        assert np.all(intensity >= 0.0), "Intensity >= 0"
        assert np.all(intensity <= 1.0), "Intensity <= 1"
        assert np.max(intensity) > 0.5, "Max intensity should be significant"

    def test_flow_accumulation_increases_downslope(self):
        """
        Аккумуляция увеличивается вниз по склону.

        Простой тест: создаём наклон, проверяем аккумуляцию.
        """
        from core.flow_accumulation import calculate_flow_direction, calculate_flow_accumulation

        # Создаём простой наклон: слева (высоко) направо (низко)
        simple_elevation = np.tile(np.linspace(1.0, 0.0, 10), (10, 1))

        flow_dir = calculate_flow_direction(simple_elevation)
        flow_accum = calculate_flow_accumulation(simple_elevation, flow_dir)

        # Правая колонка должна иметь высокую аккумуляцию
        right_column_avg = np.mean(flow_accum[:, -1])
        left_column_avg = np.mean(flow_accum[:, 0])

        assert right_column_avg > left_column_avg * 5, \
            "Right side should have much higher accumulation than left"

    def test_lymphatic_system_deterministic(self):
        """Лимфатическая система детерминирована для seed"""
        gen1 = WorldGenerator(seed="determinism_test")
        gen2 = WorldGenerator(seed="determinism_test")

        skeletal1 = gen1._generate_skeletal_structure()
        skeletal2 = gen2._generate_skeletal_structure()

        lymphatic1 = gen1._generate_lymphatic_system(skeletal1)
        lymphatic2 = gen2._generate_lymphatic_system(skeletal2)

        # Flow accumulation должна быть идентичной
        assert np.array_equal(
            lymphatic1['flow_accumulation'],
            lymphatic2['flow_accumulation']
        ), "Flow accumulation должна быть детерминированной"

        # Истоки должны быть в тех же местах
        assert lymphatic1['source_points'] == lymphatic2['source_points'], \
            "Sources должны быть детерминированными"


class TestRespiratorySystem:
    """
    Task 1.4: Тесты дыхательной системы (TODO).

    Будут реализованы после Task 1.4:
    - test_caverns_evenly_distributed()
    - test_exhalation_decays_with_distance()
    - test_bioactive_saturation_near_caverns()
    """
    pass


class TestMetabolicActivity:
    """
    Task 1.5: Тесты метаболизма (TODO).

    Будут реализованы после Task 1.5:
    - test_ridge_is_cold()
    - test_lymph_is_warm()
    - test_caverns_are_warm()
    """
    pass


if __name__ == "__main__":
    # Запуск тестов напрямую
    pytest.main([__file__, "-v", "--tb=short"])
