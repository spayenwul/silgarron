"""
Data models for world generation v2.0 (ADR-020)
Sprint 3.6: Continent and Organs - Global Skeletons
"""

from dataclasses import dataclass, field
from typing import Tuple, Dict, Optional, List
import numpy as np


@dataclass
class Organ:
    """Анатомический орган мира-организма"""
    id: str
    type: str  # 'metabolic_organ', 'digestive', 'neural_cluster', 'immune_node'
    position: Tuple[int, int]  # Координаты на карте 512×512
    radius: float  # Радиус влияния

    # Специфичные параметры
    temperature: Optional[float] = None  # Для метаболических органов
    nutrient_output: Optional[float] = None
    acid_level: Optional[float] = None  # Для желудка
    control_strength: Optional[float] = None  # Для ганглиев
    cell_production: Optional[float] = None  # Для лимфоузлов

    def __post_init__(self):
        """Валидация после создания"""
        if self.radius <= 0:
            raise ValueError(f"Organ {self.id}: radius must be positive")
        if not (0 <= self.position[0] < 512 and 0 <= self.position[1] < 512):
            raise ValueError(f"Organ {self.id}: position out of bounds")


@dataclass
class Region:
    """Анатомический регион (торакс, органоид, и т.д.)"""
    id: str
    name: str  # 'THORAX', 'DIAPHRAGM', 'ORGANOID', 'GRASPING_LIMB'
    mask: np.ndarray  # (512, 512) boolean mask
    characteristics: Dict[str, float] = field(default_factory=dict)
    # characteristics = {
    #     'elevation_bias': +0.3,
    #     'bone_density': 0.8,
    #     'respiratory_potential': 0.9
    # }

    def __post_init__(self):
        """Валидация после создания"""
        if self.mask.shape != (512, 512):
            raise ValueError(f"Region {self.id}: mask must be 512x512")
        if self.mask.dtype != bool:
            raise ValueError(f"Region {self.id}: mask must be boolean")


@dataclass
class RibData:
    """
    Данные одного ребра (rib) в анатомической структуре континента.

    Рёбра генерируются перпендикулярно позвоночнику и создают:
    - Гребни на ландшафте (heightmap influence)
    - Зоны размещения органов (intercostal zones)
    - Гидрологические барьеры (watersheds)
    """
    side: int  # -1 (left) or 1 (right)
    vertebra_index: int  # Индекс позвонка, от которого отходит ребро
    path: np.ndarray  # (N, 2) array - Bezier curve points вдоль ребра
    length: float  # Длина ребра в пикселях

    def __post_init__(self):
        """Валидация после создания"""
        if self.side not in [-1, 1]:
            raise ValueError(f"Rib side must be -1 (left) or 1 (right), got {self.side}")
        if self.path.ndim != 2 or self.path.shape[1] != 2:
            raise ValueError(f"Rib path must be (N, 2) array, got shape {self.path.shape}")
        if self.length <= 0:
            raise ValueError(f"Rib length must be positive, got {self.length}")


@dataclass
class ContinentData:
    """Данные континента"""
    mask: np.ndarray  # (512, 512) boolean - где суша
    heightmap: np.ndarray  # (512, 512) float [0, 1] - базовый рельеф
    center: Tuple[int, int]  # Центр масс континента
    major_axis: Tuple[Tuple[int, int], Tuple[int, int]]  # Начало и конец оси
    spine_path: Optional[np.ndarray] = None  # (N, 2) array - позвоночник (если используется spine mask)
    control_points: Optional[np.ndarray] = None
    ribs: List['RibData'] = field(default_factory=list)  # NEW: список рёбер

    def __post_init__(self):
        """Валидация"""
        if self.mask.shape != (512, 512) or self.heightmap.shape != (512, 512):
            raise ValueError("Continent data must be 512x512")

        # Валидация spine_path (если есть)
        if self.spine_path is not None:
            if self.spine_path.ndim != 2 or self.spine_path.shape[1] != 2:
                raise ValueError("spine_path must be (N, 2) array of coordinates")


@dataclass
class World:
    """Расширенная модель мира с континентом и органами"""
    seed: str
    world_phase: str  # 'EXHALE' или 'INHALE'
    age: str  # 'EARLY_EXHALE', 'LATE_EXHALE', и т.д.
    global_size: Tuple[int, int] = (512, 512)

    # НОВОЕ: континент и анатомия
    continent: Optional[ContinentData] = None
    organs: Dict[str, Organ] = field(default_factory=dict)
    regions: Dict[str, Region] = field(default_factory=dict)

    # Существующие поля (пока None, заполним в следующих спринтах)
    elevation: Optional[np.ndarray] = None
    temperature: Optional[np.ndarray] = None
    moisture: Optional[np.ndarray] = None
    tissue_map: Optional[np.ndarray] = None
