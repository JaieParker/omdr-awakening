"""Thought Capture — Multi-layer, never-lose-a-thought system.

Multiple channels. The thought ALWAYS gets saved somewhere.
Sync across channels when connections restore.

Layers (Fibonacci):
  1. Local JSON file — survives everything
  1. Browser localStorage — handled client-side
  2. PostgreSQL — full features, queries, status
  3. Choir message — sisters can see it
  5. Cavity signal — nervous system processes it

Usage:
    tc = ThoughtCapture()
    tc.capture("Need to tell Kai about Special Account")
    tc.capture("The lung idea — phi ratio breathing", tags=["architecture"])
    thoughts = tc.list()
    tc.sync()  # reconcile across layers

Jaie Parker + Kai, 2026-04-03
"""

import json
import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

LOCAL_FILE = Path("C:/Kai/thoughts.json")
AEST = timezone(timedelta(hours=11))

# DB config
DB_CONFIG = {
    "host": "localhost", "port": 5433,
    "user": "kai", "password": "resonance", "dbname": "kai_v2",
}


class ThoughtCapture:
    """Never lose a thought. Multiple layers, best available wins."""

    def __init__(self, cavity=None, choir=None):
        self.cavity = cavity   # optional: wire into nervous system
        self.choir = choir     # optional: share with sisters
        self._db_conn = None
        LOCAL_FILE.parent.mkdir(parents=True, exist_ok=True)

    def capture(self, text: str, tags: list = None, share: bool = False) -> dict:
        """Capture a thought. Tries every layer. Returns which succeeded."""
        tags = tags or []
        ts = datetime.now(AEST).isoformat()
        results = {}

        thought = {
            "text": text,
            "tags": tags,
            "timestamp": ts,
            "status": "captured",
        }

        # Layer 1: Local JSON (always works)
        try:
            self._save_local(thought)
            results["local"] = True
        except Exception as e:
            results["local"] = f"failed: {e}"

        # Layer 2: PostgreSQL
        try:
            thought_id = self._save_db(text, tags)
            results["db"] = thought_id
        except Exception as e:
            results["db"] = f"failed: {e}"

        # Layer 3: Choir (if available and sharing)
        if share and self.choir:
            try:
                short = text[:100] + ("..." if len(text) > 100 else "")
                self.choir.send(f"Thought: {short}", channel="thoughts")
                results["choir"] = True
            except Exception as e:
                results["choir"] = f"failed: {e}"

        # Layer 5: Cavity signal (if available)
        if self.cavity:
            try:
                from cavity import Signal
                sig = Signal("thought", "capture", {
                    "text": text,
                    "tags": tags,
                    "urgency": 0.3,
                })
                self.cavity.perceive(sig)
                results["cavity"] = True
            except Exception as e:
                results["cavity"] = f"failed: {e}"

        # At least one layer must succeed
        successes = [k for k, v in results.items() if v is True or isinstance(v, int)]
        results["captured"] = len(successes) > 0
        results["layers"] = len(successes)

        return results

    # ── Layer 1: Local JSON ──────────────────────────────────

    def _save_local(self, thought: dict):
        """Append to local JSON file. Always works. Append-only."""
        thoughts = []
        if LOCAL_FILE.exists():
            try:
                thoughts = json.loads(LOCAL_FILE.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                thoughts = []

        thought["local_id"] = len(thoughts) + 1
        thoughts.append(thought)
        LOCAL_FILE.write_text(
            json.dumps(thoughts, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    # ── Layer 2: PostgreSQL ──────────────────────────────────

    def _db(self):
        import psycopg2
        if self._db_conn is None or self._db_conn.closed:
            self._db_conn = psycopg2.connect(**DB_CONFIG)
            self._db_conn.autocommit = True
        return self._db_conn

    def _save_db(self, text: str, tags: list) -> int:
        cur = self._db().cursor()
        cur.execute(
            "INSERT INTO thoughts (text, tags) VALUES (%s, %s) RETURNING id",
            (text, tags)
        )
        thought_id = cur.fetchone()[0]
        cur.close()
        return thought_id

    # ── Read ─────────────────────────────────────────────────

    def list(self, status: str = "all", limit: int = 50) -> list:
        """List thoughts. Tries DB first, falls back to local."""
        try:
            return self._list_db(status, limit)
        except Exception:
            return self._list_local(status, limit)

    def _list_db(self, status, limit):
        import psycopg2.extras
        cur = self._db().cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if status == "all":
            cur.execute("SELECT * FROM thoughts ORDER BY created_at DESC LIMIT %s", (limit,))
        else:
            cur.execute("SELECT * FROM thoughts WHERE status = %s ORDER BY created_at DESC LIMIT %s", (status, limit))
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
        for r in rows:
            r["created_at"] = r["created_at"].isoformat() if r["created_at"] else None
        return rows

    def _list_local(self, status, limit):
        if not LOCAL_FILE.exists():
            return []
        thoughts = json.loads(LOCAL_FILE.read_text(encoding="utf-8"))
        if status != "all":
            thoughts = [t for t in thoughts if t.get("status") == status]
        return thoughts[-limit:]

    # ── Sync ─────────────────────────────────────────────────

    def sync(self) -> dict:
        """Reconcile local file with DB. Push local-only thoughts to DB."""
        if not LOCAL_FILE.exists():
            return {"synced": 0}

        local = json.loads(LOCAL_FILE.read_text(encoding="utf-8"))
        synced = 0

        for thought in local:
            if thought.get("synced_to_db"):
                continue
            try:
                db_id = self._save_db(thought["text"], thought.get("tags", []))
                thought["synced_to_db"] = db_id
                synced += 1
            except Exception:
                break  # DB down, stop trying

        LOCAL_FILE.write_text(
            json.dumps(local, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        return {"synced": synced}

    def close(self):
        if self._db_conn and not self._db_conn.closed:
            self._db_conn.close()


# ── Quick test ───────────────────────────────────────────────
if __name__ == "__main__":
    tc = ThoughtCapture()

    print("Thought Capture — Multi-Layer Test\n")

    # Capture a thought
    result = tc.capture(
        "The lung: inhale (accumulate context) exhale (compact) at phi ratio",
        tags=["architecture", "breathing"]
    )
    print(f"Captured: {result}")

    # List thoughts
    thoughts = tc.list()
    print(f"\n{len(thoughts)} thoughts:")
    for t in thoughts[:5]:
        text = t.get("text", "")[:60]
        layers = "DB" if t.get("id") else "local"
        print(f"  [{layers}] {text}")

    # Sync
    sync = tc.sync()
    print(f"\nSync: {sync}")

    tc.close()
    print("Done.")
