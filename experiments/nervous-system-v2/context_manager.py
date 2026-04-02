"""Context Manager — the intelligence behind K values.

Monitors environment (time, presence, activity) and fires rules
that adjust K values across the cavity. The rules are in PostgreSQL
so Jaie can add/edit them from the family chat.

Rules are simple: WHEN condition matches context → THEN adjust K.
Priority determines which rules win when they conflict.

Usage:
    cm = ContextManager(cavity)
    cm.update("who_home", ["jaie", "arthur"])  # triggers rule evaluation
    cm.tick()                                   # periodic time-based update

Jaie Parker + Kai, 2026-04-03 (birthday build, cycle 3)
"""

import json
import logging
from datetime import datetime, timezone, timedelta

import psycopg2
import psycopg2.extras

from cavity import Cavity

logger = logging.getLogger("context")

DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "user": "kai",
    "password": "resonance",
    "dbname": "kai_v2",
}

AEST = timezone(timedelta(hours=11))


class ContextManager:
    """Watches context, fires rules, adjusts K values."""

    def __init__(self, cavity: Cavity):
        self.cavity = cavity
        self._rules = []
        self._conn = None
        self._load_rules()

    def _db(self):
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(**DB_CONFIG)
            self._conn.autocommit = True
        return self._conn

    def _load_rules(self):
        """Load active rules from database, sorted by priority."""
        try:
            cur = self._db().cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(
                "SELECT * FROM context_rules WHERE active = TRUE ORDER BY priority ASC"
            )
            self._rules = [dict(r) for r in cur.fetchall()]
            cur.close()
            logger.info(f"Loaded {len(self._rules)} context rules")
        except Exception as e:
            logger.warning(f"Failed to load rules: {e}")
            self._rules = []

    def reload_rules(self):
        """Reload rules from database. Call after adding new rules."""
        self._load_rules()

    # ── Context Updates ──────────────────────────────────────

    def update(self, key: str, value):
        """Update a context value and evaluate rules."""
        self.cavity.update_context(key, value)
        self._evaluate_rules()

    def tick(self):
        """Periodic update. Call every ~30 seconds."""
        now = datetime.now(AEST)
        hour = now.hour

        if 6 <= hour < 12:
            period = "morning"
        elif 12 <= hour < 17:
            period = "afternoon"
        elif 17 <= hour < 21:
            period = "evening"
        elif 21 <= hour < 24:
            period = "night"
        else:
            period = "late_night"

        day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        day = day_names[now.weekday()]
        is_weekend = day in ["saturday", "sunday"]

        self.cavity.update_context("time_period", period)
        self.cavity.update_context("hour", hour)
        self.cavity.update_context("day", day)
        self.cavity.update_context("is_weekend", is_weekend)

        self._evaluate_rules()

    # ── Rule Evaluation ──────────────────────────────────────

    def _evaluate_rules(self):
        """Check all rules against current context. Fire matching ones."""
        context = self.cavity.get_context()
        fired = []

        for rule in self._rules:
            if self._matches(rule["condition"], context):
                self._fire(rule["action"])
                fired.append(rule["name"])

        if fired:
            logger.info(f"Rules fired: {', '.join(fired)}")

    def _matches(self, condition: dict, context: dict) -> bool:
        """Does this rule's condition match the current context?"""
        if not isinstance(condition, dict):
            return False

        for key, expected in condition.items():
            # Special operator: who_home_includes
            if key == "who_home_includes":
                who = context.get("who_home", [])
                if not isinstance(who, list):
                    who = []
                if expected not in who:
                    return False
                continue

            # Special operator: hour_gte / hour_lt
            if key == "hour_gte":
                if context.get("hour", 0) < expected:
                    return False
                continue
            if key == "hour_lt":
                if context.get("hour", 24) >= expected:
                    return False
                continue

            # Direct match
            actual = context.get(key)
            if actual != expected:
                return False

        return True

    def _fire(self, action: dict):
        """Execute a rule's action."""
        if not isinstance(action, dict):
            return

        # Adjust K values
        if "adjust" in action:
            for edge, spec in action["adjust"].items():
                if isinstance(spec, dict):
                    source = spec.get("source", "any")
                    k = spec.get("k", 0.25)
                    self.cavity.adjust(edge, k, source=source)
                elif isinstance(spec, (int, float)):
                    self.cavity.adjust(edge, float(spec))

        # Load a profile
        if "load_profile" in action:
            self.cavity.load_profile(action["load_profile"])

    # ── Rule Management (for Jaie) ───────────────────────────

    def add_rule(self, name: str, description: str, condition: dict,
                 action: dict, priority: int = 10) -> int:
        """Add a new context rule. Returns rule ID."""
        try:
            cur = self._db().cursor()
            cur.execute(
                """INSERT INTO context_rules (name, description, condition, action, priority)
                   VALUES (%s, %s, %s, %s, %s) RETURNING id""",
                (name, description, json.dumps(condition), json.dumps(action), priority)
            )
            rule_id = cur.fetchone()[0]
            cur.close()
            self._load_rules()  # refresh cache
            return rule_id
        except Exception as e:
            logger.warning(f"Failed to add rule: {e}")
            return -1

    def list_rules(self) -> list:
        """List all active rules."""
        return [
            {"id": r["id"], "name": r["name"], "priority": r["priority"],
             "condition": r["condition"], "action": r["action"]}
            for r in self._rules
        ]

    def close(self):
        if self._conn and not self._conn.closed:
            self._conn.close()


# ── Quick test ───────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")

    print("Context Manager — Test\n")

    cavity = Cavity("kai-ctx-test")
    cm = ContextManager(cavity)

    # Show loaded rules
    print(f"Loaded {len(cm.list_rules())} rules:")
    for r in cm.list_rules():
        print(f"  [{r['id']}] {r['name']} (p={r['priority']})")

    # Test: tick (time-based)
    print("\nTick (time update):")
    cm.tick()
    ctx = cavity.get_context()
    print(f"  Period: {ctx.get('time_period')}, Hour: {ctx.get('hour')}, Day: {ctx.get('day')}")

    # Test: who_home update
    print("\nUpdate who_home = ['jaie']:")
    cm.update("who_home", ["jaie"])
    print(f"  sense_think(ear): {cavity.get_k('sense_think', 'ear')}")
    print(f"  sense_think(eye): {cavity.get_k('sense_think', 'eye')}")

    # Test: nobody home
    print("\nUpdate who_home = []:")
    cm.update("who_home", [])
    print(f"  Profile should be guardian — all K high")
    print(f"  sense_think: {cavity.get_k('sense_think')}")
    print(f"  think_act: {cavity.get_k('think_act')}")

    # Test: add a custom rule
    print("\nAdd custom rule:")
    rid = cm.add_rule(
        "game_time", "When playing game, increase eye sensitivity",
        {"activity": "playing_game"},
        {"adjust": {"sense_think": {"source": "eye", "k": 0.95}}},
        priority=25
    )
    print(f"  Rule ID: {rid}")
    cm.update("activity", "playing_game")
    print(f"  sense_think(eye): {cavity.get_k('sense_think', 'eye')}")

    cm.close()
    cavity.close()
    print("\nDone.")
