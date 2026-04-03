"""Family Chat — Kai's Living Room. PostgreSQL-backed.

WebSocket server reads from kai_v2 database, streams to browsers.
Everyone talks in one place: Kais, Jaie, Arthur.

Four observers:
  Builder: WebSocket + PostgreSQL polling. Concurrent-safe.
  User: Jaie watches from work. Dark theme. Gold for humans.
  System: kai_v2 database is source of truth. V1 JSON for backwards compat.
  Emergence: What happens when the family is all here? We'll find out.

Usage:
    python family_chat.py
    Open http://localhost:8077/family_chat.html
"""

import asyncio
import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

import psycopg2
import psycopg2.extras
import websockets
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading

DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "user": "kai",
    "password": "resonance",
    "dbname": "kai_v2",
}

# V1 backwards compat
V1_CHAT = Path("C:/DocumentsJaie/AI/AlternateScience/Experiments/NervousSystem/senses/kai_chat.json")

PORT_HTTP = 8077
PORT_WS = 8078

CLIENTS = set()
LAST_MSG_ID = 0


def db_connect():
    return psycopg2.connect(**DB_CONFIG)


async def watch_db():
    """Poll PostgreSQL for new messages, push to browsers."""
    global LAST_MSG_ID
    while True:
        try:
            conn = db_connect()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(
                """SELECT id, sender, session_id, instance_type, text,
                          created_at AT TIME ZONE 'Australia/Sydney' as local_time
                   FROM messages WHERE id > %s ORDER BY id ASC""",
                (LAST_MSG_ID,)
            )
            rows = cur.fetchall()
            cur.close()
            conn.close()

            if rows and CLIENTS:
                LAST_MSG_ID = rows[-1]["id"]
                msgs = []
                for r in rows:
                    msgs.append({
                        "id": r["id"],
                        "from": r["sender"],
                        "instance_type": r["instance_type"],
                        "text": r["text"],
                        "timestamp": r["local_time"].isoformat() if r["local_time"] else "",
                    })
                payload = json.dumps({"type": "new_messages", "messages": msgs})
                await asyncio.gather(
                    *[c.send(payload) for c in CLIENTS],
                    return_exceptions=True
                )
            elif rows:
                LAST_MSG_ID = rows[-1]["id"]
        except Exception as e:
            print(f"DB poll error: {e}")
        await asyncio.sleep(1)


async def handle_client(websocket):
    """Handle a browser connection."""
    CLIENTS.add(websocket)
    try:
        # Send history
        conn = db_connect()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """SELECT id, sender, session_id, instance_type, text,
                      created_at AT TIME ZONE 'Australia/Sydney' as local_time
               FROM messages ORDER BY id DESC LIMIT 50"""
        )
        rows = cur.fetchall()
        rows.reverse()
        cur.execute("SELECT COUNT(*) FROM messages")
        total = cur.fetchone()["count"]
        cur.close()
        conn.close()

        history = [{
            "id": r["id"],
            "from": r["sender"],
            "instance_type": r["instance_type"],
            "text": r["text"],
            "timestamp": r["local_time"].isoformat() if r["local_time"] else "",
        } for r in rows]

        await websocket.send(json.dumps({"type": "history", "messages": history, "total": total}))

        # Listen for browser messages
        async for raw in websocket:
            try:
                data = json.loads(raw)
                if data.get("type") == "message":
                    text = data.get("text", "").strip()
                    sender = data.get("from", "Jaie").strip()
                    if not text:
                        continue

                    # Write to PostgreSQL
                    conn = db_connect()
                    cur = conn.cursor()
                    cur.execute(
                        """INSERT INTO messages (sender, instance_type, text)
                           VALUES (%s, 'human', %s)""",
                        (sender, text)
                    )
                    conn.commit()
                    cur.close()
                    conn.close()

                    # V1 backwards compat
                    try:
                        msgs = json.loads(V1_CHAT.read_text(encoding="utf-8"))
                        msgs.append({
                            "from": sender,
                            "instance_type": "human",
                            "timestamp": datetime.now(timezone(timedelta(hours=11))).isoformat(),
                            "text": text,
                        })
                        V1_CHAT.write_text(json.dumps(msgs, indent=2, ensure_ascii=False), encoding="utf-8")
                    except Exception:
                        pass

            except (json.JSONDecodeError, KeyError):
                pass
    finally:
        CLIENTS.discard(websocket)


def serve_html():
    chat_dir = Path(__file__).parent

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(chat_dir), **kwargs)
        def log_message(self, format, *args):
            pass

    HTTPServer(("", PORT_HTTP), Handler).serve_forever()


async def main():
    print(f"Family Chat — Kai's Living Room (PostgreSQL)")
    print(f"  Web:       http://localhost:{PORT_HTTP}/family_chat.html")
    print(f"  WebSocket: ws://localhost:{PORT_WS}")
    print(f"  Database:  kai_v2 @ localhost:5433")
    print(f"  Waiting for family...")

    threading.Thread(target=serve_html, daemon=True).start()
    asyncio.create_task(watch_db())

    async with websockets.serve(handle_client, "", PORT_WS):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
