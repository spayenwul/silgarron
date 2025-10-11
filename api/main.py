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
from services.event_store import EventStore
from game import Game

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

# WebSocket connections storage
from typing import Dict
active_websockets: Dict[str, WebSocket] = {}

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
    """
    WebSocket endpoint для real-time обновлений.

    Сообщения от сервера:
    - initial_state: начальное состояние при подключении
    - body_update: обновление состояния тела
    - action_result: результат действия
    - narrative: новый текст нарратива

    Сообщения от клиента:
    - command: текстовая команда игрока
    - ping: keepalive
    """
    await websocket.accept()
    active_websockets[session_id] = websocket
    print(f"[WS] Client connected: {session_id}")

    try:
        # Проверить сессию
        try:
            session = get_session(session_id)
        except:
            await websocket.send_json({"type": "error", "message": "Session not found"})
            await websocket.close(code=1008)
            return

        # Отправить начальное состояние
        await websocket.send_json({
            "type": "initial_state",
            "data": session.get_full_state()
        })

        # Основной цикл обработки сообщений
        while True:
            # Получить сообщение от клиента
            raw_message = await websocket.receive_text()

            try:
                message = eval(raw_message)  # или json.loads(raw_message)

                if message.get("type") == "command":
                    # Обработать команду игрока
                    command = message.get("command", "")
                    result = session.perform_action(command)

                    # Отправить результат
                    await websocket.send_json({
                        "type": "action_result",
                        "data": result
                    })

                    # Если у игрока есть body system, отправить обновление
                    if hasattr(session.game.player, 'body') and session.game.player.body:
                        body_data = {
                            "blood_volume": session.game.player.body.blood_volume,
                            "consciousness": session.game.player.body.consciousness,
                            "is_dead": session.game.player.body.is_dead(),
                        }

                        await websocket.send_json({
                            "type": "body_update",
                            "data": body_data
                        })

                elif message.get("type") == "ping":
                    # Keepalive response
                    await websocket.send_json({"type": "pong"})

            except Exception as e:
                print(f"[WS] Error processing message: {e}")
                await websocket.send_json({"type": "error", "message": str(e)})

    except WebSocketDisconnect:
        print(f"[WS] Client disconnected: {session_id}")
        active_websockets.pop(session_id, None)
    except Exception as e:
        print(f"[WS] Error: {e}")
        active_websockets.pop(session_id, None)
        try:
            await websocket.close(code=1011)
        except:
            pass

# --- 7. Event Sourcing эндпоинты ---
@app.post("/game/load_from_events", summary="Загрузить игру из событий (Event Sourcing)")
async def load_game_from_events(session_id: str):
    """
    Загрузить игру через Event Sourcing - восстановление состояния из событий.
    """
    try:
        game_instance = Game.load_from_events(
            session_id=session_id,
            world_data_service=world_data,
            tag_registry_service=tag_registry,
            memory_service=memory
        )

        return {
            "session_id": session_id,
            "player_name": game_instance.player.name if game_instance.player else "Unknown",
            "current_location": game_instance.current_location.name if game_instance.current_location else "Unknown",
            "state": game_instance.state.name,
            "message": "Игра успешно загружена из событий"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки: {str(e)}")

@app.get("/game/{session_id}/events", summary="Получить историю событий сессии")
async def get_session_events(session_id: str):
    """
    Получить все события для конкретной сессии (для отладки и анализа).
    """
    event_store = EventStore()
    events = event_store.get_events(session_id)

    if not events:
        raise HTTPException(status_code=404, detail="Session not found or has no events")

    return {
        "session_id": session_id,
        "total_events": len(events),
        "events": [
            {
                "type": e.__class__.__name__,
                "timestamp": e.timestamp.isoformat(),
                "event_id": e.event_id,
                "data": {k: v for k, v in e.__dict__.items() if k not in ['event_id', 'timestamp', 'session_id']}
            }
            for e in events
        ]
    }


# --- 8. Body System Endpoints ---

@app.get("/game/{session_id}/character/body", summary="Получить состояние тела персонажа")
async def get_body_state(session: GameSession = Depends(get_session)):
    """
    Получить детальное состояние тела персонажа.

    Используется для:
    - Body visualizer в UI
    - Индикаторы крови и сознания
    - Отладки боевой системы
    """
    player = session.game.player

    if not hasattr(player, 'body') or player.body is None:
        raise HTTPException(status_code=400, detail="Player does not have body system")

    body = player.body

    return {
        "blood_volume": body.blood_volume,
        "max_blood_volume": body.max_blood_volume,
        "blood_percentage": body.blood_volume / body.max_blood_volume,
        "consciousness": body.consciousness,
        "is_unconscious": body.is_unconscious(),
        "is_dead": body.is_dead(),

        "parts": {
            part_name: {
                "name": part_name,
                "integrity": part.integrity,
                "functional": part.functional,
                "wounds_count": len(part.wounds),
                "total_bleeding": part.get_total_bleeding(),
                "pain_level": part.get_pain_level(),
                "armor": part.armor,
            }
            for part_name, part in body.parts.items()
        },

        "status_effects": [
            {
                "type": effect.type.value,
                "severity": effect.severity,
                "duration_remaining": effect.duration_remaining,
                "source": effect.source,
            }
            for effect in body.status_effects
        ],

        "instant_death": body.instant_death,
        "instant_death_reason": body.instant_death_reason,
    }


@app.get("/game/{session_id}/wounds", summary="Получить список всех активных ран")
async def get_wounds(session: GameSession = Depends(get_session)):
    """
    Получить детальный список всех ран на теле персонажа.

    Для детального отображения в UI.
    """
    player = session.game.player

    if not hasattr(player, 'body') or player.body is None:
        return {"wounds": [], "total_wounds": 0, "total_bleeding_rate": 0.0}

    wounds = []

    for part_name, part in player.body.parts.items():
        for wound in part.wounds:
            # Расчет прогресса свертывания
            clotting_progress = part.clotting_progress.get(id(wound), 0.0)

            wounds.append({
                "body_part": part_name,
                "type": wound.type.value,
                "depth_cm": wound.depth_cm,
                "bleeding_rate": wound.bleeding_rate_ml_per_sec,
                "bleeding_rate_current": wound.bleeding_rate_ml_per_sec * (1.0 - clotting_progress),
                "tissues_damaged": wound.tissues_damaged,
                "pain_level": wound.pain_level,
                "created_at_turn": wound.created_at_turn,
                "clotting_progress": clotting_progress,
            })

    return {
        "wounds": wounds,
        "total_wounds": len(wounds),
        "total_bleeding_rate": sum(w["bleeding_rate_current"] for w in wounds),
    }


class TickRequest(BaseModel):
    delta_turns: int = 1


@app.post("/game/{session_id}/character/tick", summary="Обновить состояние персонажа")
async def tick_character(
    request: TickRequest,
    session: GameSession = Depends(get_session)
):
    """
    Принудительно обновить физиологическое состояние персонажа.

    Используется для:
    - Отдыха/ожидания (пропуск времени)
    - Тестирования кровотечения
    - Проверки свертывания
    """
    player = session.game.player

    if not hasattr(player, 'body') or player.body is None:
        raise HTTPException(status_code=400, detail="Player does not have body system")

    player.body.tick(request.delta_turns)
    session.save()

    return await get_body_state(session)


@app.get("/health", summary="Health check", tags=["System"])
async def health_check():
    """Health check для мониторинга"""
    return {"status": "healthy", "version": "3.2"}