# services/world_graph_service.py
import networkx as nx
from typing import Dict, List, Tuple, Optional

class WorldGraph:
    """
    ТЕПЕРЬ ТОЛЬКО логика графа — без знания о файлах!
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        # Используем DiGraph, т.к. пути могут быть односторонними (например, прыжок со скалы)
        self.graph = nx.DiGraph() 
    
    def add_location(self, location_id: str, location_data: dict):
        """Добавляет локацию в граф, извлекая позицию из ее паспорта."""
        position = location_data.get("position", (0.0, 0.0))
        self.graph.add_node(location_id, **location_data, visited=False, discovered=False)
    
    def connect_locations(self, from_id: str, to_id: str, distance: float = 1.0, bidirectional: bool = True, **kwargs):
        """Создаёт связь между локациями."""
        self.graph.add_edge(from_id, to_id, distance=distance, discovered=False, **kwargs)
        if bidirectional:
            self.graph.add_edge(to_id, from_id, distance=distance, discovered=False, **kwargs)
    
    def get_neighbors(self, location_id: str) -> List[Dict]:
        """Возвращает список соседних локаций."""
        if not self.graph.has_node(location_id):
            return []
        
        neighbors = []
        for neighbor_id in self.graph.neighbors(location_id):
            node_data = self.graph.nodes[neighbor_id]
            edge_data = self.graph.edges[location_id, neighbor_id]
            neighbors.append({
                "id": neighbor_id,
                "name": node_data.get("name"),
                "type": node_data.get("type"),
                "locked": bool(edge_data.get("condition")),
                **edge_data
            })
        return neighbors

    def mark_visited(self, location_id: str):
        """
        Помечает локацию как посещенную и открывает ее саму и все пути к ней
        для отображения на карте.
        """
        if not self.graph.has_node(location_id):
            print(f"⚠️ Попытка пометить несуществующую локацию как посещенную: {location_id}")
            return

        # Помечаем саму локацию
        self.graph.nodes[location_id]['visited'] = True
        self.graph.nodes[location_id]['discovered'] = True
        
        # Открываем для обзора все соседние локации и пути к ним
        for neighbor_id in self.graph.neighbors(location_id):
            if self.graph.has_node(neighbor_id):
                self.graph.nodes[neighbor_id]['discovered'] = True
                # Открываем только путь ИЗ текущей локации К соседу
                self.graph.edges[location_id, neighbor_id]['discovered'] = True
    
    def to_dict(self) -> dict:
        """Превращает граф в словарь (для сохранения)."""
        return {
            "session_id": self.session_id,
            "nodes": {
                node_id: data 
                for node_id, data in self.graph.nodes(data=True)
            },
            "edges": [
                {
                    "from": u,
                    "to": v,
                    "data": data
                }
                for u, v, data in self.graph.edges(data=True)
            ]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'WorldGraph':
        """Восстанавливает граф из словаря (при загрузке)."""
        instance = cls(data.get("session_id", "unknown"))
        
        # Восстанавливаем узлы
        if "nodes" in data:
            for node_id, node_data in data["nodes"].items():
                instance.graph.add_node(node_id, **node_data)
        
        # Восстанавливаем рёбра
        if "edges" in data:
            for edge in data["edges"]:
                instance.graph.add_edge(edge["from"], edge["to"], **edge["data"])
        
        return instance