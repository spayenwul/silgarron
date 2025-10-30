"""
Генератор мира v3.0 - Чистая имплементация WP1
Sprint 3.6: WP1 (Основа мира - Phase 0, 1a, 1b)

Архитектура v3.0:
- Phase 0: Seed & Meta
- Phase 1a: Spine Creation
- Phase 1b: Continent Growth & Organ Placement
- Phase 2: Skeleton (BEFORE vessels!) - WP2
- Phase 3: Vessels (density-aware) - WP2
- Phase 4-7: WP3, WP4

Критические изменения v3.0:
- Skeleton генерируется ДО Vessels (артерии огибают кости)
"""

import numpy as np
import hashlib
from typing import Tuple, Dict, Optional, List
from dataclasses import dataclass
from scipy.interpolate import splprep, splev
from scipy import ndimage
from scipy.ndimage import binary_opening, binary_closing, gaussian_filter

# Используем существующие модели
from core.models.world import World, Organ, ContinentData, RibData
from core.perlin_noise import generate_perlin_map
from core.perlin_noise import PerlinNoise


class WorldGeneratorV3:
    """
    Генератор мира v3.0 - Чистая имплементация WP1

    WP1 включает:
    - Phase 0: Seed и Meta-параметры
    - Phase 1a: Spine Creation (позвоночник)
    - Phase 1b: Continent Growth + Organ Placement
    """

    def __init__(self, config: dict):
        """
        Инициализация генератора

        Args:
            config: Словарь конфигурации (из YAML)
        """
        self.config = config
        self.global_size = tuple(config['global_settings']['map_size'])
        self.noise_gen = PerlinNoise()

    def generate_wp1(self, seed: str) -> World:
        """
        Генерация WP1: Основа мира (макро-структура)

        Args:
            seed: Строковый seed для детерминированности

        Returns:
            World с континентом и органами
        """
        print(f"[WP1] Generating world foundation from seed: {seed}")

        # Phase 0: Seed & Meta
        world = self._initialize_world(seed)
        print(f"  > Phase 0: World initialized (phase={world.world_phase}, age={world.age})")

        # Phase 1a: Spine Creation
        spine_path, spine_influence, control_points = self._generate_spine(seed)
        print(f"  > Phase 1a: Spine created ({len(spine_path)} points from {len(control_points)} control points)")

        # Phase 1a: Rib Generation (NEW!)
        rib_config = self.config.get('rib_generation', {})
        rib_seed = self._hash_seed(seed, "ribs")
        ribs = self._generate_ribs(spine_path, rib_config, rib_seed)
        print(f"  > Phase 1a: {len(ribs)} ribs generated")

        # Phase 1b: Continent Growth
        world.continent = self._generate_continent(seed, spine_path, spine_influence, control_points, ribs)
        print(f"  > Phase 1b: Continent generated (land={world.continent.mask.sum() / world.continent.mask.size * 100:.1f}%)")

        # Phase 1b: Organ Placement
        world.organs = self._place_organs(world.continent)
        print(f"  > Phase 1b: {len(world.organs)} organs placed")

        print("[WP1] Foundation complete!")
        return world

    # ========== PHASE 0: SEED & META ==========

    def _initialize_world(self, seed: str) -> World:
        """
        Phase 0: Инициализация мира с детерминированными параметрами

        Args:
            seed: Строковый seed

        Returns:
            World объект с метаданными
        """
        return World(
            seed=seed,
            world_phase=self.config['global_settings']['world_phase'],
            age=self.config['global_settings']['world_age'],
            global_size=self.global_size
        )

    def _hash_seed(self, base_seed: str, suffix: str) -> int:
        """
        Создаёт детерминированный int seed для генератора

        Args:
            base_seed: Базовый seed мира
            suffix: Суффикс для разделения генераторов ("continent", "spine", и т.д.)

        Returns:
            int seed в диапазоне [0, 2^31)
        """
        combined = f"{base_seed}_{suffix}"
        hash_bytes = hashlib.sha256(combined.encode()).digest()
        return int.from_bytes(hash_bytes[:4], 'big') % (2**31)

    # ========== PHASE 1a: SPINE CREATION ==========

    def _generate_spine(self, seed: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
            """
            Phase 1a: Генерация позвоночника (spine) - ФИНАЛЬНАЯ ВЕРСИЯ v5
            """
            spine_seed = self._hash_seed(seed, "spine")
            
            spine_config = self.config['spine_generation']
            path_config = spine_config['path']
            smoothing_config = spine_config['smoothing']
            influence_config = spine_config['influence']
            direction_config = spine_config['direction']

            # 1. (ИЗМЕНЕНО) Генерация пути через кривую Безье
            spine_raw, control_points = self._generate_bezier_spine(spine_seed, path_config)

            # 2. Сглаживание B-spline (теперь опционально, для небольшой финализации)
            if smoothing_config.get('factor', 0) > 0:
                spine_smooth = self._smooth_spine(spine_raw, smoothing=smoothing_config['factor'])
            else:
                spine_smooth = spine_raw

            # 3. Применение поворота
            angle_rad = 0.0
            if direction_config.get('randomize', False):
                angle_seed = self._hash_seed(seed, "spine_angle")
                angle_rad = (angle_seed / (2**31 - 1)) * 2 * np.pi
            else:
                angle_rad = direction_config.get('angle_rad', 0.0)

            if angle_rad != 0.0:
                map_center = (self.global_size[0] / 2, self.global_size[1] / 2)
                spine_smooth = self._rotate_path(spine_smooth, angle_rad, map_center)
                control_points = self._rotate_path(control_points, angle_rad, map_center)

            # 4. Influence field
            influence_mask = self._create_spine_influence_mask(
                spine_smooth,
                max_influence=influence_config['max_distance']
            )

            return spine_smooth, influence_mask, control_points

    def _bezier_curve(self, control_points: np.ndarray, num_points: int) -> np.ndarray:
            """
            Вычисляет точки на кривой Безье по заданным контрольным точкам.
            """
            n = len(control_points) - 1
            t = np.linspace(0, 1, num_points)
            
            # Факториалы для биномиальных коэффициентов
            from scipy.special import comb
            
            curve = np.zeros((num_points, 2))
            for i in range(n + 1):
                # Биномиальный коэффициент
                bernstein_poly = comb(n, i) * (t ** i) * ((1 - t) ** (n - i))
                curve += np.outer(bernstein_poly, control_points[i])
                
            return curve

    def _generate_control_points_with_sine(self, seed: int, path_config: dict, sine_config: dict) -> np.ndarray:
        """
        Генерирует контрольные точки позвоночника используя sine-wave метод.

        Метод из procedural-spine-visualizer (App.tsx lines 78-89).
        Использует математические синусоидальные волны для создания плавных,
        предсказуемых органических форм позвоночника.

        Преимущества по сравнению с Perlin walker:
        - Детерминированный и предсказуемый
        - Простой математический контроль
        - Не требует библиотек шума
        - 70% меньше кода

        Args:
            seed: Int seed для генерации
            path_config: Конфигурация пути (num_control_points)
            sine_config: Параметры sine-wave (num_vertebrae, vertebra_spacing, spine_curvature)

        Returns:
            np.ndarray формы (num_vertebrae, 2) с координатами точек позвоночника
        """
        map_width, map_height = self.global_size

        # Параметры из config
        num_vertebrae = sine_config.get('num_vertebrae', 33)
        vertebra_spacing = sine_config.get('vertebra_spacing', 12.0)
        spine_curvature = sine_config.get('spine_curvature', 0.1)
        start_y_fraction = sine_config.get('start_y_fraction', 0.1)

        # Инициализация массива позвонков
        vertebrae = np.zeros((num_vertebrae, 2))

        # Начальная точка (центр сверху)
        current_x = map_width / 2
        current_y = map_height * start_y_fraction

        # Начальный угол (вниз)
        angle = np.pi / 2

        # Seed для вариативности начального угла
        angle_seed_hash = self._hash_seed(str(seed), "sine_start_angle")
        initial_angle_offset = (angle_seed_hash / (2**31 - 1)) * 0.5 - 0.25  # [-0.25, 0.25] rad
        angle += initial_angle_offset

        # Генерация позвонков
        for i in range(num_vertebrae):
            vertebrae[i] = [current_x, current_y]

            # Sine-wave curvature (ключевая формула из visualizer)
            angle_offset = np.sin(i * 0.2) * spine_curvature
            angle += angle_offset

            # Шаг в текущем направлении
            current_x += np.cos(angle) * vertebra_spacing
            current_y += np.sin(angle) * vertebra_spacing

        return vertebrae

    def _generate_control_points_with_walker(self, seed: int, path_config: dict, walker_config: dict) -> np.ndarray:
        """
        Генерирует контрольные точки с помощью "2D-странника" (walker),
        который движется по полю шума Перлина. Этот метод позволяет
        создавать спирали, кольца и сложные органические изгибы.

        Метод работает по принципу "случайного блуждания с направлением":
        1. Начинает из стартовой точки
        2. На каждом шаге поворачивает на угол, определяемый шумом Перлина
        3. Делает шаг фиксированной длины в новом направлении
        4. Повторяет процесс для создания плавного пути

        Улучшения v3.0:
        - Инерция поворота для более плавных изгибов
        - Отталкивание от границ карты
        - Притяжение к центру карты (централизация)
        - Контроль мин/макс расстояния между точками
        - Детерминированность через seed

        Args:
            seed: Int seed для генератора шума
            path_config: Конфигурация пути (num_control_points, start_fraction)
            walker_config: Параметры walker (step_length, turn_strength, и т.д.)

        Returns:
            np.ndarray формы (num_control_points, 2) с координатами контрольных точек
        """
        walker_noise = PerlinNoise(seed=seed)
        map_width, map_height = self.global_size

        num_points = path_config['num_control_points']
        step_len = walker_config.get('step_length', 30.0)
        turn_strength = walker_config.get('turn_strength', 3.5)
        noise_scale = walker_config.get('noise_scale', 250.0)
        inertia = walker_config.get('inertia', 0.7)

        # Границы и центрирование
        boundary_repulsion = walker_config.get('boundary_repulsion', 50.0)
        repulsion_strength = walker_config.get('repulsion_strength', 0.3)
        center_attraction = walker_config.get('center_attraction', 0.15)
        center_attraction_radius = walker_config.get('center_attraction_radius', 150.0)

        # Контроль длины между точками
        min_step_distance = walker_config.get('min_step_distance', 40.0)
        max_step_distance = walker_config.get('max_step_distance', 100.0)

        control_points = np.zeros((num_points, 2))

        # Начальная позиция (центр, верхняя часть)
        control_points[0] = [map_width / 2, map_height * path_config['start_fraction']]

        # Центр карты для притяжения
        map_center = np.array([map_width / 2, map_height / 2])

        # Начальный угол из seed для вариативности
        angle_seed_hash = self._hash_seed(str(seed), "walker_angle")
        current_angle = (angle_seed_hash / (2**31 - 1)) * 2 * np.pi

        # Для инерции храним предыдущее изменение угла
        prev_angle_delta = 0.0

        for i in range(1, num_points):
            pos_x, pos_y = control_points[i-1]
            current_pos = np.array([pos_x, pos_y])

            # 1. Получаем значение шума в текущей точке
            noise_val = walker_noise.noise_2d(
                pos_x / noise_scale,
                pos_y / noise_scale
            )

            # 2. Превращаем шум в изменение угла с учётом инерции
            raw_angle_delta = noise_val * turn_strength
            angle_delta = inertia * prev_angle_delta + (1 - inertia) * raw_angle_delta
            prev_angle_delta = angle_delta

            # 3. Отталкивание от границ (мягкое)
            boundary_turn = 0.0

            if pos_x < boundary_repulsion:
                boundary_turn += repulsion_strength * (1.0 - pos_x / boundary_repulsion)
            if pos_x > map_width - boundary_repulsion:
                boundary_turn -= repulsion_strength * (1.0 - (map_width - pos_x) / boundary_repulsion)
            if pos_y < boundary_repulsion:
                boundary_turn += repulsion_strength * (1.0 - pos_y / boundary_repulsion) * 0.5
            if pos_y > map_height - boundary_repulsion:
                boundary_turn -= repulsion_strength * (1.0 - (map_height - pos_y) / boundary_repulsion) * 0.5

            angle_delta += boundary_turn

            # 4. НОВОЕ: Притяжение к центру карты (централизация)
            # Вычисляем вектор к центру
            to_center = map_center - current_pos
            dist_to_center = np.linalg.norm(to_center)

            # Если walker далеко от центра, добавляем притяжение
            if dist_to_center > center_attraction_radius:
                # Нормализуем вектор к центру
                to_center_normalized = to_center / dist_to_center

                # Угол к центру
                angle_to_center = np.arctan2(to_center_normalized[1], to_center_normalized[0])

                # Разница между текущим углом и углом к центру
                angle_diff = angle_to_center - current_angle

                # Нормализация разницы угла к диапазону [-π, π]
                angle_diff = (angle_diff + np.pi) % (2 * np.pi) - np.pi

                # Сила притяжения пропорциональна расстоянию от комфортной зоны
                excess_distance = dist_to_center - center_attraction_radius
                attraction_force = center_attraction * (excess_distance / center_attraction_radius)
                attraction_force = min(attraction_force, 1.0)  # Ограничиваем максимум

                # Добавляем поворот к центру
                angle_delta += angle_diff * attraction_force

            # Обновляем текущий угол
            current_angle += angle_delta

            # 5. Делаем шаг в новом направлении
            dx = np.cos(current_angle) * step_len
            dy = np.sin(current_angle) * step_len
            new_pos = current_pos + np.array([dx, dy])

            # 6. НОВОЕ: Контроль расстояния между точками
            # Вычисляем фактическое расстояние до предыдущей точки
            actual_distance = np.linalg.norm(new_pos - control_points[i-1])

            # Если расстояние выходит за пределы, масштабируем вектор шага
            if actual_distance < min_step_distance:
                # Слишком близко - увеличиваем расстояние
                scale_factor = min_step_distance / actual_distance
                step_vector = new_pos - control_points[i-1]
                new_pos = control_points[i-1] + step_vector * scale_factor
            elif actual_distance > max_step_distance:
                # Слишком далеко - уменьшаем расстояние
                scale_factor = max_step_distance / actual_distance
                step_vector = new_pos - control_points[i-1]
                new_pos = control_points[i-1] + step_vector * scale_factor

            # 7. Жёсткий clamp к границам (на всякий случай)
            margin = 10.0
            new_pos[0] = np.clip(new_pos[0], margin, map_width - margin)
            new_pos[1] = np.clip(new_pos[1], margin, map_height - margin)

            control_points[i] = new_pos

        return control_points

    def _generate_bezier_spine(self, seed: int, path_config: dict) -> Tuple[np.ndarray, np.ndarray]:
        """
        Генерация позвоночника v10 (SINE-WAVE METHOD).

        Использует математические sine-wave кривые из procedural-spine-visualizer
        для создания плавных, предсказуемых органических форм позвоночника.

        Args:
            seed: Int seed для генерации
            path_config: Конфигурация пути из config

        Returns:
            Tuple[spine_path, control_points]:
                - spine_path: (num_vertebrae, 2) финальный путь позвоночника
                - control_points: (num_vertebrae, 2) позвонки (используются как контрольные точки)
        """
        spine_config = self.config['spine_generation']
        sine_config = spine_config.get('sine_params', {})
        map_width, map_height = self.global_size

        # Генерация позвонков через sine-wave метод
        vertebrae = self._generate_control_points_with_sine(seed, path_config, sine_config)

        # Sine-wave метод генерирует готовый детальный путь,
        # поэтому vertebrae одновременно являются и spine_path и control_points
        spine_path = vertebrae

        # Clamp к безопасным границам
        safe_margin = map_width * 0.05
        spine_path[:, 0] = np.clip(spine_path[:, 0], safe_margin, map_width - safe_margin)
        spine_path[:, 1] = np.clip(spine_path[:, 1], safe_margin, map_height - safe_margin)

        # Возвращаем позвонки как путь и как контрольные точки
        return spine_path, vertebrae

    def _generate_ribs(self, spine_path: np.ndarray, config: dict, seed: int) -> List[RibData]:
        """
        Генерирует рёбра (ribs) перпендикулярно позвоночнику.

        Портировано из procedural-spine-visualizer (App.tsx lines 91-134).
        Рёбра создают:
        - Гребни на ландшафте (heightmap influence)
        - Зоны размещения органов (intercostal zones)
        - Гидрологические барьеры (watersheds)

        Args:
            spine_path: (N, 2) array координат позвоночника
            config: rib_generation секция из YAML
            seed: int seed для детерминированности

        Returns:
            List[RibData] - список рёбер с обеих сторон
        """
        ribs = []

        if not config.get('enabled', False):
            return ribs

        # Параметры из config
        num_rib_pairs = config.get('num_rib_pairs', 12)
        thoracic_start = config.get('thoracic_start_index', 8)
        max_rib_length = config.get('max_rib_length', 120.0)
        rib_curvature = config.get('rib_curvature', 0.7)
        rib_angle_factor = config.get('rib_angle_factor', 0.4)
        rib_length_taper = config.get('rib_length_taper', 0.4)
        rib_stride = config.get('rib_stride', 1)
        rib_asymmetry = config.get('rib_asymmetry', 0.0)

        # RNG для asymmetry
        rng = np.random.RandomState(seed)

        # Грудная клетка (thoracic region): от thoracic_start до конца позвоночника
        thoracic_end = len(spine_path) - 1
        rib_index = 0

        for i in range(thoracic_start, thoracic_end):
            # Пропускаем позвонки согласно rib_stride
            if (i - thoracic_start) % rib_stride != 0:
                continue

            # Вычисляем касательную к позвоночнику (tangent)
            if i == 0:
                tangent_vec = spine_path[i + 1] - spine_path[i]
            elif i == len(spine_path) - 1:
                tangent_vec = spine_path[i] - spine_path[i - 1]
            else:
                # Центральная разность для плавности
                tangent_vec = spine_path[i + 1] - spine_path[i - 1]

            tangent_angle = np.arctan2(tangent_vec[1], tangent_vec[0])

            # Normal angle (перпендикуляр к позвоночнику)
            normal_angle = tangent_angle + np.pi / 2

            # Bell-curve tapering: рёбра длиннее в середине, короче по краям
            progress = rib_index / (num_rib_pairs - 1) if num_rib_pairs > 1 else 0.5
            progress = np.clip(progress, 0.0, 1.0)  # Безопасность

            # sin(π * progress) всегда в [0, 1] для progress in [0, 1]
            sin_value = np.sin(np.pi * progress)
            sin_value = max(0.0, sin_value)  # Гарантируем неотрицательность

            taper_factor = np.power(sin_value, rib_length_taper)
            current_length = max_rib_length * taper_factor

            # Пропускаем рёбра с очень малой длиной (< 5px)
            if current_length < 5.0 or np.isnan(current_length):
                rib_index += 1
                continue

            # Генерируем рёбра с обеих сторон
            for side in [-1, 1]:
                # Asymmetry: случайно пропускаем некоторые рёбра
                if rng.random() < rib_asymmetry:
                    continue

                # Создаём Quadratic Bezier curve для ребра
                rib_path = self._create_bezier_rib(
                    start_point=spine_path[i],
                    normal_angle=normal_angle * side,
                    tangent_angle=tangent_angle,
                    length=current_length,
                    curvature=rib_curvature,
                    angle_factor=rib_angle_factor,
                    num_points=20  # Детализация кривой
                )

                # Создаём RibData
                rib = RibData(
                    side=side,
                    vertebra_index=i,
                    path=rib_path,
                    length=current_length
                )
                ribs.append(rib)

            rib_index += 1

        return ribs

    def _create_bezier_rib(self, start_point: np.ndarray, normal_angle: float,
                           tangent_angle: float, length: float, curvature: float,
                           angle_factor: float, num_points: int = 20) -> np.ndarray:
        """
        Создаёт Quadratic Bezier curve для одного ребра.

        Портировано из App.tsx lines 116-126.

        Args:
            start_point: (2,) точка начала (на позвоночнике)
            normal_angle: угол нормали (перпендикуляр к позвоночнику)
            tangent_angle: угол касательной к позвоночнику
            length: длина ребра
            curvature: коэффициент изгиба [0.1-1.5]
            angle_factor: наклон вперёд/назад [-0.5-1.5]
            num_points: количество точек в кривой

        Returns:
            np.ndarray формы (num_points, 2) - точки вдоль ребра
        """
        # Конечная точка ребра
        end_x = start_point[0] + np.cos(normal_angle) * length + \
                np.cos(tangent_angle) * length * angle_factor
        end_y = start_point[1] + np.sin(normal_angle) * length + \
                np.sin(tangent_angle) * length * angle_factor

        # Контрольная точка для Bezier (создаёт изгиб)
        control_x = start_point[0] + np.cos(normal_angle) * length * curvature + \
                    np.cos(tangent_angle) * length * 0.1
        control_y = start_point[1] + np.sin(normal_angle) * length * curvature + \
                    np.sin(tangent_angle) * length * 0.1

        # Quadratic Bezier curve: P(t) = (1-t)^2 * P0 + 2*(1-t)*t * P1 + t^2 * P2
        # P0 = start, P1 = control, P2 = end
        t = np.linspace(0, 1, num_points).reshape(-1, 1)

        P0 = start_point
        P1 = np.array([control_x, control_y])
        P2 = np.array([end_x, end_y])

        curve = (1 - t)**2 * P0 + 2 * (1 - t) * t * P1 + t**2 * P2

        return curve

    def _create_smooth_spline_from_points(self, control_points: np.ndarray, points_per_segment: int = 20) -> np.ndarray:
        """
        Создаёт гладкий сплайн, который проходит близко к контрольным точкам.
        (ВЕРСИЯ 3.0, СТАБИЛЬНАЯ) - Идеально подходит для отрисовки "позвонков".
        """
        if len(control_points) < 3:
            t = np.linspace(0, 1, points_per_segment * 2).reshape(-1, 1)
            return control_points[0] * (1 - t) + control_points[1] * t

        all_segments = []

        p0, p1 = control_points[0], control_points[1]
        mid_p0_p1 = (p0 + p1) / 2
        first_segment = self._bezier_curve(np.array([p0, p0, mid_p0_p1]), points_per_segment)
        all_segments.append(first_segment)

        for i in range(len(control_points) - 2):
            p_start, p_control, p_end = control_points[i], control_points[i+1], control_points[i+2]
            start_point = (p_start + p_control) / 2
            end_point = (p_control + p_end) / 2
            segment = self._bezier_curve(np.array([start_point, p_control, end_point]), points_per_segment)
            all_segments.append(segment)

        pn_2, pn_1 = control_points[-2], control_points[-1]
        mid_last = (pn_2 + pn_1) / 2
        last_segment = self._bezier_curve(np.array([mid_last, pn_1, pn_1]), points_per_segment)
        all_segments.append(last_segment)

        return np.vstack(all_segments)

    def _rotate_path(self, path: np.ndarray, angle_rad: float, origin: Tuple[float, float]) -> np.ndarray:
        """
        Поворачивает путь (массив точек) вокруг заданной точки.

        Args:
            path: Массив (N, 2) с координатами точек.
            angle_rad: Угол поворота в радианах.
            origin: Точка (x, y), вокруг которой происходит поворот.

        Returns:
            Массив (N, 2) с новыми координатами.
        """
        ox, oy = origin
        px, py = path[:, 0], path[:, 1]

        qx = ox + np.cos(angle_rad) * (px - ox) - np.sin(angle_rad) * (py - oy)
        qy = oy + np.sin(angle_rad) * (px - ox) + np.cos(angle_rad) * (py - oy)

        return np.column_stack([qx, qy])

    def _smooth_spine(self, spine_raw: np.ndarray, smoothing: float = 100.0) -> np.ndarray:
        """
        Сглаживание хребта B-spline интерполяцией

        Args:
            spine_raw: (N, 2) сырые координаты
            smoothing: Параметр сглаживания (больше = глаже)

        Returns:
            (N, 2) сглаженные координаты
        """
        x_raw, y_raw = spine_raw[:, 0], spine_raw[:, 1]

        # B-spline fit
        tck, u = splprep([x_raw, y_raw], s=smoothing, k=3)

        # Вычисление сглаженных точек
        u_new = np.linspace(0, 1, len(spine_raw))
        x_smooth, y_smooth = splev(u_new, tck)

        return np.column_stack([x_smooth, y_smooth])

    def _create_spine_influence_mask(self, spine_path: np.ndarray,
                                    max_influence: float = 200.0) -> np.ndarray:
        """
        Создание поля влияния хребта (затухание по расстоянию)

        Args:
            spine_path: (N, 2) координаты хребта
            max_influence: Максимальное расстояние влияния (px)

        Returns:
            (512, 512) influence map [0, 1]
        """
        influence_mask = np.zeros(self.global_size, dtype=np.float32)

        for (sx, sy) in spine_path:
            # Сетка координат
            y, x = np.ogrid[:self.global_size[1], :self.global_size[0]]

            # Евклидово расстояние
            distance = np.sqrt((x - sx)**2 + (y - sy)**2)

            # Линейное затухание
            influence = np.maximum(0, 1.0 - distance / max_influence)

            # Максимум из всех точек (overlay)
            influence_mask = np.maximum(influence_mask, influence)

        # Ensure float32 dtype
        return influence_mask.astype(np.float32)

    # ========== PHASE 1b: CONTINENT GROWTH ==========

    def _generate_continent(self, seed: str, spine_path: np.ndarray, spine_influence: np.ndarray,
                           control_points: np.ndarray, ribs: List[RibData]) -> ContinentData:
        """
        Phase 1b: Генерация континента

        Args:
            seed: Базовый seed мира
            spine_path: Координаты позвоночника
            spine_influence: Поле влияния позвоночника
            control_points: Контрольные точки позвоночника
            ribs: Список рёбер (NEW!)

        Returns:
            ContinentData с маской, heightmap, геометрией, рёбрами
        """
        continent_seed = self._hash_seed(seed, "continent")
        config = self.config['continent_generation']

        # 1. Базовый heightmap (Perlin Noise)
        heightmap = self._generate_heightmap(continent_seed, config['perlin_noise'])

        # 2. Применение spine influence
        sea_level_override = config['sea_level_spine_mode']
        heightmap_masked, sea_level = self._apply_spine_influence(
            heightmap, spine_influence,
            sea_level_override=sea_level_override
        )

        # 2.5. Применение rib influence (NEW!)
        rib_config = self.config.get('rib_generation', {})
        if rib_config.get('enabled', False) and len(ribs) > 0:
            heightmap_masked = self._apply_rib_influence_to_heightmap(heightmap_masked, ribs, rib_config)

        # 3. Создание маски континента
        continent_mask = self._create_continent_mask(heightmap_masked, sea_level, config['smoothing'])

        # 4. Расчёт геометрии
        center, major_axis = self._calculate_continent_geometry(continent_mask)

        return ContinentData(
            mask=continent_mask,
            heightmap=heightmap_masked,
            center=center,
            major_axis=major_axis,
            spine_path=spine_path,
            control_points=control_points,
            ribs=ribs  # NEW: сохраняем рёбра
        )

    def _apply_rib_influence_to_heightmap(self, heightmap: np.ndarray, ribs: List[RibData],
                                          rib_config: dict) -> np.ndarray:
        """
        Применяет влияние рёбер к heightmap, создавая гребни (ridges) вдоль рёбер.

        Рёбра создают возвышенности на ландшафте, формируя горные хребты и водоразделы.
        Высота уменьшается с расстоянием от ребра (Gaussian falloff).

        Args:
            heightmap: (512, 512) исходный heightmap
            ribs: Список рёбер
            rib_config: Конфигурация рёбер (rib_height_multiplier, rib_influence_radius)

        Returns:
            (512, 512) heightmap с добавленными рёберными гребнями
        """
        if len(ribs) == 0:
            return heightmap

        height_multiplier = rib_config.get('rib_height_multiplier', 0.3)
        influence_radius = rib_config.get('rib_influence_radius', 15.0)

        # Создаём копию для модификации
        modified_heightmap = heightmap.copy()

        # Для каждого ребра
        for rib in ribs:
            # Проходим по каждой точке вдоль ребра
            for i, point in enumerate(rib.path):
                x, y = int(point[0]), int(point[1])

                # Пропускаем точки вне границ
                if not (0 <= x < self.global_size[0] and 0 <= y < self.global_size[1]):
                    continue

                # Высота ребра уменьшается от позвоночника к концу (taper)
                progress = i / len(rib.path)
                taper = 1.0 - progress  # Максимум у позвоночника, минимум на конце

                # Добавляем Gaussian bump вокруг точки ребра
                for dy in range(-int(influence_radius * 2), int(influence_radius * 2) + 1):
                    for dx in range(-int(influence_radius * 2), int(influence_radius * 2) + 1):
                        px, py = x + dx, y + dy

                        if not (0 <= px < self.global_size[0] and 0 <= py < self.global_size[1]):
                            continue

                        # Расстояние от центра ребра
                        dist = np.sqrt(dx**2 + dy**2)

                        if dist <= influence_radius * 2:
                            # Gaussian falloff
                            gaussian = np.exp(-(dist**2) / (2 * influence_radius**2))
                            height_addition = height_multiplier * gaussian * taper

                            # Добавляем высоту (не заменяем!)
                            modified_heightmap[py, px] = min(1.0, modified_heightmap[py, px] + height_addition)

        return modified_heightmap

    def _generate_heightmap(self, seed: int, perlin_config: dict) -> np.ndarray:
        """
        Генерация базового heightmap через Perlin Noise

        Args:
            seed: Int seed для Perlin
            perlin_config: Конфигурация Perlin Noise

        Returns:
            (512, 512) heightmap [0, 1]
        """
        return generate_perlin_map(
            width=self.global_size[0],
            height=self.global_size[1],
            seed=seed,
            scale=perlin_config['scale'],
            octaves=perlin_config['octaves'],
            persistence=perlin_config['persistence'],
            lacunarity=perlin_config['lacunarity'],
            normalize_to_01=True
        )

    def _apply_spine_influence(self, heightmap: np.ndarray, spine_mask: np.ndarray,
                              sea_level_override: float = 0.20) -> Tuple[np.ndarray, float]:
        """
        Модуляция heightmap через spine influence

        Args:
            heightmap: Базовый heightmap
            spine_mask: Поле влияния позвоночника
            sea_level_override: Скорректированный sea_level

        Returns:
            (heightmap_masked, sea_level)
        """
        # Blend heightmap with spine influence (additive, not multiplicative)
        # This prevents creating "holes" where spine influence is low
        alpha = 0.7  # Weight of spine influence
        heightmap_masked = heightmap * (1 - alpha) + (heightmap * spine_mask) * alpha

        # Ensure float32
        heightmap_masked = heightmap_masked.astype(np.float32)

        # Компенсация умножения: ниже sea_level
        return heightmap_masked, sea_level_override

    def _create_continent_mask(self, heightmap: np.ndarray, sea_level: float,
                              smoothing_config: dict) -> np.ndarray:
        """
        Создание маски континента с морфологическим сглаживанием

        Args:
            heightmap: Heightmap
            sea_level: Порог суша/океан
            smoothing_config: Параметры сглаживания

        Returns:
            (512, 512) boolean mask
        """
        # 1. Базовый threshold
        mask = (heightmap > sea_level).astype(bool)

        # 2. Удаление маленьких островов
        mask = binary_opening(mask, iterations=smoothing_config['binary_opening_iterations'])

        # 3. Заполнение маленьких заливов
        mask = binary_closing(mask, iterations=smoothing_config['binary_closing_iterations'])

        # 4. Gaussian blur для финального сглаживания
        mask_float = gaussian_filter(mask.astype(float), sigma=smoothing_config['gaussian_sigma'])
        mask = (mask_float > smoothing_config['final_threshold']).astype(bool)

        # 5. Keep only largest connected component (remove small islands)
        labeled, num_features = ndimage.label(mask)
        if num_features > 1:
            # Find sizes of all components
            component_sizes = ndimage.sum(mask, labeled, range(1, num_features + 1))
            # Keep only the largest
            largest_component = np.argmax(component_sizes) + 1
            mask = (labeled == largest_component)

        return mask

    def _calculate_continent_geometry(self, mask: np.ndarray) -> Tuple[Tuple[int, int],
                                                                        Tuple[Tuple[int, int], Tuple[int, int]]]:
        """
        Вычисление center of mass и major axis (через PCA)

        Args:
            mask: Boolean mask континента

        Returns:
            (center, major_axis)
            - center: (cx, cy) координаты центра масс
            - major_axis: ((x1, y1), (x2, y2)) начало и конец оси
        """
        # Center of mass
        cy, cx = ndimage.center_of_mass(mask)

        if np.isnan(cx) or np.isnan(cy):
            cx, cy = self.global_size[0] // 2, self.global_size[1] // 2

        center = (int(cx), int(cy))

        # Координаты всех точек суши
        y_coords, x_coords = np.where(mask)

        if len(x_coords) == 0:
            # Fallback: диагональ карты
            return center, ((0, 0), (self.global_size[0], self.global_size[1]))

        coords = np.column_stack([x_coords, y_coords])

        # PCA
        mean = coords.mean(axis=0)
        centered = coords - mean

        # Covariance matrix
        cov_matrix = np.cov(centered.T)
        eigenvalues, eigenvectors = np.linalg.eig(cov_matrix)

        # Главный компонент (максимальная дисперсия)
        principal_component = eigenvectors[:, eigenvalues.argmax()]

        # Проекции на главную ось
        projections = centered @ principal_component

        # Крайние точки
        min_idx = projections.argmin()
        max_idx = projections.argmax()

        start_point = tuple(coords[min_idx].astype(int))
        end_point = tuple(coords[max_idx].astype(int))

        major_axis = (start_point, end_point)

        return center, major_axis

    # ========== PHASE 1b: ORGAN PLACEMENT ==========

    def _place_organs(self, continent: ContinentData) -> Dict[str, Organ]:
        """
        Phase 1b: Размещение анатомических органов

        Args:
            continent: Данные континента

        Returns:
            Словарь органов {id: Organ}
        """
        organs = {}
        organ_config = self.config['organs']

        # 1. Metabolic Core (центр масс)
        organs['organ_metabolic_core'] = Organ(
            id='organ_metabolic_core',
            type='metabolic_organ',
            position=continent.center,
            radius=organ_config['metabolic_organ']['radius'],
            temperature=organ_config['metabolic_organ']['temperature'],
            nutrient_output=organ_config['metabolic_organ']['nutrient_output']
        )

        # 2. Stomach (южная низина)
        metabolic_y = continent.center[1]
        stomach_pos = self._find_lowland(
            continent,
            search_region=(metabolic_y + 20, min(metabolic_y + 80, self.global_size[1]))
        )
        organs['organ_stomach'] = Organ(
            id='organ_stomach',
            type='digestive',
            position=stomach_pos,
            radius=organ_config['digestive']['radius'],
            temperature=organ_config['digestive']['temperature'],
            acid_level=organ_config['digestive']['acid_level']
        )

        # 3. Neural Clusters (вдоль major axis)
        (x1, y1), (x2, y2) = continent.major_axis

        for i, position_fraction in enumerate(organ_config['neural_cluster']['placement_params']['positions']):
            x = int(x1 + (x2 - x1) * position_fraction)
            y = int(y1 + (y2 - y1) * position_fraction)

            control_strength = organ_config['neural_cluster']['control_strength']
            control_strength -= i * organ_config['neural_cluster']['control_decay']

            organs[f'ganglion_{i}'] = Organ(
                id=f'ganglion_{i}',
                type='neural_cluster',
                position=(x, y),
                radius=organ_config['neural_cluster']['radius'],
                control_strength=control_strength
            )

        # 4. Lymph Node (возвышенность у первого ганглия)
        ganglion_pos = organs['ganglion_0'].position
        lymph_pos = self._find_elevation(continent, near=ganglion_pos, radius=50)
        organs['lymph_node_sclerite'] = Organ(
            id='lymph_node_sclerite',
            type='immune_node',
            position=lymph_pos,
            radius=organ_config['immune_node']['radius'],
            cell_production=organ_config['immune_node']['cell_production']
        )

        return organs

    def _find_lowland(self, continent: ContinentData,
                     search_region: Tuple[int, int]) -> Tuple[int, int]:
        """
        Находит низину в заданном регионе

        Args:
            continent: Данные континента
            search_region: (y_min, y_max) для поиска

        Returns:
            (x, y) координаты низины
        """
        y_min, y_max = search_region
        search_mask = continent.mask.copy()
        search_mask[:y_min, :] = False
        search_mask[y_max:, :] = False

        if not search_mask.any():
            # Fallback: центр региона
            return (continent.center[0], (y_min + y_max) // 2)

        # Находим точку с минимальной высотой
        heightmap_masked = np.where(search_mask, continent.heightmap, np.inf)
        min_y, min_x = np.unravel_index(heightmap_masked.argmin(), heightmap_masked.shape)

        return (int(min_x), int(min_y))

    def _find_elevation(self, continent: ContinentData,
                       near: Tuple[int, int], radius: int = 50) -> Tuple[int, int]:
        """
        Находит возвышенность рядом с заданной точкой

        Args:
            continent: Данные континента
            near: (x, y) координаты центра поиска
            radius: Радиус поиска

        Returns:
            (x, y) координаты возвышенности
        """
        cx, cy = near

        # Маска поиска: круг радиуса radius
        y, x = np.ogrid[:self.global_size[1], :self.global_size[0]]
        distance = np.sqrt((x - cx)**2 + (y - cy)**2)
        search_mask = (distance < radius) & continent.mask

        if not search_mask.any():
            # Fallback: сама точка near
            return near

        # Находим точку с максимальной высотой
        heightmap_masked = np.where(search_mask, continent.heightmap, -np.inf)
        max_y, max_x = np.unravel_index(heightmap_masked.argmax(), heightmap_masked.shape)

        return (int(max_x), int(max_y))
