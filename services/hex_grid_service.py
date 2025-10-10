# services/hex_grid_service.py
"""
Сервис для работы с гексагональными картами.
Использует библиотеку hexy для математики.

Примечание: hexy использует HexMap и HexTile, а не HexGrid/Hex
"""
from typing import List, Tuple, Optional, Set
from dataclasses import dataclass, field
from config import settings
import hexy as hx
import numpy as np

def _axial_to_cube_single(q: int, r: int) -> np.ndarray:
    """Конвертировать одну axial координату в cube (для hexy API)."""
    axial = np.array([[q, r]])
    cube = hx.axial_to_cube(axial)
    return cube[0]  # Вернуть 1D array

def _cube_to_axial_single(cube: np.ndarray) -> Tuple[int, int]:
    """Конвертировать одну cube координату в axial (для hexy API)."""
    cube_2d = cube.reshape(1, 3)
    axial = hx.cube_to_axial(cube_2d)
    return int(axial[0][0]), int(axial[0][1])

@dataclass
class HexCell:
    """Ячейка на гексагональной карте (axial coordinates)."""
    q: int  # Axial координата q
    r: int  # Axial координата r
    terrain_type: str = "grass"
    is_passable: bool = True
    entities: List[str] = field(default_factory=list)

    @property
    def cube_coords(self) -> Tuple[int, int, int]:
        """Конвертация в cube coordinates для hexy"""
        cube = _axial_to_cube_single(self.q, self.r)
        return tuple(cube)

class HexGridService:
    """
    Сервис для работы с гексагональными картами.
    Использует библиотеку hexy для всей математики.
    """

    def __init__(self, radius: int = None):
        self.radius = radius or settings.hex_grid_radius
        self.cells: dict[Tuple[int, int], HexCell] = {}

    def initialize_empty_grid(self) -> None:
        """Создать пустую гексагональную карту в радиусе."""
        # Используем hexy's get_disk чтобы получить все гексы в радиусе
        # hexy требует cube coordinates (3D numpy array)
        center = np.array([0, 0, 0])
        disk = hx.get_disk(center, self.radius)

        for cube_coords in disk:
            # Конвертируем cube coords обратно в axial
            q, r = _cube_to_axial_single(cube_coords)
            cell = HexCell(q=q, r=r)
            self.cells[(q, r)] = cell

    def get_cell(self, q: int, r: int) -> Optional[HexCell]:
        """Получить ячейку по координатам."""
        return self.cells.get((q, r))

    def set_cell(self, cell: HexCell) -> None:
        """Установить ячейку."""
        self.cells[(cell.q, cell.r)] = cell

    def get_neighbors(self, q: int, r: int) -> List[HexCell]:
        """Получить соседние ячейки."""
        neighbors = []

        # Конвертируем axial в cube для hexy
        cube = _axial_to_cube_single(q, r)

        # hexy использует направления для получения соседей
        for direction in hx.ALL_DIRECTIONS:
            neighbor_cube = hx.get_neighbor(cube, direction)
            neighbor_q, neighbor_r = _cube_to_axial_single(neighbor_cube)
            cell = self.get_cell(neighbor_q, neighbor_r)
            if cell:
                neighbors.append(cell)

        return neighbors

    def calculate_distance(self, q1: int, r1: int, q2: int, r2: int) -> int:
        """Вычислить расстояние между двумя ячейками."""
        cube1 = _axial_to_cube_single(q1, r1)
        cube2 = _axial_to_cube_single(q2, r2)
        return hx.get_cube_distance(cube1, cube2)

    def find_path(
        self,
        start_q: int,
        start_r: int,
        end_q: int,
        end_r: int,
        max_cost: int = 100
    ) -> Optional[List[Tuple[int, int]]]:
        """
        Найти путь между двумя ячейками.

        Примечание: hexy не имеет встроенного A*, используем простую линию
        или можно реализовать A* вручную.

        Returns:
            Список координат (q, r) или None если путь не найден
        """
        # Конвертируем в cube coordinates для hexy
        start_cube = _axial_to_cube_single(start_q, start_r)
        end_cube = _axial_to_cube_single(end_q, end_r)

        # Используем get_hex_line для простого пути
        try:
            path_cube = hx.get_hex_line(start_cube, end_cube)
            # Конвертируем обратно в axial coordinates
            path_axial = []
            for cube_coords in path_cube:
                q, r = _cube_to_axial_single(cube_coords)
                path_axial.append((q, r))
            return path_axial
        except Exception as e:
            print(f"⚠️ Ошибка поиска пути: {e}")
            return None

    def get_hexes_in_radius(
        self,
        center_q: int,
        center_r: int,
        radius: int
    ) -> List[HexCell]:
        """Получить все ячейки в радиусе от центра."""
        # Конвертируем в cube coordinates для hexy
        center_cube = _axial_to_cube_single(center_q, center_r)
        disk = hx.get_disk(center_cube, radius)

        result = []
        for cube_coords in disk:
            q, r = _cube_to_axial_single(cube_coords)
            cell = self.get_cell(q, r)
            if cell:
                result.append(cell)

        return result

    def get_line_of_sight(
        self,
        from_q: int,
        from_r: int,
        to_q: int,
        to_r: int
    ) -> Tuple[bool, List[Tuple[int, int]]]:
        """
        Проверить линию видимости между двумя ячейками.

        Returns:
            (has_line_of_sight, path_coordinates)
        """
        # Конвертируем в cube coordinates для hexy
        start_cube = _axial_to_cube_single(from_q, from_r)
        end_cube = _axial_to_cube_single(to_q, to_r)

        # Получить линию между точками
        try:
            line_cube = hx.get_hex_line(start_cube, end_cube)
        except Exception:
            return False, []

        path_coords = []
        has_los = True

        for cube_coords in line_cube:
            q, r = _cube_to_axial_single(cube_coords)
            path_coords.append((q, r))
            cell = self.get_cell(q, r)

            # Если ячейка непроходима, линия видимости блокирована
            if cell and not cell.is_passable:
                has_los = False
                break

        return has_los, path_coords

    def to_dict(self) -> dict:
        """Сериализация карты."""
        return {
            "radius": self.radius,
            "cells": [
                {
                    "q": cell.q,
                    "r": cell.r,
                    "terrain": cell.terrain_type,
                    "passable": cell.is_passable,
                    "entities": cell.entities
                }
                for cell in self.cells.values()
            ]
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'HexGridService':
        """Десериализация карты."""
        service = cls(radius=data["radius"])

        for cell_data in data["cells"]:
            cell = HexCell(
                q=cell_data["q"],
                r=cell_data["r"],
                terrain_type=cell_data["terrain"],
                is_passable=cell_data["passable"],
                entities=cell_data["entities"]
            )
            service.set_cell(cell)

        return service
