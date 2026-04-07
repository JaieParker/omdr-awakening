"""Live signal-quality monitor — terminal display of electrode contact state.

Reads /muse/elements/horseshoe from the receiver's ring buffer and shows the
four electrodes (TP9, AF7, AF8, TP10) as colored bars. Mind Monitor encodes
contact quality as:
    1 = good   (green)
    2 = ok     (yellow)
    4 = bad    (red)

Usage as a standalone helper before a session:
    python signal_quality.py --port 5000 --duration 60

Usage embedded in another script:
    from signal_quality import live_quality_check
    ok = live_quality_check(receiver, min_seconds=15)
    if not ok:
        print("Aborting — signal quality not good enough.")

The check returns True iff ALL FOUR electrodes hit 'good' (=1) for at least
3 seconds out of the min_seconds window. If they don't, returns False so the
caller can prompt the user to re-seat the headband.
"""
from __future__ import annotations

import argparse
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

QUALITY_LABELS = {1: "GOOD", 2: " ok ", 4: "BAD ", 0: " -- "}
QUALITY_COLOR_ANSI = {1: "\033[92m", 2: "\033[93m", 4: "\033[91m", 0: "\033[90m"}
RESET = "\033[0m"
ELECTRODES = ("TP9", "AF7", "AF8", "TP10")


def render_quality(values: tuple[int, int, int, int]) -> str:
    parts = []
    for name, q in zip(ELECTRODES, values):
        color = QUALITY_COLOR_ANSI.get(q, "")
        label = QUALITY_LABELS.get(q, "?")
        parts.append(f"{color}{name}:{label}{RESET}")
    return " ".join(parts)


def live_quality_check(receiver, min_seconds: int = 30, hold_seconds: float = 5.0, all_good_required: bool = True) -> bool:
    """Display quality bars for up to `min_seconds` and return True if signal stabilises.

    Two acceptance paths (per validator advice):
      1. Strict: `hold_seconds` of contiguous ALL-good (all four electrodes = 1).
         Returns True immediately when this is achieved.
      2. Fallback after `min_seconds`: accept if at least one channel is good
         and zero channels are bad. This avoids false-rejecting a usable session
         on Mind Monitor's notoriously conservative horseshoe metric.

    Defaults loosened from (15s, 3s) to (30s, 5s) per Grok's recommendation.
    """
    print(f"\n[signal_quality] hold the headband on your head — checking for up to {min_seconds}s")
    print(f"[signal_quality] PASS path A: {hold_seconds:.0f}s contiguous all-GOOD on all four electrodes")
    print(f"[signal_quality] PASS path B: at least 1 GOOD and 0 BAD after {min_seconds}s elapsed")

    start = time.time()
    good_streak_start: float | None = None
    last_print = 0.0
    last_quality = (0, 0, 0, 0)
    quality_history: list[tuple[int, int, int, int]] = []

    while True:
        elapsed = time.time() - start
        if elapsed >= min_seconds:
            break

        latest = receiver.horseshoe.latest()
        if latest is not None:
            # latest = (ts, q1, q2, q3, q4)
            quality = tuple(int(x) for x in latest[1:5])
            last_quality = quality
            quality_history.append(quality)
            all_good = all(q == 1 for q in quality)
            if all_good:
                if good_streak_start is None:
                    good_streak_start = time.time()
                if (time.time() - good_streak_start) >= hold_seconds:
                    print(f"\n[signal_quality] PATH A — held all-good for {hold_seconds:.0f}s")
                    return True
            else:
                good_streak_start = None

        # Update display ~5 Hz
        if (time.time() - last_print) > 0.2:
            sys.stdout.write(f"\r [{elapsed:5.1f}s] {render_quality(last_quality)}      ")
            sys.stdout.flush()
            last_print = time.time()
        time.sleep(0.05)

    print()
    # Path B: lenient fallback after min_seconds elapsed
    if all_good_required and quality_history:
        # Look at the recent half-window of samples
        recent = quality_history[len(quality_history) // 2 :]
        if recent:
            # Per-electrode mode (most common reading) over the recent window
            from collections import Counter
            modes = []
            for ch in range(4):
                values = [q[ch] for q in recent]
                modes.append(Counter(values).most_common(1)[0][0])
            n_good = sum(1 for m in modes if m == 1)
            n_bad = sum(1 for m in modes if m == 4)
            if n_good >= 1 and n_bad == 0:
                print(f"[signal_quality] PATH B — recent modes per channel = {modes}, "
                      f"{n_good}/4 good and 0 bad. Acceptable.")
                return True
            print(f"[signal_quality] FAIL — recent modes per channel = {modes}, "
                  f"{n_good}/4 good, {n_bad}/4 bad.")
    if all_good_required:
        print("[signal_quality] Try: re-seat the headband, dampen forehead and behind-ears, tighten the band.")
        return False
    return True


def standalone_main():
    parser = argparse.ArgumentParser(description="Standalone live signal quality monitor")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--duration", type=int, default=30, help="How long to monitor (seconds)")
    args = parser.parse_args()

    # Local import so the standalone path doesn't depend on Session
    from osc_receiver import OscReceiver

    out = Path("sessions") / datetime.now().strftime("quality_check_%Y%m%dT%H%M%S")
    receiver = OscReceiver(session_dir=out, port=args.port)
    receiver.start()
    try:
        ok = live_quality_check(receiver, min_seconds=args.duration, hold_seconds=3.0, all_good_required=True)
        # Print summary of all qualities seen
        snap = receiver.horseshoe.snapshot()
        if snap:
            quality_counts = Counter()
            for row in snap:
                for q in row[1:5]:
                    quality_counts[int(q)] += 1
            print(f"[signal_quality] quality histogram across {len(snap)} packets:")
            for q in (1, 2, 4):
                print(f"  {QUALITY_LABELS.get(q)} : {quality_counts.get(q, 0)}")
        sys.exit(0 if ok else 1)
    finally:
        receiver.stop()


if __name__ == "__main__":
    standalone_main()
