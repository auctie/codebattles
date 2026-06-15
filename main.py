import judge0
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import json
from database import Database
import random

app = FastAPI()
db = Database()

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

rooms = {}

async def send_json(websocket: WebSocket, message: dict):
    return websocket.send_text(json.dumps(message))

@app.get("/")
async def welcome():
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/api/user-name")
async def get_user_data():
    with open('prefix.txt', 'r', encoding='utf-8') as f:
        prefix = [item.strip() for item in f]
    with open('suffix.txt', 'r', encoding='utf-8') as f:
        suffix = [item.strip() for item in f]
    return {"name" : random.choice(prefix) + random.choice(suffix)}

@app.get("/battle/{room_id}")
async def battle_page(room_id: str):
    return FileResponse(STATIC_DIR / "battle.html")

@app.post("/execute")
async def execute_code(request: Request):
    try:
        data = await request.json()
        code = data.get("code", "")
        if not code.strip():
            return {"output": "No code provided."}

        result = judge0.run(
            source_code=code,
            stdin="",
            language=judge0.PYTHON
        )
        output = result.stdout or result.stderr or "No output."
        return {"output": output}
    except Exception as e:
        return {"output": f"Execution error: {str(e)}"}

active_players = {}

@app.websocket("/ws/lobby")
async def lobby_websocket(websocket: WebSocket):
    await websocket.accept()

    player_name = websocket.query_params.get("name", "default")
    player_id = websocket.query_params.get("id", "default")

    active_players[player_id] = {"name": player_name, "id": player_id, "ws": websocket}

    players_list = [{"id": info["id"], "name": info["name"]} for pid, info in active_players.items() if player_id]
    await send_json(websocket, {"type": "online_list", "players": players_list})

    for pid, info in active_players.items():
        if pid != player_id:
            await send_json(info['ws'], {"type": "player_joined", "player": {"name": player_name, "id": player_id}})

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        del active_players[player_id]
        for pid, info in active_players.items():
            await send_json(info['ws'], {"type": "player_left", "player": {"name": player_name, "id": player_id}})


@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await websocket.accept()

    if room_id not in rooms:
        rooms[room_id] = []

    if len(rooms[room_id]) >= 2:
        await send_json(websocket, {
            "type": "error",
            "message": "Room is full. Only 2 players allowed."
        })
        await websocket.close(code=1008)
        return

    rooms[room_id].append(websocket)

    if len(rooms[room_id]) == 2:
        for conn in rooms[room_id]:
            await send_json(conn, {
                "type": "opponent_joined",
                "message": "Both players are ready! Start coding.",
                "content": db.choose_random(5)
            })

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await send_json(websocket, {
                    "type": "error",
                    "message": "Invalid JSON"
                })
                continue

            msg_type = msg.get("type")
            if msg_type == "update_code":
                content = msg.get("content", "")
                for conn in rooms[room_id]:
                    if conn != websocket:
                        await send_json(conn, {
                            "type": "update_code",
                            "content": content
                        })
            elif msg_type == "ping":
                await send_json(websocket, {"type": "pong"})
            else:
                await send_json(websocket, {
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}"
                })

    except WebSocketDisconnect:
        if websocket in rooms[room_id]:
            rooms[room_id].remove(websocket)
        if not rooms[room_id]:
            del rooms[room_id]
        else:
            remaining = rooms[room_id][0]
            await send_json(remaining, {
                "type": "opponent_left",
                "message": "Your opponent disconnected. Battle ended."
            })
