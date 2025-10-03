# api/game_session.py (ЗАВЕРШЕННАЯ ВЕРСЯ)
from typing import Optional, Dict, List
import uuid
import random

from game import Game
from services.world_graph_service import WorldGraph
from services.persistence_service import PersistenceService
from generators.spatial_location_generator import SpatialLocationGenerator
from models.location import Location
from models.character import Character
from services.llm_service import generate_location_description

class GameSession:
    """
    Инкапсулирует всю логику игровой сессии.
    API-эндпоинты только вызывают методы этого класса.
    """
    
    def __init__(
        self,
        session_id: str,
        persistence: PersistenceService,
        world_data, tag_registry, memory
    ):
        self.session_id = session_id
        self.persistence = persistence
        self.world_data = world_data
        self.tag_registry = tag_registry
        self.memory = memory
        # Эти компоненты будут загружены или созданы заново
        self.game: Optional[Game] = None
        self.world_graph: Optional[WorldGraph] = None
        self.spatial_generator: Optional[SpatialLocationGenerator] = None
        self.current_location_id: Optional[str] = None
    
    # === МЕТОДЫ-ФАСАДЫ (публичный API класса) ===
    
    def move_player_to(self, target_location_id: str) -> Dict:
        """ЕДИНАЯ точка для всей логики перемещения."""
        # 1. Проверка доступности
        neighbors = self.world_graph.get_neighbors(self.current_location_id)
        if not any(n['id'] == target_location_id for n in neighbors):
            return {"success": False, "message": "Эта локация недоступна отсюда."}
        
        # 2. Проверка условий перехода
        edge_data = self.world_graph.graph.edges[self.current_location_id, target_location_id]
        if condition := edge_data.get('condition'):
            if not self._check_condition(condition):
                return {"success": False, "message": f"Проход заблокирован. Требуется: {condition}"}

        # 3. Перемещение
        self.current_location_id = target_location_id
        self.world_graph.mark_visited(target_location_id)
        
        # 4. Обновление текущей локации в игре
        location_data = self.world_graph.graph.nodes[target_location_id]
        self.game.current_location = Location.from_dict(location_data)
        
        # 5. Генерация описания (если ещё нет)
        if not location_data.get('description'):
            context = self.game._get_layered_context(f"описание {location_data['name']}")
            description = generate_location_description(tags=location_data.get('tags', []), context=context)
            self.game.current_location.description = description
            self.world_graph.graph.nodes[target_location_id]['description'] = description
        
        # 6. Расширение мира (30% шанс)
        new_locations = self.spatial_generator.expand_from_location(target_location_id) if random.random() < 0.3 else []
        
        self._save_session()
        
        return {
            "success": True,
            "message": f"Вы переместились в: {self.game.current_location.name}",
            "current_location": self.game.current_location.to_dict(),
            "player": self.game.player.to_dict(), # Добавляем игрока
            "world_graph": self.get_discovered_world() # Добавляем карту
        }
    
    def perform_action(self, command: str) -> Dict:
        """Выполняет игровую команду и возвращает результат."""
        narrative = self.game.process_player_command(command)
        self._save_session()
        
        return {
            "narrative": narrative,
            "player": self.game.player.to_dict(),
            "current_location": self.game.current_location.to_dict(),
            "game_state": self.game.state.name,
            "world_graph": self.get_discovered_world() # Добавляем карту
        }
    
    def explore_boundaries(self) -> Dict:
        """
        Генерирует новые локации и ВОЗВРАЩАЕТ ПОЛНУЮ ОБНОВЛЕННУЮ КАРТУ.
        """
        new_locations = self.spatial_generator.expand_from_location(
            self.current_location_id
        )
        
        # Сохраняем сессию с новыми локациями
        self._save_session()
        
        # --- ИЗМЕНЕНИЕ ЗДЕСЬ ---
        # Вместо простого сообщения, возвращаем объект с сообщением И обновленным графом
        return {
            "success": True,
            "message": f"Вы обнаружили {len(new_locations)} новых локаций!",
            "world_graph": self.get_discovered_world() # <--- Возвращаем результат вызова этого метода
        }
    
    # === Методы управления состоянием сессии ===
    
    def initialize_new_game(self, player_name: str, starting_continent: str = "torax"):
        """
        Создаёт все компоненты для новой игры, выбирая случайный регион на континенте.
        """
        self.game = Game(self.world_data, self.tag_registry, self.memory)
        self.game.player = Character(name=player_name)
        
        self.world_graph = WorldGraph(self.session_id)
        self.spatial_generator = SpatialLocationGenerator(
            self.world_graph, self.game.world_data, self.game.tag_registry
        )
        
        possible_regions = self.game.world_data.get_region_types_for_continent(starting_continent)
        if not possible_regions:
            raise ValueError(f"Для континента '{starting_continent}' не найдено регионов в world_anatomy.yaml!")
        
        start_region_data = random.choice(possible_regions)
        start_region_id = start_region_data['id']
        print(f"🌍 Мир генерируется... Выбран стартовый регион: '{start_region_data['name']}' ({start_region_id})")

        start_location_id = self.spatial_generator.generate_starting_region(region_type=start_region_id)
        
        self.current_location_id = start_location_id
        
        location_data = self.world_graph.graph.nodes[start_location_id]
        self.game.current_location = Location.from_dict(location_data)
        
        description = generate_location_description(tags=location_data.get('tags', []), context=[])
        self.game.current_location.description = description
        self.world_graph.graph.nodes[start_location_id]['description'] = description
        
        self._save_session()
    
    def get_full_state(self) -> Dict:
        """Возвращает полное состояние сессии для UI."""
        return {
            "session_id": self.session_id,
            "current_location": self.game.current_location.to_dict(),
            "player": self.game.player.to_dict(),
            "world_graph": self.get_discovered_world()
        }

    def get_discovered_world(self) -> Dict:
        """Возвращает только открытые части мира (для UI)."""
        graph_data = self.world_graph.to_dict()
        
        discovered_nodes = [{"id": node_id, **node_data} for node_id, node_data in graph_data['nodes'].items() if node_data.get('discovered', False)]
        discovered_node_ids = {node['id'] for node in discovered_nodes}
        
        discovered_edges = [edge for edge in graph_data['edges'] if edge['from'] in discovered_node_ids and edge['to'] in discovered_node_ids and edge['data'].get('discovered', False)]
        
        return {
            "nodes": discovered_nodes,
            "edges": discovered_edges,
            "current_location_id": self.current_location_id
        }

    def _save_session(self):
        """Сохраняет полное состояние сессии в хранилище."""
        full_session_data = {
            "session_id": self.session_id,
            "current_location_id": self.current_location_id,
            "game_state": self.game.to_dict(),
            "world_graph_state": self.world_graph.to_dict()
        }
        self.persistence.save_game_state(self.session_id, full_session_data)

    @classmethod
    def load_session(cls, session_id: str, persistence: PersistenceService, world_data, tag_registry, memory):
        """Загружает сессию из хранилища."""
        session_data = persistence.load_game_state(session_id)
        if not session_data:
            return None
        
        instance = cls(session_id, persistence, world_data, tag_registry, memory)
        instance.current_location_id = session_data["current_location_id"]
        
        # Восстанавливаем игру
        instance.game = Game(world_data, tag_registry, memory)
        instance.game.load_from_dict(session_data["game_state"])
        
        # Восстанавливаем граф
        instance.world_graph = WorldGraph.from_dict(session_data["world_graph_state"])
        
        # Восстанавливаем генератор
        instance.spatial_generator = SpatialLocationGenerator(
            instance.world_graph, instance.game.world_data, instance.game.tag_registry
        )
        
        return instance

    def _check_condition(self, condition: str) -> bool:
        """Проверяет условия для действий (например, наличие ключа)."""
        if ":" in condition:
            cond_type, cond_value = condition.split(":", 1)
            if cond_type == "has_item":
                return self.game.player.inventory.has_item(cond_value)
        return False