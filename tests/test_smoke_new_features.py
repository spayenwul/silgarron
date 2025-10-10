# tests/test_smoke_new_features.py
"""
Smoke tests для новой функциональности:
- pydantic-settings (config.py)
- Event Sourcing
- Physical Simulation (заглушки)
- Hex Grid
"""
import pytest
import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import uuid


# ==================== CONFIG TESTS ====================

def test_config_loads_successfully():
    """Smoke test: config.py успешно загружается"""
    from config import settings

    assert settings is not None
    assert hasattr(settings, 'gemini_api_key')
    assert hasattr(settings, 'llm_model')
    assert hasattr(settings, 'saves_dir')
    assert hasattr(settings, 'hex_grid_radius')


def test_config_has_defaults():
    """Smoke test: config.py имеет дефолтные значения"""
    from config import settings

    assert settings.llm_model == "gemini-2.0-flash-exp"  # Обновлено: новая модель
    assert settings.llm_temperature == 0.7
    assert settings.max_short_term_memory == 10
    assert settings.hex_grid_radius == 15


# ==================== EVENT SOURCING TESTS ====================

def test_event_classes_exist():
    """Smoke test: все классы событий определены"""
    from models.events import (
        GameEvent, GameStarted, PlayerMoved,
        PlayerActionExecuted, ItemPickedUp, ItemDropped,
        CombatStarted, CombatEnded, CharacterDamaged,
        MemoryAdded, GameStateSaved, GameStateChanged
    )

    assert GameEvent is not None
    assert GameStarted is not None
    assert PlayerMoved is not None
    assert CombatStarted is not None


def test_event_store_can_create():
    """Smoke test: EventStore может быть создан"""
    from services.event_store import EventStore

    # Используем временную директорию
    with tempfile.TemporaryDirectory() as tmpdir:
        store = EventStore(storage_path=tmpdir)
        assert store is not None
        assert store.storage_path.exists()


def test_event_store_append_and_retrieve():
    """Smoke test: EventStore может записывать и читать события"""
    from services.event_store import EventStore
    from models.events import GameStarted

    with tempfile.TemporaryDirectory() as tmpdir:
        store = EventStore(storage_path=tmpdir)
        session_id = str(uuid.uuid4())

        # Создаём событие
        event = GameStarted(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            session_id=session_id,
            player_name="TestPlayer",
            starting_location_id="test_location"
        )

        # Записываем
        store.append(session_id, event)

        # Читаем
        events = store.get_events(session_id)
        assert len(events) == 1
        assert isinstance(events[0], GameStarted)
        assert events[0].player_name == "TestPlayer"


def test_game_has_event_sourcing_methods():
    """Smoke test: Game класс имеет методы Event Sourcing"""
    from game import Game

    assert hasattr(Game, 'load_from_events')
    assert hasattr(Game, '_emit_event')
    assert hasattr(Game, '_apply_event')


# ==================== PHYSICAL SIMULATION TESTS ====================

def test_physical_simulator_exists():
    """Smoke test: PhysicalSimulator может быть создан"""
    from combat.physical_simulator import PhysicalSimulator, PhysicalResult

    simulator = PhysicalSimulator()
    assert simulator is not None


def test_physical_result_dataclass():
    """Smoke test: PhysicalResult корректно создаётся"""
    from combat.physical_simulator import PhysicalResult

    result = PhysicalResult(
        hit=True,
        narrative="Test attack",
        damage_points=15.0,
        body_part_hit="head"
    )

    assert result.hit is True
    assert result.narrative == "Test attack"
    assert result.damage_points == 15.0
    assert result.body_part_hit == "head"


def test_physical_simulator_simulate_attack():
    """Smoke test: PhysicalSimulator.simulate_attack возвращает результат"""
    from combat.physical_simulator import PhysicalSimulator
    from models.character import Character
    from models.item import Item

    simulator = PhysicalSimulator()

    # Создаём простых персонажей (используем правильный конструктор)
    attacker = Character(name="Attacker", species="human")
    target = Character(name="Target", species="human")
    weapon = Item(name="Sword", description="A sharp sword")

    result = simulator.simulate_attack(attacker, target, weapon, {"body_part": "torso"})

    assert result is not None
    assert result.hit is not None
    assert result.narrative is not None


def test_context_builder_exists():
    """Smoke test: PhysicalContextBuilder может быть создан"""
    from combat.context_builder import PhysicalContextBuilder

    builder = PhysicalContextBuilder()
    assert builder is not None


def test_director_has_simulators():
    """Smoke test: Director имеет физические симуляторы"""
    from logic.director import Director

    director = Director()
    assert hasattr(director, 'physics_simulator')
    assert hasattr(director, 'context_builder')


# ==================== HEX GRID TESTS ====================

def test_hexy_imports():
    """Smoke test: библиотека hexy импортируется"""
    import hexy as hx

    assert hx.HexMap is not None
    assert hx.HexTile is not None
    assert hx.get_disk is not None


def test_hex_grid_service_creates():
    """Smoke test: HexGridService может быть создан"""
    from services.hex_grid_service import HexGridService, HexCell

    service = HexGridService(radius=5)
    assert service is not None
    assert service.radius == 5


def test_hex_grid_initialize():
    """Smoke test: HexGridService может инициализировать карту"""
    from services.hex_grid_service import HexGridService

    service = HexGridService(radius=3)
    service.initialize_empty_grid()

    assert len(service.cells) > 0


def test_hex_grid_basic_operations():
    """Smoke test: базовые операции HexGridService работают"""
    from services.hex_grid_service import HexGridService, HexCell

    service = HexGridService(radius=5)
    service.initialize_empty_grid()

    # Получить ячейку
    cell = service.get_cell(0, 0)
    assert cell is not None

    # Установить ячейку
    new_cell = HexCell(q=1, r=1, terrain_type="mountain")
    service.set_cell(new_cell)
    retrieved = service.get_cell(1, 1)
    assert retrieved.terrain_type == "mountain"

    # Получить соседей
    neighbors = service.get_neighbors(0, 0)
    assert len(neighbors) > 0

    # Рассчитать расстояние
    distance = service.calculate_distance(0, 0, 2, 2)
    assert distance > 0


def test_hex_grid_pathfinding():
    """Smoke test: поиск пути работает"""
    from services.hex_grid_service import HexGridService

    service = HexGridService(radius=10)
    service.initialize_empty_grid()

    path = service.find_path(0, 0, 3, 3)
    assert path is not None
    assert len(path) > 0
    assert path[0] == (0, 0)
    assert path[-1] == (3, 3)


def test_location_has_hex_grid():
    """Smoke test: Location поддерживает hex_grid"""
    from models.location import Location

    location = Location(passport={"name": "Test Location", "tags": ["forest"]})

    assert hasattr(location, 'hex_grid')
    assert hasattr(location, 'initialize_hex_grid')
    assert hasattr(location, 'get_hex_grid')


def test_location_hex_grid_lazy_init():
    """Smoke test: Location.get_hex_grid() создаёт карту при необходимости"""
    from models.location import Location

    location = Location(passport={"name": "Test Location", "tags": ["forest"]})

    assert location.hex_grid is None

    grid = location.get_hex_grid()
    assert grid is not None
    assert location.hex_grid is not None


# ==================== INTEGRATION SMOKE TEST ====================

def test_all_new_modules_import():
    """Smoke test: все новые модули импортируются без ошибок"""
    import config
    import models.events
    import services.event_store
    import combat.physical_simulator
    import combat.context_builder
    import services.hex_grid_service

    assert config is not None
    assert models.events is not None
    assert services.event_store is not None
    assert combat.physical_simulator is not None
    assert combat.context_builder is not None
    assert services.hex_grid_service is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
