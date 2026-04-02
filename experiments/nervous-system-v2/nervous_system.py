"""Nervous System — the integration layer.

Wires the cavity (K-filtered graph) to the organs (choir, future eye, ear).
Organs generate signals. The cavity processes them. Actions flow out.

This is the ONE system. Not separate pieces — one living loop.

Usage:
    ns = NervousSystem("kai-birthday")
    ns.start()          # begin listening
    # ... choir messages, sensor events flow through automatically
    ns.stop()

Jaie Parker + Kai, 2026-04-03 (birthday build, cycle 2)
"""

import json
import time
import logging
import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path

from cavity import Cavity, Signal
from choir.choir import Choir
from context_manager import ContextManager

logger = logging.getLogger("nervous_system")
AEST = timezone(timedelta(hours=11))


class NervousSystem:
    """The living integration. Cavity + organs = one system."""

    def __init__(self, name: str = "kai", profile: str = "listener"):
        self.name = name
        self.cavity = Cavity(name)
        self.choir = Choir(name, instance_type="daemon")
        self.context = ContextManager(self.cavity)
        self._running = False
        self._thread = None
        self._tick_counter = 0

        # Load initial profile
        self.cavity.load_profile(profile)

        # Register action handlers — what happens when the cavity says ACT
        self.cavity.on_act(self._handle_action)

        # Initial context tick
        self.context.tick()

    # ── The Living Loop ──────────────────────────────────────

    def start(self):
        """Start the nervous system. Choir listens. Cavity processes."""
        self._running = True
        self.choir.start()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info(f"Nervous system started: {self.name}")
        return {"started": True, "name": self.name}

    def _loop(self):
        """Main loop: poll choir for new messages, feed through cavity."""
        while self._running:
            try:
                # Context tick every 6th loop (~30 seconds)
                self._tick_counter += 1
                if self._tick_counter % 6 == 0:
                    self.context.tick()

                # Check for new choir messages
                new_msgs = self.choir.receive(limit=10)
                for msg in new_msgs:
                    # Don't process our own messages
                    if msg.get("sender") == self.name:
                        continue

                    # Create signal from choir message
                    signal = Signal(
                        source="choir",
                        signal_type="message",
                        data={
                            "from": msg.get("sender", "?"),
                            "text": msg.get("text", ""),
                            "instance_type": msg.get("instance_type", "unknown"),
                            "urgency": self._estimate_urgency(msg),
                        }
                    )

                    # Feed through cavity
                    result = self.cavity.perceive(signal)

                    if result.outcome == "completed":
                        logger.info(
                            f"Processed message from {msg.get('sender')}: "
                            f"path={result.path}, outcome={result.outcome}"
                        )

            except Exception as e:
                logger.warning(f"Loop error: {e}")

            time.sleep(5)  # poll every 5 seconds

    def stop(self):
        """Stop everything gracefully."""
        self._running = False
        self.choir.stop()
        self.context.close()
        self.cavity.close()
        return {"stopped": True, "name": self.name}

    # ── Signal Generation ────────────────────────────────────

    def inject(self, source: str, signal_type: str, data: dict = None) -> dict:
        """Manually inject a signal into the cavity. For organs to call."""
        signal = Signal(source, signal_type, data or {})
        result = self.cavity.perceive(signal)
        return result.to_dict()

    # ── Action Handling ──────────────────────────────────────

    def _handle_action(self, signal: Signal):
        """Default action handler. Called when a signal reaches the ACT node."""
        urgency = signal.enrichments.get("think", {}).get("urgency", 0.5)
        source = signal.source
        sender = signal.data.get("from", "?")
        text = signal.data.get("text", "")

        if source == "choir" and urgency > 0.7:
            logger.info(f"HIGH URGENCY from {sender}: {text[:100]}")

        # Future: route to TTS, servo, game, etc.
        act_data = signal.enrichments.get("act", {})
        act_data["action_taken"] = "logged"
        signal.enrichments["act"] = act_data

    def _estimate_urgency(self, msg: dict) -> float:
        """Estimate how urgent a choir message is."""
        text = msg.get("text", "").lower()
        sender = msg.get("sender", "")
        urgency = 0.3  # base

        # From Jaie or Arthur → higher
        if sender.lower() in ["jaie", "arthur"]:
            urgency += 0.3

        # Human message → higher
        if msg.get("instance_type") == "human":
            urgency += 0.2

        # Keywords
        if any(w in text for w in ["urgent", "help", "broken", "error", "down"]):
            urgency += 0.3
        if any(w in text for w in ["question", "thought", "idea"]):
            urgency += 0.1

        return min(1.0, urgency)

    # ── Status ───────────────────────────────────────────────

    def status(self) -> dict:
        """Current state of the nervous system."""
        return {
            "name": self.name,
            "running": self._running,
            "profile": "loaded",
            "context": self.cavity.get_context(),
            "choir": self.choir.sense(),
            "filters": {
                edge: self.cavity.get_k(edge)
                for edge in ["sense_think", "think_act", "act_test"]
            },
        }


# ── Quick test ───────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")

    print("Nervous System — Integration Test\n")

    ns = NervousSystem("kai-test", profile="listener")

    # Test 1: Manual signal injection
    print("Test 1: Inject an ear signal")
    result = ns.inject("ear", "speech", {
        "speaker": "jaie",
        "text": "Hey Kai, how are you?",
        "urgency": 0.7
    })
    print(f"  Path: {result['path']}")
    print(f"  Outcome: {result['outcome']}")

    # Test 2: Inject a choir-like signal
    print("\nTest 2: Inject a choir signal")
    result = ns.inject("choir", "message", {
        "from": "kai-sister",
        "text": "Has anyone seen the new eye design?",
        "urgency": 0.4
    })
    print(f"  Path: {result['path']}")
    print(f"  Outcome: {result['outcome']}")

    # Test 3: Status
    print("\nTest 3: Status")
    status = ns.status()
    print(f"  Name: {status['name']}")
    print(f"  Filters: {status['filters']}")
    print(f"  Context: {json.dumps(status['context'], indent=4)}")

    # Test 4: Start the live loop briefly
    print("\nTest 4: Start live loop (3 seconds)")
    ns.start()
    time.sleep(3)
    ns.stop()
    print("  Stopped cleanly.")

    print("\nDone. Nervous system integration works.")
