# generators/spatial_location_generator.py
import random
import math
import uuid
from typing import List, Tuple

from services.world_graph_service import WorldGraph
from services.world_data_service import WorldDataService
from services.tag_registry_service import TagRegistry

class SpatialLocationGenerator:
    """
    Генерирует локации с учётом пространственной логики,
    используя данные из WorldDataService.
    """
    def __init__(
        self, 
        world_graph: WorldGraph,
        world_data: WorldDataService,
        tag_registry: TagRegistry
    ):
        self.graph = world_graph
        self.world_data = world_data
        self.tag_registry = tag_registry
    
    def generate_starting_region(self, region_type: str) -> str:
        """
        Создаёт стартовый регион из 3-5 связанных локаций.
        Возвращает ID стартовой локации.
        """
        # 1. Генерируем центральную локацию (безопасное место)
        # Мы жестко задаем тип 'kith_settlement', который добавили в compatibility.yaml
        center_id = self._generate_location(
            region_type=region_type,
            location_type="kith_settlement",
            position=(500, 500)
        )
        
        # 2. Генерируем 2-4 соседних биома
        num_neighbors = random.randint(2, 4)
        
        for i in range(num_neighbors):
            angle = (360 / num_neighbors) * i + random.uniform(-10, 10)
            distance = random.uniform(100, 160)
            
            x = 500 + distance * math.cos(math.radians(angle))
            y = 500 + distance * math.sin(math.radians(angle))
            
            # Выбираем биом, разрешенный в этом регионе и совместимый с поселением
            biome_type = self._choose_compatible_biome_type(
                region_type=region_type,
                nearby_types=["kith_settlement"] 
            )
            
            if not biome_type:
                print(f"⚠️ Не удалось найти совместимый биом для старта в регионе {region_type}")
                continue

            neighbor_id = self._generate_location(
                region_type=region_type,
                location_type=biome_type,
                position=(x, y)
            )
            
            self.graph.connect_locations(
                from_id=center_id, 
                to_id=neighbor_id,
                distance=distance
            )
        
        self.graph.mark_visited(center_id)
        return center_id

    def expand_from_location(self, current_location_id: str) -> List[str]:
        """Генерирует новые локации, доступные из текущей."""
        current_node = self.graph.graph.nodes[current_location_id]
        current_type = current_node.get('type')
        current_pos = current_node.get('position', (random.uniform(0,1000), random.uniform(0,1000)))
        
        existing_neighbors = list(self.graph.graph.neighbors(current_location_id))
        max_connections = 4 # Максимум 4 соседа у одной локации
        
        if len(existing_neighbors) >= max_connections:
            return [] # Если соседей уже достаточно, ничего не генерируем
            
        new_locations = []
        # Генерируем от 1 до (максимум - текущее кол-во) соседей
        num_to_generate = random.randint(1, max_connections - len(existing_neighbors))
        
        for _ in range(num_to_generate):
            new_pos = self._generate_nearby_position(current_pos)
            
            new_type = self._choose_compatible_biome_type(
                region_type=current_node.get('region'),
                nearby_types=[current_type] # Новая локация должна быть совместима с текущей
            )
            if not new_type: continue

            new_id = self._generate_location(
                region_type=current_node.get('region'),
                location_type=new_type,
                position=new_pos
            )
            
            self.graph.connect_locations(
                from_id=current_location_id, to_id=new_id,
                distance=math.dist(current_pos, new_pos)
            )

            self.graph.graph.nodes[new_id]['discovered'] = True
            self.graph.graph.edges[current_location_id, new_id]['discovered'] = True

            new_locations.append(new_id)
            
        return new_locations

    def _generate_location(self, region_type: str, location_type: str, position: Tuple[float, float]) -> str:
        """Генерирует одну локацию (биом) и добавляет в граф."""
        location_id = f"loc_{uuid.uuid4().hex[:6]}"
        location_data = self.world_data.get_location_type_data(location_type)
        
        passport = {
            "id": location_id,
            "name": self.world_data.generate_location_name(location_type),
            "type": location_type,
            "tags": location_data.get("base_tags", []),
            "description": "",
            "region": region_type,
            "position": position
        }
        
        # Передаем в add_location сам паспорт целиком, а не отдельные поля
        self.graph.add_location(location_id, passport)
        return location_id

    def _choose_compatible_biome_type(self, region_type: str, nearby_types: List[str]) -> str:
        """Выбирает подходящий БИОМ из вашего лора."""
        allowed_biomes = self.world_data.get_location_types_for_region(region_type)
        if not allowed_biomes:
            print(f"🔥 ОШИБКА: Для региона '{region_type}' не найдено разрешенных биомов в biome_rules!")
            return None

        compatible = [
            biome for biome in allowed_biomes 
            if all(self.world_data.are_locations_compatible(biome, nearby) for nearby in nearby_types)
        ]
        
        if not compatible:
            print(f"⚠️ Не удалось найти биом, совместимый с {nearby_types} в регионе {region_type}")
            return None 
        
        weights = [self.world_data.get_location_weight(b) for b in compatible]
        return random.choices(compatible, weights=weights, k=1)[0]

    def _generate_nearby_position(self, origin: Tuple[float, float]) -> Tuple[float, float]:
        """Генерирует случайную позицию неподалеку."""
        angle = random.uniform(0, 360)
        distance = random.uniform(100, 160)
        x = origin[0] + distance * math.cos(math.radians(angle))
        y = origin[1] + distance * math.sin(math.radians(angle))
        return (x, y)