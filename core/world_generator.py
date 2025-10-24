"""
World Generator - Генератор живого мира Сильгаррон (256×256 hex)

Этот модуль реализует анатомическую генерацию мира как живого организма:
- Скелетная структура (хребет + рёбра)
- Лимфатическая система (каналы циркуляции)
- Дыхательная система (альвеолярные каверны + выдох спор)
- Метаболическая активность (температура тканей)
- Типы тканей (биомы)

См. ADR-013, ADR-014, ADR-015 для деталей архитектуры.
"""

import hashlib
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import numpy as np
import yaml
from core.perlin_noise import PerlinNoise
from core.flow_accumulation import (
    calculate_flow_direction,
    calculate_flow_accumulation,
    find_lymph_sources,
    create_lymph_channels_mask,
    resolve_flat_areas
)
from core.poisson_sampling import place_alveolar_caverns
from core.exhalation import spread_exhalation, create_bioactive_mask
from core.tissue_assignment import TissueAssignmentEngine
from models.global_sector import GlobalSector, WorldMap


class WorldGenerator:
    """
    Детерминированный генератор глобальной hex-карты 256×256.

    Ключевые принципы:
    1. Seed-based: один seed → всегда одна и та же карта
    2. Анатомический подход: мир = живой организм
    3. Поэтапная генерация: скелет → лимфа → дыхание → метаболизм → ткани

    Использование:
        >>> gen = WorldGenerator(seed="silgarron_alpha")
        >>> map_data = gen.generate()
        >>> print(f"Generated {len(map_data.sectors)} sectors")
    """

    def __init__(self, seed: str, width: int = 256, height: int = 256, config_path: Optional[str] = None):
        """
        Инициализирует генератор мира.

        Args:
            seed: Строковый seed для детерминированной генерации
            width: Ширина карты в гексах (по умолчанию 256)
            height: Высота карты в гексах (по умолчанию 256)
            config_path: Путь к generation_config.yaml (опционально)

        Примечания:
            - Seed преобразуется в 64-битное число через SHA-256
            - RNG инициализируется этим числом для воспроизводимости
            - Размер 256×256 фиксирован согласно ADR-012
            - Если config_path не указан, используются параметры по умолчанию
        """
        self.seed_string = seed
        self.width = width
        self.height = height

        # Преобразуем строковый seed в целое число
        self.seed_int = self._hash_seed(seed)

        # Инициализируем генератор случайных чисел NumPy
        self.rng = np.random.default_rng(self.seed_int)

        # Загружаем конфигурацию
        self.config = self._load_config(config_path)

    def _hash_seed(self, seed: str) -> int:
        """
        Преобразует строковый seed в детерминированное 64-битное целое число.

        Использует SHA-256 для обеспечения:
        - Детерминизма (одна строка → одно число всегда)
        - Равномерного распределения (разные строки → разные числа)
        - Необратимости (число → строка невозможно)

        Args:
            seed: Произвольная строка (UTF-8)

        Returns:
            Целое число в диапазоне [0, 2^63-1]

        Примеры:
            >>> gen = WorldGenerator("test")
            >>> gen.seed_int  # Всегда одинаковое число
            5234892304892304823

            >>> gen2 = WorldGenerator("test")
            >>> gen.seed_int == gen2.seed_int
            True
        """
        # Кодируем строку в байты
        seed_bytes = seed.encode('utf-8')

        # Вычисляем SHA-256 хеш
        hash_bytes = hashlib.sha256(seed_bytes).digest()

        # Берём первые 8 байт (64 бита) и преобразуем в int
        seed_int = int.from_bytes(hash_bytes[:8], byteorder='big')

        # Ограничиваем до 2^63-1 (signed int64 для совместимости)
        return seed_int & 0x7FFFFFFFFFFFFFFF

    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Загружает конфигурацию из YAML файла или возвращает дефолтные значения.

        Args:
            config_path: Путь к generation_config.yaml (опционально)

        Returns:
            Dictionary с параметрами генерации

        Raises:
            FileNotFoundError: Если указанный config_path не существует
            yaml.YAMLError: Если YAML файл некорректен
        """
        # Если путь не указан, используем дефолтный
        if config_path is None:
            config_path = "data/generation_config.yaml"

        # Проверяем существование файла
        config_file = Path(config_path)
        if not config_file.exists():
            print(f"[WARNING] Config file not found: {config_path}")
            print("[WARNING] Using default parameters")
            return self._get_default_config()

        # Загружаем YAML
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            print(f"[OK] Loaded config from: {config_path}")
            return config
        except yaml.YAMLError as e:
            print(f"[ERROR] Failed to parse YAML: {e}")
            print("[WARNING] Using default parameters")
            return self._get_default_config()

    def _get_param(self, *keys, default=None):
        """
        Безопасно извлекает вложенный параметр из конфигурации.

        Args:
            *keys: Последовательность ключей для доступа (напр., 'skeletal', 'perlin', 'scale')
            default: Значение по умолчанию, если ключ не найден

        Returns:
            Значение параметра или default

        Example:
            >>> scale = self._get_param('skeletal', 'perlin', 'scale', default=100.0)
        """
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def _get_default_config(self) -> Dict[str, Any]:
        """
        Возвращает дефолтные параметры генерации (hardcoded fallback).

        Returns:
            Dictionary с дефолтными параметрами (совпадают с generation_config.yaml)
        """
        return {
            'skeletal': {
                'perlin': {
                    'scale': 100.0,
                    'octaves': 4,
                    'persistence': 0.5,
                    'lacunarity': 2.0
                },
                'ridge': {
                    'center_x': 0.5,
                    'width': 0.15,
                    'intensity': 1.0
                },
                'ribs': {
                    'count': 8,
                    'spacing': 25.0,
                    'thickness': 8.0,
                    'intensity': 1.0
                },
                'weights': {
                    'base': 0.6,
                    'ridge': 0.3,
                    'ribs': 0.1
                }
            },
            'lymphatic': {
                'flow': {
                    'min_accumulation_for_source': 100,
                    'channel_threshold': 0.02
                },
                'flat_resolution': {
                    'noise_scale': 500.0,
                    'noise_strength': 0.001
                },
                'sources': {
                    'max_sources': 20,
                    'min_distance': 30
                }
            },
            'respiratory': {
                'caverns': {
                    'min_distance': 30.0,
                    'max_caverns': 100,
                    'k_attempts': 30,
                    'elevation_min': 0.2,
                    'elevation_max': 0.7
                },
                'exhalation': {
                    'decay_rate': 0.92,
                    'min_threshold': 0.01,
                    'elevation_penalty': 0.1
                },
                'bioactive': {
                    'threshold': 0.3
                }
            },
            'metabolic': {
                'base_temperature': 0.5,
                'contributions': {
                    'bone_penalty': 0.4,
                    'lymph_bonus': 0.3,
                    'bioactive_bonus': 0.25,
                    'lowland_bonus': 0.2
                },
                'thresholds': {
                    'bone_ridge': 0.7,
                    'lowland_elevation': 0.4
                }
            },
            'tissues': {
                'rules_path': 'data/tissue_rules.yaml'
            }
        }

    def generate(self) -> Dict[str, Any]:
        """
        Генерирует полную глобальную карту 256×256.

        Фазы генерации (по ADR-013):
        1. Скелетная структура - хребет + рёбра (Perlin + Ridge mask)
        2. Лимфатическая система - каналы циркуляции (D8 Flow Accumulation)
        3. Дыхательная система - каверны + выдох спор (Poisson + BFS)
        4. Метаболическая активность - температура тканей
        5. Назначение типов тканей - биомы на основе параметров

        Returns:
            Dict с ключами:
                - 'seed': строковый seed
                - 'width': ширина карты
                - 'height': высота карты
                - 'skeletal': данные скелетной системы
                - 'lymphatic': данные лимфатической системы
                - 'respiratory': данные дыхательной системы
                - 'metabolic': данные метаболизма
                - 'sectors': словарь GlobalSector объектов
                - 'generator_version': версия генератора

        Примечания:
            - Вызывается только после инициализации
            - Детерминирован для данного seed
            - Занимает ~5-30 секунд в зависимости от оборудования
        """
        print(f"[WorldGenerator] Generating world from seed: '{self.seed_string}'")
        print(f"[WorldGenerator] Seed int: {self.seed_int}")
        print(f"[WorldGenerator] Map size: {self.width}x{self.height}")

        # TODO: Phase 1.2 - Skeletal structure
        skeletal_data = self._generate_skeletal_structure()

        # TODO: Phase 1.3 - Lymphatic system
        lymphatic_data = self._generate_lymphatic_system(skeletal_data)

        # TODO: Phase 1.4 - Respiratory system
        respiratory_data = self._generate_respiratory_system(skeletal_data)

        # TODO: Phase 1.5 - Metabolic activity
        metabolic_data = self._generate_metabolic_activity(
            skeletal_data, lymphatic_data, respiratory_data
        )

        # Phase 2 - Tissue assignment
        tissue_data = self._assign_tissue_types(
            skeletal_data, lymphatic_data, respiratory_data, metabolic_data
        )

        # Phase 3 - Create WorldMap with GlobalSector objects
        world_map = self._create_world_map(
            skeletal_data, lymphatic_data, respiratory_data, metabolic_data, tissue_data
        )

        print(f"[WorldGenerator] Generation complete!")

        return {
            'seed': self.seed_string,
            'seed_int': self.seed_int,
            'width': self.width,
            'height': self.height,
            'skeletal': skeletal_data,
            'lymphatic': lymphatic_data,
            'respiratory': respiratory_data,
            'metabolic': metabolic_data,
            'tissues': tissue_data,
            'world_map': world_map,
            'generator_version': '0.1.0-sprint3.5'
        }

    def _generate_skeletal_structure(self) -> Dict[str, Any]:
        """
        Генерирует скелетную структуру (хребет + рёбра).

        Task 1.2: Ridge-biased Perlin Noise
        - Базовый рельеф через Perlin Noise
        - Ridge mask для вертикального "позвоночника"
        - Rib mask для боковых "рёбер"

        Returns:
            Dict с ключами:
                - 'elevation': np.ndarray (256, 256) - высоты [0.0, 1.0]
                - 'ridge_mask': np.ndarray (256, 256) - маска хребта
                - 'rib_mask': np.ndarray (256, 256) - маска рёбер

        Примечания:
            - Хребет проходит вертикально по центру (x ≈ 128)
            - Рёбра отходят от хребта под углами
            - См. docs/sprint_3.5_implementation/02_PERLIN_NOISE_EXPLAINED.md
        """
        print("[WorldGenerator] Phase 1.2: Generating skeletal structure...")

        # 1. Базовый микрорельеф (Perlin Noise)
        base_elevation = self._generate_base_elevation()
        print(f"  - Base elevation generated (range: {base_elevation.min():.3f}-{base_elevation.max():.3f})")

        # 2. Ridge mask (вертикальный "позвоночник")
        ridge_mask = self._generate_ridge_mask()
        print(f"  - Ridge mask generated (max: {ridge_mask.max():.3f})")

        # 3. Rib mask (боковые "рёбра")
        rib_mask = self._generate_rib_mask()
        print(f"  - Rib mask generated (max: {rib_mask.max():.3f})")

        # 4. Комбинируем: базовый шум + хребет + рёбра
        # Веса из конфигурации (по умолчанию: 60% Base + 30% Ridge + 10% Ribs)
        weight_base = self._get_param('skeletal', 'weights', 'base', default=0.6)
        weight_ridge = self._get_param('skeletal', 'weights', 'ridge', default=0.3)
        weight_ribs = self._get_param('skeletal', 'weights', 'ribs', default=0.1)

        elevation = (
            base_elevation * weight_base +   # Базовый шум (основа естественности)
            ridge_mask * weight_ridge +      # Хребет (структура)
            rib_mask * weight_ribs           # Рёбра (детали)
        )

        # Нормализуем в [0, 1]
        elevation = np.clip(elevation, 0.0, 1.0)

        print(f"  - Final elevation combined (60% Base + 30% Ridge + 10% Ribs)")
        print(f"  - Range: {elevation.min():.3f}-{elevation.max():.3f}, mean: {elevation.mean():.3f}")

        return {
            'elevation': elevation,
            'ridge_mask': ridge_mask,
            'rib_mask': rib_mask
        }

    def _generate_base_elevation(self) -> np.ndarray:
        """
        Генерирует базовый микрорельеф через Perlin Noise.

        Создаёт "органическую текстуру" с плавными холмами и долинами.

        Returns:
            np.ndarray (height, width) - высоты в [0, 1]
        """
        perlin = PerlinNoise(seed=self.seed_int)

        # Получаем параметры из конфигурации
        scale = self._get_param('skeletal', 'perlin', 'scale', default=100.0)
        octaves = self._get_param('skeletal', 'perlin', 'octaves', default=4)
        persistence = self._get_param('skeletal', 'perlin', 'persistence', default=0.5)
        lacunarity = self._get_param('skeletal', 'perlin', 'lacunarity', default=2.0)

        elevation = perlin.fractal_noise_2d(
            width=self.width,
            height=self.height,
            scale=scale / self.width * 8.0,  # Масштабируем относительно размера карты
            octaves=octaves,
            persistence=persistence,
            lacunarity=lacunarity
        )

        # Преобразуем из [-1, 1] в [0, 1]
        elevation = (elevation + 1.0) / 2.0

        return elevation.astype(np.float32)

    def _generate_ridge_mask(self) -> np.ndarray:
        """
        Генерирует маску хребта (вертикальная ось "позвоночника").

        Использует гауссову функцию с синусоидальными изгибами для создания
        органичного "позвоночника" вместо идеально прямой линии.

        Returns:
            np.ndarray (height, width) - интенсивность хребта [0, 1]
        """
        ridge = np.zeros((self.height, self.width), dtype=np.float32)

        # Получаем параметры из конфигурации
        ridge_center_x = self._get_param('skeletal', 'ridge', 'center_x', default=0.5)
        ridge_width = self._get_param('skeletal', 'ridge', 'width', default=0.15)
        ridge_intensity = self._get_param('skeletal', 'ridge', 'intensity', default=1.0)

        center_x = int(self.width * ridge_center_x)  # Центр хребта (по умолчанию: 128 для 256×256)

        # Создаём сетки координат
        y_coords = np.arange(self.height)
        x_coords = np.arange(self.width)
        Y, X = np.meshgrid(y_coords, x_coords, indexing='ij')

        # Добавляем изгибы (wiggle) для органичности
        # Используем синусоиду с разными частотами для "змеевидности"
        wiggle_amplitude = 12  # Амплитуда изгиба (в пикселях)
        wiggle_frequency = 0.03  # Частота волны (0.03 → ~8 волн на карту)

        # Основная синусоида
        wiggle = wiggle_amplitude * np.sin(Y * wiggle_frequency * 2 * np.pi)

        # Добавляем вторую гармонику для сложности
        wiggle += wiggle_amplitude * 0.3 * np.sin(Y * wiggle_frequency * 2 * np.pi * 2.5 + np.pi/4)

        # Центр хребта с изгибом
        spine_center = center_x + wiggle

        # Расстояние каждой точки от изгибающегося хребта
        distance = np.abs(X - spine_center)

        # Нормализуем (0 = центр, 1 = край)
        normalized_dist = distance / (self.width / 2)

        # Гауссова функция: e^(-k * dist^2)
        # k зависит от ширины хребта (width=0.15 → k≈5)
        k = 1.0 / (ridge_width ** 2)
        ridge_strength = np.exp(-k * normalized_dist**2) * ridge_intensity

        ridge[:, :] = ridge_strength

        # Добавляем низкочастотный шум для органичности краёв
        noise_perlin = PerlinNoise(seed=self.seed_int + 1000)  # +1000 для другого шума
        ridge_noise = noise_perlin.fractal_noise_2d(
            width=self.width,
            height=self.height,
            scale=4.0,  # Низкая частота
            octaves=2,  # Мало деталей
            persistence=0.5
        )
        ridge_noise = (ridge_noise + 1.0) / 2.0  # Нормализуем в [0, 1]

        # Добавляем 10% шума к маске
        ridge = ridge * (0.9 + 0.2 * ridge_noise)
        ridge = np.clip(ridge, 0.0, 1.0)

        return ridge

    def _generate_rib_mask(self) -> np.ndarray:
        """
        Генерирует маску рёбер (боковые структуры, отходящие от хребта).

        Использует косинусную волну с нерегулярностью и изгибами для создания
        органичных "рёбер" вместо идеально прямых линий.

        Returns:
            np.ndarray (height, width) - интенсивность рёбер [0, ~0.15]
        """
        ribs = np.zeros((self.height, self.width), dtype=np.float32)

        center_x = self.width // 2
        rib_spacing = 40      # Увеличено расстояние между рёбрами
        rib_angle = 30        # Угол наклона рёбер (градусы)
        rib_strength = 0.15   # Уменьшена максимальная сила (было 0.3)

        # Создаём сетки координат
        y_coords = np.arange(self.height)
        x_coords = np.arange(self.width)
        Y, X = np.meshgrid(y_coords, x_coords, indexing='ij')

        # Расстояние от центра по X
        dx = X - center_x

        # Добавляем шум для вариации угла наклона
        angle_noise_perlin = PerlinNoise(seed=self.seed_int + 2000)
        angle_noise = angle_noise_perlin.fractal_noise_2d(
            width=self.width,
            height=self.height,
            scale=3.0,
            octaves=2
        )
        # Вариация угла: ±10 градусов
        angle_variation = angle_noise * 10
        effective_angle = rib_angle + angle_variation

        # Периодическая функция для рёбер (с учётом изменяющегося угла)
        angle_rad = np.radians(effective_angle)
        rib_phase = (Y + dx * np.tan(angle_rad)) / rib_spacing

        # Добавляем вариацию в spacing (нерегулярность рёбер)
        spacing_noise_perlin = PerlinNoise(seed=self.seed_int + 3000)
        spacing_noise = spacing_noise_perlin.fractal_noise_2d(
            width=self.width,
            height=self.height,
            scale=5.0,
            octaves=2
        )
        # Вариация в spacing: ±20%
        rib_phase += spacing_noise * 0.2

        # Косинусная волна (только положительные значения)
        rib_wave = np.maximum(0, np.cos(rib_phase * 2 * np.pi))

        # Затухание от центра (чем дальше от хребта, тем слабее)
        distance_from_ridge = np.abs(dx) / (self.width / 2)
        decay = np.exp(-2 * distance_from_ridge**2)

        # Добавляем "толщину" рёбер - они не должны быть линиями
        # Применяем степень для заострения пиков
        rib_wave = np.power(rib_wave, 1.5)

        # Комбинируем
        ribs = rib_wave * decay * rib_strength

        # Добавляем общий низкочастотный шум для органичности
        organic_noise_perlin = PerlinNoise(seed=self.seed_int + 4000)
        organic_noise = organic_noise_perlin.fractal_noise_2d(
            width=self.width,
            height=self.height,
            scale=6.0,
            octaves=2
        )
        organic_noise = (organic_noise + 1.0) / 2.0  # [0, 1]

        # Модулируем рёбра шумом
        ribs = ribs * (0.8 + 0.4 * organic_noise)
        ribs = np.clip(ribs, 0.0, 1.0)

        return ribs.astype(np.float32)

    def _generate_lymphatic_system(self, skeletal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Генерирует лимфатическую систему (каналы циркуляции).

        Task 1.3: D8 Flow Accumulation
        - Поиск истоков (возвышенности на хребте)
        - D8 Flow Accumulation для русел
        - Лимфотоки текут вниз от хребта

        Args:
            skeletal_data: Результат _generate_skeletal_structure()

        Returns:
            Dict с ключами:
                - 'flow_direction': np.ndarray - направления потока (D8)
                - 'flow_accumulation': np.ndarray - интенсивность потока
                - 'source_points': List[Tuple[int, int]] - истоки
                - 'lymph_channels': np.ndarray - маска каналов
                - 'lymph_intensity': np.ndarray - нормализованная интенсивность

        Примечания:
            - Лимфа = "кровь" организма
            - Течёт от хребта к низинам
            - См. docs/sprint_3.5_implementation/03_D8_FLOW_ACCUMULATION.md
        """
        print("[WorldGenerator] Phase 1.3: Generating lymphatic system...")

        elevation = skeletal_data['elevation']
        ridge_mask = skeletal_data['ridge_mask']

        # 1. Разрешаем плоские области (добавляем микрошум)
        elevation_perturbed = resolve_flat_areas(elevation, self.rng)
        print(f"  - Flat areas resolved (micro-noise added)")

        # 2. Вычисляем направления потока (D8)
        flow_direction = calculate_flow_direction(elevation_perturbed)
        unique_dirs = np.unique(flow_direction)
        print(f"  - Flow directions calculated ({len(unique_dirs)} unique directions)")

        # 3. Вычисляем аккумуляцию потока
        flow_accumulation = calculate_flow_accumulation(elevation_perturbed, flow_direction)
        print(f"  - Flow accumulation calculated (max: {flow_accumulation.max():.1f})")

        # 4. Находим истоки лимфотоков в предгорьях хребта
        # СТРОГИЕ критерии для единой интегрированной системы
        source_points = find_lymph_sources(
            elevation=elevation,
            ridge_mask=ridge_mask,
            flow_accumulation=flow_accumulation,
            num_sources=6,                      # Меньше истоков = меньше хаоса
            elevation_range=(0.55, 0.75),       # СТРОГО предгорья (узкий диапазон!)
            min_ridge=0.7,                      # ТОЛЬКО сильный хребет (было 0.5)
            max_accumulation=3.0,               # Ещё строже (было 5.0)
            rng=self.rng
        )
        print(f"  - Lymph sources found: {len(source_points)} points")

        # 5. Создаём маски лимфатических каналов
        # СТРОГИЙ порог - только главные артерии
        lymph_channels, lymph_intensity = create_lymph_channels_mask(
            flow_accumulation=flow_accumulation,
            threshold_percentile=95.0  # Верхние 5% аккумуляции (было 90 = 10%)
        )
        channel_count = np.sum(lymph_channels)
        print(f"  - Lymph channels created: {int(channel_count)} cells")

        return {
            'flow_direction': flow_direction,
            'flow_accumulation': flow_accumulation,
            'source_points': source_points,
            'lymph_channels': lymph_channels,
            'lymph_intensity': lymph_intensity
        }

    def _generate_respiratory_system(self, skeletal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Генерирует дыхательную систему (альвеолярные каверны + выдох).

        Task 1.4: Poisson Disk Sampling + BFS Exhalation
        - Равномерное размещение каверн (Poisson Disk Sampling)
        - BFS с затуханием для распространения спор
        - Каверны = источники выброса биоактивных веществ

        Args:
            skeletal_data: Результат _generate_skeletal_structure()

        Returns:
            Dict с ключами:
                - 'caverns': List[Tuple[int, int]] - координаты каверн
                - 'exhalation_influence': np.ndarray - концентрация выброса
                - 'bioactive_saturation': np.ndarray - насыщение спорами

        Примечания:
            - Фаза Выдоха (ADR-014): каверны источают споры
            - Концентрация убывает с расстоянием
            - См. docs/sprint_3.5_implementation/04_POISSON_SAMPLING.md
            - См. docs/sprint_3.5_implementation/05_BFS_EXHALATION.md
        """
        print("[WorldGenerator] Phase 1.4: Generating respiratory system...")

        elevation = skeletal_data['elevation']

        # 1. Place alveolar caverns (Poisson Disk Sampling)
        # Criteria: Uniformly distributed, in soft tissue (not peaks, not lowlands)
        caverns = place_alveolar_caverns(
            width=self.width,
            height=self.height,
            elevation=elevation,
            min_distance=30.0,           # Minimum 30 pixels between caverns
            elevation_range=(0.2, 0.7),  # Soft tissue range (not bone peaks, not lowlands)
            max_caverns=100,             # Limit to 100 caverns
            k_attempts=30,               # 30 attempts per active point
            rng=self.rng
        )
        print(f"  - Alveolar caverns placed: {len(caverns)} caverns (Poisson Disk Sampling)")

        # 2. Spread exhalation influence (BFS with decay)
        # Spores spread from caverns with decreasing intensity
        exhalation_influence = spread_exhalation(
            caverns=caverns,
            width=self.width,
            height=self.height,
            decay_rate=0.92,            # 92% intensity preserved per step
            min_threshold=0.01,         # Stop when intensity < 1%
            elevation=elevation,        # Consider terrain
            elevation_penalty=0.1       # 10% penalty for uphill spread
        )
        print(f"  - Exhalation influence spread (BFS with decay=0.92)")

        # 3. Create bioactive saturation zones
        # Zones with high exhalation intensity = bioactive
        bioactive_mask, bioactive_saturation = create_bioactive_mask(
            exhalation_intensity=exhalation_influence,
            threshold=0.3  # 30% intensity threshold
        )

        bioactive_count = np.sum(bioactive_mask)
        bioactive_ratio = bioactive_count / (self.width * self.height)
        print(f"  - Bioactive saturation calculated: {bioactive_ratio*100:.1f}% of map")

        return {
            'caverns': caverns,
            'exhalation_influence': exhalation_influence,
            'bioactive_saturation': bioactive_saturation
        }

    def _generate_metabolic_activity(
        self,
        skeletal_data: Dict[str, Any],
        lymphatic_data: Dict[str, Any],
        respiratory_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Генерирует метаболическую активность (температура тканей).

        Task 1.5: Temperature Synthesis
        - Температура = f(elevation, lymph_flow, exhalation)
        - Хребет холодный (кость)
        - Лимфа тёплая (активная циркуляция)
        - Каверны тёплые (выброс энергии)

        Args:
            skeletal_data: Скелетная структура
            lymphatic_data: Лимфатическая система
            respiratory_data: Дыхательная система

        Returns:
            Dict с ключами:
                - 'temperature': np.ndarray - температура [0.0, 1.0]

        Примечания:
            - Температура ≠ климат, это активность тканей
            - Высокая температура = активный метаболизм
            - См. Sprint 3.5, Task 1.5
        """
        print("[WorldGenerator] Phase 1.5: Generating metabolic activity...")

        elevation = skeletal_data['elevation']
        ridge_mask = skeletal_data['ridge_mask']
        lymph_intensity = lymphatic_data['lymph_intensity']
        bioactive_saturation = respiratory_data['bioactive_saturation']

        # Metabolic temperature calculation
        # Temperature = base + bone_penalty + lymph_bonus + bioactive_bonus

        # 1. Base temperature (normalized to 0.5 = moderate)
        base_temp = np.full((self.height, self.width), 0.5, dtype=np.float32)

        # 2. Bone penalty (ridge = cold, dead tissue)
        # High ridge (>0.7) = cold bone structure
        bone_mask = ridge_mask > 0.7
        bone_penalty = np.where(bone_mask, ridge_mask * 0.4, 0.0)  # Up to -0.4

        # 3. Lymph bonus (circulation = warmth)
        # High lymph flow = active metabolism
        lymph_bonus = lymph_intensity * 0.3  # Up to +0.3

        # 4. Bioactive bonus (exhalation = metabolic activity)
        # High bioactive saturation = warm, active tissues
        bioactive_bonus = bioactive_saturation * 0.25  # Up to +0.25

        # 5. Elevation modifier (lowlands = active, soft tissues)
        # Low elevation (<0.4) = warm soft tissues
        lowland_mask = elevation < 0.4
        lowland_bonus = np.where(lowland_mask, (0.4 - elevation) * 0.2, 0.0)  # Up to +0.08

        # Combine all factors
        temperature = base_temp - bone_penalty + lymph_bonus + bioactive_bonus + lowland_bonus

        # Clamp to [0, 1]
        temperature = np.clip(temperature, 0.0, 1.0)

        # Calculate statistics
        mean_temp = float(temperature.mean())
        min_temp = float(temperature.min())
        max_temp = float(temperature.max())

        print(f"  - Metabolic temperature calculated")
        print(f"  - Temperature range: {min_temp:.3f} - {max_temp:.3f}, mean: {mean_temp:.3f}")
        print(f"  - Cold zones (bone): {np.sum(temperature < 0.3) / temperature.size * 100:.1f}%")
        print(f"  - Warm zones (active): {np.sum(temperature > 0.7) / temperature.size * 100:.1f}%")

        return {
            'temperature': temperature
        }

    def _assign_tissue_types(
        self,
        skeletal_data: Dict[str, Any],
        lymphatic_data: Dict[str, Any],
        respiratory_data: Dict[str, Any],
        metabolic_data: Dict[str, Any]
    ) -> Dict[Any, Any]:
        """
        Назначает типы тканей (биомы) для каждого гекса.

        Task 2.1-2.2: Rule-based tissue assignment
        - Читает rules из data/tissue_rules.yaml
        - Применяет систему приоритетов
        - Создаёт GlobalSector для каждого гекса

        Args:
            skeletal_data: Скелетная структура
            lymphatic_data: Лимфатическая система
            respiratory_data: Дыхательная система
            metabolic_data: Метаболизм

        Returns:
            Dict[Tuple[int, int], GlobalSector] - секторы по координатам (q, r)

        Примечания:
            - Ткани = биомы (дерма, мышца, кость, хитин и т.д.)
            - Правила проверяются в порядке приоритета
            - См. Sprint 3.5, Task 2.1-2.2
        """
        print("[WorldGenerator] Phase 2: Assigning tissue types...")

        # Load tissue assignment engine
        engine = TissueAssignmentEngine(rules_path="data/tissue_rules.yaml")

        # Extract data
        elevation = skeletal_data['elevation']
        ridge_mask = skeletal_data['ridge_mask']
        lymph_intensity = lymphatic_data['lymph_intensity']
        lymph_channels = lymphatic_data['lymph_channels']
        bioactive_saturation = respiratory_data['bioactive_saturation']
        temperature = metabolic_data['temperature']
        cavern_positions = respiratory_data['caverns']
        lymph_sources = lymphatic_data['source_points']

        # Assign tissue types for entire map
        tissue_map, tissue_info = engine.assign_tissue_map(
            elevation=elevation,
            ridge_mask=ridge_mask,
            lymph_intensity=lymph_intensity,
            lymph_channels=lymph_channels,
            bioactive_saturation=bioactive_saturation,
            temperature=temperature,
            cavern_positions=cavern_positions,
            lymph_sources=lymph_sources
        )

        print(f"  - Tissue assignment complete")

        return {
            'tissue_map': tissue_map,
            'tissue_info': tissue_info
        }

    def _create_world_map(
        self,
        skeletal_data: Dict[str, Any],
        lymphatic_data: Dict[str, Any],
        respiratory_data: Dict[str, Any],
        metabolic_data: Dict[str, Any],
        tissue_data: Dict[str, Any]
    ) -> WorldMap:
        """
        Creates WorldMap object with GlobalSector instances.

        Phase 3: Data Models
        - Converts numpy arrays to GlobalSector objects
        - Stores in WorldMap container
        - Ready for JSON export

        Args:
            skeletal_data: Skeletal structure
            lymphatic_data: Lymphatic system
            respiratory_data: Respiratory system
            metabolic_data: Metabolic activity
            tissue_data: Tissue assignment

        Returns:
            WorldMap object with all sectors

        Notes:
            - Creates 65,536 GlobalSector objects (256x256)
            - Takes ~5 seconds
        """
        print("[WorldGenerator] Phase 3: Creating WorldMap with GlobalSector objects...")

        # Create WorldMap container
        world_map = WorldMap(seed=self.seed_string, width=self.width, height=self.height)

        # Extract data arrays
        elevation = skeletal_data['elevation']
        ridge_mask = skeletal_data['ridge_mask']
        rib_mask = skeletal_data['rib_mask']
        lymph_intensity = lymphatic_data['lymph_intensity']
        lymph_channels = lymphatic_data['lymph_channels']
        bioactive_saturation = respiratory_data['bioactive_saturation']
        temperature = metabolic_data['temperature']
        tissue_map = tissue_data['tissue_map']
        tissue_info = tissue_data['tissue_info']

        # Create sets for special positions
        lymph_source_positions = set(lymphatic_data['source_points'])
        cavern_positions = set(respiratory_data['caverns'])

        # Create GlobalSector for each hex
        for y in range(self.height):
            for x in range(self.width):
                # Get tissue info for this cell
                tissue_int = tissue_map[y, x]
                tissue = tissue_info[tissue_int]

                # Create sector
                sector = GlobalSector(
                    offset_x=x,
                    offset_y=y,
                    elevation=float(elevation[y, x]),
                    ridge_mask=float(ridge_mask[y, x]),
                    rib_mask=float(rib_mask[y, x]),
                    lymph_intensity=float(lymph_intensity[y, x]),
                    bioactive_saturation=float(bioactive_saturation[y, x]),
                    temperature=float(temperature[y, x]),
                    tissue_id=tissue['id'],
                    tissue_name=tissue['name'],
                    tissue_color=tissue['color'],
                    tissue_tags=tuple(tissue['tags']),
                    is_lymph_channel=bool(lymph_channels[y, x]),
                    is_lymph_source=(y, x) in lymph_source_positions,
                    is_cavern=(y, x) in cavern_positions
                )

                world_map.add_sector(sector)

        print(f"  - Created {len(world_map.sectors)} GlobalSector objects")

        # Show statistics
        stats = world_map.get_statistics()
        print(f"  - Average elevation: {stats['average_elevation']:.3f}")
        print(f"  - Average temperature: {stats['average_temperature']:.3f}")
        print(f"  - Lymph channels: {stats['lymph_channels']}")
        print(f"  - Caverns: {stats['caverns']}")

        return world_map


if __name__ == "__main__":
    # Простой пример использования
    print("=== WorldGenerator Test ===")

    gen = WorldGenerator(seed="test_world")
    result = gen.generate()

    print(f"\nGeneration results:")
    print(f"  Seed: {result['seed']}")
    print(f"  Size: {result['width']}x{result['height']}")
    print(f"  Tissue types: {len(result['tissues']['tissue_info'])}")
    print(f"  WorldMap: {result['world_map']}")
    print(f"  Version: {result['generator_version']}")
