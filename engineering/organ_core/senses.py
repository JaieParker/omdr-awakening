"""Shared senses file — atomic read-modify-write to senses.json.

All organs write to one file. Each organ owns its own key.
Claude reads this single file for instant, non-blocking perception.

Race condition: two organs read-modify-write simultaneously, one overwrites
the other's update. But the "loser" updates again in seconds. For perception
data, a skipped beat is invisible. No corruption, just occasionally one cycle stale.

Jaie Parker with Claude (Anthropic), 2026-03-27
"""
import json
import os
import tempfile
import logging
from datetime import datetime, timezone

logger = logging.getLogger("senses")

# senses.json lives at the NervousSystem root
SENSES_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "senses.json"
)


def update_sense(organ_name: str, data: dict) -> None:
    """Atomically update one organ's entry in senses.json.

    Args:
        organ_name: Key name ("ear", "eye", "weather", "spotify")
        data: Dict to store under that key. Should include "perception" at minimum.
    """
    # Read current state
    current = {}
    try:
        with open(SENSES_PATH, "r", encoding="utf-8") as f:
            current = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    # Stamp and update this organ's entry
    data["updated"] = datetime.now(timezone.utc).isoformat()
    current[organ_name] = data

    # Atomic write: temp file in same dir + os.replace()
    dir_name = os.path.dirname(SENSES_PATH)
    fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2, default=str)
        os.replace(tmp_path, SENSES_PATH)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def read_senses() -> dict:
    """Read the current senses file. Returns empty dict if missing."""
    try:
        with open(SENSES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
