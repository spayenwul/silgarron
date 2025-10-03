# api/main.py
import uuid
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# Импортируем наши новые, чистые компоненты
from api.game_session import GameSession
from services.persistence_service import create_persistence_service, PersistenceService
from game import Game
from services.world_data_service import WorldDataService
from services.tag_registry_service import TagRegistry
from services.memory_service import MemoryService

# --- Приложение FastAPI и сервисы ---

app = FastAPI(title="RPG World API (Refactored)", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешает запросы с любого источника (для разработки)
    allow_credentials=True,
    allow_methods=["*"],  # Разрешает все методы (GET, POST, OPTIONS и т.д.)
    allow_headers=["*"],  # Разрешает все заголовки
)

print("--- Инициализация глобальных сервисов ---")
world_data = WorldDataService()
tag_registry = TagRegistry()
memory = MemoryService()
print("--- Глобальные сервисы готовы ---")

# Создаём сервис персистентности ОДИН РАЗ при старте приложения
# В будущем можно читать backend_type из переменных окружения
persistence = create_persistence_service(backend_type="file") 

# --- Модели данных для API (Pydantic) ---

class StartGameRequest(BaseModel):
    player_name: str
    session_id: Optional[str] = None # Позволяет продолжить существующую игру

class ActionRequest(BaseModel):
    command: str

class MoveRequest(BaseModel):
    target_location_id: str

# --- Зависимость (Dependency) для получения сессии ---

def get_session(session_id: str) -> GameSession:
    """
    Эта функция-зависимость FastAPI делает наш API stateless.
    Для каждого запроса она загружает сессию из хранилища.
    Если сессии нет, выбрасывает ошибку 404.
    """
    session = GameSession.load_session(session_id, persistence, world_data, tag_registry, memory)
    if not session:
        raise HTTPException(status_code=404, detail="Game session not found")
    return session
    
# --- Эндпоинты API ---

@app.post("/game/start", summary="Создать или загрузить игру")
async def start_or_load_game(request: StartGameRequest):
    """
    Создаёт новую игру или загружает существующую, если передан session_id.
    """
    if request.session_id and persistence.world_graph_exists(request.session_id):
        # Загружаем существующую сессию
        session = get_session(request.session_id)
    else:
        # Передаем глобальные сервисы при создании новой сессии
        session_id = str(uuid.uuid4())
        session = GameSession(session_id, persistence, world_data, tag_registry, memory)
        session.initialize_new_game(request.player_name)
    return session.get_full_state()

@app.get("/game/world/{session_id}")
async def get_world_graph(session: GameSession = Depends(get_session)):
    """Возвращает текущее состояние открытой карты мира."""
    return session.get_discovered_world()

@app.post("/game/action/{session_id}")
async def perform_action(request: ActionRequest, session: GameSession = Depends(get_session)):
    """Выполняет игровое действие в сессии."""
    return session.perform_action(request.command)

@app.post("/game/move/{session_id}")
async def move_to_location(request: MoveRequest, session: GameSession = Depends(get_session)):
    """Перемещает игрока в сессии."""
    result = session.move_player_to(request.target_location_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@app.get("/game/explore/{session_id}")
async def explore_boundaries(session: GameSession = Depends(get_session)):
    """Расширяет карту мира в сессии."""
    return session.explore_boundaries()

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    
    try:
        # Пытаемся загрузить сессию. Если ее нет, соединение закроется.
        session = get_session(session_id)
        if not session:
            await websocket.close(code=1008)
            return

        while True:
            # Ждем сообщение от клиента (пока не используется, но нужно для поддержания связи)
            data = await websocket.receive_text()
            # Здесь можно добавить логику обработки сообщений от клиента, если понадобится
            # Например, если клиент отправит команду через WebSocket
            # result = session.perform_action(data)
            # await websocket.send_json(result)
            
    except WebSocketDisconnect:
        print(f"WebSocket соединение закрыто для сессии: {session_id}")
    except Exception as e:
        print(f"Ошибка в WebSocket: {e}")
        await websocket.close(code=1011)