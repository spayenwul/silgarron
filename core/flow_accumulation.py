"""
D8 Flow Accumulation - Hydrological algorithm for Lymphatic System

Реализует алгоритм D8 (Deterministic 8-direction) для моделирования
течения жидкости по рельефу.

Используется для генерации лимфатической системы Сильгаррона.

См. docs/sprint_3.5_implementation/03_D8_FLOW_ACCUMULATION.md для деталей.
"""

import numpy as np
from typing import List, Tuple


# D8 направления: (dy, dx, code)
# Codes: 1=E, 2=SE, 4=S, 8=SW, 16=W, 32=NW, 64=N, 128=NE
D8_DIRECTIONS = [
    (-1,  0, 64),   # N (север)
    (-1,  1, 128),  # NE (северо-восток)
    ( 0,  1, 1),    # E (восток)
    ( 1,  1, 2),    # SE (юго-восток)
    ( 1,  0, 4),    # S (юг)
    ( 1, -1, 8),    # SW (юго-запад)
    ( 0, -1, 16),   # W (запад)
    (-1, -1, 32),   # NW (северо-запад)
]

# Обратная карта: code → (dy, dx)
DIRECTION_DECODE = {
    64: (-1,  0),   # N
    128: (-1,  1),  # NE
    1: ( 0,  1),    # E
    2: ( 1,  1),    # SE
    4: ( 1,  0),    # S
    8: ( 1, -1),    # SW
    16: ( 0, -1),   # W
    32: (-1, -1),   # NW
    0: ( 0,  0),    # No flow (sink)
}


def calculate_flow_direction(elevation: np.ndarray) -> np.ndarray:
    """
    Вычисляет направление потока для каждой ячейки (D8 algorithm).

    Для каждой ячейки определяет направление к соседу с минимальной высотой.

    Args:
        elevation: np.ndarray (height, width) - карта высот

    Returns:
        flow_dir: np.ndarray (height, width) dtype=uint8
                  Код направления потока:
                  64=N, 128=NE, 1=E, 2=SE, 4=S, 8=SW, 16=W, 32=NW, 0=sink

    Примечания:
        - 0 означает локальный минимум (сток)
        - Края карты считаются стоками
    """
    height, width = elevation.shape
    flow_dir = np.zeros((height, width), dtype=np.uint8)

    for y in range(height):
        for x in range(width):
            current_height = elevation[y, x]

            # Найти соседа с минимальной высотой
            min_height = current_height
            flow_code = 0  # 0 = sink (локальный минимум)

            for dy, dx, code in D8_DIRECTIONS:
                ny, nx = y + dy, x + dx

                # Проверка границ
                if 0 <= ny < height and 0 <= nx < width:
                    neighbor_height = elevation[ny, nx]

                    # Строгое неравенство: только если сосед НИЖЕ
                    if neighbor_height < min_height:
                        min_height = neighbor_height
                        flow_code = code

            flow_dir[y, x] = flow_code

    return flow_dir


def calculate_flow_accumulation(
    elevation: np.ndarray,
    flow_dir: np.ndarray
) -> np.ndarray:
    """
    Вычисляет аккумуляцию потока (количество ячеек, втекающих в данную).

    Обрабатывает ячейки от высоких к низким, накапливая поток вниз по течению.

    Args:
        elevation: np.ndarray (height, width) - карта высот
        flow_dir: np.ndarray (height, width) - направления потока

    Returns:
        accumulation: np.ndarray (height, width) dtype=float32
                      Количество ячеек, которые втекают в данную (включая её саму)

    Примечания:
        - Минимальное значение = 1.0 (только сама ячейка)
        - Высокие значения = главные русла (много втекающих ячеек)
    """
    height, width = elevation.shape
    accumulation = np.ones((height, width), dtype=np.float32)

    # Создаём список ячеек, отсортированных по высоте (от высоких к низким)
    # Используем np.argsort для производительности
    flat_elevation = elevation.flatten()
    sorted_indices = np.argsort(-flat_elevation)  # Минус для reverse sort

    # Преобразуем flat indices обратно в (y, x)
    y_coords = sorted_indices // width
    x_coords = sorted_indices % width

    # Обрабатываем от истоков к устьям
    for i in range(len(sorted_indices)):
        y = y_coords[i]
        x = x_coords[i]

        current_accum = accumulation[y, x]
        direction = flow_dir[y, x]

        if direction == 0:
            continue  # Локальный минимум (сток) - не передаём дальше

        # Декодируем направление
        dy, dx = DIRECTION_DECODE[direction]
        ny, nx = y + dy, x + dx

        # Проверка границ (на всякий случай)
        if 0 <= ny < height and 0 <= nx < width:
            # Передаём аккумуляцию вниз по потоку
            accumulation[ny, nx] += current_accum

    return accumulation


def find_lymph_sources(
    elevation: np.ndarray,
    ridge_mask: np.ndarray,
    flow_accumulation: np.ndarray,
    num_sources: int = 8,
    elevation_range: Tuple[float, float] = (0.5, 0.8),
    min_ridge: float = 0.5,
    max_accumulation: float = 5.0,
    rng: np.random.Generator = None
) -> List[Tuple[int, int]]:
    """
    Находит истоки лимфатических каналов в предгорьях хребта.

    Критерии отбора (анатомическая модель):
    - Находятся на хребте (ridge_mask > min_ridge)
    - В ПРЕДГОРЬЯХ (elevation в диапазоне [0.5, 0.8])
      → НЕ на самых высоких пиках (это "кость")
      → НЕ в низинах (это устья, а не истоки)
    - Малая аккумуляция (локальные пики, не в руслах)

    Биологическая интерпретация:
    - Предгорья хребта = "фильтрующие органы" (почки, печень)
    - Оттуда лимфа течёт вниз к периферии (очистные зоны)
    - Единая интегрированная система от центра к краям

    Args:
        elevation: Карта высот
        ridge_mask: Маска хребта (0.0-1.0)
        flow_accumulation: Аккумуляция потока
        num_sources: Количество истоков для генерации
        elevation_range: Диапазон высот для истоков (min, max)
        min_ridge: Минимальное значение ridge mask
        max_accumulation: Максимальная аккумуляция (истоки не в руслах)
        rng: Random generator для детерминизма

    Returns:
        List[(y, x)] - координаты истоков лимфотоков

    Примечания:
        - Диапазон [0.5, 0.8] = предгорья (не пики, не низины)
        - Это обеспечивает течение от хребта к краям
        - Формирует единую систему "кровообращения"
    """
    min_elev, max_elev = elevation_range

    # Маска кандидатов (КРИТИЧНО: диапазон высоты, а не только минимум!)
    candidates = (
        (ridge_mask > min_ridge) &                      # На хребте
        (elevation >= min_elev) &                       # Не слишком низко
        (elevation <= max_elev) &                       # Не слишком высоко (предгорья!)
        (flow_accumulation <= max_accumulation)        # Не в главных руслах
    )

    # Находим координаты кандидатов
    y_coords, x_coords = np.where(candidates)

    if len(y_coords) == 0:
        # Нет подходящих точек - ослабляем критерии (расширяем диапазон)
        candidates = (
            (ridge_mask > min_ridge * 0.3) &
            (elevation >= min_elev * 0.8) &
            (elevation <= max_elev * 1.2)
        )
        y_coords, x_coords = np.where(candidates)

    if len(y_coords) == 0:
        # Всё ещё нет - возвращаем пустой список
        return []

    # Выбираем num_sources с учётом распределения по карте
    if len(y_coords) > num_sources:
        # Сортируем по высоте (от высоких к низким)
        heights = elevation[y_coords, x_coords]
        sorted_indices = np.argsort(heights)[::-1]

        # Выбираем источники с минимальным расстоянием между ними
        selected_indices = []
        min_distance = 40  # Минимум 40 пикселей между источниками

        for idx in sorted_indices:
            y, x = y_coords[idx], x_coords[idx]

            # Проверяем расстояние до уже выбранных
            too_close = False
            for sel_idx in selected_indices:
                sel_y, sel_x = y_coords[sel_idx], x_coords[sel_idx]
                distance = np.sqrt((y - sel_y)**2 + (x - sel_x)**2)
                if distance < min_distance:
                    too_close = True
                    break

            if not too_close:
                selected_indices.append(idx)

            if len(selected_indices) >= num_sources:
                break

        # Если не набрали достаточно (слишком строгий min_distance), берём топ-N
        if len(selected_indices) < num_sources:
            selected_indices = sorted_indices[:num_sources].tolist()

        y_coords = y_coords[selected_indices]
        x_coords = x_coords[selected_indices]

    sources = [(int(y), int(x)) for y, x in zip(y_coords, x_coords)]
    return sources


def create_lymph_channels_mask(
    flow_accumulation: np.ndarray,
    threshold_percentile: float = 90.0
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Создаёт маску лимфатических каналов на основе аккумуляции.

    Ячейки с высокой аккумуляцией = главные русла (лимфатические каналы).

    Args:
        flow_accumulation: Карта аккумуляции потока
        threshold_percentile: Процентиль для порога (90 = верхние 10%)

    Returns:
        lymph_mask: np.ndarray (binary) - 1 где канал, 0 где нет
        lymph_intensity: np.ndarray (float) - нормализованная интенсивность [0,1]
    """
    # Определяем порог (верхние X% аккумуляции)
    threshold = np.percentile(flow_accumulation, threshold_percentile)

    # Бинарная маска каналов
    lymph_mask = (flow_accumulation >= threshold).astype(np.float32)

    # Нормализованная интенсивность (для визуализации)
    max_accum = flow_accumulation.max()
    if max_accum > 0:
        lymph_intensity = flow_accumulation / max_accum
    else:
        lymph_intensity = np.zeros_like(flow_accumulation)

    lymph_intensity = np.clip(lymph_intensity, 0.0, 1.0)

    return lymph_mask, lymph_intensity


def resolve_flat_areas(elevation: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """
    Разрешает плоские области добавлением малого шума.

    В плоских зонах D8 не может определить направление потока.
    Добавление микроскопического шума решает проблему.

    Args:
        elevation: Оригинальная карта высот
        rng: Random generator для детерминизма

    Returns:
        perturbed_elevation: Карта с добавленным микрошумом
    """
    # Добавляем очень малый шум (1e-6 от диапазона)
    noise_amplitude = 1e-6
    noise = rng.random(elevation.shape) * noise_amplitude

    perturbed = elevation + noise
    return perturbed.astype(np.float32)


if __name__ == "__main__":
    # Простой тест
    print("=== D8 Flow Accumulation Test ===")

    # Создаём простой рельеф: наклон слева-направо
    test_elevation = np.tile(np.linspace(1.0, 0.0, 10), (10, 1))

    print("Test elevation shape:", test_elevation.shape)
    print("Test elevation range:", test_elevation.min(), "-", test_elevation.max())

    # Вычисляем flow direction
    flow_dir = calculate_flow_direction(test_elevation)
    print("\nFlow directions calculated")
    print("Unique direction codes:", np.unique(flow_dir))

    # Вычисляем flow accumulation
    flow_accum = calculate_flow_accumulation(test_elevation, flow_dir)
    print("\nFlow accumulation calculated")
    print("Accumulation range:", flow_accum.min(), "-", flow_accum.max())
    print("Max accumulation at:", np.unravel_index(flow_accum.argmax(), flow_accum.shape))

    # Проверяем: правая колонка должна иметь высокую аккумуляцию
    print("\nRight column accumulation (should be high):")
    print(flow_accum[:, -1])

    print("\n[OK] Basic test passed!")
