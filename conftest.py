"""
Pytest configuration and shared fixtures.
This file is automatically discovered by pytest.
"""

import pytest
import sys
from pathlib import Path

# Добавляем корень проекта в sys.path
# чтобы импорты работали из tests/
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# ===================================
# SERVICE FIXTURES
# ===================================

@pytest.fixture
def world_data():
    """WorldDataService fixture"""
    from services.world_data_service import WorldDataService
    return WorldDataService()


@pytest.fixture
def tag_registry():
    """TagRegistry fixture"""
    from services.tag_registry_service import TagRegistry
    return TagRegistry()


@pytest.fixture
def memory():
    """MemoryService fixture"""
    from services.memory_service import MemoryService
    return MemoryService()


# ===================================
# GAME FIXTURES
# ===================================

@pytest.fixture
def game(world_data, tag_registry, memory):
    """Game instance fixture"""
    from game import Game
    return Game(world_data, tag_registry, memory)


@pytest.fixture
def character():
    """Basic character fixture"""
    from models.character import Character
    return Character(name="Test Hero")


@pytest.fixture
def location():
    """Basic location fixture"""
    from models.location import Location
    return Location(passport={
        "name": "Test Location",
        "tags": ["test", "safe"],
        "description": "A test location"
    })


# ===================================
# COMBAT FIXTURES (will be used in Phase 1)
# ===================================

@pytest.fixture
def body_system():
    """BodySystem fixture (Phase 1)"""
    # TODO: Uncomment after Phase 1
    # from combat.body_system import BodySystem
    # return BodySystem()
    pass


@pytest.fixture
def weapon():
    """Basic weapon fixture (Phase 1)"""
    # TODO: Uncomment after Phase 1
    # from models.item import Weapon
    # return Weapon(
    #     name="Test Sword",
    #     description="A test weapon",
    #     weapon_type="sword",
    #     weight_kg=1.0,
    #     length_cm=80.0,
    #     sharpness=0.8,
    #     material="steel",
    #     damage_type="slash"
    # )
    pass


# ===================================
# MOCK FIXTURES
# ===================================

@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing without API calls"""
    def _mock(response_text: str):
        """Returns a function that mocks _send_prompt_to_gemini"""
        def mock_send(request_package):
            return response_text
        return mock_send
    return _mock


# ===================================
# PYTEST HOOKS
# ===================================

def pytest_configure(config):
    """Called before test collection"""
    print("\n[TEST] Pytest configured for AI-Driven RPG")
    print(f"[INFO] Project root: {project_root}")


def pytest_collection_modifyitems(config, items):
    """Called after test collection, before execution"""
    for item in items:
        # Auto-mark slow tests
        if "llm" in item.nodeid.lower() or "simulation" in item.nodeid.lower():
            item.add_marker(pytest.mark.slow)
