"""Experiment 1 — Eyes-closed vs eyes-open baseline ("hello world" of EEG).

This is the first thing we run tonight. It is the most replicated finding
in EEG science: alpha-band power (8-13 Hz) increases ~1.5-3x at temporal
and parietal sites when the eyes close. If we see it, the device works,
the headband fit is good, and our pipeline is computing what we think it is.
If we don't, we debug before doing anything more interesting.

Protocol:
    pre-flight: signal quality check (~30 seconds)
    1.  Eyes open  — 60 s
    2.  Eyes closed — 60 s
    3.  Eyes open  — 60 s
    4.  Eyes closed — 60 s

Total: ~5 minutes including the pre-flight.

Cues: simple console messages. (Audio cues via winsound stdlib if available.)

After the run, analyse_session is invoked automatically and the result printed.

Usage:
    python experiment_1_eyes_closed.py [--port 5000] [--subject jaie] [--no-quality-gate]
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from session import Session
from signal_quality import live_quality_check
from analyse_session import analyse_session, write_summary, plot_segments

# Try to use winsound for audible cues on Windows; fall back to ASCII bell.
try:
    import winsound  # type: ignore
    def beep(freq: int = 880, ms: int = 220):
        try:
            winsound.Beep(freq, ms)
        except Exception:
            print("\a", end="", flush=True)
except Exception:  # pragma: no cover
    def beep(freq: int = 880, ms: int = 220):
        print("\a", end="", flush=True)


def cue_open(seconds: int):
    print(f"\n>>> EYES OPEN — relax, look at the screen, blink normally — {seconds}s <<<")
    beep(880, 220)


def cue_closed(seconds: int):
    print(f"\n>>> EYES CLOSED — let the eyes rest, breathe normally — {seconds}s <<<")
    beep(440, 220)
    beep(440, 220)


def countdown(seconds: int, label: str):
    end = time.time() + seconds
    while time.time() < end:
        remaining = int(round(end - time.time()))
        sys.stdout.write(f"\r  {label}: {remaining:3d}s remaining   ")
        sys.stdout.flush()
        time.sleep(0.5)
    sys.stdout.write(f"\r  {label}: done.                 \n")
    sys.stdout.flush()


def main():
    parser = argparse.ArgumentParser(description="Experiment 1 — eyes-closed baseline")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--subject", default="jaie")
    parser.add_argument("--block-seconds", type=int, default=60)
    parser.add_argument("--blocks", type=int, default=6, help="Total blocks (alternating open/closed) — default 6 (3 open, 3 closed) per validator advice")
    parser.add_argument("--no-quality-gate", action="store_true", help="Skip the pre-flight signal-quality gate")
    parser.add_argument("--quality-seconds", type=int, default=30)
    args = parser.parse_args()

    here = Path(__file__).parent

    print("=" * 60)
    print(" EXPERIMENT 1 — Eyes-closed vs Eyes-open baseline")
    print("=" * 60)
    print(f"  Subject: {args.subject}")
    print(f"  Blocks: {args.blocks} x {args.block_seconds}s, alternating open/closed")
    print(f"  Total recording: ~{args.blocks * args.block_seconds}s + setup")
    print(f"  Goal: detect alpha enhancement (closed/open ratio > 1.5)")
    print("\n  Make sure Mind Monitor is streaming to this PC and the headband is on.")
    input("  Press ENTER when ready... ")

    notes = (
        f"Experiment 1 — eyes-closed baseline. "
        f"{args.blocks} blocks of {args.block_seconds}s alternating eyes-open and eyes-closed. "
        f"Quality gate: {not args.no_quality_gate}."
    )

    with Session("eyes-closed-baseline", subject=args.subject, port=args.port,
                 sessions_root=here / "sessions", notes=notes) as s:
        # Pre-flight signal quality check
        if not args.no_quality_gate:
            ok = live_quality_check(s.receiver, min_seconds=args.quality_seconds, hold_seconds=3.0)
            if not ok:
                print("\n[experiment_1] Aborting — signal quality didn't reach all-good.")
                print("[experiment_1] Re-seat the headband (dampen TP9/TP10 against the ears, AF7/AF8 against the forehead) and re-run.")
                return 2
            print("[experiment_1] Signal quality OK — starting protocol.\n")

        # Protocol: alternating open/closed blocks
        for i in range(args.blocks):
            if i % 2 == 0:
                s.mark(f"eyes_open_block_{i + 1}")
                cue_open(args.block_seconds)
            else:
                s.mark(f"eyes_closed_block_{i + 1}")
                cue_closed(args.block_seconds)
            countdown(args.block_seconds, f"block {i + 1}/{args.blocks}")

        s.mark("session_end")
        beep(660, 400)
        print("\n[experiment_1] Recording complete. Stopping receiver and analysing...\n")
        session_dir = s.session_dir

    # Analysis
    analysis = analyse_session(session_dir)
    write_summary(session_dir, analysis)
    plot_segments(session_dir, analysis)

    print("=" * 60)
    print(" ANALYSIS")
    print("=" * 60)
    for n in analysis.notes:
        print(f"  {n}")
    ratio = analysis.alpha_enhancement_pooled_temporal
    if ratio is None:
        print("\n  No closed/open contrast computed.")
        return 3
    # Threshold lowered from 1.5x to 1.2x: validators converged that TP9/TP10
    # alpha is ~1.2-2x at temporal vs 2-4x at occipital, and Muse cannot reach
    # occipital. 1.2x is the realistic temporal-only pass criterion.
    verdict = "STRONG" if ratio > 1.5 else ("MODERATE" if ratio > 1.2 else ("WEAK" if ratio > 1.0 else "NONE"))
    print(f"\n  Pooled temporal alpha enhancement (closed/open) = {ratio:.2f}x  [{verdict}]")
    print("  (literature: 1.2-2x at temporal sites; Muse cannot reach occipital)")

    # Per-channel reporting — validators flagged that pooling can hide channel-specific effects
    if analysis.alpha_enhancement_per_channel:
        print("\n  Per-channel alpha enhancement:")
        for ch, r in analysis.alpha_enhancement_per_channel.items():
            print(f"    {ch}: {r:.2f}x")

    if ratio > 1.2:
        print("\n  RESULT: device works, signal quality good, pipeline measures correctly.")
        print("  You are clear to run Experiment 3 (and optionally Experiment 2 as exploratory pilot).")
        return 0
    elif ratio > 1.0:
        print("\n  RESULT: weak effect — try again with the headband re-seated.")
        print("  If individual alpha peak (in summary) is outside 8-13 Hz, the band-power may understate it.")
        return 4
    else:
        print("\n  RESULT: no effect detected. Triage:")
        print("    1. Inspect raw eeg.csv for obvious flatlines or saturation")
        print("    2. Check per-channel results above (one channel may be bad)")
        print("    3. Check individual_alpha_peak_hz in analysis_summary.json (may be outside 8-13)")
        print("    4. Verify headband contact at the temporal sites (behind-ears, dampened)")
        return 5


if __name__ == "__main__":
    sys.exit(main())
