"""
Генератор мира v2.0 (ADR-020)
Композиционная генерация от органов с двухэтапной архитектурой
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path

from core.models.world import World, Organ, Region, ContinentData
from core.perlin_noise import generate_perlin_map
from services.world_config_v2 import WorldGenerationConfigV2


class WorldGeneratorV2:
    """
    Генератор мира v2.0

    Архитектура:
    - ЭТАП 0: Глобальные Скелеты (512×512) - этот класс
    - ЭТАП 1: Детализация Чанков (4096×4096) - Sprint 3.9
    """

    def __init__(self, config_path: str = 'config/world_generation_v2.yaml'):
        """
        Инициализация генератора

        Args:
            config_path: Путь к файлу конфигурации
        """
        # Используем конфиг-менеджер вместо прямого YAML
        self.config_manager = WorldGenerationConfigV2.from_yaml(config_path)

        # Валидируем конфигурацию
        if not self.config_manager.validate():
            raise ValueError("Invalid configuration file")

        # Получаем данные через менеджер
        self.config = self.config_manager.to_dict()
        self.global_size = self.config_manager.get_global_size()

    def generate(self, seed: str) -> World:
        """
        Главный метод генерации (ЭТАП 0: Глобальные Скелеты)

        Args:
            seed: Строка-seed для детерминированной генерации

        Returns:
            World объект с континентом и органами
        """
        print(f"🌍 Generating world from seed: {seed}")
        print(f"📐 Global size: {self.global_size}")

        # СЛОЙ 0: Seed & Meta
        world = self._initialize_world(seed)

        # СЛОЙ 0.5: Континент (макро-рельеф)
        print("  → LAYER 0.5: Generating continent...")
        world.continent = self._generate_continent(seed)

        # СЛОЙ 1: Анатомия (органы + регионы)
        print("  → LAYER 1: Placing organs...")
        world.organs = self._place_organs(seed, world.continent)

        print("  → LAYER 1: Defining regions...")
        world.regions = self._define_regions(world.continent, world.organs)

        print("✅ Global skeletons generated")
        return world

    # ========== СЛОЙ 0: SEED & META ==========

    def _initialize_world(self, seed: str) -> World:
        """Инициализация мира с meta-параметрами"""
        return World(
            seed=seed,
            world_phase=self.config_manager.get_world_phase(),
            age=self.config_manager.get_world_age(),
            global_size=self.global_size
        )

    # ========== СЛОЙ 0.5: КОНТИНЕНТ ==========

    def _generate_continent(self, seed: str) -> ContinentData:
        """
        Генерация континента (макро-рельеф)

        Алгоритм:
        1. Низкочастотный Perlin Noise → базовый heightmap
        2. (Опционально) Маска формы → центрирование континента
        3. Умножение: heightmap * shape_mask → финальный heightmap
        4. Threshold → continent_mask (суша vs океан)
        5. Морфологические операции → сглаживание береговой линии
        6. Gaussian blur → финальное сглаживание
        7. Расчёт геометрии → center, major_axis

        Args:
            seed: Строка-seed для детерминированной генерации

        Returns:
            ContinentData с маской, heightmap, центром и осью
        """
        config = self.config['continent']

        # 1. Генерация базового heightmap (Perlin Noise)
        # Используем hash от seed для детерминированности
        perlin_seed = hash(seed + "continent") % (2**31)

        heightmap = generate_perlin_map(
            width=self.global_size[0],
            height=self.global_size[1],
            seed=perlin_seed,
            scale=config['perlin_noise']['scale'],
            octaves=config['perlin_noise']['octaves'],
            persistence=config['perlin_noise']['persistence'],
            lacunarity=config['perlin_noise']['lacunarity'],
            normalize_to_01=True  # Уже в [0, 1]
        )

        # 2. Применение маски формы (если включено)
        shape_mask_enabled = config.get('shape_mask', {}).get('enabled', False)
        spine_path = None  # Будет заполнен, если используется spine mask

        if shape_mask_enabled:
            shape_config = config['shape_mask']
            mask_type = shape_config.get('type', 'ellipse')

            if mask_type == 'spine':
                # НОВЫЙ ПОДХОД: Генерация на основе хребта
                spine_config = shape_config.get('spine', {})

                # Генерируем путь хребта
                spine_seed = hash(seed + "spine") % (2**31)
                spine_path = self._generate_spine_path(
                    seed=spine_seed,
                    width=self.global_size[0],
                    height=self.global_size[1],
                    num_points=spine_config.get('num_points', 100),
                    curvature=spine_config.get('curvature', 0.3),
                    start_fraction=spine_config.get('start_fraction', 0.15),
                    end_fraction=spine_config.get('end_fraction', 0.85),
                    direction_angle=spine_config.get('direction_angle', 0.0)
                )

                # Создаем поле влияния вокруг хребта
                shape_mask = self._create_spine_influence_mask(
                    spine_path=spine_path,
                    width=self.global_size[0],
                    height=self.global_size[1],
                    max_influence=spine_config.get('max_influence', 200.0)
                )
            else:
                # СТАРЫЙ ПОДХОД: Геометрические фигуры (ellipse/radial)
                shape_mask = self._create_shape_mask(
                    width=self.global_size[0],
                    height=self.global_size[1],
                    mask_type=mask_type,
                    radius_x=shape_config.get('radius_x', 0.35),
                    radius_y=shape_config.get('radius_y', 0.45)
                )

            # 3. Комбинируем шум и форму (умножение)
            heightmap = heightmap * shape_mask

        # 4. Определение суши vs океана
        # Если shape_mask включена, используем sea_level_override (обычно ниже)
        if shape_mask_enabled and 'sea_level_override' in config.get('shape_mask', {}):
            sea_level = config['shape_mask']['sea_level_override']
        else:
            sea_level = config['sea_level']

        continent_mask = (heightmap > sea_level).astype(bool)

        # 5. Морфологические операции для сглаживания
        from scipy import ndimage
        from scipy.ndimage import morphology

        # Binary opening (удаляет маленькие острова)
        continent_mask = morphology.binary_opening(
            continent_mask,
            iterations=config['smoothing']['binary_opening_iterations']
        )

        # Binary closing (заполняет маленькие заливы)
        continent_mask = morphology.binary_closing(
            continent_mask,
            iterations=config['smoothing']['binary_closing_iterations']
        )

        # 6. Gaussian blur для финального сглаживания
        continent_float = ndimage.gaussian_filter(
            continent_mask.astype(float),
            sigma=config['smoothing']['gaussian_sigma']
        )

        # Применяем threshold снова после blur
        continent_mask = (continent_float > config['smoothing']['final_threshold']).astype(bool)

        # 7. Расчёт геометрии континента
        center = self._calculate_center_of_mass(continent_mask)
        major_axis = self._calculate_major_axis(continent_mask)

        return ContinentData(
            mask=continent_mask,
            heightmap=heightmap,
            center=center,
            major_axis=major_axis,
            spine_path=spine_path  # None если spine mask не используется
        )

    def _calculate_center_of_mass(self, mask: np.ndarray) -> Tuple[int, int]:
        """
        Расчёт центра масс континента

        Args:
            mask: Бинарная маска континента

        Returns:
            (x, y) координаты центра масс
        """
        from scipy import ndimage
        cy, cx = ndimage.center_of_mass(mask)

        # Если маска пустая, ndimage вернет nan
        if np.isnan(cx) or np.isnan(cy):
            # Возвращаем центр карты как fallback
            return (self.global_size[0] // 2, self.global_size[1] // 2)

        return (int(cx), int(cy))

    def _calculate_major_axis(self, mask: np.ndarray) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """
        Расчёт главной оси континента (самая длинная ось)

        Метод: PCA (Principal Component Analysis) на координатах суши

        Args:
            mask: Бинарная маска континента

        Returns:
            ((x1, y1), (x2, y2)) - начало и конец главной оси
        """
        # Получаем координаты всех точек суши
        y_coords, x_coords = np.where(mask)

        if len(x_coords) == 0:
            # Нет суши - возвращаем центр карты
            center = (self.global_size[0] // 2, self.global_size[1] // 2)
            return (center, center)

        coords = np.column_stack([x_coords, y_coords])

        # Центрируем данные
        mean = coords.mean(axis=0)
        centered = coords - mean

        # PCA: находим главный компонент (направление максимальной дисперсии)
        cov_matrix = np.cov(centered.T)
        eigenvalues, eigenvectors = np.linalg.eig(cov_matrix)

        # Главный eigenvector (соответствует максимальному eigenvalue)
        principal_component = eigenvectors[:, eigenvalues.argmax()]

        # Проецируем все точки на главный компонент
        projections = centered @ principal_component

        # Находим крайние точки (начало и конец оси)
        min_idx = projections.argmin()
        max_idx = projections.argmax()

        start_point = coords[min_idx]
        end_point = coords[max_idx]

        return (
            (int(start_point[0]), int(start_point[1])),
            (int(end_point[0]), int(end_point[1]))
        )

    def _generate_spine_path(self, seed: int, width: int, height: int,
                            num_points: int = 100, curvature: float = 0.3,
                            start_fraction: float = 0.15, end_fraction: float = 0.85,
                            direction_angle: float = 0.0) -> np.ndarray:
        """
        Генерация процедурного пути позвоночника с правильным направлением

        ИСПРАВЛЕНО:
        - Хребет НЕ занимает всю карту (start_fraction -> end_fraction)
        - Направление роста учитывается через direction_angle
        - Noise применяется ПЕРПЕНДИКУЛЯРНО к направлению роста

        Args:
            seed: Seed для детерминированности
            width: Ширина карты
            height: Высота карты
            num_points: Количество точек вдоль хребта
            curvature: Максимальное отклонение от центральной линии (0-1)
            start_fraction: Начало хребта (0-1, доля от высоты)
            end_fraction: Конец хребта (0-1, доля от высоты)
            direction_angle: Угол наклона хребта в радианах (0 = вертикально вниз)

        Returns:
            (N, 2) массив координат [[x1, y1], [x2, y2], ...]
        """
        from core.perlin_noise import generate_perlin_map

        # Генерируем 1D Perlin Noise для отклонения от центральной линии
        noise_1d = generate_perlin_map(
            width=num_points,
            height=1,
            seed=seed,
            scale=20,  # Низкая частота для плавных изгибов
            octaves=3,
            persistence=0.5,
            lacunarity=2.0,
            normalize_to_01=True
        ).flatten()

        # Преобразуем [0, 1] в [-1, 1] для симметричных отклонений
        noise_1d = (noise_1d - 0.5) * 2.0

        # Центр карты
        center_x = width / 2
        center_y = height / 2

        # Начало и конец хребта (с отступами!)
        start_y = height * start_fraction
        end_y = height * end_fraction

        # Направление роста (вектор)
        direction_x = np.sin(direction_angle)
        direction_y = np.cos(direction_angle)  # cos(0) = 1 (вниз), cos(pi) = -1 (вверх)

        # Перпендикулярное направление (для отклонений)
        perpendicular_x = -direction_y
        perpendicular_y = direction_x

        # Максимальное отклонение
        max_deviation = width * curvature

        path = []
        for i in range(num_points):
            # Параметр вдоль хребта (0 -> 1)
            t = i / (num_points - 1)

            # Базовая позиция вдоль центральной линии роста
            # Начинаем от start_y, двигаемся к end_y вдоль направления
            spine_length = end_y - start_y
            base_y = start_y + t * spine_length

            # X остается в центре если direction_angle = 0
            # Но смещается если есть наклон
            base_x = center_x + direction_x * (base_y - center_y)

            # Применяем шумовое отклонение ПЕРПЕНДИКУЛЯРНО к направлению роста
            deviation = noise_1d[i] * max_deviation
            x = base_x + perpendicular_x * deviation
            y = base_y + perpendicular_y * deviation

            # Clamp в пределах карты
            x = int(np.clip(x, 0, width - 1))
            y = int(np.clip(y, 0, height - 1))

            path.append([x, y])

        return np.array(path)

    def _create_spine_influence_mask(self, spine_path: np.ndarray,
                                    width: int, height: int,
                                    max_influence: float = 200.0) -> np.ndarray:
        """
        Создание поля влияния вокруг позвоночника

        Использует distance transform для вычисления расстояния каждого пикселя
        до ближайшей точки на пути хребта.

        Args:
            spine_path: (N, 2) массив координат хребта
            width: Ширина карты
            height: Высота карты
            max_influence: Максимальная дистанция влияния (в пикселях)

        Returns:
            (height, width) массив [0, 1] где 1.0 = на хребте, 0.0 = далеко
        """
        from scipy.spatial import cKDTree

        # Создаем сетку всех координат на карте
        y_coords, x_coords = np.mgrid[0:height, 0:width]
        grid_points = np.vstack([x_coords.ravel(), y_coords.ravel()]).T

        # Используем cKDTree для быстрого поиска ближайших соседей
        tree = cKDTree(spine_path)
        distances, _ = tree.query(grid_points, k=1)

        # Преобразуем в карту
        distance_map = distances.reshape((height, width))

        # Инвертируем: чем меньше расстояние, тем больше влияние
        # 1.0 на хребте, 0.0 на расстоянии max_influence и дальше
        influence_mask = 1.0 - (distance_map / max_influence)
        influence_mask = np.clip(influence_mask, 0, 1)

        return influence_mask

    def _create_shape_mask(self, width: int, height: int, mask_type: str = "ellipse",
                          radius_x: float = 0.35, radius_y: float = 0.45) -> np.ndarray:
        """
        Создание маски формы для центрирования континента

        Алгоритм:
        1. Создаем сетку координат (x, y)
        2. Для каждой точки вычисляем расстояние от центра (нормализованное)
        3. Инвертируем: центр = 1.0, края = 0.0
        4. Clamp в [0, 1]

        Args:
            width: Ширина карты
            height: Высота карты
            mask_type: Тип маски ("ellipse" или "radial")
            radius_x: Радиус по X (как доля ширины карты, 0-1)
            radius_y: Радиус по Y (как доля высоты карты, 0-1)

        Returns:
            2D массив [0, 1] где 1.0 = центр, 0.0 = края
        """
        # Создаем сетку координат
        y, x = np.ogrid[:height, :width]

        # Центр карты
        center_x = width / 2
        center_y = height / 2

        if mask_type == "ellipse":
            # Эллиптическая маска
            # Радиусы в пикселях
            radius_x_px = width * radius_x
            radius_y_px = height * radius_y

            # Нормализованное расстояние от центра (формула эллипса)
            distance_from_center = np.sqrt(
                ((x - center_x)**2 / radius_x_px**2) +
                ((y - center_y)**2 / radius_y_px**2)
            )
        else:  # radial
            # Круговая маска
            radius_px = min(width, height) * radius_x  # Используем radius_x для обоих

            # Евклидово расстояние от центра
            distance_from_center = np.sqrt(
                (x - center_x)**2 + (y - center_y)**2
            ) / radius_px

        # Инвертируем: центр = 1.0, края = 0.0
        shape_mask = 1.0 - distance_from_center

        # Clamp в [0, 1]
        shape_mask = np.clip(shape_mask, 0, 1)

        return shape_mask

    # ========== СЛОЙ 1: АНАТОМИЯ ==========

    def _place_organs(self, seed: str, continent: ContinentData) -> Dict[str, Organ]:
        """
        Размещение органов на континенте

        Sprint 3.6 - Задача 3.1
        """
        raise NotImplementedError("To be implemented in Task 3.1")

    def _define_regions(self, continent: ContinentData, organs: Dict[str, Organ]) -> Dict[str, Region]:
        """
        Определение региональных масок

        Sprint 3.6 - Задача 3.2
        """
        raise NotImplementedError("To be implemented in Task 3.2")
