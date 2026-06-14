import judge0
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import json

app = FastAPI()

# === Path setup ===
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# === In-memory rooms: room_id -> list of WebSocket connections ===
rooms = {}

# === Helper functions ===
def send_json(websocket: WebSocket, message: dict):
    """Send a JSON message to a WebSocket"""
    return websocket.send_text(json.dumps(message))

# === Routes ===
@app.get("/")
async def welcome():
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/battle/{room_id}")
async def battle_page(room_id: str):
    return FileResponse(STATIC_DIR / "battle.html")

# === Code execution endpoint using Judge0 ===
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

# === WebSocket endpoint with protocol ===
@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await websocket.accept()

    # Create room if not exists
    if room_id not in rooms:
        rooms[room_id] = []

    # Enforce max 2 players
    if len(rooms[room_id]) >= 2:
        await send_json(websocket, {
            "type": "error",
            "message": "Room is full. Only 2 players allowed."
        })
        await websocket.close(code=1008)
        return

    # Add to room
    rooms[room_id].append(websocket)

    # Notify both players when room is ready (2 players)
    if len(rooms[room_id]) == 2:
        for conn in rooms[room_id]:
            await send_json(conn, {
                "type": "opponent_joined",
                "message": "Both players are ready! Start coding."
            })

    try:
        while True:
            raw = await websocket.receive_text()
            # Parse JSON
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await send_json(websocket, {
                    "type": "error",
                    "message": "Invalid JSON"
                })
                continue

            # Validate message type
            msg_type = msg.get("type")
            if msg_type == "update_code":
                content = msg.get("content", "")
                # Forward to the other client in the same room
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
        # Remove disconnected client
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
