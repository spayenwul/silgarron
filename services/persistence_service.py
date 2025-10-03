# services/persistence_service.py
from pathlib import Path
from typing import Dict, Optional, Any
import json
from abc import ABC, abstractmethod

class PersistenceBackend(ABC):
    """Абстрактный интерфейс для хранилищ."""
    
    @abstractmethod
    def save(self, key: str, data: dict) -> bool:
        pass
    
    @abstractmethod
    def load(self, key: str) -> Optional[dict]:
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        pass
    
    @abstractmethod
    def list_all(self) -> list[str]:
        pass


class FilePersistenceBackend(PersistenceBackend):
    """Хранилище на основе файловой системы."""
    
    def __init__(self, base_path: str = "saves"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
    
    def save(self, key: str, data: dict) -> bool:
        try:
            filepath = self.base_path / f"{key}.json"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения {key}: {e}")
            return False
    
    def load(self, key: str) -> Optional[dict]:
        try:
            filepath = self.base_path / f"{key}.json"
            if not filepath.exists():
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Ошибка загрузки {key}: {e}")
            return None
    
    def exists(self, key: str) -> bool:
        filepath = self.base_path / f"{key}.json"
        return filepath.exists()
    
    def delete(self, key: str) -> bool:
        try:
            filepath = self.base_path / f"{key}.json"
            if filepath.exists():
                filepath.unlink()
            return True
        except Exception as e:
            print(f"❌ Ошибка удаления {key}: {e}")
            return False
    
    def list_all(self) -> list[str]:
        return [f.stem for f in self.base_path.glob("*.json")]


class RedisPersistenceBackend(PersistenceBackend):
    """Хранилище на основе Redis (для production)."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        import redis
        self.client = redis.from_url(redis_url, decode_responses=True)
    
    def save(self, key: str, data: dict) -> bool:
        try:
            self.client.set(key, json.dumps(data, ensure_ascii=False))
            return True
        except Exception as e:
            print(f"❌ Redis save error {key}: {e}")
            return False
    
    def load(self, key: str) -> Optional[dict]:
        try:
            data = self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            print(f"❌ Redis load error {key}: {e}")
            return None
    
    def exists(self, key: str) -> bool:
        return bool(self.client.exists(key))
    
    def delete(self, key: str) -> bool:
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            print(f"❌ Redis delete error {key}: {e}")
            return False
    
    def list_all(self) -> list[str]:
        return [key.decode() for key in self.client.keys("*")]


class PersistenceService:
    """
    Единая точка доступа к сохранению/загрузке данных.
    Поддерживает разные backend'ы (файлы, Redis, БД).
    """
    
    def __init__(self, backend: PersistenceBackend):
        self.backend = backend
    
    # === Методы для WorldGraph ===
    
    def save_world_graph(self, session_id: str, graph_data: dict) -> bool:
        key = f"world_graph_{session_id}"
        return self.backend.save(key, graph_data)
    
    def load_world_graph(self, session_id: str) -> Optional[dict]:
        key = f"world_graph_{session_id}"
        return self.backend.load(key)
    
    def world_graph_exists(self, session_id: str) -> bool:
        key = f"world_graph_{session_id}"
        return self.backend.exists(key)
    
    # === Методы для Game (полное состояние игры) ===
    
    def save_game_state(self, session_id: str, game_data: dict) -> bool:
        key = f"game_state_{session_id}"
        return self.backend.save(key, game_data)
    
    def load_game_state(self, session_id: str) -> Optional[dict]:
        key = f"game_state_{session_id}"
        return self.backend.load(key)
    
    # === Методы для пользовательских сохранений ===
    
    def save_user_game(self, save_name: str, full_data: dict) -> bool:
        """Полное сохранение игры игроком (Save Game)."""
        key = f"user_save_{save_name}"
        return self.backend.save(key, full_data)
    
    def load_user_game(self, save_name: str) -> Optional[dict]:
        key = f"user_save_{save_name}"
        return self.backend.load(key)
    
    def list_user_saves(self) -> list[str]:
        all_keys = self.backend.list_all()
        return [k.replace("user_save_", "") for k in all_keys if k.startswith("user_save_")]
    
    def delete_user_save(self, save_name: str) -> bool:
        key = f"user_save_{save_name}"
        return self.backend.delete(key)


# === Фабрика для создания нужного backend'а ===

def create_persistence_service(backend_type: str = "file") -> PersistenceService:
    """
    Фабричный метод для создания сервиса с нужным backend'ом.
    
    Args:
        backend_type: "file", "redis", "sqlite" (в будущем)
    """
    if backend_type == "file":
        backend = FilePersistenceBackend(base_path="saves")
    elif backend_type == "redis":
        backend = RedisPersistenceBackend(redis_url="redis://localhost:6379")
    else:
        raise ValueError(f"Unknown backend type: {backend_type}")
    
    return PersistenceService(backend)