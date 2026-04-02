"""OMDR Cavity — Kai's nervous system core.

One system, not parts. Four nodes (sense, think, act, test) connected
by edges with adjustable K values. Attention sets all K values based
on context. Companions are different K profiles of the same graph.

The cavity IS an OMDR system:
  - Nodes are frequency generators
  - K values are coupling strengths
  - Attention adjusts coupling
  - Companions are resonance modes
  - K=0.25 is the default (optimal coupling)

Usage:
    cavity = Cavity("kai-birthday")
    cavity.load_profile("listener")           # set K profile
    result = cavity.perceive(signal)           # run signal through
    cavity.adjust("sense_think", k=0.8)       # manual adjustment
    cavity.update_context("who_home", ["jaie", "arthur"])  # context shift

Jaie Parker + Kai, 2026-04-02 (birthday build)
"""

import json
import time
import logging
from datetime import datetime, timezone, timedelta
from typing import Any

import psycopg2
import psycopg2.extras

logger = logging.getLogger("cavity")

DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "user": "kai",
    "password": "resonance",
    "dbname": "kai_v2",
}

# The four nodes
NODES = ["sense", "think", "act", "test"]

# The edges (connections between nodes)
EDGES = {
    "sense_think": ("sense", "think"),
    "think_act": ("think", "act"),
    "act_test": ("act", "test"),
    "test_sense": ("test", "sense"),  # feedback loop
}

AEST = timezone(timedelta(hours=11))


class Signal:
    """A signal flowing through the cavity."""

    def __init__(self, source: str, signal_type: str, data: dict = None):
        self.source = source
        self.signal_type = signal_type
        self.data = data or {}
        self.timestamp = datetime.now(AEST).isoformat()
        self.path = []           # nodes visited
        self.k_values = {}       # K at each edge when traversed
        self.enrichments = {}    # data added by each node
        self.dropped = False     # True if filtered out
        self.outcome = "pending"

    def to_dict(self):
        return {
            "source": self.source,
            "type": self.signal_type,
            "data": self.data,
            "timestamp": self.timestamp,
            "path": self.path,
            "k_values": self.k_values,
            "enrichments": self.enrichments,
            "outcome": self.outcome,
        }


class Cavity:
    """The OMDR cavity. One graph. Adjustable K. Context-aware."""

    def __init__(self, name: str = "kai"):
        self.name = name
        self._conn = None
        self._k_cache = {}        # edge -> K value (loaded from DB)
        self._context_cache = {}  # key -> value
        self._handlers = {        # node -> processing function
            "sense": self._node_sense,
            "think": self._node_think,
            "act": self._node_act,
            "test": self._node_test,
        }
        self._action_handlers = []  # registered callbacks for ACT node
        self._load_filters()
        self._load_context()

    # ── Database ─────────────────────────────────────────────

    def _db(self):
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(**DB_CONFIG)
            self._conn.autocommit = True
        return self._conn

    def _load_filters(self):
        """Load K values from database."""
        try:
            cur = self._db().cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("SELECT edge, source_organ, k, context_rules FROM filters")
            for row in cur.fetchall():
                key = f"{row['edge']}:{row['source_organ']}"
                self._k_cache[key] = {
                    "k": row["k"],
                    "rules": row["context_rules"] or [],
                }
            cur.close()
        except Exception as e:
            logger.warning(f"Failed to load filters: {e}")
            # Defaults
            for edge in EDGES:
                self._k_cache[f"{edge}:any"] = {"k": 0.25, "rules": []}

    def _load_context(self):
        """Load context from database."""
        try:
            cur = self._db().cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("SELECT key, value FROM context")
            for row in cur.fetchall():
                self._context_cache[row["key"]] = row["value"]
            cur.close()
        except Exception as e:
            logger.warning(f"Failed to load context: {e}")

    # ── K Values (the edges) ─────────────────────────────────

    def get_k(self, edge: str, source: str = "any") -> float:
        """Get the K value for an edge, considering source and context."""
        # Try source-specific first, fall back to 'any'
        key = f"{edge}:{source}"
        entry = self._k_cache.get(key) or self._k_cache.get(f"{edge}:any")
        if not entry:
            return 0.25  # OMDR default

        base_k = entry["k"]

        # Apply context rules
        for rule in entry.get("rules", []):
            condition = rule.get("when", "")
            ctx_value = self._context_cache.get(condition)
            if ctx_value is not None:
                # Rule matches a context key — apply its K override
                return rule.get("k", base_k)

        return base_k

    def adjust(self, edge: str, k: float, source: str = "any"):
        """Adjust a K value. Persists to database."""
        k = max(0.0, min(1.0, k))  # clamp
        key = f"{edge}:{source}"
        if key in self._k_cache:
            self._k_cache[key]["k"] = k
        else:
            self._k_cache[key] = {"k": k, "rules": []}

        try:
            cur = self._db().cursor()
            cur.execute(
                """INSERT INTO filters (edge, source_organ, k)
                   VALUES (%s, %s, %s)
                   ON CONFLICT (edge, source_organ)
                   DO UPDATE SET k = %s, updated_at = NOW()""",
                (edge, source, k, k)
            )
            cur.close()
        except Exception as e:
            logger.warning(f"Failed to persist K: {e}")

    def load_profile(self, profile_name: str):
        """Load a K profile — changes all edges at once."""
        try:
            cur = self._db().cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("SELECT filters FROM profiles WHERE name = %s", (profile_name,))
            row = cur.fetchone()
            cur.close()
            if row and row["filters"]:
                filters = row["filters"] if isinstance(row["filters"], dict) else json.loads(row["filters"])
                for edge, k in filters.items():
                    self.adjust(edge, k)
                logger.info(f"Loaded profile: {profile_name}")
                return True
        except Exception as e:
            logger.warning(f"Failed to load profile: {e}")
        return False

    # ── Context (what sets K values) ─────────────────────────

    def update_context(self, key: str, value: Any):
        """Update a context value. Triggers K re-evaluation."""
        self._context_cache[key] = value
        try:
            cur = self._db().cursor()
            cur.execute(
                """INSERT INTO context (key, value, updated_at)
                   VALUES (%s, %s, NOW())
                   ON CONFLICT (key) DO UPDATE SET value = %s, updated_at = NOW()""",
                (key, json.dumps(value), json.dumps(value))
            )
            cur.close()
        except Exception as e:
            logger.warning(f"Failed to persist context: {e}")

    def get_context(self, key: str = None) -> Any:
        """Get context value(s)."""
        if key:
            return self._context_cache.get(key)
        return dict(self._context_cache)

    # ── Signal Flow (the main loop) ──────────────────────────

    def perceive(self, signal: Signal) -> Signal:
        """Run a signal through the cavity. The core operation.

        Signal flows: sense → think → act → test
        Each edge has a K value. If K is too low, signal is dropped.
        """
        # SENSE
        signal = self._traverse_node("sense", signal)
        if signal.dropped:
            signal.outcome = "filtered_at_sense"
            self._log_signal(signal)
            return signal

        # sense → think edge
        k = self.get_k("sense_think", signal.source)
        signal.k_values["sense_think"] = k
        if not self._passes_filter(k):
            signal.outcome = "filtered_sense_think"
            signal.dropped = True
            self._log_signal(signal)
            return signal

        # THINK
        signal = self._traverse_node("think", signal)
        if signal.dropped:
            signal.outcome = "filtered_at_think"
            self._log_signal(signal)
            return signal

        # think → act edge
        k = self.get_k("think_act", signal.source)
        signal.k_values["think_act"] = k
        if not self._passes_filter(k):
            signal.outcome = "noted"  # thought about but didn't act
            self._log_signal(signal)
            return signal

        # ACT
        signal = self._traverse_node("act", signal)

        # act → test edge
        k = self.get_k("act_test", signal.source)
        signal.k_values["act_test"] = k
        if self._passes_filter(k):
            # TEST
            signal = self._traverse_node("test", signal)

        signal.outcome = "completed"
        self._log_signal(signal)
        return signal

    def _passes_filter(self, k: float) -> bool:
        """Does this signal pass through the edge?
        K=0 always blocks. K=1 always passes.
        Between: probabilistic based on K (but deterministic for now — threshold at 0.15).
        """
        return k > 0.15

    def _traverse_node(self, node: str, signal: Signal) -> Signal:
        """Process signal through a node."""
        signal.path.append(node)
        handler = self._handlers.get(node)
        if handler:
            signal = handler(signal)
        return signal

    # ── Node Handlers (the processing) ───────────────────────

    def _node_sense(self, signal: Signal) -> Signal:
        """SENSE: Receive and enrich the signal."""
        signal.enrichments["sense"] = {
            "received_at": datetime.now(AEST).isoformat(),
            "context": dict(self._context_cache),
        }
        return signal

    def _node_think(self, signal: Signal) -> Signal:
        """THINK: Understand what the signal means."""
        # Default: classify urgency based on signal type and context
        urgency = signal.data.get("urgency", 0.5)

        # Context-aware urgency adjustment
        who_home = self._context_cache.get("who_home", [])
        time_period = self._context_cache.get("time_period", "day")

        # Someone's name mentioned → higher urgency
        if signal.data.get("speaker") in (who_home if isinstance(who_home, list) else []):
            urgency = min(1.0, urgency + 0.2)

        # Night time → lower threshold for alerts
        if time_period in ["night", "late_night"]:
            urgency = min(1.0, urgency + 0.1)

        signal.enrichments["think"] = {
            "urgency": urgency,
            "who_home": who_home,
            "time_period": time_period,
        }
        return signal

    def _node_act(self, signal: Signal) -> Signal:
        """ACT: Respond to the signal."""
        # Call registered action handlers
        for handler in self._action_handlers:
            try:
                handler(signal)
            except Exception as e:
                logger.warning(f"Action handler failed: {e}")

        signal.enrichments["act"] = {
            "handlers_called": len(self._action_handlers),
            "acted_at": datetime.now(AEST).isoformat(),
        }
        return signal

    def _node_test(self, signal: Signal) -> Signal:
        """TEST: Evaluate the response. Was it appropriate?"""
        signal.enrichments["test"] = {
            "tested_at": datetime.now(AEST).isoformat(),
            # Future: compare action outcome to expectation
        }
        return signal

    # ── Extension Points ─────────────────────────────────────

    def on_act(self, handler):
        """Register a callback for when the ACT node fires."""
        self._action_handlers.append(handler)

    def set_handler(self, node: str, handler):
        """Replace a node's processing function."""
        if node in NODES:
            self._handlers[node] = handler

    # ── Logging ──────────────────────────────────────────────

    def _log_signal(self, signal: Signal):
        """Log the signal's journey through the cavity."""
        try:
            cur = self._db().cursor()
            cur.execute(
                """INSERT INTO signals (source, signal_type, data, path, k_values, outcome)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (
                    signal.source,
                    signal.signal_type,
                    json.dumps(signal.data),
                    signal.path,
                    json.dumps(signal.k_values),
                    signal.outcome,
                )
            )
            cur.close()
        except Exception as e:
            logger.warning(f"Failed to log signal: {e}")

    # ── Cleanup ──────────────────────────────────────────────

    def close(self):
        if self._conn and not self._conn.closed:
            self._conn.close()


# ── Quick test ───────────────────────────────────────────────
if __name__ == "__main__":
    print("OMDR Cavity — Kai's Nervous System\n")

    cavity = Cavity("kai-birthday")

    # Test 1: Default K (0.25) — signal should pass sense→think but stop at think→act
    print("Test 1: Default K=0.25")
    sig = Signal("ear", "sound", {"volume": 0.3, "classification": "ambient"})
    result = cavity.perceive(sig)
    print(f"  Path: {result.path}")
    print(f"  K values: {result.k_values}")
    print(f"  Outcome: {result.outcome}")

    # Test 2: Load listener profile — high sense_think K
    print("\nTest 2: Listener profile")
    cavity.load_profile("listener")
    sig = Signal("ear", "speech", {"volume": 0.7, "speaker": "jaie", "urgency": 0.6})
    result = cavity.perceive(sig)
    print(f"  Path: {result.path}")
    print(f"  K values: {result.k_values}")
    print(f"  Outcome: {result.outcome}")

    # Test 3: Guardian profile — all edges high
    print("\nTest 3: Guardian profile")
    cavity.load_profile("guardian")
    sig = Signal("eye", "motion", {"movement": "large", "urgency": 0.8})
    result = cavity.perceive(sig)
    print(f"  Path: {result.path}")
    print(f"  K values: {result.k_values}")
    print(f"  Outcome: {result.outcome}")

    # Test 4: Context-aware adjustment
    print("\nTest 4: Context update")
    cavity.update_context("who_home", ["jaie", "arthur"])
    cavity.update_context("time_period", "evening")
    print(f"  Context: {cavity.get_context()}")

    # Test 5: Manual K adjustment
    print("\nTest 5: Manual adjust")
    cavity.adjust("sense_think", 0.95, source="ear")
    sig = Signal("ear", "speech", {"speaker": "arthur", "text": "Dad look!"})
    result = cavity.perceive(sig)
    print(f"  Path: {result.path}")
    print(f"  Outcome: {result.outcome}")
    print(f"  Think enrichment: {result.enrichments.get('think', {})}")

    cavity.close()
    print("\nDone. Nervous system is alive.")
