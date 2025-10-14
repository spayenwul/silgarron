# services/hex_world_service.py
"""
Центральная служба управления миром с полностью переработанной логикой
для поддержки двухуровневой карты (Регионы -> Биомы).
1. ✅ Биомы теперь имеют свои гексагональные координаты внутри региона.
2. ✅ Разделены методы для получения глобальной и локальной карт.
3. ✅ Убраны пиксельные расчеты для биомов, теперь они часть сетки.
"""

import uuid
import math
import random
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, asdict
from pathlib import Path
import json
from services.config_loader import WorldGenerationConfig
from services.compatibility_service import CompatibilityService
# ==================== МАТЕМАТИКА ГЕКСОВ (Без изменений) ====================

@dataclass
class HexCoord:
    """Кубические координаты гексагональной сетки"""
    q: int
    r: int
    s: int
    
    def __post_init__(self):
        assert self.q + self.r + self.s == 0, f"Invalid hex coordinates: {self.q}, {self.r}, {self.s}"
    
    def __hash__(self):
        return hash((self.q, self.r))
    
    def __eq__(self, other):
        return isinstance(other, HexCoord) and self.q == other.q and self.r == other.r
    
    def __repr__(self):
        return f"HexCoord(q={self.q}, r={self.r})"
    
    @classmethod
    def from_axial(cls, q: int, r: int):
        return cls(q, r, -q - r)
    
    def to_tuple(self) -> Tuple[int, int, int]:
        """Для сериализации"""
        return (self.q, self.r, self.s)
    
    @classmethod
    def from_tuple(cls, data: Tuple[int, int, int]):
        return cls(data[0], data[1], data[2])
    
    @classmethod
    def from_string(cls, coord_str: str):
        q, r = map(int, coord_str.split(','))
        return cls.from_axial(q, r)
    
    def to_string(self) -> str:
        return f"{self.q},{self.r}"
    
    def neighbors(self) -> List['HexCoord']:
        directions = [
            (1, 0, -1), (1, -1, 0), (0, -1, 1),
            (-1, 0, 1), (-1, 1, 0), (0, 1, -1)
        ]
        return [HexCoord(self.q + dq, self.r + dr, self.s + ds) for dq, dr, ds in directions]
    
    def distance_to(self, other: 'HexCoord') -> int:
        return (abs(self.q - other.q) + abs(self.r - other.r) + abs(self.s - other.s)) // 2
    
    def to_pixel(self, hex_size: float = 100) -> Tuple[float, float]:
        x = hex_size * (math.sqrt(3) * self.q + math.sqrt(3) / 2 * self.r)
        y = hex_size * (3 / 2 * self.r)
        return (x, y)


# ==================== МОДЕЛИ ДАННЫХ (Изменены) ====================

@dataclass
class RegionData:
    id: str
    hex_coord: HexCoord
    region_type: str
    name: str
    description: str
    tags: List[str]
    biome_ids: List[str]
    discovered: bool = False
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['hex_coord'] = self.hex_coord.to_tuple()
        return d
    
    @classmethod
    def from_dict(cls, data: dict):
        data['hex_coord'] = HexCoord.from_tuple(data['hex_coord'])
        return cls(**data)


@dataclass
class BiomeData:
    """ИЗМЕНЕНО: Биом теперь имеет hex_coord вместо pixel_position."""
    id: str
    parent_region_id: str
    hex_coord: HexCoord  # <-- ИЗМЕНЕНИЕ: Координата на локальной карте
    biome_type: str
    name: str
    description: str
    tags: List[str]
    location_ids: List[str]
    discovered: bool = False
    visited: bool = False
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['hex_coord'] = self.hex_coord.to_tuple()
        return d
    
    @classmethod
    def from_dict(cls, data: dict):
        data['hex_coord'] = HexCoord.from_tuple(data['hex_coord'])
        return cls(**data)


# ==================== ГЛАВНЫЙ СЕРВИС ====================
class HexWorldService:
    def __init__(self, session_id: str, world_data_service, tag_registry, compatibility_service: CompatibilityService, config: WorldGenerationConfig = None):
        self.session_id = session_id
        self.world_data = world_data_service
        self.tag_registry = tag_registry
        self.compatibility = compatibility_service
        self.config = config or WorldGenerationConfig.from_yaml()
        self.regions: Dict[str, RegionData] = {}
        self.biomes: Dict[str, BiomeData] = {}
        self.hex_to_region: Dict[HexCoord, str] = {}
    
    def generate_continent(self, continent_id: str, radius: int = None) -> str:
        radius = radius or self.config.default_continent_radius
        allowed_types = self.world_data.get_region_types_for_continent(continent_id)
        if not allowed_types: raise ValueError(f"No region types for continent {continent_id}")
        center_hex, center_region_id = HexCoord.from_axial(0, 0), None
        for q in range(-radius, radius + 1):
            for r in range(max(-radius, -q - radius), min(radius, -q + radius) + 1):
                hex_coord = HexCoord.from_axial(q, r)
                region_type_data = random.choice(allowed_types)
                region = self._create_region(hex_coord, region_type_data, continent_id)
                self.regions[region.id], self.hex_to_region[hex_coord] = region, region.id
                if hex_coord == center_hex: center_region_id = region.id
        if center_region_id: self.discover_region(center_region_id)
        return center_region_id
    
    def _create_region(self, hex_coord: HexCoord, region_type_data: dict, continent_id: str) -> RegionData:
        region_id = f"reg_{continent_id}_{hex_coord.q}_{hex_coord.r}"
        return RegionData(id=region_id, hex_coord=hex_coord, region_type=region_type_data['id'], name=region_type_data['name'], description=region_type_data.get('description', ''), tags=region_type_data.get('base_tags', []), biome_ids=[])
    
    def discover_region(self, region_id: str) -> List[str]:
        """
        Генерация биомов внутри региона с использованием CompatibilityService.
        """
        region = self.regions.get(region_id)
        if not region or region.discovered:
            return region.biome_ids if region else []

        region.discovered = True
        target_biome_count = random.randint(self.config.min_biomes_per_region, self.config.max_biomes_per_region)
        
        # Получаем список всех возможных биомов для этого типа региона
        allowed_biome_candidates = self.world_data.get_all_biome_data_for_region(region.region_type)
        if not allowed_biome_candidates:
            return []

        biome_coords = self._generate_local_biome_layout(target_biome_count)
        placed_biomes_map: Dict[HexCoord, Dict] = {}

        for coord in biome_coords:
            # Находим соседей, которые уже размещены
            neighbor_coords = coord.neighbors()
            placed_neighbors_data = [placed_biomes_map[nc] for nc in neighbor_coords if nc in placed_biomes_map]

            # --- ОСНОВНАЯ ЛОГИКА ---
            # Просим сервис совместимости найти лучший биом, учитывая соседей
            best_biome_data = self.compatibility.find_best_biome_for_region(
                allowed_biome_candidates,
                placed_neighbors_data
            )
            # ---------------------

            if best_biome_data:
                biome = self._create_biome(region, best_biome_data['id'], coord)
                self.biomes[biome.id] = biome
                region.biome_ids.append(biome.id)
                placed_biomes_map[coord] = self.world_data.get_biome_data(biome.biome_type)

        return region.biome_ids

        created_biomes = []
        if self.config.guarantee_settlement and "kith_settlement" in allowed_biome_ids and biome_coords:
            center_coord = biome_coords.pop(0)
            settlement = self._create_biome(region, "kith_settlement", center_coord)
            created_biomes.append(settlement)

        for coord in biome_coords:
            if len(created_biomes) >= target_biome_count: break
            potential_types = [b for b in allowed_biome_ids if b != 'kith_settlement']
            if not potential_types: break
            potential_weights = [self.world_data.get_location_weight(b) for b in potential_types]
            chosen_type = random.choices(potential_types, weights=potential_weights, k=1)[0]
            biome = self._create_biome(region, chosen_type, coord)
            created_biomes.append(biome)

        for biome in created_biomes:
            self.biomes[biome.id] = biome
            region.biome_ids.append(biome.id)
        return [b.id for b in created_biomes]

    def _generate_local_biome_layout(self, count: int) -> List[HexCoord]:
        """
        ИСПРАВЛЕНО: Генерирует компактный кластер гексов, а не линию.
        """
        if count == 0: return []
        coords = {HexCoord.from_axial(0, 0)}
        boundary = [HexCoord.from_axial(0, 0)]
        
        while len(coords) < count:
            if not boundary: # На случай, если что-то пойдет не так
                break
            # Выбираем случайный гекс на границе кластера
            hex_to_expand = random.choice(boundary)
            # Ищем его свободных соседей
            free_neighbors = [n for n in hex_to_expand.neighbors() if n not in coords]
            
            if free_neighbors:
                new_hex = random.choice(free_neighbors)
                coords.add(new_hex)
                boundary.append(new_hex)
            else:
                # Если у этого гекса нет свободных соседей, он больше не на границе
                boundary.remove(hex_to_expand)
                
        # Возвращаем центральный гекс первым для поселения
        final_list = list(coords)
        center_hex = HexCoord.from_axial(0,0)
        if center_hex in final_list:
            final_list.remove(center_hex)
            final_list.insert(0, center_hex)
        return final_list[:count]

    def _create_biome(self, region: RegionData, biome_type: str, hex_coord: HexCoord) -> BiomeData:
        biome_id = f"biome_{uuid.uuid4().hex[:8]}"
        biome_data = self.world_data.get_location_type_data(biome_type)
        biome_name = self.world_data.generate_location_name(biome_type)
        return BiomeData(id=biome_id, parent_region_id=region.id, hex_coord=hex_coord, biome_type=biome_type, name=biome_name, description="", tags=biome_data.get('base_tags', []), location_ids=[], discovered=True)
    
    def get_accessible_biomes(self, current_biome_id: str) -> List[Dict]:
        if current_biome_id not in self.biomes: return []
        current_biome, accessible = self.biomes[current_biome_id], []
        neighbor_coords = current_biome.hex_coord.neighbors()
        region = self.regions[current_biome.parent_region_id]
        for biome_id in region.biome_ids:
            biome = self.biomes[biome_id]
            if biome.hex_coord in neighbor_coords:
                accessible.append({"id": biome.id, "name": biome.name, "type": biome.biome_type, "distance": 1, "visited": biome.visited, "locked": False})
        return accessible
    
    def mark_biome_visited(self, biome_id: str):
        if biome_id in self.biomes: self.biomes[biome_id].visited = self.biomes[biome_id].discovered = True
    
    def explore_from_biome(self, current_biome_id: str) -> List[str]:
        if current_biome_id not in self.biomes: return []
        current_region = self.regions[self.biomes[current_biome_id].parent_region_id]
        new_biomes = []
        for hex_coord in current_region.hex_coord.neighbors():
            if hex_coord in self.hex_to_region:
                neighbor_region_id = self.hex_to_region[hex_coord]
                if not self.regions[neighbor_region_id].discovered:
                    new_biomes.extend(self.discover_region(neighbor_region_id))
        return new_biomes

    def get_world_map_for_ui(self) -> Dict:
        nodes, edges = [], []
        discovered_regions = {r_id: r for r_id, r in self.regions.items() if r.discovered}
        for r_id, region in discovered_regions.items():
            nodes.append({"id": r_id, "name": region.name, "type": "region", "position": region.hex_coord.to_pixel(self.config.hex_size * 2.0)})
            for neighbor_coord in region.hex_coord.neighbors():
                neighbor_id = self.hex_to_region.get(neighbor_coord)
                if neighbor_id and neighbor_id in discovered_regions:
                    edges.append({"from": r_id, "to": neighbor_id, "data": {}})
        return {"nodes": nodes, "edges": list({tuple(sorted(e.values())[1:]) for e in edges})} # Remove duplicates

    def get_local_map_for_ui(self, region_id: str, current_biome_id: str) -> Dict:
        if region_id not in self.regions: return {"nodes": [], "edges": []}
        nodes, edges, region = [], [], self.regions[region_id]
        biomes_in_region = {b_id: self.biomes[b_id] for b_id in region.biome_ids}
        for biome_id, biome in biomes_in_region.items():
            nodes.append({"id": biome.id, "name": biome.name, "type": biome.biome_type, "tags": biome.tags, "position": biome.hex_coord.to_pixel(self.config.hex_size * 0.9), "description": biome.description, "visited": biome.visited})
            for neighbor_coord in biome.hex_coord.neighbors():
                for pid, pbiome in biomes_in_region.items():
                    if pbiome.hex_coord == neighbor_coord:
                        edges.append({"from": biome_id, "to": pid, "data": {"distance": 1}}); break
        return {"nodes": nodes, "edges": edges, "current_location_id": current_biome_id}

    def to_dict(self) -> dict: return {"session_id": self.session_id, "regions": {r: d.to_dict() for r, d in self.regions.items()}, "biomes": {b: d.to_dict() for b, d in self.biomes.items()}, "hex_to_region": {h.to_string(): r for h, r in self.hex_to_region.items()}, "config": self.config.to_dict()}
    @classmethod
    def from_dict(cls, data: dict, world_data_service, tag_registry):
        config = WorldGenerationConfig(**data.get("config", {})) if "config" in data else None
        instance = cls(data["session_id"], world_data_service, tag_registry, config)
        instance.regions = {rid: RegionData.from_dict(rdata) for rid, rdata in data["regions"].items()}
        instance.biomes = {bid: BiomeData.from_dict(bdata) for bid, bdata in data["biomes"].items()}
        instance.hex_to_region = {HexCoord.from_string(h_str): r_id for h_str, r_id in data["hex_to_region"].items()}
        return instance

    # ========== ЭКСПОРТ ДЛЯ UI (Изменено) ==========

    def get_world_map_for_ui(self) -> Dict:
        """НОВОЕ: Возвращает граф только для ГЛОБАЛЬНОЙ карты регионов."""
        nodes = []
        edges = []
        
        for r_id, region in self.regions.items():
            if region.discovered:
                nodes.append({
                    "id": r_id, "name": region.name, "type": "region",
                    "position": region.hex_coord.to_pixel(self.config.hex_size * 2.5) # Увеличиваем масштаб
                })
                # Добавляем ребра к соседям
                for neighbor_coord in region.hex_coord.neighbors():
                    if neighbor_coord in self.hex_to_region:
                        neighbor_id = self.hex_to_region[neighbor_coord]
                        if self.regions[neighbor_id].discovered:
                            edges.append({"from": r_id, "to": neighbor_id, "data": {}})
                            
        return {"nodes": nodes, "edges": edges}

    def get_local_map_for_ui(self, region_id: str, current_biome_id: str) -> Dict:
        """ИЗМЕНЕНО: Возвращает граф для ЛОКАЛЬНОЙ карты биомов."""
        if region_id not in self.regions: return {"nodes": [], "edges": []}
        
        nodes = []
        edges = []
        region = self.regions[region_id]
        
        for biome_id in region.biome_ids:
            biome = self.biomes[biome_id]
            nodes.append({
                "id": biome_id, "name": biome.name, "type": biome.biome_type, "tags": biome.tags,
                "position": biome.hex_coord.to_pixel(self.config.hex_size * 0.8), # Уменьшаем масштаб
                "description": biome.description, "visited": biome.visited
            })
            # Добавляем ребра к соседям
            for neighbor_coord in biome.hex_coord.neighbors():
                # Ищем биом с такой координатой в текущем регионе
                for potential_neighbor_id in region.biome_ids:
                    if self.biomes[potential_neighbor_id].hex_coord == neighbor_coord:
                        edges.append({"from": biome_id, "to": potential_neighbor_id, "data": {"distance": 1}})
                        break # нашли соседа, идем к следующему
                        
        return {"nodes": nodes, "edges": edges, "current_location_id": current_biome_id}

    # ========== СОХРАНЕНИЕ/ЗАГРУЗКА (Адаптировано) ==========
    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "regions": {rid: r.to_dict() for rid, r in self.regions.items()},
            "biomes": {bid: b.to_dict() for bid, b in self.biomes.items()},
            "hex_to_region": {hc.to_string(): r_id for hc, r_id in self.hex_to_region.items()},
            "config": self.config.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: dict, world_data_service, tag_registry):
        config = WorldGenerationConfig(**data.get("config", {})) if "config" in data else None
        instance = cls(data["session_id"], world_data_service, tag_registry, config)
        
        instance.regions = {rid: RegionData.from_dict(rdata) for rid, rdata in data["regions"].items()}
        instance.biomes = {bid: BiomeData.from_dict(bdata) for bid, bdata in data["biomes"].items()}
        instance.hex_to_region = {HexCoord.from_string(h_str): r_id for h_str, r_id in data["hex_to_region"].items()}
        
        return instance