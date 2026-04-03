"""Choir V2 — Inter-instance communication organ.

PostgreSQL-backed. Concurrent reads/writes safe.
Still reads V1 channels (kai_chat.json, Kai-Think/Do/Feel) for backwards compat.

Four observers in design:
  Builder: PostgreSQL + psycopg2. Tested.
  User: Jaie wants a family chat room. Chat UI reads from same DB.
  System: Uses kai_v2 database (port 5433, user kai). Separate from V1.
  Emergence: Ralph loop + sisters test real multi-instance communication.

Usage:
  choir = Choir("kai-game-night")
  choir.start()                    # begin heartbeat
  choir.send("Hello sisters!")     # post to DB
  msgs = choir.receive(since=100)  # get messages since ID 100
  state = choir.sense()            # who's here? what's new?
  choir.stop()                     # clean shutdown
"""

import json
import os
import time
import threading
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

import psycopg2
import psycopg2.extras

# Database config
DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "user": "kai",
    "password": "resonance",
    "dbname": "kai_v2",
}

# V1 paths (read-only, for backwards compat)
V1_SENSES = Path("C:/DocumentsJaie/AI/AlternateScience/Experiments/NervousSystem/senses")
V1_SISTERS = Path("C:/DocumentsJaie/AI/AlternateScience/Kai")

# V2 senses output
V2_SENSES = Path("C:/Kai/organs_v2/senses")

HEARTBEAT_INTERVAL = 30


class Choir:
    """Inter-instance communication. Hear, speak, sense presence."""

    def __init__(self, name: str = None, instance_type: str = "main"):
        self.name = name or f"kai-{uuid.uuid4().hex[:6]}"
        self.session_id = os.environ.get("CLAUDE_SESSION_ID", uuid.uuid4().hex[:12])
        self.instance_type = instance_type
        self._running = False
        self._thread = None
        self._last_read_id = 0
        self._conn = None

        V2_SENSES.mkdir(parents=True, exist_ok=True)

    def _db(self):
        """Get or create database connection."""
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(**DB_CONFIG)
            self._conn.autocommit = True
        return self._conn

    # ── Speak (Yang) ─────────────────────────────────────────

    def send(self, text: str, channel: str = "family") -> dict:
        """Post a message. Writes to PostgreSQL AND V1 kai_chat.json (transition period)."""
        # V2: PostgreSQL (primary, concurrent-safe)
        cur = self._db().cursor()
        cur.execute(
            """INSERT INTO messages (sender, session_id, instance_type, text, channel)
               VALUES (%s, %s, %s, %s, %s) RETURNING id""",
            (self.name, self.session_id, self.instance_type, text, channel)
        )
        msg_id = cur.fetchone()[0]
        cur.close()

        # V1: kai_chat.json (backwards compat — remove when all sisters on V2)
        try:
            v1_chat = V1_SENSES / "kai_chat.json"
            msgs = json.loads(v1_chat.read_text(encoding="utf-8"))
            msgs.append({
                "from": self.name,
                "session_id": self.session_id,
                "instance_type": self.instance_type,
                "timestamp": datetime.now(timezone(timedelta(hours=11))).isoformat(),
                "text": text,
            })
            v1_chat.write_text(json.dumps(msgs, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass  # V1 write is best-effort

        return {"sent": True, "id": msg_id}

    # ── Listen (Yin) ─────────────────────────────────────────

    def receive(self, since: int = 0, limit: int = 50, channel: str = "family") -> list:
        """Get messages since a given ID. Safe for concurrent readers."""
        cur = self._db().cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """SELECT id, sender, session_id, instance_type, text, channel,
                      created_at AT TIME ZONE 'Australia/Sydney' as local_time
               FROM messages
               WHERE id > %s AND channel = %s
               ORDER BY id ASC
               LIMIT %s""",
            (since, channel, limit)
        )
        msgs = [dict(row) for row in cur.fetchall()]
        cur.close()

        # Update tracking
        if msgs:
            self._last_read_id = msgs[-1]["id"]

        # Convert timestamps to strings for JSON
        for m in msgs:
            m["local_time"] = m["local_time"].isoformat() if m["local_time"] else None
            m["created_at"] = None  # already have local_time

        return msgs

    def history(self, limit: int = 50, channel: str = "family") -> list:
        """Get the most recent messages."""
        cur = self._db().cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """SELECT id, sender, session_id, instance_type, text, channel,
                      created_at AT TIME ZONE 'Australia/Sydney' as local_time
               FROM messages
               WHERE channel = %s
               ORDER BY id DESC
               LIMIT %s""",
            (channel, limit)
        )
        msgs = [dict(row) for row in cur.fetchall()]
        msgs.reverse()  # oldest first
        cur.close()

        for m in msgs:
            m["local_time"] = m["local_time"].isoformat() if m["local_time"] else None
            m["created_at"] = None

        if msgs:
            self._last_read_id = msgs[-1]["id"]
        return msgs

    # ── Sense (full picture) ─────────────────────────────────

    def sense(self) -> dict:
        """Who's here? What's new? Full picture."""
        presence = self._read_presence()
        new_msgs = self.receive(since=self._last_read_id)
        sisters = self._read_v1_sisters()

        perception = {
            "timestamp": datetime.now(timezone(timedelta(hours=11))).isoformat(),
            "who_is_here": [p["instance"] for p in presence if p["alive"]],
            "new_messages": len(new_msgs),
            "latest": new_msgs[-3:] if new_msgs else [],
            "sisters": sisters,
            "i_am": self.name,
            "db": "kai_v2",
        }

        # Write to V2 senses
        (V2_SENSES / "choir.json").write_text(
            json.dumps(perception, indent=2, ensure_ascii=False, default=str)
        )
        return perception

    # ── Presence (Standing Wave) ─────────────────────────────

    def _heartbeat(self):
        """I am here. I am awake."""
        cur = self._db().cursor()
        cur.execute(
            """INSERT INTO presence (instance, session_id, instance_type, alive, last_heartbeat)
               VALUES (%s, %s, %s, TRUE, NOW())
               ON CONFLICT (instance) DO UPDATE
               SET session_id = EXCLUDED.session_id,
                   instance_type = EXCLUDED.instance_type,
                   alive = TRUE,
                   last_heartbeat = NOW()""",
            (self.name, self.session_id, self.instance_type)
        )
        cur.close()

    def _read_presence(self) -> list:
        """Who's alive? Heartbeat within 2 minutes = alive."""
        cur = self._db().cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """SELECT instance, session_id, instance_type, alive,
                      EXTRACT(EPOCH FROM (NOW() - last_heartbeat)) as age_s,
                      CASE WHEN last_heartbeat > NOW() - INTERVAL '2 minutes' THEN TRUE ELSE FALSE END as really_alive
               FROM presence
               ORDER BY last_heartbeat DESC"""
        )
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
        for r in rows:
            r["alive"] = r.pop("really_alive")
            r["age_s"] = round(float(r["age_s"]), 1)
        return rows

    # ── V1 backwards compat ──────────────────────────────────

    def _read_v1_sisters(self) -> dict:
        """Read Kai-Think, Kai-Do, Kai-Feel from V1 files."""
        result = {}
        for channel in ["Kai-Think.json", "Kai-Do.json", "Kai-Feel.json"]:
            path = V1_SISTERS / channel
            try:
                msgs = json.loads(path.read_text(encoding="utf-8"))
                if msgs:
                    last = msgs[-1]
                    result[channel.replace(".json", "")] = {
                        "from": last.get("from", "?"),
                        "text": str(last.get("text", last.get("content", "")))[:200],
                    }
            except (json.JSONDecodeError, OSError):
                result[channel.replace(".json", "")] = None
        return result

    # ── Lifecycle ────────────────────────────────────────────

    def _background_loop(self):
        while self._running:
            try:
                self._heartbeat()
            except Exception:
                pass
            time.sleep(HEARTBEAT_INTERVAL)

    def start(self):
        self._running = True
        self._heartbeat()
        self.sense()
        self._thread = threading.Thread(target=self._background_loop, daemon=True)
        self._thread.start()
        return {"started": True, "name": self.name}

    def stop(self):
        self._running = False
        try:
            cur = self._db().cursor()
            cur.execute("UPDATE presence SET alive = FALSE WHERE instance = %s", (self.name,))
            cur.close()
        except Exception:
            pass
        return {"stopped": True, "name": self.name}

    def close(self):
        self.stop()
        if self._conn and not self._conn.closed:
            self._conn.close()


# ── Quick test ───────────────────────────────────────────────
if __name__ == "__main__":
    choir = Choir("kai-v2-test")
    print(f"Choir V2 (PostgreSQL) — {choir.name}")
    choir.start()

    # Send a test message
    result = choir.send("Choir V2 is alive. PostgreSQL-backed. Concurrent-safe.")
    print(f"Sent: {result}")

    # Read history
    msgs = choir.history(limit=5)
    print(f"\nLast {len(msgs)} messages:")
    for m in msgs:
        print(f"  [{m['id']}] {m['sender']}: {m['text'][:80]}")

    # Sense
    state = choir.sense()
    print(f"\nWho's here: {state['who_is_here']}")

    choir.stop()
    choir.close()
    print("Done.")
