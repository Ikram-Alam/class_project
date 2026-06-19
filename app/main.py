from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from .game import GameSession

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Dungeon Crawler AI", version="1.0.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name="index.html")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    session = GameSession()
    await websocket.send_json({"type": "state", "state": session.state.to_payload()})

    try:
        while True:
            payload = await websocket.receive_json()
            message_type = payload.get("type")

            if message_type == "new_game":
                difficulty = payload.get("difficulty", "medium")
                state = session.reset(difficulty)
                await websocket.send_json({"type": "state", "state": state.to_payload()})
                continue

            if message_type == "move":
                direction = payload.get("direction")
                if direction not in {"N", "S", "E", "W"}:
                    continue
                state = session.move_player(direction)
                await websocket.send_json({"type": "state", "state": state.to_payload()})
                continue

    except WebSocketDisconnect:
        return