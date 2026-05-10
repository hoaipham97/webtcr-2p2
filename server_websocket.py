import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

clients = {}


@app.get("/")
def home():
    return {"status": "ok"}


@app.websocket("/ws/{role}")
async def websocket_endpoint(websocket: WebSocket, role: str):
    await websocket.accept()
    clients[role] = websocket
    print(f"{role} connected")

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)

            target = data.get("target")
            if target in clients:
                await clients[target].send_text(json.dumps(data))
            else:
                print(f"Target {target} not connected")

    except WebSocketDisconnect:
        print(f"{role} disconnected")
        if clients.get(role) == websocket:
            del clients[role]