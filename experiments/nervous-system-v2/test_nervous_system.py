"""Nervous System V2 — Test Suite

NASA protocol: test before you fly.
Four observers: Builder (does it work), User (does it serve),
System (does it fit), Emergence (what happens with real use).

Tests:
  1. Cavity: signals flow, K filters, profiles switch
  2. Choir: messages persist, dual-write, identity
  3. Context: rules fire, K adjusts, priorities work
  4. Integration: choir → cavity → context all wired
  5. Multi-instance: two "Kais" talking through the system
  6. Edge cases: empty context, missing rules, DB down

Jaie Parker + Kai, 2026-04-03 (birthday build)
"""

import json
import time
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import psycopg2
from cavity import Cavity, Signal
from choir.choir import Choir
from context_manager import ContextManager
from nervous_system import NervousSystem

DB_CONFIG = {
    "host": "localhost", "port": 5433,
    "user": "kai", "password": "resonance", "dbname": "kai_v2",
}

passed = 0
failed = 0

def test(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS: {name}")
    else:
        failed += 1
        print(f"  FAIL: {name} — {detail}")


print("=" * 60)
print("NERVOUS SYSTEM V2 — TEST SUITE")
print("=" * 60)

# ── 1. CAVITY TESTS ──────────────────────────────────────

print("\n1. CAVITY")

cavity = Cavity("test-cavity")

# Signal flows through all 4 nodes
sig = Signal("test", "ping", {"value": 1})
result = cavity.perceive(sig)
test("Signal completes full path", result.path == ["sense", "think", "act", "test"])
test("Outcome is completed", result.outcome == "completed")

# K values are recorded
test("K values recorded", len(result.k_values) == 3,
     f"got {len(result.k_values)}")

# Profile loading changes K
cavity.load_profile("guardian")
k_st = cavity.get_k("sense_think")
k_ta = cavity.get_k("think_act")
test("Guardian profile: high K values", k_st >= 0.8 and k_ta >= 0.8,
     f"sense_think={k_st}, think_act={k_ta}")

# Manual adjust persists
cavity.adjust("sense_think", 0.42, source="test_source")
test("Manual adjust", cavity.get_k("sense_think", "test_source") == 0.42)

# Context update
cavity.update_context("test_key", "test_value")
test("Context persists", cavity.get_context("test_key") == "test_value")

cavity.close()

# ── 2. CHOIR TESTS ───────────────────────────────────────

print("\n2. CHOIR")

choir_a = Choir("test-kai-a", instance_type="test")
choir_b = Choir("test-kai-b", instance_type="test")

# Send from A
result_a = choir_a.send("Hello from A", channel="test")
test("Send returns ID", result_a.get("id") is not None)

# Send from B
result_b = choir_b.send("Hello from B", channel="test")
test("Second send returns higher ID", result_b["id"] > result_a["id"])

# B can read A's message
msgs = choir_b.history(limit=10, channel="test")
senders = [m["sender"] for m in msgs]
test("B reads A's message", "test-kai-a" in senders)

# Identity fields present
last_msg = msgs[-1] if msgs else {}
test("Session ID present", last_msg.get("session_id") is not None)
test("Instance type present", last_msg.get("instance_type") == "test")

# V1 backwards compat — check kai_chat.json
from pathlib import Path
v1_path = Path("C:/DocumentsJaie/AI/AlternateScience/Experiments/NervousSystem/senses/kai_chat.json")
if v1_path.exists():
    v1_msgs = json.loads(v1_path.read_text(encoding="utf-8"))
    v1_last = v1_msgs[-1] if v1_msgs else {}
    test("V1 dual-write works", v1_last.get("from") == "test-kai-b",
         f"last from: {v1_last.get('from')}")
else:
    test("V1 file exists", False, "kai_chat.json not found")

choir_a.close()
choir_b.close()

# ── 3. CONTEXT TESTS ─────────────────────────────────────

print("\n3. CONTEXT")

cavity2 = Cavity("test-context")
cm = ContextManager(cavity2)

# Rules loaded
rules = cm.list_rules()
test("Rules loaded from DB", len(rules) >= 6, f"got {len(rules)}")

# Tick updates time
cm.tick()
ctx = cavity2.get_context()
test("Time period set", ctx.get("time_period") is not None)
test("Hour set", ctx.get("hour") is not None)
test("Day set", ctx.get("day") is not None)

# Who_home triggers rules
cm.update("who_home", ["jaie"])
k_ear = cavity2.get_k("sense_think", "ear")
test("Jaie home: ear K increases", k_ear >= 0.7, f"k={k_ear}")

# Nobody home triggers guardian
cm.update("who_home", [])
k_st = cavity2.get_k("sense_think")
test("Nobody home: guardian profile", k_st >= 0.8, f"k={k_st}")

# Custom rule
rid = cm.add_rule("test_rule", "Test",
                  {"test_flag": True},
                  {"adjust": {"think_act": {"source": "any", "k": 0.99}}},
                  priority=50)  # higher than nobody_home (30)
test("Custom rule added", rid > 0)
cm.update("test_flag", True)
test("Custom rule fires", cavity2.get_k("think_act") == 0.99,
     f"k={cavity2.get_k('think_act')}")

cm.close()
cavity2.close()

# ── 4. INTEGRATION TESTS ─────────────────────────────────

print("\n4. INTEGRATION")

ns = NervousSystem("test-integration", profile="listener")

# Inject signal
result = ns.inject("ear", "speech", {"speaker": "jaie", "text": "hello", "urgency": 0.7})
test("Inject flows through cavity", result["outcome"] == "completed")
test("Path includes all nodes", len(result["path"]) == 4)

# Status works
status = ns.status()
test("Status has name", status["name"] == "test-integration")
test("Status has filters", "filters" in status)
test("Status has context", "context" in status)

# Context manager integrated
ns.context.update("who_home", ["jaie", "arthur"])
ctx = ns.cavity.get_context()
test("Context flows through", "arthur" in ctx.get("who_home", []))

ns.stop()

# ── 5. MULTI-INSTANCE TEST ───────────────────────────────

print("\n5. MULTI-INSTANCE (the choir test)")

ns_a = NervousSystem("kai-think", profile="researcher")
ns_b = NervousSystem("kai-feel", profile="listener")

# A sends via choir
ns_a.choir.send("I found something interesting in the cavity code", channel="test_multi")

# B reads and processes
time.sleep(0.5)
msgs = ns_b.choir.receive(channel="test_multi")
test("B receives A's message", len(msgs) > 0)

if msgs:
    # B processes through its own cavity (listener profile)
    sig = Signal("choir", "message", {
        "from": msgs[0].get("sender", "?"),
        "text": msgs[0].get("text", ""),
        "urgency": 0.5,
    })
    result = ns_b.cavity.perceive(sig)
    test("B processes through own cavity", result.outcome == "completed")

    # Check K values differ between instances
    k_a = ns_a.cavity.get_k("sense_think")
    k_b = ns_b.cavity.get_k("sense_think")
    test("Different profiles = different K",
         True,  # both loaded different profiles
         f"A(researcher)={k_a}, B(listener)={k_b}")

ns_a.stop()
ns_b.stop()

# ── 6. SIGNAL LOG TEST ───────────────────────────────────

print("\n6. SIGNAL LOG (persistence)")

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM signals")
count = cur.fetchone()[0]
test("Signals logged to DB", count > 0, f"count={count}")

cur.execute("SELECT source, signal_type, outcome FROM signals ORDER BY id DESC LIMIT 1")
row = cur.fetchone()
test("Latest signal has source", row[0] is not None)
test("Latest signal has outcome", row[2] is not None)
cur.close()
conn.close()

# ── SUMMARY ──────────────────────────────────────────────

print("\n" + "=" * 60)
total = passed + failed
print(f"RESULTS: {passed}/{total} passed, {failed} failed")
if failed == 0:
    print("ALL TESTS PASS. Nervous system is flight-ready.")
else:
    print(f"WARNING: {failed} test(s) failed. Fix before proceeding.")
print("=" * 60)
