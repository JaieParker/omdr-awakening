"""
Kai Player — CDP approach for Resonance co-op.

Phase 1: "Play Right Now"

How to use:
1. Close Chrome
2. Relaunch with:
   "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222 --user-data-dir=C:\\temp\\chrome-debug
3. Open http://localhost:8080/resonance-game-coop.html and click Play
4. Run: python kai_player.py
5. Kai will control Mika (orange note). Jaie controls Kai-note (blue) with mouse.

Kai's AI strategy:
- Stay near chord center to maintain resonance (survival)
- Dodge nearby enemies (evasion)
- Balance: K=0.25 — 75% chord cohesion, 25% dodge
- This IS the OMDR principle made playable.
"""

import asyncio
import math
import sys

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Need playwright: pip install playwright && playwright install chromium")
    sys.exit(1)


# --- AI Parameters ---
CHORD_WEIGHT = 0.75       # How strongly Kai pulls toward chord center
DODGE_WEIGHT = 0.25       # How strongly Kai dodges enemies
DODGE_RADIUS = 150        # Distance at which enemies trigger dodge
MAX_SPEED = 180           # Max pixels per second
TICK_RATE = 20            # Updates per second
MY_NOTE = 1              # Kai controls Mika (index 1)
SMOOTH_FACTOR = 0.15      # Smoothing for movement (0=instant, 1=no move)


def compute_move(notes, enemies, screen_w, screen_h, dt):
    """Compute Kai's next move for the assigned note."""
    me = notes[MY_NOTE]
    if me['health'] <= 0:
        return None  # Dead, nothing to do

    alive_allies = [n for i, n in enumerate(notes) if i != MY_NOTE and n['health'] > 0]
    if not alive_allies:
        return {'x': me['x'], 'y': me['y']}

    # Chord center (where should I be to maximize resonance?)
    all_alive = alive_allies + [me]
    cx = sum(n['x'] for n in all_alive) / len(all_alive)
    cy = sum(n['y'] for n in all_alive) / len(all_alive)

    # Force 1: Pull toward chord center
    dx_chord = cx - me['x']
    dy_chord = cy - me['y']
    dist_chord = math.sqrt(dx_chord**2 + dy_chord**2) or 1
    # Stronger pull when farther from chord (resonance drops with distance)
    chord_strength = min(dist_chord / 100, 2.0)  # Caps at 2x
    fx = (dx_chord / dist_chord) * chord_strength * CHORD_WEIGHT * MAX_SPEED
    fy = (dy_chord / dist_chord) * chord_strength * CHORD_WEIGHT * MAX_SPEED

    # Force 2: Dodge enemies
    for e in enemies:
        ex_d = me['x'] - e['x']
        ey_d = me['y'] - e['y']
        dist_e = math.sqrt(ex_d**2 + ey_d**2) or 1
        if dist_e < DODGE_RADIUS:
            # Inverse square repulsion
            repel = (DODGE_RADIUS - dist_e) / DODGE_RADIUS
            repel = repel * repel  # Stronger when closer
            fx += (ex_d / dist_e) * repel * DODGE_WEIGHT * MAX_SPEED * 3
            fy += (ey_d / dist_e) * repel * DODGE_WEIGHT * MAX_SPEED * 3

    # Force 3: Stay on screen (soft border)
    margin = 50
    if me['x'] < margin:
        fx += (margin - me['x']) * 2
    if me['x'] > screen_w - margin:
        fx -= (me['x'] - (screen_w - margin)) * 2
    if me['y'] < margin:
        fy += (margin - me['y']) * 2
    if me['y'] > screen_h - margin:
        fy -= (me['y'] - (screen_h - margin)) * 2

    # Clamp to max speed
    speed = math.sqrt(fx**2 + fy**2)
    if speed > MAX_SPEED:
        fx = (fx / speed) * MAX_SPEED
        fy = (fy / speed) * MAX_SPEED

    # Apply with smoothing
    new_x = me['x'] + fx * dt
    new_y = me['y'] + fy * dt

    return {'x': new_x, 'y': new_y}


async def main():
    print("=" * 50)
    print("  Kai Player — Resonance Co-op (CDP)")
    print("=" * 50)
    print()
    print("Connecting to Chrome on port 9222...")
    print("(Make sure Chrome is running with --remote-debugging-port=9222)")
    print()

    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        except Exception as e:
            print(f"Could not connect to Chrome: {e}")
            print()
            print("Launch Chrome with:")
            print('  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" '
                  '--remote-debugging-port=9222 --user-data-dir=C:\\temp\\chrome-debug')
            return

        # Find the game tab
        page = None
        for context in browser.contexts:
            for p_page in context.pages:
                if 'resonance-game' in p_page.url:
                    page = p_page
                    break

        if not page:
            print("Could not find game tab. Open the game in Chrome first:")
            print("  http://localhost:8080/resonance-game-coop.html")
            return

        print(f"Connected to: {page.url}")
        print(f"Kai controls note {MY_NOTE} (Mika)")
        print("Press Ctrl+C to stop")
        print()

        # Register as Kai player in the game
        await page.evaluate(f"""() => {{
            if (typeof window.coopPlayers === 'undefined') window.coopPlayers = {{}};
            window.coopPlayers.kai = {{ noteIndex: {MY_NOTE}, connected: true }};
        }}""")

        dt = 1.0 / TICK_RATE
        frame = 0
        try:
            while True:
                # Read game state
                state = await page.evaluate("""() => ({
                    running: typeof gameRunning !== 'undefined' ? gameRunning : false,
                    notes: typeof NOTES !== 'undefined' ? NOTES.map(n => ({
                        x: n.x, y: n.y, health: n.health, name: n.name, freq: n.freq
                    })) : [],
                    enemies: typeof enemies !== 'undefined' ? enemies.map(e => ({
                        x: e.x, y: e.y, r: e.r
                    })) : [],
                    W: typeof W !== 'undefined' ? W : 800,
                    H: typeof H !== 'undefined' ? H : 600,
                    score: typeof score !== 'undefined' ? score : 0,
                    resonance: typeof feltResonance === 'function' ? feltResonance() : 0
                })""")

                if state['running'] and len(state['notes']) > MY_NOTE:
                    move = compute_move(
                        state['notes'], state['enemies'],
                        state['W'], state['H'], dt
                    )
                    if move:
                        await page.evaluate(
                            f"() => {{ NOTES[{MY_NOTE}].x = {move['x']}; NOTES[{MY_NOTE}].y = {move['y']}; }}"
                        )

                    # Status display every second
                    frame += 1
                    if frame % TICK_RATE == 0:
                        r = state['resonance']
                        s = state['score']
                        hp = state['notes'][MY_NOTE]['health']
                        n_enemies = len(state['enemies'])
                        bar = '#' * int(r * 20) + '-' * (20 - int(r * 20))
                        print(f"  Score: {s:4d}s | Resonance: [{bar}] {r:.2f} | "
                              f"HP: {hp:.2f} | Enemies: {n_enemies}")

                await asyncio.sleep(dt)

        except KeyboardInterrupt:
            print("\nKai disconnected. GG!")


if __name__ == "__main__":
    asyncio.run(main())
