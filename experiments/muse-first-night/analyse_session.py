"""Analyse a recorded session — alpha enhancement, FFT, pairwise coherence.

Loads the CSV files written by OscReceiver for a single session, slices by
the markers (transitions written via Session.mark), and computes:

  1. Per-channel alpha-band power (8-13 Hz) for each labelled segment
  2. Alpha-enhancement ratio: mean(eyes-closed alpha) / mean(eyes-open alpha)
     This is the canonical EEG sanity check. Eyes closed should give ~1.5-3x
     more alpha at the occipital and parietal sites. With Muse 4-channel
     placement (TP9, AF7, AF8, TP10), the temporal sites (TP9, TP10) are
     where the effect is most reliable.
  3. Pairwise magnitude-squared coherence at alpha and theta between channel
     pairs across the same segments (the harmonic-balance precursor)
  4. PSD plot per channel per condition
  5. JSON summary saved next to the data

The scoring is deliberately permissive — the alpha-enhancement ratio is
computed; whether it crosses any "real effect" threshold is the user's call.
We DO flag the enhancement ratio as a single number per channel and let the
operator decide.

Usage:
    python analyse_session.py sessions/20260407T193000_eyes-closed-baseline
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

import numpy as np
from scipy import signal as sp_signal

EEG_CHANNELS = ("TP9", "AF7", "AF8", "TP10")
ALPHA_BAND = (8.0, 13.0)
THETA_BAND = (4.0, 8.0)
BETA_BAND = (13.0, 30.0)
DELTA_BAND = (0.5, 4.0)
SAMPLE_RATE_NOMINAL = 256


@dataclass
class SegmentAnalysis:
    label: str
    start_wall: float
    end_wall: float
    duration_s: float
    n_samples: int
    sample_rate_hz: float
    alpha_uv2_per_channel: list[float]
    theta_uv2_per_channel: list[float]
    beta_uv2_per_channel: list[float]
    delta_uv2_per_channel: list[float]


@dataclass
class SessionAnalysis:
    session_dir: str
    n_eeg_samples: int
    sample_rate_hz: float
    segments: list[SegmentAnalysis]
    alpha_enhancement_per_channel: dict[str, float] | None
    alpha_enhancement_pooled_temporal: float | None
    coherence_alpha_pairs: dict[str, float]
    notes: list[str]


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_eeg(session_dir: Path) -> tuple[np.ndarray, np.ndarray]:
    """Return (timestamps, eeg) where eeg has shape (n_samples, 4)."""
    path = session_dir / "eeg.csv"
    if not path.exists():
        raise FileNotFoundError(f"No EEG data at {path}")
    ts, ch = [], []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 5:
                continue
            try:
                ts.append(float(row[0]))
                ch.append([float(row[1]), float(row[2]), float(row[3]), float(row[4])])
            except ValueError:
                continue
    return np.asarray(ts), np.asarray(ch)


def load_markers(session_dir: Path) -> list[tuple[float, str]]:
    path = session_dir / "markers.csv"
    if not path.exists():
        return []
    out: list[tuple[float, str]] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 2:
                try:
                    out.append((float(row[0]), row[1]))
                except ValueError:
                    continue
    return out


# ---------------------------------------------------------------------------
# Spectral helpers
# ---------------------------------------------------------------------------

def estimate_sample_rate(timestamps: np.ndarray) -> float:
    if len(timestamps) < 2:
        return float(SAMPLE_RATE_NOMINAL)
    intervals = np.diff(timestamps)
    intervals = intervals[(intervals > 0) & (intervals < 0.1)]  # discard outliers
    if len(intervals) == 0:
        return float(SAMPLE_RATE_NOMINAL)
    return float(1.0 / np.median(intervals))


def bandpower(samples: np.ndarray, fs: float, band: tuple[float, float]) -> float:
    """Welch PSD integrated over a frequency band, in (uV^2)."""
    if len(samples) < int(fs * 0.5):
        return float("nan")
    nperseg = min(int(fs * 2), len(samples))
    freqs, psd = sp_signal.welch(samples, fs=fs, nperseg=nperseg)
    mask = (freqs >= band[0]) & (freqs <= band[1])
    if not mask.any():
        return float("nan")
    return float(np.trapezoid(psd[mask], freqs[mask]))


def coherence_in_band(x: np.ndarray, y: np.ndarray, fs: float, band: tuple[float, float]) -> float:
    """Mean magnitude-squared coherence between x and y over a frequency band."""
    if len(x) < int(fs * 0.5) or len(y) < int(fs * 0.5):
        return float("nan")
    nperseg = min(int(fs * 2), len(x))
    freqs, cxy = sp_signal.coherence(x, y, fs=fs, nperseg=nperseg)
    mask = (freqs >= band[0]) & (freqs <= band[1])
    if not mask.any():
        return float("nan")
    return float(np.mean(cxy[mask]))


def imag_coherence_in_band(x: np.ndarray, y: np.ndarray, fs: float, band: tuple[float, float]) -> float:
    """Mean ABSOLUTE imaginary coherence over a frequency band.

    Imaginary coherence is robust against zero-phase volume conduction artifacts
    that plague the 4-channel Muse — only signals with a non-zero phase lag
    contribute, so spurious instantaneous-mixing common across nearby electrodes
    is filtered out. Recommended by 2/3 validators (Grok + Claude) over plain
    magnitude-squared coherence for this hardware.

    We compute it from the cross-spectral density via Welch.
    """
    if len(x) < int(fs * 0.5) or len(y) < int(fs * 0.5):
        return float("nan")
    nperseg = min(int(fs * 2), len(x))
    freqs, csd = sp_signal.csd(x, y, fs=fs, nperseg=nperseg)
    _, pxx = sp_signal.welch(x, fs=fs, nperseg=nperseg)
    _, pyy = sp_signal.welch(y, fs=fs, nperseg=nperseg)
    denom = np.sqrt(pxx * pyy)
    # Avoid division-by-zero
    denom = np.where(denom > 1e-30, denom, 1e-30)
    coh_complex = csd / denom
    imag_coh = np.abs(np.imag(coh_complex))
    mask = (freqs >= band[0]) & (freqs <= band[1])
    if not mask.any():
        return float("nan")
    return float(np.mean(imag_coh[mask]))


def individual_alpha_peak(samples: np.ndarray, fs: float, search: tuple[float, float] = (6.0, 15.0)) -> float:
    """Find the peak frequency in a wider search window than the canonical 8-13 Hz alpha band.

    Some individuals have alpha peaks at 7 Hz or 14 Hz; if our analysis only looks
    at 8-13 Hz we'll miss the effect entirely. Diagnostic for the null case.
    Returns NaN if no peak is found.
    """
    if len(samples) < int(fs * 1.0):
        return float("nan")
    nperseg = min(int(fs * 4), len(samples))
    freqs, psd = sp_signal.welch(samples, fs=fs, nperseg=nperseg)
    mask = (freqs >= search[0]) & (freqs <= search[1])
    if not mask.any():
        return float("nan")
    sub_freqs = freqs[mask]
    sub_psd = psd[mask]
    if len(sub_psd) == 0:
        return float("nan")
    return float(sub_freqs[np.argmax(sub_psd)])


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def segments_from_markers(markers: list[tuple[float, str]]) -> list[tuple[str, float, float]]:
    """Convert sequential markers into (label, start_ts, end_ts) tuples.

    Heuristic: each marker starts a new segment with that label, ending when
    the next marker arrives. The label of the segment is the marker that
    OPENED it.
    """
    if len(markers) < 2:
        return []
    out = []
    for i in range(len(markers) - 1):
        label, start_ts = markers[i][1], markers[i][0]
        end_ts = markers[i + 1][0]
        out.append((label, start_ts, end_ts))
    return out


def analyse_segment(
    timestamps: np.ndarray,
    eeg: np.ndarray,
    label: str,
    start_ts: float,
    end_ts: float,
    fs: float,
) -> SegmentAnalysis:
    mask = (timestamps >= start_ts) & (timestamps <= end_ts)
    seg = eeg[mask]
    n = len(seg)

    alpha = [bandpower(seg[:, c], fs, ALPHA_BAND) for c in range(4)]
    theta = [bandpower(seg[:, c], fs, THETA_BAND) for c in range(4)]
    beta = [bandpower(seg[:, c], fs, BETA_BAND) for c in range(4)]
    delta = [bandpower(seg[:, c], fs, DELTA_BAND) for c in range(4)]

    return SegmentAnalysis(
        label=label,
        start_wall=start_ts,
        end_wall=end_ts,
        duration_s=end_ts - start_ts,
        n_samples=n,
        sample_rate_hz=fs,
        alpha_uv2_per_channel=alpha,
        theta_uv2_per_channel=theta,
        beta_uv2_per_channel=beta,
        delta_uv2_per_channel=delta,
    )


def analyse_session(session_dir: Path) -> SessionAnalysis:
    timestamps, eeg = load_eeg(session_dir)
    markers = load_markers(session_dir)
    fs = estimate_sample_rate(timestamps)
    notes: list[str] = []
    notes.append(f"Loaded {len(eeg)} EEG samples; estimated sample rate {fs:.1f} Hz")
    if abs(fs - SAMPLE_RATE_NOMINAL) > 16:
        notes.append(f"WARNING: sample rate {fs:.1f} Hz differs from nominal 256 Hz by >16 Hz")

    segs_def = segments_from_markers(markers)
    if not segs_def:
        notes.append("No marker pairs found — skipping segment analysis (whole-session stats only)")
        whole = analyse_segment(timestamps, eeg, "whole_session", timestamps[0], timestamps[-1], fs)
        segments = [whole]
    else:
        segments = [analyse_segment(timestamps, eeg, lbl, s, e, fs) for lbl, s, e in segs_def]

    # Alpha enhancement: ratio of alpha during eyes_closed vs eyes_open segments.
    closed = [s for s in segments if "closed" in s.label.lower()]
    opened = [s for s in segments if "open" in s.label.lower()]
    enhancement: Optional[dict[str, float]] = None
    pooled_temporal: Optional[float] = None
    if closed and opened:
        enhancement = {}
        for c, name in enumerate(EEG_CHANNELS):
            mean_closed = np.nanmean([s.alpha_uv2_per_channel[c] for s in closed])
            mean_open = np.nanmean([s.alpha_uv2_per_channel[c] for s in opened])
            enhancement[name] = float(mean_closed / mean_open) if mean_open > 0 else float("nan")
        # Pooled temporal channels (TP9, TP10) — most reliable for alpha
        temporal = [(0, "TP9"), (3, "TP10")]
        closed_temp = np.nanmean([
            s.alpha_uv2_per_channel[idx] for s in closed for idx, _ in temporal
        ])
        open_temp = np.nanmean([
            s.alpha_uv2_per_channel[idx] for s in opened for idx, _ in temporal
        ])
        pooled_temporal = float(closed_temp / open_temp) if open_temp > 0 else float("nan")
        notes.append(f"Alpha enhancement (closed/open) per channel: {enhancement}")
        notes.append(f"Pooled temporal alpha enhancement: {pooled_temporal:.2f}")
    else:
        notes.append("No closed/open segment pair found — alpha enhancement not computed")

    # Pairwise coherence at alpha (whole-session)
    # We compute BOTH magnitude-squared coherence and imaginary coherence —
    # the latter is robust against volume conduction artifacts on a 4-channel
    # headband (recommended by Grok + Claude validators).
    coh = {}
    icoh = {}
    pairs = [(0, 1, "TP9-AF7"), (0, 2, "TP9-AF8"), (0, 3, "TP9-TP10"),
             (1, 2, "AF7-AF8"), (1, 3, "AF7-TP10"), (2, 3, "AF8-TP10")]
    for i, j, name in pairs:
        coh[name] = coherence_in_band(eeg[:, i], eeg[:, j], fs, ALPHA_BAND)
        icoh[name] = imag_coherence_in_band(eeg[:, i], eeg[:, j], fs, ALPHA_BAND)

    # Individual alpha peak frequencies per channel (whole session)
    iaf = {EEG_CHANNELS[c]: individual_alpha_peak(eeg[:, c], fs) for c in range(4)}
    notes.append(f"Individual alpha peak frequencies (Hz): {iaf}")

    analysis = SessionAnalysis(
        session_dir=str(session_dir),
        n_eeg_samples=len(eeg),
        sample_rate_hz=fs,
        segments=segments,
        alpha_enhancement_per_channel=enhancement,
        alpha_enhancement_pooled_temporal=pooled_temporal,
        coherence_alpha_pairs=coh,
        notes=notes,
    )
    # Attach the extra fields without breaking the dataclass shape
    analysis.imag_coherence_alpha_pairs = icoh  # type: ignore
    analysis.individual_alpha_peak_hz = iaf  # type: ignore
    return analysis


# ---------------------------------------------------------------------------
# Plot + summary
# ---------------------------------------------------------------------------

def plot_segments(session_dir: Path, analysis: SessionAnalysis) -> Optional[Path]:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as e:
        analysis.notes.append(f"matplotlib unavailable, skipping plot: {e}")
        return None

    if not analysis.segments:
        return None
    seg_labels = [s.label for s in analysis.segments]
    fig, ax = plt.subplots(figsize=(10, 5))
    width = 0.18
    x = np.arange(len(seg_labels))
    for c, name in enumerate(EEG_CHANNELS):
        vals = [s.alpha_uv2_per_channel[c] for s in analysis.segments]
        ax.bar(x + (c - 1.5) * width, vals, width, label=name)
    ax.set_xticks(x)
    ax.set_xticklabels(seg_labels, rotation=15)
    ax.set_ylabel("Alpha power (uV^2)")
    ax.set_title(f"Alpha (8-13 Hz) per segment — {Path(session_dir).name}")
    ax.legend()
    out = Path(session_dir) / "alpha_per_segment.png"
    fig.tight_layout()
    fig.savefig(out, dpi=120)
    plt.close(fig)
    return out


def write_summary(session_dir: Path, analysis: SessionAnalysis) -> Path:
    out = Path(session_dir) / "analysis_summary.json"
    payload = {
        "session_dir": analysis.session_dir,
        "n_eeg_samples": analysis.n_eeg_samples,
        "sample_rate_hz": analysis.sample_rate_hz,
        "segments": [asdict(s) for s in analysis.segments],
        "alpha_enhancement_per_channel": analysis.alpha_enhancement_per_channel,
        "alpha_enhancement_pooled_temporal": analysis.alpha_enhancement_pooled_temporal,
        "coherence_alpha_pairs": analysis.coherence_alpha_pairs,
        "imag_coherence_alpha_pairs": getattr(analysis, "imag_coherence_alpha_pairs", None),
        "individual_alpha_peak_hz": getattr(analysis, "individual_alpha_peak_hz", None),
        "notes": analysis.notes,
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, default=str)
    return out


def main():
    parser = argparse.ArgumentParser(description="Analyse a single session")
    parser.add_argument("session_dir", type=Path)
    args = parser.parse_args()
    if not args.session_dir.exists():
        print(f"Session directory not found: {args.session_dir}")
        sys.exit(1)
    analysis = analyse_session(args.session_dir)
    summary = write_summary(args.session_dir, analysis)
    plot = plot_segments(args.session_dir, analysis)
    print(f"\n=== ANALYSIS COMPLETE ===")
    for note in analysis.notes:
        print(f"  {note}")
    print(f"\nSummary written to: {summary}")
    if plot:
        print(f"Plot written to:    {plot}")
    if analysis.alpha_enhancement_pooled_temporal is not None:
        ratio = analysis.alpha_enhancement_pooled_temporal
        # Threshold lowered from 1.5x -> 1.2x for the temporal-only Muse pooling.
        # Validators converged: TP9/TP10 alpha is ~1.2-2x at temporal vs 2-4x occipital.
        verdict = "STRONG" if ratio > 1.5 else ("MODERATE" if ratio > 1.2 else ("WEAK" if ratio > 1.0 else "NONE"))
        print(f"\nAlpha enhancement (closed/open, temporal channels pooled): {ratio:.2f}x  [{verdict}]")
        print("  (literature: 1.2-2x at temporal sites — Muse cannot reach occipital)")
    iaf = getattr(analysis, "individual_alpha_peak_hz", None)
    if iaf:
        print(f"\nIndividual alpha peak frequencies (search 6-15 Hz):")
        for ch, hz in iaf.items():
            print(f"  {ch}: {hz:.2f} Hz")
        print("  (canonical 8-13 Hz; if your peak is outside that, the band-power\n   may understate the real alpha — diagnostic for null cases)")


if __name__ == "__main__":
    main()
