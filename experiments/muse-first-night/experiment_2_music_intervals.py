"""Experiment 2 — Listening to musical intervals (consonance vs dissonance).

OMDR's universal-resonance prediction: cross-channel coherence in EEG should
rise more for consonant intervals (small-integer ratios) than for dissonant
ones. This is the simplest possible test of that prediction with one device,
one subject, and one evening.

Protocol:
    For each of 5 stimuli, repeated twice in randomised order:
        20s rest (silence)
        20s stimulus
    Stimuli:
        - perfect octave        2:1   (220 Hz + 440 Hz)
        - perfect fifth         3:2   (220 Hz + 330 Hz)
        - major third           5:4   (220 Hz + 275 Hz)
        - minor second (diss)  16:15  (220 Hz + 234.67 Hz)
        - tritone (diss)       √2:1   (220 Hz + 311.13 Hz)

Total: ~7 minutes (5 stim × 2 reps × 40 s = 400 s + setup overhead).

The analysis (run after) compares pairwise alpha-band coherence across the
4 channels for each stimulus condition. OMDR prediction: octave > fifth >
third > tritone ≈ minor second.

This is one subject one night — it is NOT a publishable result on its own.
It IS a real attempt to look for the predicted ordering. A null result is
informative either way.

Each stimulus is generated on the fly with two pure sine waves (no harmonics)
to keep the test as clean as possible. Stereo, 44100 Hz, 16-bit PCM.

Usage:
    python experiment_2_music_intervals.py [--port 5000] [--subject jaie]
"""
from __future__ import annotations

import argparse
import io
import math
import random
import struct
import sys
import time
import wave
from pathlib import Path

import numpy as np

from session import Session
from signal_quality import live_quality_check
from analyse_session import analyse_session, write_summary, EEG_CHANNELS, ALPHA_BAND, coherence_in_band, load_eeg, load_markers, segments_from_markers, estimate_sample_rate

try:
    import winsound  # type: ignore
except Exception:  # pragma: no cover
    winsound = None  # type: ignore

SAMPLE_RATE_AUDIO = 44100
ROOT_HZ = 220.0  # A3
STIMULUS_S = 20.0
REST_S = 20.0
N_REPS = 2

INTERVALS = [
    ("octave_2_1",     2.0,           "perfect octave (consonant)"),
    ("fifth_3_2",      3.0 / 2.0,     "perfect fifth (consonant)"),
    ("third_5_4",      5.0 / 4.0,     "major third (consonant)"),
    ("tritone_sqrt2",  math.sqrt(2.0),"tritone (dissonant)"),
    ("minor_second_16_15", 16.0/15.0, "minor second (dissonant)"),
]


# ---------------------------------------------------------------------------
# Stimulus generation
# ---------------------------------------------------------------------------

def make_interval_wav(root_hz: float, ratio: float, duration_s: float, fade_s: float = 0.05) -> bytes:
    """Generate a stereo PCM16 WAV in-memory of two sine waves at root + root*ratio."""
    n = int(SAMPLE_RATE_AUDIO * duration_s)
    t = np.arange(n) / SAMPLE_RATE_AUDIO
    a = 0.3 * np.sin(2 * np.pi * root_hz * t)
    b = 0.3 * np.sin(2 * np.pi * root_hz * ratio * t)
    # Apply linear fade in/out to avoid clicks
    fade_n = int(SAMPLE_RATE_AUDIO * fade_s)
    if fade_n > 0:
        env = np.ones(n)
        env[:fade_n] = np.linspace(0.0, 1.0, fade_n)
        env[-fade_n:] = np.linspace(1.0, 0.0, fade_n)
        a *= env
        b *= env
    # Stereo: left = root (a), right = harmonic (b). Slight mix of both in each ear so the chord is coherent.
    left = (0.7 * a + 0.5 * b)
    right = (0.5 * a + 0.7 * b)
    # Clip to [-1, 1] just in case
    left = np.clip(left, -1.0, 1.0)
    right = np.clip(right, -1.0, 1.0)
    # Interleave and convert to int16
    interleaved = np.empty(n * 2, dtype=np.int16)
    interleaved[0::2] = (left * 32767).astype(np.int16)
    interleaved[1::2] = (right * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE_AUDIO)
        w.writeframes(interleaved.tobytes())
    return buf.getvalue()


def play_wav_blocking(wav_bytes: bytes):
    """Play WAV bytes via winsound. Blocking — returns when playback finishes (or after duration)."""
    if winsound is None:
        print("[experiment_2] WARNING: winsound not available; using silent stub")
        time.sleep(STIMULUS_S)
        return
    # winsound.PlaySound with SND_MEMORY plays the in-memory WAV buffer.
    flags = winsound.SND_MEMORY | winsound.SND_NODEFAULT
    winsound.PlaySound(wav_bytes, flags)
    # PlaySound is synchronous when SND_ASYNC is NOT set, but blocks for the file
    # only — for memory we need to wait the duration ourselves.
    time.sleep(STIMULUS_S)
    winsound.PlaySound(None, winsound.SND_PURGE)


# ---------------------------------------------------------------------------
# Analysis specific to this experiment
# ---------------------------------------------------------------------------

def per_stimulus_coherence(session_dir: Path) -> dict:
    """For each stimulus segment, compute pairwise alpha coherence and return summary."""
    timestamps, eeg = load_eeg(session_dir)
    markers = load_markers(session_dir)
    fs = estimate_sample_rate(timestamps)
    segs_def = segments_from_markers(markers)
    pairs = [(0, 1, "TP9-AF7"), (0, 2, "TP9-AF8"), (0, 3, "TP9-TP10"),
             (1, 2, "AF7-AF8"), (1, 3, "AF7-TP10"), (2, 3, "AF8-TP10")]
    results: dict[str, dict] = {}
    for label, start_ts, end_ts in segs_def:
        if not label.startswith("stim_"):
            continue
        mask = (timestamps >= start_ts) & (timestamps <= end_ts)
        seg = eeg[mask]
        per_pair = {}
        for i, j, pair_name in pairs:
            per_pair[pair_name] = coherence_in_band(seg[:, i], seg[:, j], fs, ALPHA_BAND)
        # Average coherence across all pairs = global alpha coherence index
        valid = [v for v in per_pair.values() if not (v != v)]  # NaN filter
        global_idx = float(sum(valid) / len(valid)) if valid else float("nan")
        # Aggregate by stimulus name (drop "stim_X_" prefix)
        stim_key = label.replace("stim_", "").rsplit("_rep", 1)[0]
        results.setdefault(stim_key, {"runs": [], "pairs": []})
        results[stim_key]["runs"].append(global_idx)
        results[stim_key]["pairs"].append(per_pair)
    # Mean per stimulus
    summary: dict[str, dict] = {}
    for stim, payload in results.items():
        runs = [r for r in payload["runs"] if not (r != r)]
        summary[stim] = {
            "n_reps": len(runs),
            "mean_global_alpha_coherence": float(sum(runs) / len(runs)) if runs else float("nan"),
            "runs": runs,
        }
    return summary


def main():
    parser = argparse.ArgumentParser(description="Experiment 2 — Music intervals")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--subject", default="jaie")
    parser.add_argument("--reps", type=int, default=N_REPS)
    parser.add_argument("--no-quality-gate", action="store_true")
    parser.add_argument("--quality-seconds", type=int, default=20)
    parser.add_argument("--seed", type=int, default=None, help="Random seed for stimulus order")
    args = parser.parse_args()

    here = Path(__file__).parent

    print("=" * 60)
    print(" EXPERIMENT 2 — Music intervals (consonance vs dissonance)")
    print(" *** EXPLORATORY PILOT — UNDERPOWERED WITH n=2 REPS ***")
    print("=" * 60)
    print(f"  Subject: {args.subject}")
    print(f"  Stimuli: {len(INTERVALS)} intervals × {args.reps} reps")
    print(f"  Each: {REST_S:.0f}s rest + {STIMULUS_S:.0f}s stimulus")
    print(f"  Total: ~{len(INTERVALS) * args.reps * (REST_S + STIMULUS_S) / 60:.1f} minutes")
    print("\n  IMPORTANT: All three external validators flagged this as severely")
    print("  underpowered for tonight (n=2 per condition). Treat the result as a")
    print("  PILOT only — informative for protocol refinement, NOT for inference.")
    print("  If you are tired or short on time, SKIP this experiment and run E3 instead.")
    print("\n  PUT ON HEADPHONES (or quiet speakers) — pure sine waves, low volume")
    input("  Press ENTER when ready (or Ctrl+C to skip)... ")

    # Build the run plan: each (interval, rep) pair, randomised
    rng = random.Random(args.seed)
    plan = []
    for interval in INTERVALS:
        for rep in range(args.reps):
            plan.append((interval, rep + 1))
    rng.shuffle(plan)

    # Pre-generate all WAVs (avoids latency mid-experiment)
    print("[experiment_2] Pre-generating stimuli...")
    wavs = {}
    for name, ratio, _ in INTERVALS:
        wavs[name] = make_interval_wav(ROOT_HZ, ratio, STIMULUS_S)
    print(f"[experiment_2] {len(wavs)} stimuli ready.\n")

    notes = (
        f"Experiment 2 — music intervals. {len(INTERVALS)} stimuli x {args.reps} reps in randomised order. "
        f"Each: {REST_S}s rest + {STIMULUS_S}s stimulus."
    )

    with Session("music-intervals", subject=args.subject, port=args.port,
                 sessions_root=here / "sessions", notes=notes) as s:
        if not args.no_quality_gate:
            ok = live_quality_check(s.receiver, min_seconds=args.quality_seconds, hold_seconds=3.0)
            if not ok:
                print("\n[experiment_2] Aborting — signal quality not good enough.")
                return 2

        print("[experiment_2] Starting protocol. Sit still, eyes closed, listen to the tones.\n")
        for i, ((name, ratio, desc), rep) in enumerate(plan):
            print(f"--- ({i + 1}/{len(plan)}) {desc} (ratio {ratio:.4f}) rep {rep} ---")
            s.mark(f"rest_before_{name}_rep{rep}")
            print(f"   silence ({REST_S:.0f}s) ...")
            time.sleep(REST_S)
            s.mark(f"stim_{name}_rep{rep}")
            print(f"   stimulus ({STIMULUS_S:.0f}s) ...")
            play_wav_blocking(wavs[name])
        s.mark("session_end")
        session_dir = s.session_dir

    # Analyse
    print("\n[experiment_2] Analysing per-stimulus coherence...")
    base = analyse_session(session_dir)
    write_summary(session_dir, base)
    per_stim = per_stimulus_coherence(session_dir)
    out = session_dir / "music_intervals_summary.json"
    import json
    with open(out, "w", encoding="utf-8") as f:
        json.dump({
            "stimuli": [{"name": n, "ratio": r, "desc": d} for n, r, d in INTERVALS],
            "per_stimulus_coherence_alpha": per_stim,
        }, f, indent=2, ensure_ascii=False)

    print("=" * 60)
    print(" PER-STIMULUS GLOBAL ALPHA COHERENCE (mean across runs)")
    print("=" * 60)
    # Sort by mean coherence so the ordering is visible
    rows = sorted(
        ((stim, payload["mean_global_alpha_coherence"], payload["n_reps"]) for stim, payload in per_stim.items()),
        key=lambda r: -r[1] if r[1] == r[1] else 0,  # NaN-safe descending
    )
    for stim, mean_coh, n in rows:
        print(f"  {stim:24s}  mean coherence = {mean_coh:.4f}   (n={n})")
    print(f"\n  Saved: {out}")
    print("\n  Look at the ordering. OMDR prediction: octave > fifth > third > dissonant intervals.")
    print("  This is one night, one subject — informative, not conclusive.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
