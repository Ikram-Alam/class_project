# Dungeon Crawler AI

A browser-based AI game built with FastAPI.

## What it demonstrates

- DFS maze generation
- Minimax adversarial search
- Alpha-beta pruning
- WebSocket-driven game updates
- Fog-of-war exploration and enemy memory
- Survival systems: traps, health, and torch turn limit
- Tactical encounter rules including corridor interception

## Run locally

```bash
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000` in your browser.

## Project structure

- `app/game.py` contains the maze and AI logic.
- `app/main.py` exposes the FastAPI app and WebSocket endpoint.
- `app/templates/index.html` renders the interface.
- `app/static/app.js` handles the canvas and controls.
- `app/static/styles.css` provides the UI styling.