"""LSL recorder — subscribes to Muse LSL outlets and saves each stream to FIF.

Replaces LabRecorder.exe for our purposes. Uses mne-lsl's inlet API to pull
samples from every LSL stream the Muse (via OpenMuse) is publishing, then
saves each stream as a separate MNE FIF file in the session's BIDS directory.

The recorder is the Path A writer in the dual-path architecture. It only
writes files; it never touches the database. Post-session ingestion
(separate script) reads the FIF files and populates Postgres Path B.

Design choices (per the STORAGE-PLAN-v2 synthesis + the non-destructive
principle + the round-2 validator catches):

1. FIF instead of XDF — because XDF has no mature Python writer and
   MNE-Python reads FIF natively. We can convert FIF to EDF or XDF at
   session end if we need those formats for interop. FIF is the primary
   persistent format.

2. One FIF per stream — because each stream has a different sample rate
   and MNE's Raw is single-sample-rate. Cross-stream alignment happens
   at analysis time using the dual timestamp pairs stored in the marker
   and clock-sync metadata files.

3. Three timestamps per marker and sync event — host_clock_us (wall),
   lsl_clock_us (LSL unified). Device clock is not exposed by mne-lsl
   so we store NULL there and capture it via a side channel if needed.

4. Markers go via a dedicated LSL StringMarkers outlet that the experiment
   scripts push to (Gemini round-2 catch). The recorder subscribes to the
   markers outlet the same as any other Muse stream; at session end the
   marker samples are written as a JSON sidecar.

5. Y-split ready: multiple recorders can subscribe to the same LSL
   streams simultaneously without interfering. A live signal-quality
   display can run in parallel to this recorder without any coupling.

Usage:
    from lsl_recorder import Recorder

    with Recorder(session_dir="data/sub-jaie/ses-20260408T190000",
                  stream_filter=lambda s: s.name.startswith("Muse-") or s.name == "OMDR-Markers",
                  duration_s=360) as rec:
        rec.wait_until_done()

    # Files written to session_dir:
    #   eeg_raw.fif               — EEG stream as MNE Raw
    #   optics_raw.fif            — OPTICS stream as MNE Raw
    #   accgyro_raw.fif           — ACCGYRO stream as MNE Raw
    #   battery_raw.fif           — BATTERY stream as MNE Raw
    #   markers.json              — LSL StringMarkers + host timestamps
    #   clock_sync.json           — sync events captured at session start/end
    #   session_manifest.json     — session-level metadata (stream inventory, start/end, etc.)

Kai (Anthropic Claude instance) with Jaie Parker, 2026-04-07 overnight build.
"""
from __future__ import annotations

import json
import time
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Optional

import numpy as np


# ---------------------------------------------------------------------------
# Stream slug mapping — converts "Muse-EEG" → "eeg", etc.
# ---------------------------------------------------------------------------

def _stream_slug(stream_name: str) -> str:
    """Return a short file-safe slug for a stream name.

    'Muse-EEG (00:55:DA:BB:D9:53)' -> 'eeg'
    'Muse-OPTICS (00:55:DA:BB:D9:53)' -> 'optics'
    'Muse-ACCGYRO (00:55:DA:BB:D9:53)' -> 'accgyro'
    'Muse-BATTERY (00:55:DA:BB:D9:53)' -> 'battery'
    'OMDR-Markers' -> 'markers'
    """
    # Strip the MAC-address suffix and the 'Muse-' prefix
    base = stream_name.split(" ", 1)[0]
    if base.startswith("Muse-"):
        return base[len("Muse-"):].lower()
    if base.startswith("OMDR-"):
        return base[len("OMDR-"):].lower()
    return base.lower()


# ---------------------------------------------------------------------------
# Stream buffer — collects samples from one LSL inlet during recording
# ---------------------------------------------------------------------------

@dataclass
class StreamBuffer:
    name: str
    slug: str
    stype: str
    n_channels: int
    sfreq: float
    channel_labels: list[str]
    channel_units: list[str]
    source_id: str
    samples: list = field(default_factory=list)       # list of per-sample arrays
    lsl_times: list = field(default_factory=list)     # list of float LSL timestamps
    host_times: list = field(default_factory=list)    # list of float host wall-clock times
    n_chunks: int = 0
    n_dropped_reads: int = 0


# ---------------------------------------------------------------------------
# Recorder
# ---------------------------------------------------------------------------

class Recorder:
    """Background recorder that subscribes to LSL streams and saves to FIF.

    Parameters
    ----------
    session_dir : Path-like
        Directory where files will be written. Created if missing.
    stream_filter : Callable[[StreamInfo], bool]
        Returns True for streams to record. If None, records all discoverable streams.
    duration_s : float | None
        Stop automatically after this many seconds. If None, run until stop() is called.
    resolve_timeout_s : float
        How long to wait for LSL streams to become discoverable before giving up.
    min_streams : int
        Minimum number of streams that must be discovered before recording starts.
    """

    def __init__(
        self,
        session_dir: str | Path,
        stream_filter: Optional[Callable[[object], bool]] = None,
        duration_s: Optional[float] = None,
        resolve_timeout_s: float = 15.0,
        min_streams: int = 1,
    ):
        self.session_dir = Path(session_dir)
        self.stream_filter = stream_filter or (lambda s: True)
        self.duration_s = duration_s
        self.resolve_timeout_s = resolve_timeout_s
        self.min_streams = min_streams

        self.buffers: dict[str, StreamBuffer] = {}
        self.clock_sync_events: list[dict] = []
        self.started_at_host: Optional[float] = None
        self.ended_at_host: Optional[float] = None
        self._stop_flag = threading.Event()
        self._worker: Optional[threading.Thread] = None
        self._inlets: list = []
        self._exc: Optional[BaseException] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def start(self) -> None:
        if self._worker is not None:
            raise RuntimeError("Recorder already started")
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self._worker = threading.Thread(target=self._run, daemon=False)
        self._worker.start()

    def stop(self) -> None:
        self._stop_flag.set()
        if self._worker is not None:
            self._worker.join(timeout=30.0)
        self._worker = None

    def wait_until_done(self) -> None:
        """Block until the recorder's duration_s elapses or stop() is called."""
        if self._worker is None:
            raise RuntimeError("Recorder not started")
        self._worker.join()
        if self._exc is not None:
            raise self._exc

    def __enter__(self) -> "Recorder":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()

    # ------------------------------------------------------------------
    # Background worker
    # ------------------------------------------------------------------
    def _run(self) -> None:
        try:
            from mne_lsl.lsl import resolve_streams, StreamInlet, local_clock

            # Resolve streams and filter
            print(f"[recorder] resolving LSL streams for up to {self.resolve_timeout_s}s...")
            t_start = time.time()
            streams = []
            while time.time() - t_start < self.resolve_timeout_s:
                found = resolve_streams(timeout=2.0)
                filtered = [s for s in found if self.stream_filter(s)]
                if len(filtered) >= self.min_streams:
                    streams = filtered
                    break
                streams = filtered
                time.sleep(0.5)
            if not streams:
                raise RuntimeError("No LSL streams found matching the filter")
            print(f"[recorder] found {len(streams)} streams: {[s.name for s in streams]}")

            # Create inlets + buffers
            for s in streams:
                inlet = StreamInlet(s, max_buffered=600)
                inlet.open_stream()
                sinfo = inlet.get_sinfo()
                ch_info = sinfo.get_channel_info()
                ch_names = (ch_info or {}).get("ch_names", [f"ch{i}" for i in range(s.n_channels)])
                # Units — check if the channel info has them
                ch_units = []
                chs = (ch_info or {}).get("chs", [])
                for ch in chs:
                    u = ch.get("unit") if isinstance(ch, dict) else None
                    ch_units.append(str(u) if u is not None else "unknown")
                while len(ch_units) < s.n_channels:
                    ch_units.append("unknown")

                slug = _stream_slug(s.name)
                self.buffers[s.name] = StreamBuffer(
                    name=s.name,
                    slug=slug,
                    stype=s.stype,
                    n_channels=s.n_channels,
                    sfreq=s.sfreq,
                    channel_labels=ch_names,
                    channel_units=ch_units,
                    source_id=s.source_id,
                )
                self._inlets.append((s, inlet))

            # Session start sync event
            self.started_at_host = time.time()
            self.clock_sync_events.append({
                "label": "session_start",
                "host_clock_us": int(self.started_at_host * 1e6),
                "lsl_clock_sec": float(local_clock()),
            })
            print(f"[recorder] recording started at host time {self.started_at_host}")

            # Recording loop
            deadline = (self.started_at_host + self.duration_s) if self.duration_s else None
            while not self._stop_flag.is_set():
                if deadline is not None and time.time() >= deadline:
                    break
                for s, inlet in self._inlets:
                    # Pull up to ~100 ms worth of samples per poll per stream
                    max_samples = max(1, int(s.sfreq * 0.15)) if s.sfreq > 0 else 32
                    try:
                        chunk, ts = inlet.pull_chunk(timeout=0.02, max_samples=max_samples)
                    except Exception as e:
                        self.buffers[s.name].n_dropped_reads += 1
                        continue
                    if chunk is None or len(chunk) == 0:
                        continue
                    now = time.time()
                    buf = self.buffers[s.name]
                    # Store each sample with both its LSL time and the host time at pull moment
                    for i, sample in enumerate(chunk):
                        buf.samples.append(list(sample))
                        buf.lsl_times.append(float(ts[i]) if i < len(ts) else float("nan"))
                        # All samples in a chunk share the same pull-moment host time — good enough
                        buf.host_times.append(now)
                    buf.n_chunks += 1
                time.sleep(0.005)

            # Session end sync event
            self.ended_at_host = time.time()
            self.clock_sync_events.append({
                "label": "session_end",
                "host_clock_us": int(self.ended_at_host * 1e6),
                "lsl_clock_sec": float(local_clock()),
            })
            print(f"[recorder] recording stopped at host time {self.ended_at_host}")

            # Close inlets
            for s, inlet in self._inlets:
                try:
                    inlet.close_stream()
                except Exception:
                    pass

            # Persist to disk
            self._save()

        except BaseException as e:
            self._exc = e
            print(f"[recorder] ERROR: {type(e).__name__}: {e}")
            raise

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def _save(self) -> None:
        import mne

        manifest = {
            "started_at_host_us": int((self.started_at_host or 0) * 1e6),
            "ended_at_host_us": int((self.ended_at_host or 0) * 1e6),
            "duration_s": (self.ended_at_host - self.started_at_host) if (self.started_at_host and self.ended_at_host) else None,
            "streams": [],
        }

        # Pull markers aside from the regular stream save path
        markers_buf = None
        regular_bufs: list[StreamBuffer] = []
        for buf in self.buffers.values():
            if buf.slug == "markers":
                markers_buf = buf
            else:
                regular_bufs.append(buf)

        for buf in regular_bufs:
            n_samples = len(buf.samples)
            stream_manifest = {
                "name": buf.name,
                "slug": buf.slug,
                "stype": buf.stype,
                "n_channels": buf.n_channels,
                "sfreq_nominal": buf.sfreq,
                "n_samples_collected": n_samples,
                "channel_labels": buf.channel_labels,
                "channel_units": buf.channel_units,
                "source_id": buf.source_id,
                "n_chunks": buf.n_chunks,
                "n_dropped_reads": buf.n_dropped_reads,
                "fif_path": None,
                "timestamps_path": None,
            }
            if n_samples == 0:
                print(f"[recorder] {buf.name}: no samples collected, skipping FIF")
                manifest["streams"].append(stream_manifest)
                continue

            # MNE expects (n_channels, n_samples)
            data = np.asarray(buf.samples, dtype=np.float64).T
            # Pick MNE channel types based on the stream kind
            kind_to_mnetype = {
                "eeg": "eeg",
                "optics": "misc",     # MNE doesn't have a first-class fNIRS type for raw; "fnirs_od" exists but needs specific formatting
                "accgyro": "misc",
                "battery": "misc",
                "ppg": "misc",
            }
            ch_type = kind_to_mnetype.get(buf.slug, "misc")

            # Estimate actual sample rate from LSL timestamps
            if len(buf.lsl_times) >= 2:
                dt = np.diff(buf.lsl_times)
                dt = dt[(dt > 0) & np.isfinite(dt)]
                sfreq_actual = float(1.0 / np.median(dt)) if len(dt) > 0 else float(buf.sfreq)
            else:
                sfreq_actual = float(buf.sfreq)
            stream_manifest["sfreq_actual"] = sfreq_actual

            info = mne.create_info(
                ch_names=buf.channel_labels[:buf.n_channels],
                sfreq=sfreq_actual,
                ch_types=[ch_type] * buf.n_channels,
            )
            raw = mne.io.RawArray(data, info, verbose="ERROR")
            fif_path = self.session_dir / f"{buf.slug}_raw.fif"
            raw.save(fif_path, overwrite=True, verbose="ERROR")
            stream_manifest["fif_path"] = str(fif_path.relative_to(self.session_dir))

            # Save LSL + host timestamps as a separate .npz (MNE Raw doesn't preserve them)
            ts_path = self.session_dir / f"{buf.slug}_timestamps.npz"
            np.savez(
                ts_path,
                lsl_times=np.asarray(buf.lsl_times, dtype=np.float64),
                host_times=np.asarray(buf.host_times, dtype=np.float64),
            )
            stream_manifest["timestamps_path"] = str(ts_path.relative_to(self.session_dir))

            manifest["streams"].append(stream_manifest)
            print(f"[recorder] saved {buf.name}: {n_samples} samples -> {fif_path.name}")

        # Markers: save as JSON (not FIF — markers are strings, not numeric)
        if markers_buf is not None and markers_buf.samples:
            markers_json = [
                {
                    "lsl_clock_sec": float(t),
                    "host_clock_us": int(h * 1e6),
                    "label": s[0] if isinstance(s, (list, tuple)) and len(s) > 0 else str(s),
                }
                for t, h, s in zip(markers_buf.lsl_times, markers_buf.host_times, markers_buf.samples)
            ]
            markers_path = self.session_dir / "markers.json"
            with open(markers_path, "w", encoding="utf-8") as f:
                json.dump(markers_json, f, indent=2)
            print(f"[recorder] saved {len(markers_json)} markers -> {markers_path.name}")
            manifest["markers_path"] = "markers.json"
        else:
            manifest["markers_path"] = None

        # Clock sync events
        sync_path = self.session_dir / "clock_sync.json"
        with open(sync_path, "w", encoding="utf-8") as f:
            json.dump(self.clock_sync_events, f, indent=2)
        manifest["clock_sync_path"] = "clock_sync.json"

        # Session manifest
        manifest_path = self.session_dir / "session_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, default=str)
        print(f"[recorder] wrote manifest -> {manifest_path}")


# ---------------------------------------------------------------------------
# CLI entry point for standalone testing
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    from datetime import datetime

    parser = argparse.ArgumentParser(description="LSL recorder — saves Muse LSL streams to FIF")
    parser.add_argument("--session-dir", type=str, default=None, help="Output directory (default: data/sub-jaie/ses-<timestamp>)")
    parser.add_argument("--duration", type=float, default=30.0, help="Recording duration in seconds")
    parser.add_argument("--subject", type=str, default="jaie", help="Subject ID for default path")
    parser.add_argument("--all", action="store_true", help="Record ALL discoverable streams instead of just Muse-*")
    args = parser.parse_args()

    if args.session_dir is None:
        ts = datetime.now().strftime("%Y%m%dT%H%M%S")
        args.session_dir = f"data/sub-{args.subject}/ses-{ts}"

    def stream_filter(s):
        if args.all:
            return True
        return s.name.startswith("Muse-") or s.name == "OMDR-Markers"

    with Recorder(session_dir=args.session_dir, stream_filter=stream_filter, duration_s=args.duration) as rec:
        rec.wait_until_done()

    print(f"\nRecorder finished. Output in: {args.session_dir}")
