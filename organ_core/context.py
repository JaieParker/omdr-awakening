"""PipelineContext — the neurotransmitter environment.

Shared mutable state accessible to all processors in a pipeline.
Holds the raw audio buffer, calibration state, processor stats,
and free-form shared values.
"""
from collections import deque
from typing import Any, Optional
import numpy as np


class PipelineContext:
    """Shared state for all processors in a pipeline."""

    def __init__(self, audio_buffer_seconds: float = 30.0, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self._max_audio_samples = int(audio_buffer_seconds * sample_rate)
        self.raw_audio_buffer: deque = deque()
        self._audio_samples_count = 0

        self.plane_state_key: Optional[dict] = None
        self.is_calibrated: bool = False

        self._stats: dict[str, dict] = {}
        self._shared: dict[str, Any] = {}

    # --- Shared key-value store ---

    def get(self, key: str, default: Any = None) -> Any:
        return self._shared.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._shared[key] = value

    # --- Raw audio buffer ---

    def push_audio(self, audio_chunk: np.ndarray) -> None:
        """Push a chunk of audio into the rolling buffer."""
        self.raw_audio_buffer.append(audio_chunk)
        self._audio_samples_count += len(audio_chunk)
        # Trim oldest chunks if over budget
        while self._audio_samples_count > self._max_audio_samples and self.raw_audio_buffer:
            oldest = self.raw_audio_buffer.popleft()
            self._audio_samples_count -= len(oldest)

    def get_recent_audio(self, seconds: float) -> np.ndarray:
        """Get the last N seconds of audio from the buffer."""
        if not self.raw_audio_buffer:
            return np.array([], dtype=np.float32)
        all_audio = np.concatenate(list(self.raw_audio_buffer))
        requested_samples = int(seconds * self.sample_rate)
        if len(all_audio) <= requested_samples:
            return all_audio
        return all_audio[-requested_samples:]

    # --- Processor stats ---

    def record_stat(self, processor_name: str, elapsed_ms: float) -> None:
        if processor_name not in self._stats:
            self._stats[processor_name] = {"call_count": 0, "total_ms": 0.0}
        self._stats[processor_name]["call_count"] += 1
        self._stats[processor_name]["total_ms"] += elapsed_ms

    def get_stats(self, processor_name: str) -> dict:
        if processor_name not in self._stats:
            return {"call_count": 0, "total_ms": 0.0, "avg_ms": 0.0}
        s = self._stats[processor_name]
        return {
            "call_count": s["call_count"],
            "total_ms": s["total_ms"],
            "avg_ms": s["total_ms"] / s["call_count"] if s["call_count"] > 0 else 0.0,
        }
