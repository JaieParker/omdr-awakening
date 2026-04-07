"""Mock LSL publisher — creates synthetic Muse LSL outlets for end-to-end testing.

Publishes four LSL outlets matching the observed Athena stream profile:
  Muse-EEG      8 channels @ 256 Hz  (float32)
  Muse-OPTICS   16 channels @ 64 Hz  (float32)
  Muse-ACCGYRO  6 channels @ 52 Hz   (float32)
  Muse-BATTERY  1 channel @ 0.2 Hz   (float32)

Channel labels match the reference data seeded in schemas/002_reference_data.sql.

Key feature: during configurable "eyes closed" windows, the EEG stream gets
an extra 10 Hz sine wave (alpha band) with realistic amplitude. This lets
the end-to-end test verify that experiment_1 → recorder → ingest → features
can recover a known alpha enhancement ratio without any real hardware.

Usage:
    # Run in one terminal, lets the outlets publish forever:
    python mock_lsl_publisher.py --duration 600 --closed-windows 30:60 90:120

    # In another terminal, run the experiment:
    python experiment_1_eyes_closed_v3.py --subject jaie --skip-input

    # Or let the test script orchestrate both via subprocess.
"""
from __future__ import annotations

import argparse
import math
import random
import sys
import threading
import time
from typing import Optional

import numpy as np


SAMPLE_RATES = {
    "eeg": 256.0,
    "optics": 64.0,
    "accgyro": 52.0,
    "battery": 0.2,
}

EEG_CH_NAMES = ["EEG_TP9", "EEG_AF7", "EEG_AF8", "EEG_TP10", "AUX_1", "AUX_2", "AUX_3", "AUX_4"]
OPTICS_CH_NAMES = [
    "OPTICS_LO_NIR", "OPTICS_RO_NIR", "OPTICS_LO_IR", "OPTICS_RO_IR",
    "OPTICS_LI_NIR", "OPTICS_RI_NIR", "OPTICS_LI_IR", "OPTICS_RI_IR",
    "OPTICS_LO_RED", "OPTICS_RO_RED", "OPTICS_LO_AMB", "OPTICS_RO_AMB",
    "OPTICS_LI_RED", "OPTICS_RI_RED", "OPTICS_LI_AMB", "OPTICS_RI_AMB",
]
ACCGYRO_CH_NAMES = ["ACC_X", "ACC_Y", "ACC_Z", "GYRO_X", "GYRO_Y", "GYRO_Z"]


def _is_in_closed_window(t_rel: float, windows: list[tuple[float, float]]) -> bool:
    return any(start <= t_rel <= end for start, end in windows)


# Global flag flipped by the OMDR-Markers listener thread when it sees
# eyes_closed_* / eyes_open_* markers. Used when --listen-markers is set.
_eyes_closed_flag = threading.Event()


def _gen_eeg_sample(t_rel: float, closed_windows: list[tuple[float, float]],
                    use_marker_flag: bool = False) -> list[float]:
    """Generate one 8-channel EEG sample (in microvolts).

    Base signal is brown-ish noise; during closed windows (or when the
    eyes_closed marker flag is set), add a 10 Hz sine wave with amplitude
    ~30 uV to the temporal channels (TP9, TP10) and a smaller amount to
    AF7/AF8. Textbook alpha enhancement signature.

    Alpha boost source precedence:
      - If use_marker_flag is True: use the global _eyes_closed_flag
      - Otherwise: use the wall-clock windows
    """
    if use_marker_flag:
        is_closed = _eyes_closed_flag.is_set()
    else:
        is_closed = _is_in_closed_window(t_rel, closed_windows)
    alpha_amp = 30.0 if is_closed else 4.0
    alpha = alpha_amp * math.sin(2 * math.pi * 10 * t_rel)
    beta = 4.0 * math.sin(2 * math.pi * 22 * t_rel)
    theta = 3.0 * math.sin(2 * math.pi * 6 * t_rel)
    mains = 1.5 * math.sin(2 * math.pi * 50 * t_rel)
    noise_std = 5.0

    def ch(scale_alpha: float, scale_other: float) -> float:
        return (scale_alpha * alpha + scale_other * (beta + theta + mains) + random.gauss(0, noise_std))

    return [
        ch(1.0, 1.0),   # TP9  — strong alpha
        ch(0.3, 1.0),   # AF7  — weak alpha (forehead)
        ch(0.3, 1.0),   # AF8  — weak alpha
        ch(1.0, 1.0),   # TP10 — strong alpha
        ch(0.1, 0.8),   # AUX_1
        ch(0.1, 0.8),   # AUX_2
        ch(0.1, 0.8),   # AUX_3
        ch(0.1, 0.8),   # AUX_4
    ]


def _gen_optics_sample(t_rel: float) -> list[float]:
    """Generate one 16-channel optics sample. Baseline levels per channel
    with slow drift; enough structure to be recorded but no physiological
    meaning (mock only)."""
    base = [
        6.9, 5.4, 0.02, 0.017,
        10.41, 10.26, 10.40, 10.26,
        3.1, 3.0, 1.5, 1.4,
        3.2, 3.1, 1.5, 1.4,
    ]
    drift = 0.02 * math.sin(2 * math.pi * 0.1 * t_rel)
    return [b + drift + random.gauss(0, 0.005) for b in base]


def _gen_accgyro_sample(t_rel: float) -> list[float]:
    """Mock accelerometer + gyro. Head upright, slight sway."""
    return [
        -0.2 + 0.05 * math.sin(2 * math.pi * 0.3 * t_rel) + random.gauss(0, 0.02),  # ACC_X
        -0.14 + 0.03 * math.sin(2 * math.pi * 0.3 * t_rel) + random.gauss(0, 0.02), # ACC_Y
        -0.96 + random.gauss(0, 0.02),                                              # ACC_Z (gravity)
        random.gauss(0, 5.0),   # GYRO_X
        random.gauss(0, 5.0),   # GYRO_Y
        random.gauss(0, 5.0),   # GYRO_Z
    ]


def _gen_battery_sample(t_rel: float, start_pct: float = 99.9) -> list[float]:
    # Slow linear drop, ~0.01% per second
    return [start_pct - 0.01 * t_rel]


# ---------------------------------------------------------------------------
# Publisher
# ---------------------------------------------------------------------------

def _make_outlets():
    from mne_lsl.lsl import StreamInfo, StreamOutlet

    outlets = {}

    # EEG
    info = StreamInfo("Muse-EEG (MOCK-00:00:00:00:00:00)", "EEG", 8, SAMPLE_RATES["eeg"], "float32", "mock_muse_eeg")
    # Add channel labels via the info XML description (mne-lsl convenience)
    try:
        info.set_channel_names(EEG_CH_NAMES)
        info.set_channel_units(["microvolt"] * 8)
        info.set_channel_types(["eeg"] * 8)
    except Exception:
        pass
    outlets["eeg"] = StreamOutlet(info, chunk_size=32, max_buffered=360)

    # OPTICS
    info = StreamInfo("Muse-OPTICS (MOCK-00:00:00:00:00:00)", "PPG", 16, SAMPLE_RATES["optics"], "float32", "mock_muse_optics")
    try:
        info.set_channel_names(OPTICS_CH_NAMES)
        info.set_channel_units(["microamp"] * 16)
        info.set_channel_types(["misc"] * 16)
    except Exception:
        pass
    outlets["optics"] = StreamOutlet(info, chunk_size=16, max_buffered=360)

    # ACCGYRO
    info = StreamInfo("Muse-ACCGYRO (MOCK-00:00:00:00:00:00)", "ACCGYRO", 6, SAMPLE_RATES["accgyro"], "float32", "mock_muse_accgyro")
    try:
        info.set_channel_names(ACCGYRO_CH_NAMES)
        info.set_channel_units(["g", "g", "g", "deg/s", "deg/s", "deg/s"])
        info.set_channel_types(["misc"] * 6)
    except Exception:
        pass
    outlets["accgyro"] = StreamOutlet(info, chunk_size=8, max_buffered=360)

    # BATTERY
    info = StreamInfo("Muse-BATTERY (MOCK-00:00:00:00:00:00)", "Markers", 1, SAMPLE_RATES["battery"], "float32", "mock_muse_battery")
    try:
        info.set_channel_names(["BATTERY_PERCENT"])
        info.set_channel_units(["percent"])
        info.set_channel_types(["misc"])
    except Exception:
        pass
    outlets["battery"] = StreamOutlet(info, chunk_size=1, max_buffered=60)

    return outlets


def _markers_listener_thread() -> None:
    """Subscribe to the OMDR-Markers LSL stream and flip _eyes_closed_flag
    based on received markers. Runs until the mock publisher exits."""
    from mne_lsl.lsl import resolve_streams, StreamInlet
    print("[mock_lsl_publisher] listening for OMDR-Markers stream...", flush=True)
    # Retry resolve in a loop — the experiment script may not have created
    # the outlet yet when we start.
    for attempt in range(30):
        streams = resolve_streams(timeout=1.0)
        markers_streams = [s for s in streams if s.name == "OMDR-Markers"]
        if markers_streams:
            break
        time.sleep(0.5)
    else:
        print("[mock_lsl_publisher] WARNING: no OMDR-Markers stream found, alpha flag will never flip", flush=True)
        return

    inlet = StreamInlet(markers_streams[0], max_buffered=30)
    inlet.open_stream()
    print(f"[mock_lsl_publisher] subscribed to OMDR-Markers (sfreq={markers_streams[0].sfreq}, dtype={markers_streams[0].dtype})", flush=True)

    poll_count = 0
    last_heartbeat = time.time()
    while True:
        try:
            # Use pull_chunk which handles irregular-rate streams more reliably
            # than pull_sample in mne-lsl for string streams.
            chunk, timestamps = inlet.pull_chunk(timeout=0.2, max_samples=32)
            poll_count += 1
            now = time.time()
            if now - last_heartbeat > 3.0:
                print(f"[mock_lsl_publisher] listener heartbeat: {poll_count} polls, "
                      f"flag_set={_eyes_closed_flag.is_set()}", flush=True)
                last_heartbeat = now
            if chunk is None or len(chunk) == 0:
                continue
            # chunk is a list of samples; each sample is a list of channels.
            # For our 1-channel StringMarkers stream, each sample is [label]
            for sample in chunk:
                if isinstance(sample, (list, tuple)) and len(sample) > 0:
                    label = str(sample[0])
                else:
                    label = str(sample)
                print(f"[mock_lsl_publisher] RECEIVED marker: '{label}'", flush=True)
                if "closed" in label.lower():
                    _eyes_closed_flag.set()
                    print(f"[mock_lsl_publisher] alpha boost ON  ({label})", flush=True)
                elif "open" in label.lower():
                    _eyes_closed_flag.clear()
                    print(f"[mock_lsl_publisher] alpha boost OFF ({label})", flush=True)
                elif label == "session_end":
                    print(f"[mock_lsl_publisher] session_end seen, listener exiting", flush=True)
                    try: inlet.close_stream()
                    except Exception: pass
                    return
        except Exception as e:
            print(f"[mock_lsl_publisher] markers listener error: {type(e).__name__}: {e}", flush=True)
            break
    try: inlet.close_stream()
    except Exception: pass


def run(duration_s: float, closed_windows: list[tuple[float, float]],
        listen_markers: bool = False,
        stop_event: Optional[threading.Event] = None) -> None:
    """Publish synthetic LSL streams until duration_s elapses or stop_event is set."""
    # Start markers listener thread if requested
    if listen_markers:
        listener = threading.Thread(target=_markers_listener_thread, daemon=True)
        listener.start()
    outlets = _make_outlets()
    print(f"[mock_lsl_publisher] outlets created: {list(outlets.keys())}")
    print(f"[mock_lsl_publisher] running for {duration_s:.0f}s, closed windows: {closed_windows}")

    t_start = time.time()
    next_eeg     = t_start
    next_optics  = t_start
    next_accgyro = t_start
    next_battery = t_start + 5.0  # first battery sample after 5s

    dt_eeg     = 1.0 / SAMPLE_RATES["eeg"]
    dt_optics  = 1.0 / SAMPLE_RATES["optics"]
    dt_accgyro = 1.0 / SAMPLE_RATES["accgyro"]
    dt_battery = 1.0 / SAMPLE_RATES["battery"]

    sent = {"eeg": 0, "optics": 0, "accgyro": 0, "battery": 0}

    try:
        while True:
            now = time.time()
            t_rel = now - t_start
            if t_rel >= duration_s:
                break
            if stop_event is not None and stop_event.is_set():
                break

            if now >= next_eeg:
                # mne-lsl requires numpy arrays for numeric push_sample
                outlets["eeg"].push_sample(np.asarray(_gen_eeg_sample(t_rel, closed_windows, use_marker_flag=listen_markers), dtype=np.float32))
                sent["eeg"] += 1
                next_eeg += dt_eeg
            if now >= next_optics:
                outlets["optics"].push_sample(np.asarray(_gen_optics_sample(t_rel), dtype=np.float32))
                sent["optics"] += 1
                next_optics += dt_optics
            if now >= next_accgyro:
                outlets["accgyro"].push_sample(np.asarray(_gen_accgyro_sample(t_rel), dtype=np.float32))
                sent["accgyro"] += 1
                next_accgyro += dt_accgyro
            if now >= next_battery:
                outlets["battery"].push_sample(np.asarray(_gen_battery_sample(t_rel), dtype=np.float32))
                sent["battery"] += 1
                next_battery += dt_battery

            time.sleep(0.0005)
    except KeyboardInterrupt:
        print("\n[mock_lsl_publisher] interrupted")

    print(f"[mock_lsl_publisher] done. Sent: {sent}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_windows(s: str) -> list[tuple[float, float]]:
    """Parse '30:60,90:120' into [(30, 60), (90, 120)]."""
    out = []
    for part in s.split(","):
        if not part.strip():
            continue
        a, b = part.split(":")
        out.append((float(a), float(b)))
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mock LSL publisher for testing the v3 pipeline")
    parser.add_argument("--duration", type=float, default=60.0)
    parser.add_argument("--closed-windows", type=str, default="",
                        help="Comma-separated start:end pairs in seconds for 'eyes closed' alpha-boost windows. Ignored if --listen-markers is set.")
    parser.add_argument("--listen-markers", action="store_true",
                        help="Subscribe to the OMDR-Markers LSL stream and flip alpha boost based on eyes_closed_* / eyes_open_* markers. Self-synchronizes with the experiment script without needing wall-clock window math.")
    args = parser.parse_args()

    windows = _parse_windows(args.closed_windows) if args.closed_windows else []
    run(args.duration, windows, listen_markers=args.listen_markers)
