"""Post-session feature computation — slow, retryable.

Reads a completed session's FIF files + markers.json, computes derived
features, and writes them to Postgres analysis_results table. Can be
re-run safely against the same session to update features when the
method versions change.

Per the non-destructive principle, everything in this file is ANALYSIS
layer, not storage. Clock-drift correction, fNIRS lag offsets, window
choices (Fibonacci vs dyadic), and unit conversions are all parameterized
here, not baked into the data.

Currently computes:
  - Individual alpha peak frequency per EEG channel (6-15 Hz search)
  - Per-segment alpha band power (8-13 Hz) for each labelled segment
  - Alpha enhancement ratio (eyes-closed / eyes-open) per channel
  - Pooled temporal alpha enhancement (TP9 + TP10 primary metric)
  - Pairwise coherence (magnitude-squared) at alpha band for EEG channels
  - Pairwise imaginary coherence (volume-conduction-robust) at alpha band

Future features (not computed tonight but schema ready):
  - EEG-fNIRS cross-coherence with configurable lag offset
  - Multi-taper spectral analysis
  - Phase-locking value (PLV) and wPLI
  - Harmonic balance metric (the OMDR-specific feature)

Usage:
    from post_session_features import compute_features
    result = compute_features(
        session_dir=Path("experiments/muse-first-night/data/sub-jaie/ses-20260408T190000"),
        session_id=UUID("..."),
    )
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import UUID

import numpy as np
from scipy import signal as sp_signal

# Band definitions (analysis-layer parameters, all mutable)
BAND_DELTA = (0.5, 4.0)
BAND_THETA = (4.0, 8.0)
BAND_ALPHA = (8.0, 13.0)
BAND_BETA  = (13.0, 30.0)
BAND_GAMMA = (30.0, 45.0)

# Default channel pools for the 8-channel Athena EEG layout
TEMPORAL_CHANNELS = ["EEG_TP9", "EEG_TP10"]
FRONTAL_CHANNELS  = ["EEG_AF7", "EEG_AF8"]
AUX_CHANNELS      = ["AUX_1", "AUX_2", "AUX_3", "AUX_4"]

METHOD_NAME = "eyes_closed_baseline_v2"
METHOD_VERSION = "1.0.0"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _db_config() -> dict:
    return {
        "host":     os.environ.get("OMDR_BCI_PGHOST", "localhost"),
        "port":     int(os.environ.get("OMDR_BCI_PGPORT", "5432")),
        "dbname":   os.environ.get("OMDR_BCI_PGDATABASE", "omdr_bci"),
        "user":     os.environ.get("OMDR_BCI_PGUSER", "kai"),
        "password": os.environ.get("OMDR_BCI_PGPASSWORD", "resonance"),
    }


def _connect():
    import psycopg2
    return psycopg2.connect(**_db_config())


def _bandpower(samples: np.ndarray, sfreq: float, band: tuple[float, float]) -> float:
    if len(samples) < int(sfreq * 0.5):
        return float("nan")
    nperseg = min(int(sfreq * 2), len(samples))
    freqs, psd = sp_signal.welch(samples, fs=sfreq, nperseg=nperseg)
    mask = (freqs >= band[0]) & (freqs <= band[1])
    if not mask.any():
        return float("nan")
    return float(np.trapezoid(psd[mask], freqs[mask]))


def _individual_alpha_peak(samples: np.ndarray, sfreq: float,
                           search: tuple[float, float] = (6.0, 15.0)) -> float:
    if len(samples) < int(sfreq * 1.0):
        return float("nan")
    nperseg = min(int(sfreq * 4), len(samples))
    freqs, psd = sp_signal.welch(samples, fs=sfreq, nperseg=nperseg)
    mask = (freqs >= search[0]) & (freqs <= search[1])
    if not mask.any():
        return float("nan")
    sub_freqs = freqs[mask]
    sub_psd = psd[mask]
    return float(sub_freqs[int(np.argmax(sub_psd))])


def _coherence_in_band(x: np.ndarray, y: np.ndarray, sfreq: float,
                       band: tuple[float, float]) -> float:
    if len(x) < int(sfreq * 0.5) or len(y) < int(sfreq * 0.5):
        return float("nan")
    nperseg = min(int(sfreq * 2), len(x))
    freqs, cxy = sp_signal.coherence(x, y, fs=sfreq, nperseg=nperseg)
    mask = (freqs >= band[0]) & (freqs <= band[1])
    return float(np.mean(cxy[mask])) if mask.any() else float("nan")


def _imag_coherence_in_band(x: np.ndarray, y: np.ndarray, sfreq: float,
                            band: tuple[float, float]) -> float:
    if len(x) < int(sfreq * 0.5) or len(y) < int(sfreq * 0.5):
        return float("nan")
    nperseg = min(int(sfreq * 2), len(x))
    freqs, csd = sp_signal.csd(x, y, fs=sfreq, nperseg=nperseg)
    _, pxx = sp_signal.welch(x, fs=sfreq, nperseg=nperseg)
    _, pyy = sp_signal.welch(y, fs=sfreq, nperseg=nperseg)
    denom = np.sqrt(pxx * pyy)
    denom = np.where(denom > 1e-30, denom, 1e-30)
    coh_complex = csd / denom
    imag_coh = np.abs(np.imag(coh_complex))
    mask = (freqs >= band[0]) & (freqs <= band[1])
    return float(np.mean(imag_coh[mask])) if mask.any() else float("nan")


# ---------------------------------------------------------------------------
# Segment extraction
# ---------------------------------------------------------------------------

@dataclass
class Segment:
    label: str
    started_lsl_sec: float
    ended_lsl_sec: float
    is_eyes_closed: bool
    is_eyes_open: bool


def _load_markers(session_dir: Path) -> list[dict]:
    p = session_dir / "markers.json"
    if not p.exists():
        return []
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def _markers_to_segments(markers: list[dict]) -> list[Segment]:
    """Convert sequential markers into (label, start, end) segments.

    Each marker opens a new segment; that segment ends when the next marker
    arrives. session_start and session_end bound the first and last
    segments but aren't themselves data-bearing labels.
    """
    if len(markers) < 2:
        return []
    segs = []
    for i in range(len(markers) - 1):
        label = markers[i]["label"]
        start = float(markers[i]["lsl_clock_sec"])
        end = float(markers[i + 1]["lsl_clock_sec"])
        if label in ("session_start", "session_end"):
            continue
        segs.append(Segment(
            label=label,
            started_lsl_sec=start,
            ended_lsl_sec=end,
            is_eyes_closed="closed" in label.lower(),
            is_eyes_open="open" in label.lower(),
        ))
    return segs


# ---------------------------------------------------------------------------
# FIF loading
# ---------------------------------------------------------------------------

def _load_eeg_fif(session_dir: Path):
    """Return (raw, lsl_timestamps, host_timestamps) for the EEG FIF."""
    import mne
    fif_path = session_dir / "eeg_raw.fif"
    if not fif_path.exists():
        return None, None, None
    raw = mne.io.read_raw_fif(fif_path, preload=True, verbose="ERROR")
    ts_path = session_dir / "eeg_timestamps.npz"
    lsl_ts, host_ts = None, None
    if ts_path.exists():
        data = np.load(ts_path)
        lsl_ts = data.get("lsl_times")
        host_ts = data.get("host_times")
    return raw, lsl_ts, host_ts


# ---------------------------------------------------------------------------
# Main compute entry
# ---------------------------------------------------------------------------

def compute_features(session_dir: Path, session_id: Optional[UUID] = None,
                     tolerance_factor: float = 3.0) -> dict:
    """Compute features for one session; optionally write results to Postgres.

    Parameters
    ----------
    session_dir : Path
        BIDS session directory containing eeg_raw.fif, markers.json, etc.
    session_id : UUID or None
        If provided, write analysis_results rows linked to this session_id.
        If None, only compute and return results without DB writes.
    tolerance_factor : float
        Analysis-time parameter for any tolerance-based filters.

    Returns
    -------
    dict
        Full result blob with all computed features.
    """
    session_dir = Path(session_dir).resolve()
    raw, lsl_ts, host_ts = _load_eeg_fif(session_dir)
    if raw is None:
        return {"error": "no eeg_raw.fif found in session_dir"}

    markers = _load_markers(session_dir)
    segments = _markers_to_segments(markers)

    sfreq = float(raw.info["sfreq"])
    ch_names = raw.ch_names
    data = raw.get_data()  # shape (n_channels, n_samples)
    n_channels, n_samples = data.shape

    result: dict = {
        "method": METHOD_NAME,
        "version": METHOD_VERSION,
        "session_dir": str(session_dir),
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "sfreq": sfreq,
        "ch_names": list(ch_names),
        "n_samples": n_samples,
        "n_segments": len(segments),
        "parameters": {
            "band_alpha": list(BAND_ALPHA),
            "band_theta": list(BAND_THETA),
            "band_beta": list(BAND_BETA),
            "band_delta": list(BAND_DELTA),
            "band_gamma": list(BAND_GAMMA),
            "individual_alpha_peak_search": [6.0, 15.0],
            "temporal_channels": TEMPORAL_CHANNELS,
            "frontal_channels": FRONTAL_CHANNELS,
            "aux_channels": AUX_CHANNELS,
            "tolerance_factor": tolerance_factor,
        },
    }

    # --- Individual alpha peak per channel (over whole recording) -------------
    iaf = {}
    for c, name in enumerate(ch_names):
        iaf[name] = _individual_alpha_peak(data[c], sfreq)
    result["individual_alpha_peak_hz"] = iaf

    # --- Per-segment band powers ----------------------------------------------
    if not segments or lsl_ts is None:
        result["segment_analysis"] = None
        result["alpha_enhancement"] = {"pooled_temporal": None, "per_channel": None,
                                        "note": "no segments or no LSL timestamps found"}
    else:
        segment_features = []
        # Use the LSL timestamps to convert LSL-clock segment boundaries
        # to sample indices
        lsl_ts = np.asarray(lsl_ts, dtype=np.float64)
        for seg in segments:
            # Find the subset of samples falling within this segment by LSL clock
            mask = (lsl_ts >= seg.started_lsl_sec) & (lsl_ts <= seg.ended_lsl_sec)
            if not mask.any():
                continue
            idx = np.where(mask)[0]
            start_idx, end_idx = int(idx[0]), int(idx[-1]) + 1
            seg_data = data[:, start_idx:end_idx]
            per_ch_alpha = [_bandpower(seg_data[c], sfreq, BAND_ALPHA) for c in range(n_channels)]
            per_ch_beta  = [_bandpower(seg_data[c], sfreq, BAND_BETA)  for c in range(n_channels)]
            per_ch_theta = [_bandpower(seg_data[c], sfreq, BAND_THETA) for c in range(n_channels)]
            segment_features.append({
                "label": seg.label,
                "duration_s": seg.ended_lsl_sec - seg.started_lsl_sec,
                "n_samples": end_idx - start_idx,
                "is_eyes_closed": seg.is_eyes_closed,
                "is_eyes_open": seg.is_eyes_open,
                "alpha_per_channel": per_ch_alpha,
                "beta_per_channel": per_ch_beta,
                "theta_per_channel": per_ch_theta,
            })
        result["segment_analysis"] = segment_features

        # --- Alpha enhancement ratio ------------------------------------------
        closed = [s for s in segment_features if s["is_eyes_closed"]]
        opened = [s for s in segment_features if s["is_eyes_open"]]
        ae: dict = {
            "pooled_temporal": None,
            "pooled_frontal": None,
            "per_channel": None,
        }
        if closed and opened:
            per_ch = {}
            for c, name in enumerate(ch_names):
                closed_vals = np.array([s["alpha_per_channel"][c] for s in closed])
                open_vals   = np.array([s["alpha_per_channel"][c] for s in opened])
                mean_closed = float(np.nanmean(closed_vals))
                mean_open   = float(np.nanmean(open_vals))
                per_ch[name] = (mean_closed / mean_open) if mean_open > 0 else float("nan")
            ae["per_channel"] = per_ch

            def _pool(channels: list[str]) -> Optional[float]:
                vals = [per_ch[c] for c in channels if c in per_ch and per_ch[c] == per_ch[c]]
                return float(np.nanmean(vals)) if vals else None

            ae["pooled_temporal"] = _pool(TEMPORAL_CHANNELS)
            ae["pooled_frontal"]  = _pool(FRONTAL_CHANNELS)
        result["alpha_enhancement"] = ae

    # --- Pairwise coherence at alpha (whole recording) ------------------------
    coh = {}
    icoh = {}
    # All unique pairs
    for i in range(n_channels):
        for j in range(i + 1, n_channels):
            pair_name = f"{ch_names[i]}-{ch_names[j]}"
            coh[pair_name]  = _coherence_in_band(data[i], data[j], sfreq, BAND_ALPHA)
            icoh[pair_name] = _imag_coherence_in_band(data[i], data[j], sfreq, BAND_ALPHA)
    result["alpha_coherence_msc"] = coh
    result["alpha_coherence_imag"] = icoh

    # --- Persist summary JSON next to the FIF -------------------------------
    summary_path = session_dir / "analysis_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, default=str)

    # --- Write to Postgres if session_id provided --------------------------
    if session_id is not None:
        try:
            conn = _connect()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO analysis_results (
                                session_id, method, version, parameters, result, code_version
                            )
                            VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, %s)""",
                        (
                            str(session_id),
                            METHOD_NAME,
                            METHOD_VERSION,
                            json.dumps(result["parameters"], default=str),
                            json.dumps(result, default=str),
                            None,  # code_version — could be filled with git hash
                        ),
                    )
                conn.commit()
            finally:
                conn.close()
        except Exception as e:
            result["db_write_error"] = f"{type(e).__name__}: {e}"

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Compute features for a completed session")
    parser.add_argument("session_dir", type=Path)
    parser.add_argument("--session-id", type=str, default=None)
    args = parser.parse_args()
    session_id = UUID(args.session_id) if args.session_id else None
    result = compute_features(args.session_dir, session_id=session_id)
    if "alpha_enhancement" in result and result["alpha_enhancement"]:
        ae = result["alpha_enhancement"]
        if ae.get("pooled_temporal") is not None:
            print(f"Pooled temporal alpha enhancement: {ae['pooled_temporal']:.2f}x")
        if ae.get("per_channel"):
            print("Per-channel:")
            for ch, r in ae["per_channel"].items():
                print(f"  {ch}: {r:.2f}x")
    print(f"Full results written to: {args.session_dir}/analysis_summary.json")
