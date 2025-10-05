# api/main.py
import uuid
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# Импортируем компоненты проекта
from api.game_session import GameSession
from services.persistence_service import create_persistence_service
from services.world_data_service import WorldDataService
from services.tag_registry_service import TagRegistry
from services.memory_service import MemoryService

# --- 1. СНАЧАЛА создаем экземпляр приложения FastAPI ---
app = FastAPI(title="RPG World API (Refactored)", version="3.2")

# --- 2. ПОТОМ добавляем к нему Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 3. Инициализируем глобальные сервисы ---
print("--- Инициализация глобальных сервисов ---")
world_data = WorldDataService()
tag_registry = TagRegistry()
memory = MemoryService()
persistence = create_persistence_service(backend_type="file")
print("--- Глобальные сервисы готовы ---")

# --- 4. Определяем модели данных для API ---
class StartGameRequest(BaseModel):
    player_name: str
    session_id: Optional[str] = None

class ActionRequest(BaseModel):
    command: str

class MoveRequest(BaseModel):
    target_location_id: str

# --- 5. Определяем "зависимость" для получения сессии ---
def get_session(session_id: str) -> GameSession:
    session = GameSession.load_session(session_id, persistence, world_data, tag_registry, memory)
    if not session:
        raise HTTPException(status_code=404, detail="Game session not found")
    return session

# --- 6. Определяем эндпоинты (маршруты) API ---
@app.post("/game/start", summary="Создать или загрузить игру")
async def start_or_load_game(request: StartGameRequest):
    if request.session_id and persistence.backend.exists(f"game_state_{request.session_id}"):
        session = get_session(request.session_id)
    else:
        session_id = str(uuid.uuid4())
        session = GameSession(session_id, persistence, world_data, tag_registry, memory)
        session.initialize_new_game(request.player_name)
    return session.get_full_state()

@app.get("/game/world_map/{session_id}", summary="Получить глобальную карту мира")
async def get_world_map(session: GameSession = Depends(get_session)):
    return session.get_world_map()

@app.get("/game/local_map/{session_id}", summary="Получить локальную карту текущего региона")
async def get_local_map(session: GameSession = Depends(get_session)):
    return session.get_local_map()

@app.post("/game/action/{session_id}")
async def perform_action(request: ActionRequest, session: GameSession = Depends(get_session)):
    return session.perform_action(request.command)

@app.post("/game/move/{session_id}")
async def move_to_location(request: MoveRequest, session: GameSession = Depends(get_session)):
    result = session.move_player_to(request.target_location_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@app.get("/game/explore/{session_id}")
async def explore_boundaries(session: GameSession = Depends(get_session)):
    return session.explore_boundaries()

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    try:
        session = get_session(session_id)
        if not session:
            await websocket.close(code=1008)
            return
        while True:
            await websocket.receive_text() # Просто поддерживаем соединение
    except WebSocketDisconnect:
        print(f"WebSocket соединение закрыто для сессии: {session_id}")
    except Exception as e:
        print(f"Ошибка в WebSocket: {e}")
        await websocket.close(code=1011)