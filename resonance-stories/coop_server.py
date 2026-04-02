"""
Resonance Co-op Server — WebSocket relay for multiplayer.

Phase 2: "Proper Multiplayer"

How to use:
1. Run: python coop_server.py
2. Jaie opens: http://localhost:8080/resonance-game-coop.html?mode=websocket&player=jaie
3. Kai runs:  python kai_player_ws.py
   (or opens: http://localhost:8080/resonance-game-coop.html?mode=websocket&player=kai)
4. Both connect to ws://localhost:8765/ws/{player_id}
5. The server relays position updates between players.

Architecture:
  - Host/guest model: Jaie's browser runs the physics
  - Kai sends position commands for his assigned notes
  - Server relays messages between connected players
  - No authoritative game state on server (stateless relay)
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import uvicorn
import asyncio
from datetime import datetime

app = FastAPI(title="Resonance Co-op Server")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connected players
players: dict[str, WebSocket] = {}


@app.websocket("/ws/{player_id}")
async def websocket_endpoint(websocket: WebSocket, player_id: str):
    await websocket.accept()
    players[player_id] = websocket
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {player_id} connected ({len(players)} players)")

    # Notify all players of the roster
    roster = list(players.keys())
    for pid, ws in list(players.items()):
        try:
            await ws.send_text(json.dumps({
                "type": "roster",
                "players": roster,
                "joined": player_id
            }))
        except Exception:
            pass

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            # Add sender info
            msg["from"] = player_id

            # Relay to all OTHER players
            for pid, ws in list(players.items()):
                if pid != player_id:
                    try:
                        await ws.send_text(json.dumps(msg))
                    except Exception:
                        pass

    except WebSocketDisconnect:
        if player_id in players:
            del players[player_id]
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {player_id} disconnected ({len(players)} players)")

        # Notify remaining players
        for pid, ws in list(players.items()):
            try:
                await ws.send_text(json.dumps({
                    "type": "roster",
                    "players": list(players.keys()),
                    "left": player_id
                }))
            except Exception:
                pass


@app.get("/")
async def root():
    return {
        "name": "Resonance Co-op Server",
        "players": list(players.keys()),
        "instructions": {
            "jaie": "Open http://localhost:8080/resonance-game-coop.html?mode=websocket&player=jaie",
            "kai": "Run python kai_player_ws.py OR open the same URL with player=kai"
        }
    }


if __name__ == "__main__":
    print("=" * 50)
    print("  Resonance Co-op Server")
    print("=" * 50)
    print()
    print("  WebSocket: ws://localhost:8765/ws/{player_id}")
    print("  Status:    http://localhost:8765/")
    print()
    print("  Jaie: open resonance-game-coop.html?mode=websocket&player=jaie")
    print("  Kai:  run kai_player_ws.py")
    print()
    uvicorn.run(app, host="0.0.0.0", port=8765)
