# api/game_session.py (УЛУЧШЕННАЯ ВЕРСИЯ)
from typing import Optional, Dict, List
from game import Game
from services.hex_world_service import HexWorldService
from services.config_loader import WorldGenerationConfig
from services.persistence_service import PersistenceService
from services.compatibility_service import CompatibilityService
from models.location import Location
from models.character import Character
from services.llm_service import generate_location_description
import yaml
from pathlib import Path

class GameSession:
    def __init__(
        self, session_id: str, persistence: PersistenceService,
        world_data, tag_registry, memory, config: WorldGenerationConfig = None
    ):
        self.session_id = session_id
        self.persistence = persistence
        self.world_data = world_data
        self.tag_registry = tag_registry
        self.memory = memory
        self.config = config or WorldGenerationConfig()
        
        self.game: Optional[Game] = None
        self.hex_world: Optional[HexWorldService] = None
        self.current_biome_id: Optional[str] = None
    
    @property
    def current_region_id(self) -> Optional[str]:
        """Получает ID текущего региона из текущего биома."""
        if self.current_biome_id and self.current_biome_id in self.hex_world.biomes:
            return self.hex_world.biomes[self.current_biome_id].parent_region_id
        return None

    def move_player_to(self, target_biome_id: str) -> Dict:
        if not (self.hex_world and self._validate_biome_exists(target_biome_id)):
            return {"success": False, "message": f"Биом {target_biome_id} не существует."}
        
        accessible = self.hex_world.get_accessible_biomes(self.current_biome_id)
        if not any(b['id'] == target_biome_id for b in accessible):
            return {"success": False, "message": "Этот биом недоступен отсюда."}
        
        self.current_biome_id = target_biome_id
        self.hex_world.mark_biome_visited(target_biome_id)
        
        biome_data = self.hex_world.biomes[target_biome_id]
        self.game.current_location = self._create_location_view(biome_data)
        
        if not biome_data.description:
            biome_data.description = self._generate_biome_description(biome_data)
            self.game.current_location.description = biome_data.description
        
        self._save_session()
        
        return {
            "success": True, "message": f"Вы переместились в: {biome_data.name}",
            "current_location": self.game.current_location.to_dict(),
            "player": self.game.player.to_dict(),
            "world_graph": self.get_local_map() # <-- ИЗМЕНЕНИЕ: Отдаем локальную карту
        }
    
    def perform_action(self, command: str) -> Dict:
        # ... (без изменений, но теперь возвращает локальную карту)
        narrative = self.game.process_player_command(command)
        self._save_session()
        return {
            "narrative": narrative,
            "player": self.game.player.to_dict(),
            "current_location": self.game.current_location.to_dict(),
            "game_state": self.game.state.name,
            "world_graph": self.get_local_map() # <-- ИЗМЕНЕНИЕ
        }

    def explore_boundaries(self) -> Dict:
        new_biome_ids = self.hex_world.explore_from_biome(self.current_biome_id)
        self._save_session()
        message = f"Вы обнаружили {len(new_biome_ids)} новых биомов в соседних регионах!" if new_biome_ids else "Вы не нашли новых мест. Все соседние регионы уже открыты."
        return {"success": True, "message": message, "world_graph": self.get_world_map()} # <-- ИЗМЕНЕНИЕ: Отдаем глобальную карту

    def initialize_new_game(self, player_name: str, starting_continent: str = "torax"):
        continent_data = self.world_data.get_continent_data(starting_continent)
        if not continent_data:
            raise ValueError(f"Континент '{starting_continent}' не найден")

        self.game = Game(self.world_data, self.tag_registry, self.memory)
        self.game.player = Character(name=player_name)

        # Создаем CompatibilityService с tags_registry и generation_rules
        generation_rules = self._load_generation_rules()
        tags_registry_data = self._load_tags_registry()
        compatibility_service = CompatibilityService(generation_rules, tags_registry_data)

        self.hex_world = HexWorldService(
            self.session_id,
            self.world_data,
            self.tag_registry,
            compatibility_service,
            self.config
        )
        center_region_id = self.hex_world.generate_continent(starting_continent, radius=self.config.default_continent_radius)
        
        center_region = self.hex_world.regions[center_region_id]
        settlement_biome = self._find_settlement_in_region(center_region)
        if not settlement_biome:
            settlement_biome = self.hex_world.biomes[center_region.biome_ids[0]]
        
        self.current_biome_id = settlement_biome.id
        self.hex_world.mark_biome_visited(settlement_biome.id)
        
        self.game.current_location = self._create_location_view(settlement_biome)
        settlement_biome.description = self._generate_biome_description(settlement_biome)
        self.game.current_location.description = settlement_biome.description
        
        self._save_session()
        print(f"✅ Игра инициализирована. Стартовая локация: {settlement_biome.name}")
    
    def get_full_state(self) -> Dict:
        return {
            "session_id": self.session_id,
            "current_location": self.game.current_location.to_dict(),
            "player": self.game.player.to_dict(),
            "world_graph": self.get_local_map() # <-- ИЗМЕНЕНИЕ
        }

    def get_world_map(self) -> Dict:
        """НОВОЕ: Возвращает глобальную карту регионов."""
        return self.hex_world.get_world_map_for_ui()
    
    def get_local_map(self) -> Dict:
        """ИЗМЕНЕНО: Возвращает локальную карту биомов."""
        if not self.current_region_id: return {"nodes": [], "edges": []}
        return self.hex_world.get_local_map_for_ui(self.current_region_id, self.current_biome_id)
    
    # ========== СОХРАНЕНИЕ/ЗАГРУЗКА ==========
    
    def _save_session(self):
        full_session_data = {
            "session_id": self.session_id,
            "current_biome_id": self.current_biome_id,
            "game_state": self.game.to_dict(),
            "hex_world_state": self.hex_world.to_dict()
        }
        self.persistence.save_game_state(self.session_id, full_session_data)

    @classmethod
    def load_session(cls, session_id: str, persistence: PersistenceService, world_data, tag_registry, memory, config: WorldGenerationConfig = None):
        session_data = persistence.load_game_state(session_id)
        if not session_data:
            return None

        instance = cls(session_id, persistence, world_data, tag_registry, memory, config)
        instance.current_biome_id = session_data["current_biome_id"]
        instance.game = Game(world_data, tag_registry, memory)
        instance.game.load_from_dict(session_data["game_state"])

        # Создаем CompatibilityService для загруженной сессии
        generation_rules = instance._load_generation_rules()
        tags_registry_data = instance._load_tags_registry()
        compatibility_service = CompatibilityService(generation_rules, tags_registry_data)

        instance.hex_world = HexWorldService.from_dict(
            session_data["hex_world_state"],
            world_data,
            tag_registry,
            compatibility_service
        )
        return instance
    
    def _validate_biome_exists(self, biome_id: str) -> bool:
        return biome_id in self.hex_world.biomes
    
    def _find_settlement_in_region(self, region) -> Optional[Dict]:
        for biome_id in region.biome_ids:
            biome = self.hex_world.biomes[biome_id]
            if biome.biome_type == "kith_settlement":
                return biome
        return None
    
    def _create_location_view(self, biome_data) -> Location:
        return Location.from_dict({"name": biome_data.name, "description": biome_data.description, "tags": biome_data.tags})
    
    def _generate_biome_description(self, biome_data) -> str:
        try:
            context = self.game._get_layered_context(f"описание {biome_data.name}")
            return generate_location_description(tags=biome_data.tags, context=context)
        except Exception as e:
            print(f"⚠️ Ошибка генерации описания: {e}")
            return f"Вы находитесь в биоме '{biome_data.name}'."
    
    # ========== ПРИВАТНЫЕ УТИЛИТЫ ==========
    
    def _validate_biome_exists(self, biome_id: str) -> bool:
        """Проверяет существование биома"""
        return biome_id in self.hex_world.biomes
    
    def _find_settlement_in_region(self, region) -> Optional:
        """Ищет поселение в регионе"""
        for biome_id in region.biome_ids:
            biome = self.hex_world.biomes[biome_id]
            if biome.biome_type == "kith_settlement":
                return biome
        return None
    
    def _create_location_view(self, biome_data) -> Location:
        """
        НОВОЕ: Создаёт Location как VIEW (представление) биома для Game.
        Game не владеет этим объектом, а только отображает его.
        """
        return Location.from_dict({
            "name": biome_data.name,
            "description": biome_data.description,
            "tags": biome_data.tags
        })
    
    def _generate_biome_description(self, biome_data) -> str:
        """Генерирует описание биома через LLM"""
        try:
            context = self.game._get_layered_context(f"описание {biome_data.name}")
            description = generate_location_description(
                tags=biome_data.tags,
                context=context
            )
            return description
        except Exception as e:
            print(f"⚠️ Ошибка генерации описания: {e}")
            return f"Вы находитесь в биоме '{biome_data.name}'. Здесь царит атмосфера {', '.join(biome_data.tags[:3])}."

    def _load_generation_rules(self) -> Dict:
        """Загружает generation_rules.yaml"""
        rules_path = Path(__file__).parent.parent / "data" / "generation_rules.yaml"
        with open(rules_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _load_tags_registry(self) -> Dict:
        """Загружает tags_registry.yaml"""
        tags_path = Path(__file__).parent.parent / "data" / "tags_registry.yaml"
        with open(tags_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)