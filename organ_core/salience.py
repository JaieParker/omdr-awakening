"""Salience Gate — the thalamus. Attention through change detection.

OMDR alignment:
  - Eq. 1: To exist is to change. Unchanged perception habituates.
  - Arnold tongues: Repeated same-category observations deepen the standing wave.
    Only disruption (leaving the tongue) generates salience.
  - K = 0.25: Balance between sensitivity (Yin) and selectivity (Yang).
    Too sensitive = overwhelmed. Too selective = missing things.
  - Startle = sudden decoherence: large feature delta shatters the standing wave.

Architecture:
  SalienceGateBase is abstract. Each organ provides a subclass that defines:
    - _extract_salience_features(data) -> dict of modality-specific features
    - _compute_feature_delta(current, baseline) -> float [0.0, 1.0]

Jaie Parker with Claude (Anthropic), 2026-03-27
"""
import time
import threading
from abc import abstractmethod
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

from organ_core.processor import Processor
from organ_core.context import PipelineContext


# ---------------------------------------------------------------------------
# Standing Wave — tracks one stable perceptual state (Arnold tongue)
# ---------------------------------------------------------------------------

@dataclass
class StandingWave:
    """A locked perceptual state. Deepens with each confirming observation."""

    category: str
    sub_category: str
    wave_strength: int = 1          # Arnold tongue depth
    locked_at: float = 0.0          # timestamp when wave formed
    last_confirmed: float = 0.0     # timestamp of last confirming observation
    feature_signature: dict = field(default_factory=dict)  # frozen features at lock-in

    @property
    def duration_s(self) -> float:
        """How long this wave has been standing."""
        if self.last_confirmed > 0:
            return self.last_confirmed - self.locked_at
        return 0.0


# ---------------------------------------------------------------------------
# Attention Buffer — thread-safe queue of salient events
# ---------------------------------------------------------------------------

class AttentionBuffer:
    """Thread-safe buffer of salient perceptual events.

    Events accumulate during background perception. Drained when the
    organ's hear()/see() is called — "what happened while you weren't looking."
    """

    def __init__(self, maxlen: int = 50):
        self._buffer: deque = deque(maxlen=maxlen)
        self._lock = threading.Lock()

    def push(self, event: dict) -> None:
        """Thread-safe append."""
        with self._lock:
            self._buffer.append(event)

    def drain(self) -> list:
        """Atomically return all events and clear the buffer."""
        with self._lock:
            events = list(self._buffer)
            self._buffer.clear()
            return events

    def peek(self) -> list:
        """Read without clearing."""
        with self._lock:
            return list(self._buffer)

    def __len__(self) -> int:
        with self._lock:
            return len(self._buffer)


# ---------------------------------------------------------------------------
# Salience Gate Base — the thalamus mechanism
# ---------------------------------------------------------------------------

class SalienceGateBase(Processor):
    """Abstract salience gate. Detects change, tracks habituation.

    Subclasses implement:
        _extract_salience_features(data) -> dict
        _compute_feature_delta(current, baseline) -> float [0.0, 1.0]
    """

    name = "salience_gate"
    description = "Attention gate: detects change from standing wave, scores salience"

    # Tunable thresholds — documented for easy adjustment
    DEFAULT_K = 0.25                # Attention balance (OMDR K)
    DEFAULT_STARTLE = 0.8           # Feature delta that shatters the wave
    DEFAULT_MAX_WAVE_STRENGTH = 20  # Cap on Arnold tongue depth

    def __init__(self, K: float = DEFAULT_K,
                 startle_threshold: float = DEFAULT_STARTLE,
                 max_wave_strength: int = DEFAULT_MAX_WAVE_STRENGTH):
        self.K = K
        self.startle_threshold = startle_threshold
        self.max_wave_strength = max_wave_strength

        self._standing_wave: Optional[StandingWave] = None

    def process(self, data: dict, context: PipelineContext) -> dict:
        classification = data.get("classification", {})
        category = classification.get("category", "unknown")
        sub_category = classification.get("sub_category", "")
        now = data.get("timestamp", time.time())

        # Extract modality-specific features
        features = self._extract_salience_features(data)

        # --- Compute salience ---
        score, reason, is_startle = self._score_salience(
            category, sub_category, features, now
        )

        # --- Write salience data to pipeline ---
        wave_info = None
        if self._standing_wave is not None:
            wave_info = {
                "category": self._standing_wave.category,
                "wave_strength": self._standing_wave.wave_strength,
                "duration_s": round(self._standing_wave.duration_s, 1),
            }

        data["salience"] = {
            "score": round(score, 3),
            "reason": reason,
            "is_startle": is_startle,
            "habituated": score < self.K,
            "standing_wave": wave_info,
        }

        return data

    def _score_salience(self, category: str, sub_category: str,
                        features: dict, now: float) -> tuple:
        """Core scoring logic. Returns (score, reason, is_startle)."""

        # First observation — everything is novel
        if self._standing_wave is None:
            self._standing_wave = StandingWave(
                category=category,
                sub_category=sub_category,
                wave_strength=1,
                locked_at=now,
                last_confirmed=now,
                feature_signature=features,
            )
            return (1.0, "first_observation", False)

        wave = self._standing_wave

        # Category change — standing wave shattered
        if category != wave.category:
            old_cat = wave.category
            self._standing_wave = StandingWave(
                category=category,
                sub_category=sub_category,
                wave_strength=1,
                locked_at=now,
                last_confirmed=now,
                feature_signature=features,
            )
            return (1.0, f"{old_cat}_to_{category}", False)

        # Same category — check for feature drift (startle within category)
        delta = self._compute_feature_delta(features, wave.feature_signature)
        if delta >= self.startle_threshold:
            # Sudden decoherence — wave shatters even though category matches
            self._standing_wave = StandingWave(
                category=category,
                sub_category=sub_category,
                wave_strength=1,
                locked_at=now,
                last_confirmed=now,
                feature_signature=features,
            )
            return (1.0, "startle", True)

        # Sub-category change — moderate disruption
        if sub_category != wave.sub_category:
            old_sub = wave.sub_category
            wave.sub_category = sub_category
            wave.wave_strength = max(1, wave.wave_strength // 2)  # Partial reset
            wave.last_confirmed = now
            wave.feature_signature = features
            return (0.6, f"{old_sub}_to_{sub_category}", False)

        # Confirming observation — deepen the Arnold tongue
        wave.wave_strength = min(wave.wave_strength + 1, self.max_wave_strength)
        wave.last_confirmed = now
        # Blend feature signature toward current (slow drift tolerance)
        wave.feature_signature = self._blend_features(
            wave.feature_signature, features, alpha=0.1
        )

        # Salience decays with wave strength: 1/(1 + strength * K)
        score = 1.0 / (1.0 + wave.wave_strength * self.K)

        # Feature delta adds a small boost even during habituation
        if delta > 0.3:
            score = min(score + delta * 0.3, 1.0)
            return (score, "feature_drift", False)

        return (score, "habituated", False)

    def _blend_features(self, old: dict, new: dict, alpha: float) -> dict:
        """Exponential moving average for numeric features.
        Allows slow drift without triggering startle."""
        blended = {}
        for key in old:
            old_val = old[key]
            new_val = new.get(key, old_val)
            if isinstance(old_val, (int, float)) and isinstance(new_val, (int, float)):
                blended[key] = old_val * (1 - alpha) + new_val * alpha
            else:
                blended[key] = new_val
        return blended

    # --- Abstract methods for subclasses ---

    @abstractmethod
    def _extract_salience_features(self, data: dict) -> dict:
        """Extract modality-specific features for salience comparison.

        Returns a dict of numeric (and optionally categorical) features
        that characterise the current perceptual state.
        """
        ...

    @abstractmethod
    def _compute_feature_delta(self, current: dict, baseline: dict) -> float:
        """Compute normalized distance between two feature sets.

        Returns a float in [0.0, 1.0] where:
          0.0 = identical
          1.0 = maximally different
        """
        ...
