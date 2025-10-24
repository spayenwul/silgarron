"""
Perlin Noise Generator - Improved Perlin Noise (2002)

Реализация алгоритма Perlin Noise для процедурной генерации естественного шума.
Используется для создания рельефа, текстур и других "органических" паттернов.

Основано на оригинальном алгоритме Ken Perlin (1983) с улучшениями 2002 года.

См. docs/sprint_3.5_implementation/02_PERLIN_NOISE_EXPLAINED.md для деталей.
"""

import numpy as np
from typing import Optional


class PerlinNoise:
    """
    Генератор Perlin Noise с поддержкой фрактальных октав.

    Использование:
        >>> noise = PerlinNoise(seed=42)
        >>> value = noise.noise_2d(x=0.5, y=0.3)
        >>> map_2d = noise.fractal_noise_2d(width=256, height=256, scale=8, octaves=4)
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Инициализирует генератор Perlin Noise.

        Args:
            seed: Целочисленный seed для детерминированной генерации.
                  Если None, использует np.random (недетерминировано).
        """
        self.permutation = self._generate_permutation_table(seed)

    def _generate_permutation_table(self, seed: Optional[int]) -> np.ndarray:
        """
        Создаёт таблицу перестановок для градиентов.

        Таблица содержит числа 0-255 в случайном порядке, повторённые дважды.
        Это позволяет избежать проверки выхода за границы массива.

        Args:
            seed: Seed для RNG

        Returns:
            np.ndarray размером 512 с перестановкой [0..255] * 2
        """
        if seed is not None:
            rng = np.random.default_rng(seed)
        else:
            rng = np.random

        # Создаём массив 0-255
        p = np.arange(256, dtype=np.int32)

        # Перемешиваем
        rng.shuffle(p)

        # Дублируем для избежания модуло операций
        permutation = np.concatenate([p, p])

        return permutation

    @staticmethod
    def _fade(t: np.ndarray) -> np.ndarray:
        """
        Smoothstep функция для плавной интерполяции.

        Формула: 6t^5 - 15t^4 + 10t^3

        Эта функция даёт S-образную кривую, которая плавно переходит
        от 0 к 1 с нулевыми производными на концах.

        Args:
            t: Значение(я) в диапазоне [0, 1]

        Returns:
            Сглаженное значение(я) в [0, 1]
        """
        return t * t * t * (t * (t * 6 - 15) + 10)

    @staticmethod
    def _lerp(a: np.ndarray, b: np.ndarray, t: np.ndarray) -> np.ndarray:
        """
        Линейная интерполяция между a и b.

        Args:
            a: Начальное значение(я)
            b: Конечное значение(я)
            t: Коэффициент интерполяции [0, 1]

        Returns:
            a + t * (b - a)
        """
        return a + t * (b - a)

    def _gradient(self, hash_val: np.ndarray, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        """
        Вычисляет градиентный вектор и dot product с (x, y).

        Использует 4 возможных градиента: (1,1), (-1,1), (1,-1), (-1,-1)
        Это даёт более равномерное распределение, чем случайные векторы.

        Args:
            hash_val: Хеш значение(я) для выбора градиента
            x: X компонента вектора от узла до точки
            y: Y компонента вектора от узла до точки

        Returns:
            Dot product градиента с вектором (x, y)
        """
        # Берём последние 2 бита для выбора из 4 градиентов
        h = hash_val & 3

        # Используем boolean маски для векторизации
        grad_x = np.where(h & 1, -x, x)
        grad_y = np.where(h & 2, -y, y)

        return grad_x + grad_y

    def noise_2d(self, x: float, y: float) -> float:
        """
        Вычисляет значение Perlin Noise в точке (x, y).

        Args:
            x: X координата (float)
            y: Y координата (float)

        Returns:
            Значение шума в диапазоне примерно [-1, 1]
        """
        # Найти координаты угловых узлов
        xi = int(np.floor(x)) & 255
        yi = int(np.floor(y)) & 255

        # Дробная часть (положение внутри квадрата)
        xf = x - np.floor(x)
        yf = y - np.floor(y)

        # Применить fade function
        u = self._fade(xf)
        v = self._fade(yf)

        # Хеши для 4 углов
        aa = self.permutation[self.permutation[xi]     + yi]
        ab = self.permutation[self.permutation[xi]     + yi + 1]
        ba = self.permutation[self.permutation[xi + 1] + yi]
        bb = self.permutation[self.permutation[xi + 1] + yi + 1]

        # Градиенты в 4 углах
        g1 = self._gradient(aa, xf,     yf)
        g2 = self._gradient(ba, xf - 1, yf)
        g3 = self._gradient(ab, xf,     yf - 1)
        g4 = self._gradient(bb, xf - 1, yf - 1)

        # Билинейная интерполяция
        x1 = self._lerp(g1, g2, u)
        x2 = self._lerp(g3, g4, u)

        return self._lerp(x1, x2, v)

    def noise_2d_vectorized(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        """
        Векторизованная версия noise_2d для массивов координат.

        Это НАМНОГО быстрее, чем вызывать noise_2d() в цикле!
        Для карты 256×256: ~100x ускорение.

        Args:
            x: Массив X координат
            y: Массив Y координат (той же формы, что и x)

        Returns:
            Массив значений шума (та же форма, что и x)
        """
        # Найти координаты угловых узлов
        xi = np.floor(x).astype(int) & 255
        yi = np.floor(y).astype(int) & 255

        # Дробная часть
        xf = x - np.floor(x)
        yf = y - np.floor(y)

        # Применить fade function
        u = self._fade(xf)
        v = self._fade(yf)

        # Хеши для 4 углов (векторизованно)
        aa = self.permutation[self.permutation[xi]     + yi]
        ab = self.permutation[self.permutation[xi]     + yi + 1]
        ba = self.permutation[self.permutation[xi + 1] + yi]
        bb = self.permutation[self.permutation[xi + 1] + yi + 1]

        # Градиенты в 4 углах (векторизованно)
        g1 = self._gradient(aa, xf,     yf)
        g2 = self._gradient(ba, xf - 1, yf)
        g3 = self._gradient(ab, xf,     yf - 1)
        g4 = self._gradient(bb, xf - 1, yf - 1)

        # Билинейная интерполяция (векторизованно)
        x1 = self._lerp(g1, g2, u)
        x2 = self._lerp(g3, g4, u)

        return self._lerp(x1, x2, v)

    def fractal_noise_2d(
        self,
        width: int,
        height: int,
        scale: float = 1.0,
        octaves: int = 4,
        persistence: float = 0.5,
        lacunarity: float = 2.0
    ) -> np.ndarray:
        """
        Генерирует 2D карту фрактального Perlin Noise (сумма октав).

        Комбинирует несколько слоёв Perlin Noise с разной частотой и амплитудой
        для создания детализированного "естественного" рельефа.

        Args:
            width: Ширина результирующего массива
            height: Высота результирующего массива
            scale: Масштаб (zoom). Больше = крупнее фичи.
                   scale=1 → 1 "волна" на карту
                   scale=8 → 8 "волн" на карту
            octaves: Количество слоёв (октав). Больше = детальнее.
                     1 = гладкая поверхность
                     4 = умеренная детализация
                     8 = очень детальная
            persistence: Уменьшение амплитуды каждого слоя (обычно 0.5).
                         Больше = больше влияние мелких деталей.
            lacunarity: Увеличение частоты каждого слоя (обычно 2.0).
                        Больше = быстрее растёт детализация.

        Returns:
            np.ndarray формы (height, width) со значениями в [-1, 1]
        """
        # Создаём сетку координат
        x_coords = np.linspace(0, scale, width, endpoint=False)
        y_coords = np.linspace(0, scale, height, endpoint=False)
        X, Y = np.meshgrid(x_coords, y_coords)

        # Аккумулятор для суммы октав
        total = np.zeros((height, width), dtype=np.float32)

        frequency = 1.0
        amplitude = 1.0
        max_value = 0.0  # Для нормализации

        for octave in range(octaves):
            # Генерируем октаву
            octave_noise = self.noise_2d_vectorized(X * frequency, Y * frequency)

            # Добавляем с текущей амплитудой
            total += octave_noise * amplitude

            # Обновляем для следующей октавы
            max_value += amplitude
            amplitude *= persistence
            frequency *= lacunarity

        # Нормализуем к [-1, 1]
        total = total / max_value

        return total


def generate_perlin_map(
    width: int,
    height: int,
    seed: Optional[int] = None,
    scale: float = 8.0,
    octaves: int = 4,
    persistence: float = 0.5,
    lacunarity: float = 2.0,
    normalize_to_01: bool = True
) -> np.ndarray:
    """
    Удобная функция для быстрой генерации Perlin Noise карты.

    Args:
        width: Ширина карты
        height: Высота карты
        seed: Seed для детерминированной генерации (или None)
        scale: Масштаб "zoom" (больше = крупнее фичи)
        octaves: Количество слоёв детализации
        persistence: Уменьшение амплитуды октав
        lacunarity: Увеличение частоты октав
        normalize_to_01: Если True, преобразует из [-1,1] в [0,1]

    Returns:
        np.ndarray формы (height, width)

    Пример:
        >>> elevation = generate_perlin_map(256, 256, seed=42, scale=8, octaves=4)
        >>> print(f"Min: {elevation.min():.3f}, Max: {elevation.max():.3f}")
        Min: 0.000, Max: 1.000
    """
    noise_gen = PerlinNoise(seed=seed)

    noise_map = noise_gen.fractal_noise_2d(
        width=width,
        height=height,
        scale=scale,
        octaves=octaves,
        persistence=persistence,
        lacunarity=lacunarity
    )

    if normalize_to_01:
        # Преобразуем из [-1, 1] в [0, 1]
        noise_map = (noise_map + 1.0) / 2.0

    return noise_map


if __name__ == "__main__":
    # Простой тест
    import matplotlib.pyplot as plt

    print("=== Perlin Noise Test ===")

    # Генерируем карту
    noise_map = generate_perlin_map(
        width=256,
        height=256,
        seed=42,
        scale=8,
        octaves=4
    )

    print(f"Shape: {noise_map.shape}")
    print(f"Range: [{noise_map.min():.3f}, {noise_map.max():.3f}]")
    print(f"Mean: {noise_map.mean():.3f}")

    # Визуализируем
    plt.figure(figsize=(10, 8))
    plt.imshow(noise_map, cmap='terrain', origin='lower')
    plt.colorbar(label='Elevation')
    plt.title('Perlin Noise Test (seed=42, octaves=4)')
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.savefig('perlin_noise_test.png', dpi=150, bbox_inches='tight')
    print("\nVisualization saved to: perlin_noise_test.png")
