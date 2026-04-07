"""Experiment 3 — Resting/meditation vs mental arithmetic contrast.

OMDR's prediction (Yang vs Yin): a relaxed/meditative state should show
lower beta (active processing) and higher alpha+theta than a deliberately
loaded cognitive state. This is a contrast test, not a calibration of the
"K=0.25" claim — that needs many more sessions and a richer balance metric.
For tonight, we just want to see whether the simplest possible Yin/Yang
contrast moves the EEG features in the predicted direction.

Protocol:
    pre-flight: signal quality check
    Then 4 alternating 90s blocks (counterbalanced ABAB design — fix per
    Claude validator who flagged the original fixed-order ABBA as fatigue-
    confounded). Total active recording: 360 s.

      Block 1 — REST       (90 s, eyes closed, slow breathing)
      Block 2 — ARITHMETIC (90 s, eyes closed, serial-7 from 1000)
      Block 3 — REST       (90 s)
      Block 4 — ARITHMETIC (90 s)

    The two REST blocks are pooled into a single "rest" condition for
    analysis; same for the two ARITHMETIC blocks. This averages out within-
    session drift while preserving the fast alternation.

Total: ~7-8 minutes including the pre-flight.

Predictions:
    alpha (rest) > alpha (arithmetic)        — replicated EEG finding
    beta (arithmetic) > beta (rest)          — replicated EEG finding
    theta (rest) >= theta (arithmetic)       — softer prediction
    Pairwise alpha coherence (rest) > arithmetic — OMDR-specific prediction

Usage:
    python experiment_3_meditation_contrast.py [--port 5000] [--subject jaie]
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from session import Session
from signal_quality import live_quality_check
from analyse_session import (
    analyse_session, write_summary, plot_segments,
    EEG_CHANNELS, ALPHA_BAND, THETA_BAND, BETA_BAND,
    coherence_in_band, load_eeg, load_markers, segments_from_markers, estimate_sample_rate, bandpower,
)

try:
    import winsound  # type: ignore
    def beep(freq: int = 660, ms: int = 300):
        try: winsound.Beep(freq, ms)
        except Exception: print("\a", end="", flush=True)
except Exception:  # pragma: no cover
    def beep(freq: int = 660, ms: int = 300):
        print("\a", end="", flush=True)


BLOCK_S = 90.0
N_REST_BLOCKS = 2
N_ARITH_BLOCKS = 2

# Add imag_coherence import for the volume-conduction-robust metric
from analyse_session import imag_coherence_in_band  # noqa: E402


def per_condition_stats(session_dir: Path) -> dict:
    """Compute per-condition stats by POOLING all blocks of the same condition.

    The protocol writes markers like 'rest_block_1', 'arithmetic_block_1',
    'rest_block_2', 'arithmetic_block_2'. We collect samples from all blocks
    of each condition and treat them as one big sample.
    """
    import numpy as np
    timestamps, eeg = load_eeg(session_dir)
    markers = load_markers(session_dir)
    fs = estimate_sample_rate(timestamps)
    segs = segments_from_markers(markers)
    pairs = [(0, 1, "TP9-AF7"), (0, 2, "TP9-AF8"), (0, 3, "TP9-TP10"),
             (1, 2, "AF7-AF8"), (1, 3, "AF7-TP10"), (2, 3, "AF8-TP10")]

    pooled: dict[str, list] = {"rest": [], "arithmetic": []}
    for label, start_ts, end_ts in segs:
        # Match block labels by prefix
        if label.startswith("rest_block"):
            cond = "rest"
        elif label.startswith("arithmetic_block"):
            cond = "arithmetic"
        else:
            continue
        mask = (timestamps >= start_ts) & (timestamps <= end_ts)
        seg = eeg[mask]
        if len(seg) >= int(fs * 5):
            pooled[cond].append(seg)

    out: dict[str, dict] = {}
    for cond, segs_list in pooled.items():
        if not segs_list:
            continue
        # Concatenate (per-channel)
        merged = np.concatenate(segs_list, axis=0)
        per_ch_alpha = [bandpower(merged[:, c], fs, ALPHA_BAND) for c in range(4)]
        per_ch_beta = [bandpower(merged[:, c], fs, BETA_BAND) for c in range(4)]
        per_ch_theta = [bandpower(merged[:, c], fs, THETA_BAND) for c in range(4)]
        coh = {p[2]: coherence_in_band(merged[:, p[0]], merged[:, p[1]], fs, ALPHA_BAND) for p in pairs}
        icoh = {p[2]: imag_coherence_in_band(merged[:, p[0]], merged[:, p[1]], fs, ALPHA_BAND) for p in pairs}
        coh_valid = [v for v in coh.values() if v == v]
        icoh_valid = [v for v in icoh.values() if v == v]
        out[cond] = {
            "n_blocks": len(segs_list),
            "n_samples": len(merged),
            "duration_s": float(len(merged) / fs),
            "alpha_per_channel": per_ch_alpha,
            "alpha_pooled_temporal": float((per_ch_alpha[0] + per_ch_alpha[3]) / 2),
            "beta_per_channel": per_ch_beta,
            "beta_pooled_temporal": float((per_ch_beta[0] + per_ch_beta[3]) / 2),
            "theta_per_channel": per_ch_theta,
            "theta_pooled_temporal": float((per_ch_theta[0] + per_ch_theta[3]) / 2),
            "alpha_coherence_pairs": coh,
            "alpha_coherence_global": float(sum(coh_valid) / len(coh_valid)) if coh_valid else float("nan"),
            "alpha_imag_coherence_pairs": icoh,
            "alpha_imag_coherence_global": float(sum(icoh_valid) / len(icoh_valid)) if icoh_valid else float("nan"),
        }
    return out


def main():
    parser = argparse.ArgumentParser(description="Experiment 3 — meditation vs arithmetic contrast")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--subject", default="jaie")
    parser.add_argument("--block-seconds", type=float, default=BLOCK_S, help="Duration of each block (default 90s)")
    parser.add_argument("--rest-blocks", type=int, default=N_REST_BLOCKS, help="Number of rest blocks (default 2)")
    parser.add_argument("--arithmetic-blocks", type=int, default=N_ARITH_BLOCKS, help="Number of arithmetic blocks (default 2)")
    parser.add_argument("--no-quality-gate", action="store_true")
    parser.add_argument("--quality-seconds", type=int, default=20)
    args = parser.parse_args()

    here = Path(__file__).parent

    # Build counterbalanced block plan: rest, arith, rest, arith, ...
    # Per Claude validator: fixed-order ABBA is fatigue-confounded; alternation
    # with multiple blocks of each averages out within-session drift.
    plan: list[tuple[str, int]] = []
    total_rest = args.rest_blocks
    total_arith = args.arithmetic_blocks
    rest_done = arith_done = 0
    while rest_done + arith_done < total_rest + total_arith:
        if rest_done <= arith_done and rest_done < total_rest:
            rest_done += 1
            plan.append(("rest", rest_done))
        else:
            arith_done += 1
            plan.append(("arithmetic", arith_done))

    total_seconds = len(plan) * args.block_seconds
    print("=" * 60)
    print(" EXPERIMENT 3 — Rest vs mental arithmetic (counterbalanced)")
    print("=" * 60)
    print(f"  Subject: {args.subject}")
    print(f"  {len(plan)} blocks × {args.block_seconds:.0f}s in alternating order: " + ", ".join(f"{cond[0].upper()}{i}" for cond, i in plan))
    print(f"  Total recording: ~{total_seconds:.0f}s")
    print("\n  REST blocks: eyes closed, slow easy breathing, just notice the breath.")
    print("  ARITHMETIC blocks: eyes closed, silently count down by 7 from 1000 — 993, 986, 979, ...")
    print("  If you lose your place in arithmetic, just start over from 1000.")
    print("  Eyes closed throughout — only the cognitive task changes.")
    input("  Press ENTER when ready... ")

    notes = (
        f"Experiment 3 — rest vs mental-arithmetic contrast. Counterbalanced: "
        f"{args.rest_blocks} rest + {args.arithmetic_blocks} arithmetic blocks of "
        f"{args.block_seconds:.0f}s each, alternating. Eyes closed throughout."
    )

    with Session("meditation-contrast", subject=args.subject, port=args.port,
                 sessions_root=here / "sessions", notes=notes) as s:
        if not args.no_quality_gate:
            ok = live_quality_check(s.receiver, min_seconds=args.quality_seconds, hold_seconds=3.0)
            if not ok:
                print("\n[experiment_3] Aborting — signal quality didn't reach all-good.")
                return 2

        for block_idx, (cond, n_in_cond) in enumerate(plan, 1):
            label_screen = "REST — close eyes, slow breathing" if cond == "rest" else "ARITHMETIC — count down by 7 from 1000"
            tone_a = (660, 300) if cond == "rest" else (440, 300)
            print(f"\n>>> BLOCK {block_idx}/{len(plan)} — {label_screen} — {args.block_seconds:.0f}s <<<")
            beep(*tone_a)
            if cond == "arithmetic":
                beep(*tone_a)
            s.mark(f"{cond}_block_{n_in_cond}")
            end = time.time() + args.block_seconds
            while time.time() < end:
                remaining = int(round(end - time.time()))
                sys.stdout.write(f"\r  {cond} block {n_in_cond}: {remaining:3d}s   ")
                sys.stdout.flush()
                time.sleep(0.5)
            print()

        s.mark("session_end")
        beep(660, 400)
        print("\n[experiment_3] Recording complete. Analysing...\n")
        session_dir = s.session_dir

    base = analyse_session(session_dir)
    write_summary(session_dir, base)
    plot_segments(session_dir, base)
    stats = per_condition_stats(session_dir)
    import json
    out = session_dir / "rest_vs_arithmetic.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    print("=" * 60)
    print(" REST vs ARITHMETIC")
    print("=" * 60)
    if "rest" in stats and "arithmetic" in stats:
        r = stats["rest"]
        a = stats["arithmetic"]
        def fmt(metric, r_val, a_val, predict_higher_in):
            try:
                hit = (r_val > a_val) if predict_higher_in.startswith("rest") else (a_val > r_val)
            except Exception:
                hit = False
            arrow = "->" + predict_higher_in
            mark = "[match]" if hit else "[miss] "
            print(f"  {mark} {metric:30s}  rest={r_val:.3f}  arith={a_val:.3f}   prediction: {arrow}")
        fmt("alpha (pooled temporal)", r["alpha_pooled_temporal"], a["alpha_pooled_temporal"], "rest")
        fmt("beta  (pooled temporal)", r["beta_pooled_temporal"], a["beta_pooled_temporal"], "arithmetic")
        fmt("theta (pooled temporal)", r["theta_pooled_temporal"], a["theta_pooled_temporal"], "rest (softer)")
        fmt("global alpha coherence (MSC)", r["alpha_coherence_global"], a["alpha_coherence_global"], "rest (OMDR-specific)")
        fmt("global alpha imag-coh (volume-conduction-robust)", r["alpha_imag_coherence_global"], a["alpha_imag_coherence_global"], "rest (OMDR-specific)")
        print(f"\n  rest blocks pooled: {r['n_blocks']}, total {r['duration_s']:.0f}s")
        print(f"  arithmetic blocks pooled: {a['n_blocks']}, total {a['duration_s']:.0f}s")
    print(f"\n  Saved: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
