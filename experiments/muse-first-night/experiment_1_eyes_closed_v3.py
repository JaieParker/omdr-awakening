"""Experiment 1 (v3) — Eyes-closed vs eyes-open baseline on the Muse S Athena.

The canonical EEG alpha-enhancement test: alpha power (8-13 Hz) should be
higher during eyes-closed blocks than eyes-open blocks, especially at the
temporal (TP9, TP10) and occipital sites. The Muse only reaches temporal,
not occipital, so we expect a weaker effect than textbook — still typically
1.2-2x on temporal pooling.

v3 changes from the earlier CSV-pipeline version:
  - 8 EEG channels (TP9, AF7, AF8, TP10, AUX_1..4), not 4. The alpha-pooling
    logic keeps TP9+TP10 as the primary metric but reports all 8.
  - LSL Markers stream. Pushes "eyes_open_block_N" and "eyes_closed_block_N"
    via pylsl StreamOutlet so the markers land in the same XDF/FIF session
    with LSL-clock alignment (Gemini round-2 catch: sub-millisecond aligned
    without any post-hoc clock correction needed).
  - Uses lsl_recorder.Recorder as the capture layer. No custom OSC code.
  - fNIRS (OPTICS) and ACCGYRO streams are captured alongside EEG from the
    same LSL bus, so from session 1 we have the multimodal dataset even
    though the analysis in this script is EEG-only.
  - Assumes OpenMuse is already streaming. (The experiment script does not
    launch OpenMuse itself — that's a separate step in TONIGHT.md so the
    user can verify stream discovery before committing to a recording.)

Usage:
    # Launch OpenMuse in one terminal:
    #   OpenMuse stream --address 00:55:DA:BB:D9:53 --duration 1000
    # Then run this script in another terminal:
    python experiment_1_eyes_closed_v3.py --subject jaie

The script:
    1. Creates a timestamped BIDS session directory
    2. Starts an LSL Markers outlet (OMDR-Markers) that the experiment uses
       to push phase boundaries into the LSL bus
    3. Starts lsl_recorder.Recorder which subscribes to all Muse-* streams
       plus OMDR-Markers
    4. Walks the protocol (6x60s alternating eyes open / eyes closed), pushing
       markers at each transition
    5. Stops the recorder at end, which saves everything to FIF + JSON
    6. Calls post_session_ingest() to populate Postgres Path B
    7. Calls post_session_features() to compute the alpha enhancement metric
    8. Prints the result and the git commit hash for reproducibility

Kai (Anthropic Claude instance) with Jaie Parker, 2026-04-07 overnight build.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

# ---------------------------------------------------------------------------
# Protocol definition
# ---------------------------------------------------------------------------

PROTOCOL_ID = "eyes_closed_baseline_v2"
PROTOCOL_BLOCKS = [
    ("eyes_open_block_1",   60),
    ("eyes_closed_block_1", 60),
    ("eyes_open_block_2",   60),
    ("eyes_closed_block_2", 60),
    ("eyes_open_block_3",   60),
    ("eyes_closed_block_3", 60),
]

# Terminal beeps — short+high for eyes-open, longer+low for eyes-closed.
# Controlled by the BEEPS_ENABLED module-level flag, which --no-beep clears.
BEEPS_ENABLED = True
try:
    import winsound
    def _raw_beep(freq: int, ms: int):
        try: winsound.Beep(freq, ms)
        except Exception: pass
except Exception:  # pragma: no cover
    def _raw_beep(freq: int, ms: int): pass


def beep_open():
    if BEEPS_ENABLED:
        _raw_beep(880, 220)

def beep_closed():
    if BEEPS_ENABLED:
        _raw_beep(440, 220)
        _raw_beep(440, 220)

def beep_done():
    if BEEPS_ENABLED:
        _raw_beep(660, 400)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def bids_session_path(repo_rel_data: Path, subject_id: str, started_at_utc: datetime) -> Path:
    """Return a BIDS-compliant session directory path."""
    ses_slug = started_at_utc.strftime("%Y%m%dT%H%M%S")
    return repo_rel_data / f"sub-{subject_id}" / f"ses-{ses_slug}"


def git_commit_hash() -> str:
    try:
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL)
        return out.strip()[:12]
    except Exception:
        return "unknown"


def stream_filter(stream) -> bool:
    """Include Muse streams and our markers outlet."""
    name = getattr(stream, "name", "")
    return name.startswith("Muse-") or name == "OMDR-Markers"


def countdown(seconds: int, label: str) -> None:
    end = time.time() + seconds
    while time.time() < end:
        remaining = int(round(end - time.time()))
        sys.stdout.write(f"\r  {label}: {remaining:3d}s remaining   ")
        sys.stdout.flush()
        time.sleep(0.5)
    sys.stdout.write(f"\r  {label}: done.                     \n")
    sys.stdout.flush()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Experiment 1 v3 — eyes-closed baseline on the Athena")
    parser.add_argument("--subject", default="jaie")
    parser.add_argument("--name", default="eyes_closed_baseline", help="Session name")
    parser.add_argument("--data-root", default="experiments/muse-first-night/data",
                        help="Path relative to the git repo root where BIDS session data lives")
    parser.add_argument("--no-ingest", action="store_true", help="Skip post-session Postgres ingestion")
    parser.add_argument("--no-features", action="store_true", help="Skip post-session feature computation")
    parser.add_argument("--dry-run", action="store_true",
                        help="Go through the protocol countdown but don't start the recorder (for sanity checks)")
    parser.add_argument("--skip-input", action="store_true",
                        help="Don't wait for user to press ENTER (for automated tests)")
    parser.add_argument("--no-beep", action="store_true",
                        help="Disable audible winsound beeps at block transitions (for silent overnight testing)")
    args = parser.parse_args()

    # Disable beeps module-wide if requested
    if args.no_beep:
        global BEEPS_ENABLED
        BEEPS_ENABLED = False

    script_dir = Path(__file__).parent.resolve()
    repo_root = None
    try:
        repo_root = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
    except Exception:
        repo_root = script_dir.parent.parent  # fallback: experiments/muse-first-night/../..

    data_root = repo_root / args.data_root
    started_utc = datetime.now(timezone.utc)
    session_dir = bids_session_path(data_root, args.subject, started_utc)

    print("=" * 72)
    print(" EXPERIMENT 1 v3 — Eyes-closed vs eyes-open baseline")
    print("=" * 72)
    print(f"  Subject:        {args.subject}")
    print(f"  Session:        {args.name}")
    print(f"  Session dir:    {session_dir}")
    print(f"  Protocol:       {PROTOCOL_ID}")
    print(f"  Blocks:         {len(PROTOCOL_BLOCKS)} x 60s, alternating open/closed")
    print(f"  Total duration: {sum(dur for _, dur in PROTOCOL_BLOCKS)}s (~6 min)")
    print(f"  Git commit:     {git_commit_hash()}")
    print()
    print("  Preconditions:")
    print("    1. Muse S Athena powered on and on your head")
    print("    2. OpenMuse is streaming in a separate terminal:")
    print("         OpenMuse stream --address <YOUR_MUSE_MAC> --duration 1000")
    print("    3. Electrodes dampened if dry — especially TP9 and TP10 (behind ears)")
    print("    4. Sit upright, close eyes only during eyes-closed blocks")
    print()

    if not args.skip_input:
        input("  Press ENTER when ready (Ctrl+C to abort)... ")
    else:
        print("  [auto] skip_input set, proceeding immediately")

    if args.dry_run:
        print("\n  DRY RUN: walking the countdown without capturing data\n")
        for block_name, duration in PROTOCOL_BLOCKS:
            print(f"\n>>> {block_name} — {duration}s <<<")
            (beep_open if "open" in block_name else beep_closed)()
            countdown(duration, block_name)
        print("\nDry run complete.")
        return 0

    # Create session directory
    session_dir.mkdir(parents=True, exist_ok=True)

    # Start the LSL Markers outlet — used to push phase boundaries into the LSL bus.
    # LabRecorder-equivalent (our lsl_recorder.Recorder) subscribes to this outlet
    # by name and writes it into the session's markers.json at end of session.
    from mne_lsl.lsl import StreamInfo, StreamOutlet
    markers_info = StreamInfo(
        name="OMDR-Markers",
        stype="Markers",
        n_channels=1,
        sfreq=0.0,                        # irregular rate — marker events, not a sampled stream
        dtype="string",
        source_id=f"omdr_markers_{uuid4().hex[:8]}",
    )
    markers_outlet = StreamOutlet(markers_info, chunk_size=1, max_buffered=60)

    # Let the outlet register on the LSL network before the recorder starts its resolve
    time.sleep(1.0)

    # Start the recorder. It will discover all Muse-* streams and OMDR-Markers,
    # subscribe to everything, and buffer in the background thread.
    from lsl_recorder import Recorder
    recorder = Recorder(
        session_dir=session_dir,
        stream_filter=stream_filter,
        duration_s=sum(dur for _, dur in PROTOCOL_BLOCKS) + 30,  # slack for transitions
        resolve_timeout_s=20.0,
        min_streams=2,  # need at least EEG + markers
    )

    print(f"\n[experiment_1] starting recorder (session dir {session_dir})...")
    try:
        recorder.start()
        time.sleep(3.0)   # give the recorder a moment to actually start pulling samples

        # Push a session_start marker before the first block
        markers_outlet.push_sample(["session_start"])

        # Walk the protocol
        for i, (block_name, duration) in enumerate(PROTOCOL_BLOCKS):
            print()
            is_closed = "closed" in block_name
            cue = "EYES CLOSED — let your eyes rest, breathe normally" if is_closed else "EYES OPEN — look at the screen, blink normally"
            print(f">>> BLOCK {i+1}/{len(PROTOCOL_BLOCKS)} — {cue} — {duration}s <<<")
            (beep_closed if is_closed else beep_open)()
            markers_outlet.push_sample([block_name])
            countdown(duration, block_name)

        markers_outlet.push_sample(["session_end"])
        beep_done()
        print("\n[experiment_1] protocol complete, stopping recorder...")

    finally:
        recorder.stop()

    print(f"\n[experiment_1] recording saved to {session_dir}")
    session_files = sorted(session_dir.iterdir())
    for f in session_files:
        print(f"  {f.name}")

    # Post-session ingest: populate Postgres Path B from the FIF + JSON files
    if not args.no_ingest:
        print("\n[experiment_1] running post-session ingest...")
        try:
            from post_session_ingest import ingest_session
            session_id = ingest_session(
                session_dir=session_dir,
                subject_id=args.subject,
                name=args.name,
                experiment_kind="E1",
                protocol_id=PROTOCOL_ID,
                capture_source="openmuse_direct",
                started_at_utc=started_utc,
                git_commit=git_commit_hash(),
            )
            print(f"[experiment_1] ingested as session {session_id}")
        except Exception as e:
            print(f"[experiment_1] WARNING: ingestion failed: {type(e).__name__}: {e}")
            print("[experiment_1] the raw files are still safe in the session dir; re-run post_session_ingest.py later")
            session_id = None
    else:
        print("\n[experiment_1] skipping Postgres ingestion (--no-ingest)")
        session_id = None

    # Post-session feature computation
    if not args.no_features:
        print("\n[experiment_1] running post-session feature computation...")
        try:
            from post_session_features import compute_features
            result = compute_features(session_dir=session_dir, session_id=session_id)
            if result and "alpha_enhancement" in result:
                print(f"\n{'='*72}")
                print(" RESULT")
                print(f"{'='*72}")
                ae = result["alpha_enhancement"]
                if ae.get("pooled_temporal") is not None:
                    ratio = ae["pooled_temporal"]
                    verdict = "STRONG" if ratio > 1.5 else ("MODERATE" if ratio > 1.2 else ("WEAK" if ratio > 1.0 else "NONE"))
                    print(f"  Pooled temporal alpha enhancement (closed/open) = {ratio:.2f}x  [{verdict}]")
                if ae.get("per_channel"):
                    print("  Per-channel:")
                    for ch, r in ae["per_channel"].items():
                        print(f"    {ch}: {r:.2f}x")
        except Exception as e:
            print(f"[experiment_1] WARNING: feature computation failed: {type(e).__name__}: {e}")
            print("[experiment_1] re-run post_session_features.py later against the session dir")
    else:
        print("\n[experiment_1] skipping feature computation (--no-features)")

    print(f"\n[experiment_1] done. Session at: {session_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
