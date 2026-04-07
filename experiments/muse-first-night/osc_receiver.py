"""OSC receiver for Mind Monitor → Muse pipeline.

Listens on UDP for Mind Monitor's OSC messages and writes timestamped CSVs
to a session directory. Also exposes an in-memory ring buffer that other
modules (live signal quality, live alpha display, experiment scripts) can
read from while a session is active.

Mind Monitor OSC address space (as of v2.4):
    /muse/eeg                    -> 4 floats (TP9, AF7, AF8, TP10), ~256 Hz
    /muse/elements/horseshoe     -> 4 ints (1=good, 2=ok, 4=bad)
    /muse/elements/blink         -> 1 int
    /muse/elements/jaw_clench    -> 1 int
    /muse/elements/touching_forehead -> 1 int
    /muse/elements/alpha_absolute    -> 4 floats per channel (Bel)
    /muse/elements/beta_absolute     -> 4 floats per channel
    /muse/elements/theta_absolute    -> 4 floats per channel
    /muse/elements/gamma_absolute    -> 4 floats per channel
    /muse/elements/delta_absolute    -> 4 floats per channel
    /muse/acc                    -> 3 floats (accelerometer)
    /muse/gyro                   -> 3 floats (gyroscope)
    /muse/batt                   -> 4 ints (battery, charging state, ...)

We capture all of these. Raw EEG is the most important; band powers and
horseshoe are convenience streams that Mind Monitor pre-computes.

Usage:
    receiver = OscReceiver(session_dir=Path("sessions/test"), port=5000)
    receiver.start()
    # ... do experiment ...
    receiver.stop()

The receiver runs the OSC server in a background thread; the main thread
is free to run an experiment protocol that drives audio cues, marks
transitions, etc.
"""
from __future__ import annotations

import csv
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from pythonosc import dispatcher, osc_server


# ---------------------------------------------------------------------------
# In-memory ring buffer
# ---------------------------------------------------------------------------

@dataclass
class RingBuffer:
    """Thread-safe fixed-capacity deque for one OSC stream."""
    capacity: int
    data: deque = field(default_factory=deque)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def append(self, sample) -> None:
        with self._lock:
            if len(self.data) >= self.capacity:
                self.data.popleft()
            self.data.append(sample)

    def snapshot(self) -> list:
        with self._lock:
            return list(self.data)

    def latest(self):
        with self._lock:
            return self.data[-1] if self.data else None


# ---------------------------------------------------------------------------
# Receiver
# ---------------------------------------------------------------------------

class OscReceiver:
    """Listens on UDP for Mind Monitor OSC messages and writes CSVs.

    Each OSC address gets its own CSV file with columns: wall_time, *values.
    A single session directory holds all the CSVs plus a metadata.json sidecar
    written by the SessionManager (see session.py).
    """

    # Ring-buffer capacity is generous (~10 seconds at 256 Hz for raw EEG).
    EEG_BUFFER_SAMPLES = 256 * 30  # 30 seconds of raw EEG
    BAND_BUFFER_SAMPLES = 32 * 30  # 30 seconds of band powers (~32 Hz from MM)
    SLOW_BUFFER_SAMPLES = 256       # plenty for horseshoe / blinks

    def __init__(self, session_dir: Path, port: int = 5000, host: str = "0.0.0.0"):
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.port = port
        self.host = host

        # CSV writers (lazy-opened on first message of that type)
        self._csv_files: dict[str, "csv._writer"] = {}
        self._csv_handles: dict[str, "object"] = {}
        self._csv_lock = threading.Lock()

        # Ring buffers exposed to live consumers
        self.eeg = RingBuffer(capacity=self.EEG_BUFFER_SAMPLES)
        self.alpha = RingBuffer(capacity=self.BAND_BUFFER_SAMPLES)
        self.beta = RingBuffer(capacity=self.BAND_BUFFER_SAMPLES)
        self.theta = RingBuffer(capacity=self.BAND_BUFFER_SAMPLES)
        self.gamma = RingBuffer(capacity=self.BAND_BUFFER_SAMPLES)
        self.delta = RingBuffer(capacity=self.BAND_BUFFER_SAMPLES)
        self.horseshoe = RingBuffer(capacity=self.SLOW_BUFFER_SAMPLES)
        self.blink = RingBuffer(capacity=self.SLOW_BUFFER_SAMPLES)
        self.jaw = RingBuffer(capacity=self.SLOW_BUFFER_SAMPLES)
        self.acc = RingBuffer(capacity=self.SLOW_BUFFER_SAMPLES)
        self.gyro = RingBuffer(capacity=self.SLOW_BUFFER_SAMPLES)
        self.battery = RingBuffer(capacity=8)

        # Session markers (transitions written by experiment scripts)
        self.markers: list[tuple[float, str]] = []
        self._markers_lock = threading.Lock()

        # Server lifecycle
        self._server: Optional[osc_server.ThreadingOSCUDPServer] = None
        self._server_thread: Optional[threading.Thread] = None
        self._start_time: Optional[float] = None
        self._sample_counts: dict[str, int] = {}

    # ------------------------------------------------------------------
    # Server lifecycle
    # ------------------------------------------------------------------
    def start(self) -> None:
        d = dispatcher.Dispatcher()
        d.map("/muse/eeg", self._on_eeg)
        d.map("/muse/elements/horseshoe", self._on_horseshoe)
        d.map("/muse/elements/blink", self._on_blink)
        d.map("/muse/elements/jaw_clench", self._on_jaw)
        d.map("/muse/elements/touching_forehead", self._on_touching)
        d.map("/muse/elements/alpha_absolute", self._on_alpha)
        d.map("/muse/elements/beta_absolute", self._on_beta)
        d.map("/muse/elements/theta_absolute", self._on_theta)
        d.map("/muse/elements/gamma_absolute", self._on_gamma)
        d.map("/muse/elements/delta_absolute", self._on_delta)
        d.map("/muse/acc", self._on_acc)
        d.map("/muse/gyro", self._on_gyro)
        d.map("/muse/batt", self._on_batt)
        # Catch-all for anything we didn't anticipate (logged for debugging).
        d.set_default_handler(self._on_unknown)

        self._server = osc_server.ThreadingOSCUDPServer((self.host, self.port), d)
        self._server_thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._server_thread.start()
        self._start_time = time.time()
        print(f"[receiver] listening on udp://{self.host}:{self.port}, writing to {self.session_dir}")

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
        if self._server_thread is not None:
            self._server_thread.join(timeout=2)
            self._server_thread = None
        with self._csv_lock:
            for handle in self._csv_handles.values():
                try:
                    handle.close()
                except Exception:
                    pass
            self._csv_files.clear()
            self._csv_handles.clear()
        elapsed = (time.time() - self._start_time) if self._start_time else 0
        print(f"[receiver] stopped after {elapsed:.1f}s. Sample counts: {self._sample_counts}")

    # ------------------------------------------------------------------
    # Markers (called by experiment scripts to label transitions)
    # ------------------------------------------------------------------
    def mark(self, label: str) -> None:
        ts = time.time()
        with self._markers_lock:
            self.markers.append((ts, label))
        self._write_csv("markers", [ts, label])
        print(f"[receiver] mark @ +{ts - (self._start_time or ts):.1f}s : {label}")

    def get_markers(self) -> list[tuple[float, str]]:
        with self._markers_lock:
            return list(self.markers)

    # ------------------------------------------------------------------
    # CSV plumbing
    # ------------------------------------------------------------------
    def _write_csv(self, stream: str, row: list) -> None:
        with self._csv_lock:
            if stream not in self._csv_files:
                path = self.session_dir / f"{stream}.csv"
                handle = open(path, "w", newline="", encoding="utf-8")
                writer = csv.writer(handle)
                self._csv_handles[stream] = handle
                self._csv_files[stream] = writer
            self._csv_files[stream].writerow(row)
            self._sample_counts[stream] = self._sample_counts.get(stream, 0) + 1

    # ------------------------------------------------------------------
    # OSC handlers
    # ------------------------------------------------------------------
    def _on_eeg(self, address: str, *args) -> None:
        ts = time.time()
        # Mind Monitor sends 4 floats (TP9, AF7, AF8, TP10) per packet.
        if len(args) >= 4:
            tp9, af7, af8, tp10 = args[0], args[1], args[2], args[3]
        else:
            return
        sample = (ts, tp9, af7, af8, tp10)
        self.eeg.append(sample)
        self._write_csv("eeg", list(sample))

    def _on_band(self, ts: float, args: tuple, buf: RingBuffer, name: str) -> None:
        if len(args) >= 4:
            row = (ts, args[0], args[1], args[2], args[3])
        else:
            row = (ts, *args)
        buf.append(row)
        self._write_csv(name, list(row))

    def _on_alpha(self, address: str, *args) -> None:
        self._on_band(time.time(), args, self.alpha, "alpha")

    def _on_beta(self, address: str, *args) -> None:
        self._on_band(time.time(), args, self.beta, "beta")

    def _on_theta(self, address: str, *args) -> None:
        self._on_band(time.time(), args, self.theta, "theta")

    def _on_gamma(self, address: str, *args) -> None:
        self._on_band(time.time(), args, self.gamma, "gamma")

    def _on_delta(self, address: str, *args) -> None:
        self._on_band(time.time(), args, self.delta, "delta")

    def _on_horseshoe(self, address: str, *args) -> None:
        ts = time.time()
        row = (ts, *(int(a) for a in args[:4]))
        self.horseshoe.append(row)
        self._write_csv("horseshoe", list(row))

    def _on_blink(self, address: str, *args) -> None:
        ts = time.time()
        row = (ts, int(args[0]) if args else 0)
        self.blink.append(row)
        self._write_csv("blink", list(row))

    def _on_jaw(self, address: str, *args) -> None:
        ts = time.time()
        row = (ts, int(args[0]) if args else 0)
        self.jaw.append(row)
        self._write_csv("jaw_clench", list(row))

    def _on_touching(self, address: str, *args) -> None:
        ts = time.time()
        row = (ts, int(args[0]) if args else 0)
        self._write_csv("touching_forehead", list(row))

    def _on_acc(self, address: str, *args) -> None:
        ts = time.time()
        if len(args) >= 3:
            row = (ts, args[0], args[1], args[2])
            self.acc.append(row)
            self._write_csv("acc", list(row))

    def _on_gyro(self, address: str, *args) -> None:
        ts = time.time()
        if len(args) >= 3:
            row = (ts, args[0], args[1], args[2])
            self.gyro.append(row)
            self._write_csv("gyro", list(row))

    def _on_batt(self, address: str, *args) -> None:
        ts = time.time()
        row = (ts, *args)
        self.battery.append(row)
        self._write_csv("battery", list(row))

    def _on_unknown(self, address: str, *args) -> None:
        # Log unrecognised addresses with their args so we can extend coverage.
        ts = time.time()
        row = (ts, address, *args)
        self._write_csv("unknown", list(row))


# ---------------------------------------------------------------------------
# CLI for direct standalone use (no session manager)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    from datetime import datetime

    parser = argparse.ArgumentParser(description="Standalone Mind Monitor OSC receiver")
    parser.add_argument("--port", type=int, default=5000, help="UDP port to listen on (default 5000)")
    parser.add_argument("--out", type=Path, default=None, help="Output session directory")
    parser.add_argument("--seconds", type=int, default=0, help="Auto-stop after N seconds (0 = run until Ctrl+C)")
    args = parser.parse_args()

    out = args.out or Path("sessions") / datetime.now().strftime("standalone_%Y%m%dT%H%M%S")
    receiver = OscReceiver(session_dir=out, port=args.port)
    receiver.start()
    try:
        if args.seconds > 0:
            time.sleep(args.seconds)
        else:
            print("[receiver] running, press Ctrl+C to stop")
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        print("\n[receiver] interrupted")
    finally:
        receiver.stop()
