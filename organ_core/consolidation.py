"""Fibonacci consolidation memory layers.

Each layer stores entries at a different time scale, following
phi-timed intervals. Raw → Pattern → Moment → Scene → Episode → Narrative.
Each level: less detail, more meaning, longer retention.

The dissipation follows the golden ratio — the same Fibonacci cascade
found in biological memory, emotional processing, and wave mechanics.
"""
import time
from collections import deque
from typing import Callable, Optional

PHI = 1.618033988749895

LAYER_NAMES = ["raw", "pattern", "moment", "scene", "episode", "narrative"]


class ConsolidationLayer:
    """One layer in the Fibonacci memory hierarchy."""

    def __init__(self, level: int, t0: float = 2.0, max_entries: int = 15):
        self.level = level
        self.t0 = t0
        self.interval = t0 * (PHI ** level)
        self.max_entries = max_entries
        self.buffer: deque = deque(maxlen=max_entries)
        self.last_consolidated = time.time()

    def should_consolidate(self, now: float) -> bool:
        """Check if enough time has passed since last consolidation."""
        return (now - self.last_consolidated) >= self.interval

    def add(self, entry: dict) -> None:
        """Add an entry to this layer's ring buffer."""
        self.buffer.append(entry)

    def get_recent(self, n: Optional[int] = None) -> list[dict]:
        """Get recent entries. If n specified, get last n entries."""
        entries = list(self.buffer)
        if n is not None:
            return entries[-n:]
        return entries

    def clear(self) -> None:
        """Clear the buffer."""
        self.buffer.clear()


class MemoryStack:
    """Stack of consolidation layers. Fibonacci-timed memory hierarchy.

    Push raw entries at the bottom. Consolidate upward using provided
    consolidator functions. Query at any depth level by name.
    """

    def __init__(self, t0: float = 2.0, num_layers: int = 6, max_entries: int = 15):
        self.t0 = t0
        self.layers = [
            ConsolidationLayer(level=i, t0=t0, max_entries=max_entries)
            for i in range(num_layers)
        ]
        # Map names to indices (use as many names as we have layers)
        self._name_map = {}
        for i in range(num_layers):
            if i < len(LAYER_NAMES):
                self._name_map[LAYER_NAMES[i]] = i

    def layer_index(self, name: str) -> int:
        """Get layer index by name. Raises KeyError if not found."""
        if name not in self._name_map:
            raise KeyError(
                f"Unknown layer name '{name}'. Valid: {list(self._name_map.keys())}"
            )
        return self._name_map[name]

    def push(self, entry: dict) -> None:
        """Add an entry to layer 0 (raw)."""
        self.layers[0].add(entry)

    def consolidate(self, from_level: int, to_level: int,
                    consolidator: Callable[[list[dict]], dict]) -> None:
        """Consolidate entries from one level to the next.

        Args:
            from_level: Source layer index.
            to_level: Destination layer index.
            consolidator: Function that takes a list of entries from the source
                         layer and returns a single consolidated entry for the
                         destination layer.
        """
        source = self.layers[from_level]
        entries = source.get_recent()
        if not entries:
            return
        consolidated = consolidator(entries)
        self.layers[to_level].add(consolidated)
        source.last_consolidated = time.time()

    def query(self, depth: str = "raw") -> list[dict]:
        """Query entries at a specific depth level by name."""
        idx = self.layer_index(depth)
        return self.layers[idx].get_recent()

    def stats(self) -> dict:
        """Return stats for all layers."""
        result = {"num_layers": len(self.layers)}
        for i, layer in enumerate(self.layers):
            result[f"layer_{i}_count"] = len(layer.buffer)
            result[f"layer_{i}_interval"] = layer.interval
        return result
