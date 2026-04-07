"""Live signal-quality display — Gemini Y-split second consumer.

Subscribes to the Muse-EEG LSL outlet in parallel with lsl_recorder.Recorder
(no coupling between them — both pull from the same LSL bus independently)
and shows real-time per-channel signal quality so the experimenter can
verify headband contact before starting a recording block.

This is the round-2 Gemini-recommended "Y-split" architecture: the LSL
bus IS the buffer; any number of consumers can subscribe to the same
stream simultaneously without interfering.

Two display modes:
  - "terminal" (default): ASCII bar chart in the terminal, auto-refresh
    at ~5 Hz, works in any shell. No dependencies beyond mne-lsl + numpy.
  - "matplotlib": proper scrolling plot window with 8 EEG channels,
    auto-scaled, shows the last 5 seconds. Requires matplotlib backend.

What "signal quality" means here:
  For each EEG channel we compute per-second:
    (a) RMS amplitude over the last 1s window, in microvolts
    (b) Variance-based quality score: low variance + sensible mean
        = clean, very high variance or pinned at 0 = poor contact
    (c) A simple traffic-light label derived from (a) and (b):
          GOOD — quality score >= 0.7, RMS in [1, 200] uV
          OK   — quality score 0.4-0.7, RMS in [0.5, 500] uV
          BAD  — quality score < 0.4 OR RMS outside usable range

  These are heuristic and don't replace the Muse's own HSI metric; they
  are useful because HSI is not directly exposed via the OpenMuse LSL
  outlets (only Muse-EEG samples are published, not HSI annotations).

Usage:
    # Make sure OpenMuse is already streaming (from another terminal):
    #   OpenMuse stream --address 00:55:DA:BB:D9:53 --duration 3600
    # Then run this display in yet another terminal:
    python live_display.py

    # Use --mode matplotlib for a scrolling plot window instead:
    python live_display.py --mode matplotlib

    # Run for a limited time and exit:
    python live_display.py --duration 60

Kai (Anthropic Claude instance) with Jaie Parker, 2026-04-08 overnight build.
"""
from __future__ import annotations

import argparse
import sys
import time
from collections import deque
from pathlib import Path
from typing import Optional

import numpy as np

# ANSI color helpers for terminal mode (safe to no-op on non-ANSI terminals)
ANSI_GREEN  = "\033[92m"
ANSI_YELLOW = "\033[93m"
ANSI_RED    = "\033[91m"
ANSI_GRAY   = "\033[90m"
ANSI_RESET  = "\033[0m"
ANSI_CLEAR  = "\033[2J\033[H"


# ---------------------------------------------------------------------------
# Quality scoring
# ---------------------------------------------------------------------------

def _quality_from_window(samples: np.ndarray) -> tuple[str, float, float]:
    """Return (label, rms_uv, quality_score_0_to_1) for one channel's recent samples."""
    if len(samples) < 10:
        return "NO DATA", 0.0, 0.0
    rms = float(np.sqrt(np.mean(samples**2)))
    # Mean-subtracted std to measure signal variability
    std = float(np.std(samples - np.mean(samples)))
    # Heuristic quality score:
    #   - if samples are pinned at 0 → very low quality
    #   - if samples are saturating (mean > 1000 uV) → very low quality
    #   - otherwise a smooth function of std in the typical EEG range
    score = 0.0
    if rms > 0.01 and abs(np.mean(samples)) < 2000:
        # std between 1 and 150 uV is the typical clean-EEG range
        if 1.0 <= std <= 150.0:
            score = 1.0 - max(0.0, (std - 40.0) / 200.0)
            score = max(0.0, min(1.0, score))
        elif std < 1.0:
            score = 0.1   # too flat — likely disconnected
        else:
            score = 0.2   # too noisy — likely movement or bad contact
    if score >= 0.7 and 1.0 <= rms <= 500.0:
        label = "GOOD"
    elif score >= 0.4 and 0.5 <= rms <= 1500.0:
        label = " OK "
    else:
        label = "BAD "
    return label, rms, score


def _colorize(label: str) -> str:
    if label == "GOOD":
        return f"{ANSI_GREEN}{label}{ANSI_RESET}"
    elif label == " OK ":
        return f"{ANSI_YELLOW}{label}{ANSI_RESET}"
    elif label == "BAD ":
        return f"{ANSI_RED}{label}{ANSI_RESET}"
    else:
        return f"{ANSI_GRAY}{label}{ANSI_RESET}"


# ---------------------------------------------------------------------------
# Terminal display
# ---------------------------------------------------------------------------

def run_terminal(duration_s: Optional[float] = None, refresh_hz: float = 5.0,
                 window_s: float = 1.5) -> int:
    """Run the ASCII display. Returns exit code."""
    from mne_lsl.lsl import resolve_streams, StreamInlet

    print("[live_display] resolving Muse-EEG LSL stream (up to 15s)...")
    t_start = time.time()
    eeg_stream = None
    while time.time() - t_start < 15.0:
        streams = resolve_streams(timeout=1.5)
        for s in streams:
            if s.name.startswith("Muse-EEG"):
                eeg_stream = s
                break
        if eeg_stream:
            break
        time.sleep(0.3)
    if not eeg_stream:
        print("[live_display] no Muse-EEG stream found. Make sure OpenMuse is running.")
        return 1

    print(f"[live_display] subscribed to {eeg_stream.name}")
    print(f"[live_display] n_channels={eeg_stream.n_channels}, sfreq={eeg_stream.sfreq}")

    inlet = StreamInlet(eeg_stream, max_buffered=60)
    inlet.open_stream()
    sfreq = float(eeg_stream.sfreq)
    n_ch = int(eeg_stream.n_channels)
    sinfo = inlet.get_sinfo()
    ch_info = sinfo.get_channel_info()
    ch_names = (ch_info or {}).get("ch_names", [f"ch{i}" for i in range(n_ch)])

    # Rolling buffer of the last window_s samples per channel
    buffer_size = int(window_s * sfreq) + 16
    ring = np.zeros((n_ch, buffer_size), dtype=np.float64)
    ring_pos = 0

    def _append(chunk: np.ndarray) -> None:
        nonlocal ring_pos
        n = chunk.shape[0]
        if n >= buffer_size:
            # single chunk bigger than the whole buffer — take the tail
            ring[:] = chunk[-buffer_size:, :].T
            ring_pos = 0
            return
        end = ring_pos + n
        if end <= buffer_size:
            ring[:, ring_pos:end] = chunk.T
        else:
            first = buffer_size - ring_pos
            ring[:, ring_pos:] = chunk[:first, :].T
            ring[:, :n - first] = chunk[first:, :].T
        ring_pos = (ring_pos + n) % buffer_size

    print("[live_display] starting ~5 Hz refresh. Ctrl+C to exit.\n")
    t0 = time.time()
    last_refresh = 0.0
    refresh_dt = 1.0 / refresh_hz

    try:
        while True:
            now = time.time()
            if duration_s is not None and now - t0 > duration_s:
                break

            chunk, ts = inlet.pull_chunk(timeout=0.05, max_samples=int(sfreq))
            if chunk is not None and len(chunk) > 0:
                _append(np.asarray(chunk, dtype=np.float64))

            if now - last_refresh >= refresh_dt:
                last_refresh = now
                # Render
                print(ANSI_CLEAR, end="")
                elapsed = now - t0
                print(f"  Live signal quality — {eeg_stream.name}   elapsed: {elapsed:5.1f}s   (Ctrl+C to exit)")
                print("=" * 72)
                lines = []
                any_good = False
                for c in range(n_ch):
                    samples = np.concatenate((ring[c, ring_pos:], ring[c, :ring_pos]))
                    label, rms, score = _quality_from_window(samples)
                    if label == "GOOD":
                        any_good = True
                    # Bar representation of score
                    bar_len = 20
                    filled = int(round(score * bar_len))
                    bar = "█" * filled + "·" * (bar_len - filled)
                    lines.append(f"  {ch_names[c]:9s}  {_colorize(label)}  score={score:.2f}  rms={rms:7.1f} uV  [{bar}]")
                print("\n".join(lines))
                print()
                print(f"  Temporal sites (TP9, TP10) are the weak spot for Muse — dampen behind the ears for good contact.")
                print(f"  Forehead sites (AF7, AF8) usually work dry.")
                if not any_good:
                    print(f"\n  {ANSI_RED}No channel is GOOD yet. Adjust the headband.{ANSI_RESET}")
    except KeyboardInterrupt:
        print("\n[live_display] interrupted")
    finally:
        try: inlet.close_stream()
        except Exception: pass

    return 0


# ---------------------------------------------------------------------------
# Matplotlib display (optional)
# ---------------------------------------------------------------------------

def run_matplotlib(duration_s: Optional[float] = None, refresh_hz: float = 10.0,
                   window_s: float = 5.0) -> int:
    """Scrolling plot of the last window_s seconds of all 8 EEG channels."""
    try:
        import matplotlib
        matplotlib.use("TkAgg")
        import matplotlib.pyplot as plt
    except Exception as e:
        print(f"[live_display] matplotlib not available: {e}")
        return 2

    from mne_lsl.lsl import resolve_streams, StreamInlet
    print("[live_display] resolving Muse-EEG LSL stream (up to 15s)...")
    t_start = time.time()
    eeg_stream = None
    while time.time() - t_start < 15.0:
        streams = resolve_streams(timeout=1.5)
        for s in streams:
            if s.name.startswith("Muse-EEG"):
                eeg_stream = s
                break
        if eeg_stream:
            break
        time.sleep(0.3)
    if not eeg_stream:
        print("[live_display] no Muse-EEG stream found.")
        return 1

    inlet = StreamInlet(eeg_stream, max_buffered=60)
    inlet.open_stream()
    sfreq = float(eeg_stream.sfreq)
    n_ch = int(eeg_stream.n_channels)
    sinfo = inlet.get_sinfo()
    ch_info = sinfo.get_channel_info()
    ch_names = (ch_info or {}).get("ch_names", [f"ch{i}" for i in range(n_ch)])

    buffer_size = int(window_s * sfreq) + 16
    ring = np.zeros((n_ch, buffer_size), dtype=np.float64)

    fig, axes = plt.subplots(n_ch, 1, sharex=True, figsize=(10, 9))
    if n_ch == 1:
        axes = [axes]
    lines = []
    x_axis = np.linspace(-window_s, 0, buffer_size)
    for c, ax in enumerate(axes):
        line, = ax.plot(x_axis, ring[c], lw=0.8)
        lines.append(line)
        ax.set_ylabel(ch_names[c], rotation=0, ha="right", va="center")
        ax.grid(True, alpha=0.3)
    axes[-1].set_xlabel("seconds before now")
    fig.suptitle(f"Live EEG — {eeg_stream.name}  (Ctrl+C to exit)")
    fig.tight_layout()

    ring_pos = 0
    t0 = time.time()
    refresh_dt = 1.0 / refresh_hz
    last_refresh = 0.0

    try:
        plt.ion()
        plt.show(block=False)
        while True:
            now = time.time()
            if duration_s is not None and now - t0 > duration_s:
                break
            chunk, ts = inlet.pull_chunk(timeout=0.05, max_samples=int(sfreq))
            if chunk is not None and len(chunk) > 0:
                arr = np.asarray(chunk, dtype=np.float64)
                n = arr.shape[0]
                if n >= buffer_size:
                    ring[:] = arr[-buffer_size:, :].T
                    ring_pos = 0
                else:
                    end = ring_pos + n
                    if end <= buffer_size:
                        ring[:, ring_pos:end] = arr.T
                    else:
                        first = buffer_size - ring_pos
                        ring[:, ring_pos:] = arr[:first, :].T
                        ring[:, :n - first] = arr[first:, :].T
                    ring_pos = (ring_pos + n) % buffer_size

            if now - last_refresh >= refresh_dt:
                last_refresh = now
                for c, line in enumerate(lines):
                    series = np.concatenate((ring[c, ring_pos:], ring[c, :ring_pos]))
                    line.set_ydata(series)
                    ax = axes[c]
                    ax.relim()
                    ax.autoscale_view()
                fig.canvas.draw_idle()
                plt.pause(0.01)
    except KeyboardInterrupt:
        print("\n[live_display] interrupted")
    finally:
        try: inlet.close_stream()
        except Exception: pass

    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Live EEG signal quality display")
    parser.add_argument("--mode", choices=["terminal", "matplotlib"], default="terminal")
    parser.add_argument("--duration", type=float, default=None,
                        help="Run for this many seconds then exit (default: until Ctrl+C)")
    parser.add_argument("--refresh-hz", type=float, default=5.0)
    parser.add_argument("--window-s", type=float, default=1.5,
                        help="Rolling window of recent samples used for quality scoring")
    args = parser.parse_args()

    if args.mode == "terminal":
        return run_terminal(duration_s=args.duration, refresh_hz=args.refresh_hz, window_s=args.window_s)
    else:
        return run_matplotlib(duration_s=args.duration, refresh_hz=args.refresh_hz, window_s=args.window_s)


if __name__ == "__main__":
    sys.exit(main())
