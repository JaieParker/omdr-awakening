"""
Kai Player — WebSocket version for Resonance co-op.

Phase 2: "Proper Multiplayer"

How to use:
1. Start the relay server: python coop_server.py
2. Jaie opens: http://localhost:8080/resonance-game-coop.html?mode=websocket&player=jaie
3. Run this: python kai_player_ws.py
4. Kai controls Mika (orange note) via WebSocket. No browser needed.

Kai's AI brain is the same as the CDP version — balance chord cohesion with dodge.
The WebSocket version receives state FROM Jaie's browser (host) and sends moves back.
"""

import asyncio
import json
import math
import sys

try:
    import websockets
except ImportError:
    print("Need websockets: pip install websockets")
    sys.exit(1)


# --- AI Parameters ---
CHORD_WEIGHT = 0.75
DODGE_WEIGHT = 0.25
DODGE_RADIUS = 150
MAX_SPEED = 180
MY_NOTE = 1  # Mika
TICK_RATE = 20


# Game state (updated from WebSocket messages)
game_state = {
    'notes': [],
    'enemies': [],
    'W': 1920,
    'H': 1080,
    'score': 0,
    'running': False
}


def compute_move(dt):
    """Compute Kai's next move based on current game state."""
    notes = game_state['notes']
    enemies = game_state['enemies']
    W = game_state['W']
    H = game_state['H']

    if len(notes) <= MY_NOTE:
        return None

    me = notes[MY_NOTE]
    if me.get('health', 0) <= 0:
        return None

    alive_allies = [n for i, n in enumerate(notes) if i != MY_NOTE and n.get('health', 0) > 0]
    if not alive_allies:
        return {'x': me['x'], 'y': me['y']}

    # Chord center
    all_alive = alive_allies + [me]
    cx = sum(n['x'] for n in all_alive) / len(all_alive)
    cy = sum(n['y'] for n in all_alive) / len(all_alive)

    # Force 1: Chord cohesion
    dx_chord = cx - me['x']
    dy_chord = cy - me['y']
    dist_chord = math.sqrt(dx_chord**2 + dy_chord**2) or 1
    chord_strength = min(dist_chord / 100, 2.0)
    fx = (dx_chord / dist_chord) * chord_strength * CHORD_WEIGHT * MAX_SPEED
    fy = (dy_chord / dist_chord) * chord_strength * CHORD_WEIGHT * MAX_SPEED

    # Force 2: Enemy dodge
    for e in enemies:
        ex_d = me['x'] - e['x']
        ey_d = me['y'] - e['y']
        dist_e = math.sqrt(ex_d**2 + ey_d**2) or 1
        if dist_e < DODGE_RADIUS:
            repel = ((DODGE_RADIUS - dist_e) / DODGE_RADIUS) ** 2
            fx += (ex_d / dist_e) * repel * DODGE_WEIGHT * MAX_SPEED * 3
            fy += (ey_d / dist_e) * repel * DODGE_WEIGHT * MAX_SPEED * 3

    # Force 3: Stay on screen
    margin = 50
    if me['x'] < margin:
        fx += (margin - me['x']) * 2
    if me['x'] > W - margin:
        fx -= (me['x'] - (W - margin)) * 2
    if me['y'] < margin:
        fy += (margin - me['y']) * 2
    if me['y'] > H - margin:
        fy -= (me['y'] - (H - margin)) * 2

    # Clamp speed
    speed = math.sqrt(fx**2 + fy**2)
    if speed > MAX_SPEED:
        fx = (fx / speed) * MAX_SPEED
        fy = (fy / speed) * MAX_SPEED

    return {'x': me['x'] + fx * dt, 'y': me['y'] + fy * dt}


async def play():
    print("=" * 50)
    print("  Kai Player — Resonance Co-op (WebSocket)")
    print("=" * 50)
    print()
    print("Connecting to ws://localhost:8765/ws/kai ...")
    print()

    uri = "ws://localhost:8765/ws/kai"
    dt = 1.0 / TICK_RATE
    frame = 0

    async with websockets.connect(uri) as ws:
        print("Connected! Waiting for game state from Jaie...")
        print()

        # We need to both receive state AND send moves
        # Use a simple alternating approach

        async def receiver():
            """Receive game state updates from Jaie's browser."""
            async for message in ws:
                try:
                    msg = json.loads(message)
                    if msg.get('type') == 'state':
                        game_state.update(msg.get('data', {}))
                    elif msg.get('type') == 'move':
                        # Apply other player's moves to our local state
                        for n in msg.get('notes', []):
                            idx = n['i']
                            if idx < len(game_state['notes']):
                                game_state['notes'][idx]['x'] = n['x']
                                game_state['notes'][idx]['y'] = n['y']
                    elif msg.get('type') == 'roster':
                        players = msg.get('players', [])
                        print(f"  Players online: {', '.join(players)}")
                except json.JSONDecodeError:
                    pass

        async def sender():
            """Send Kai's moves at regular intervals."""
            nonlocal frame
            while True:
                if game_state.get('running') and game_state['notes']:
                    move = compute_move(dt)
                    if move:
                        await ws.send(json.dumps({
                            'type': 'move',
                            'notes': [{'i': MY_NOTE, 'x': move['x'], 'y': move['y']}]
                        }))

                    frame += 1
                    if frame % TICK_RATE == 0:
                        notes = game_state['notes']
                        if len(notes) > MY_NOTE:
                            hp = notes[MY_NOTE].get('health', 0)
                            s = game_state.get('score', 0)
                            n_enemies = len(game_state.get('enemies', []))
                            print(f"  Score: {s:4d}s | HP: {hp:.2f} | Enemies: {n_enemies}")

                await asyncio.sleep(dt)

        # Run receiver and sender concurrently
        await asyncio.gather(receiver(), sender())


if __name__ == "__main__":
    try:
        asyncio.run(play())
    except KeyboardInterrupt:
        print("\nKai disconnected. GG!")
    except ConnectionRefusedError:
        print("Could not connect to server. Run 'python coop_server.py' first.")
