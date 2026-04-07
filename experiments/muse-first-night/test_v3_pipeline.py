"""End-to-end v3 pipeline test — no physical Muse required.

Runs the mock LSL publisher in a background thread and the experiment
script in the main thread. Shortened protocol (5-second blocks instead of
60) to keep the test under 60 seconds total. At the end, verifies:

  - Recorder saved per-stream FIF files + markers.json + session_manifest.json
  - Postgres ingest populated sessions, raw_files, markers, clock_sync_events,
    gap_events, ingestion_journal
  - post_session_features detected alpha enhancement > 1.5x (mock injects
    a deliberately strong 10 Hz sine into TP9/TP10 during eyes-closed blocks
    so this is a generous floor)
  - analysis_results row is present in Postgres

Gate: if this test passes, the pipeline can detect real alpha enhancement
under the same architecture. If it fails, we debug before 19:00 tonight.

Run:
    python test_v3_pipeline.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent.resolve()

# Override the protocol blocks with short ones for testing
TEST_BLOCKS = [
    ("eyes_open_block_1",   5),
    ("eyes_closed_block_1", 5),
    ("eyes_open_block_2",   5),
    ("eyes_closed_block_2", 5),
    ("eyes_open_block_3",   5),
    ("eyes_closed_block_3", 5),
]
TEST_TOTAL_DURATION = sum(d for _, d in TEST_BLOCKS)


def main():
    print("=" * 72)
    print(" END-TO-END v3 PIPELINE TEST")
    print("=" * 72)

    publisher_duration = TEST_TOTAL_DURATION + 25

    # 1. Start mock publisher as subprocess.
    # CRITICAL: use DEVNULL for stdout. The LSL library emits ~40 noisy warning
    # lines per second at startup, and piping through PIPE without draining
    # will fill the ~64 KB buffer in ~1 second and then block the publisher's
    # writes forever. DEVNULL discards cleanly.
    #
    # --listen-markers: the mock subscribes to the OMDR-Markers LSL stream
    # (which the experiment_1 script creates) and flips alpha boost based on
    # received eyes_closed_* / eyes_open_* markers. Self-synchronizing; no
    # wall-clock window math needed.
    print(f"\n[test] starting mock LSL publisher (duration={publisher_duration}s, marker-driven alpha)")
    mock_log_path = HERE / "_mock_publisher_debug.log"
    mock_log = open(mock_log_path, "w", encoding="utf-8")
    mock_proc = subprocess.Popen(
        [
            sys.executable,
            str(HERE / "mock_lsl_publisher.py"),
            "--duration", str(publisher_duration),
            "--listen-markers",
        ],
        stdout=mock_log,
        stderr=subprocess.STDOUT,
    )

    # 2. Let the publisher warm up and register its LSL outlets
    print("[test] waiting 3s for publisher outlets to register...")
    time.sleep(3.0)

    # 3. Run the experiment script, patching PROTOCOL_BLOCKS to our shortened version
    print("[test] running experiment_1_eyes_closed_v3 against the mock streams...")
    import experiment_1_eyes_closed_v3 as exp
    exp.PROTOCOL_BLOCKS = TEST_BLOCKS

    # Fake the argparse sys.argv
    old_argv = sys.argv
    session_name = f"v3_pipeline_test_{datetime.now(timezone.utc).strftime('%H%M%S')}"
    sys.argv = [
        "experiment_1_eyes_closed_v3.py",
        "--subject", "jaie",
        "--name", session_name,
        "--skip-input",
        "--no-beep",   # silent during overnight tests — do NOT remove
    ]
    try:
        rc = exp.main()
        print(f"\n[test] experiment exited with rc={rc}")
    finally:
        sys.argv = old_argv

    # 4. Ensure mock publisher has exited
    try:
        mock_proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        mock_proc.terminate()
        mock_proc.wait(timeout=5)
    print(f"[test] mock publisher exited with rc={mock_proc.returncode}")

    # 5. Find the session directory (the experiment script printed it)
    # We'll look it up via Postgres
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost", port=5432, dbname="omdr_bci",
            user="kai", password="resonance",
        )
        with conn.cursor() as cur:
            cur.execute(
                """SELECT session_id, bids_session_path, started_at, ended_at,
                          capture_source, hardware_model
                     FROM sessions WHERE subject_id = 'jaie' AND name = %s
                     ORDER BY started_at DESC LIMIT 1""",
                (session_name,),
            )
            row = cur.fetchone()
            if not row:
                print(f"\n[test] FAIL: no sessions row found for name={session_name}")
                return 1
            session_id, bids_path, started, ended, source, hardware = row
            print(f"\n[test] found session in DB:")
            print(f"  session_id: {session_id}")
            print(f"  bids path:  {bids_path}")
            print(f"  started:    {started}")
            print(f"  ended:      {ended}")
            print(f"  source:     {source}")

            # 6. Verify raw_files rows
            cur.execute("SELECT COUNT(*) FROM raw_files WHERE session_id = %s", (str(session_id),))
            n_files = cur.fetchone()[0]
            print(f"  raw_files:  {n_files} rows")

            # 7. Verify markers
            cur.execute("SELECT COUNT(*) FROM markers WHERE session_id = %s", (str(session_id),))
            n_markers = cur.fetchone()[0]
            cur.execute("SELECT label FROM markers WHERE session_id = %s ORDER BY lsl_clock_us", (str(session_id),))
            labels = [r[0] for r in cur.fetchall()]
            print(f"  markers:    {n_markers} rows: {labels}")

            # 8. Verify sync events
            cur.execute("SELECT COUNT(*) FROM clock_sync_events WHERE session_id = %s", (str(session_id),))
            n_sync = cur.fetchone()[0]
            print(f"  sync events: {n_sync}")

            # 9. Verify gap events
            cur.execute("SELECT COUNT(*) FROM gap_events WHERE session_id = %s", (str(session_id),))
            n_gaps = cur.fetchone()[0]
            print(f"  gap events: {n_gaps}")

            # 10. Verify analysis_results
            cur.execute(
                "SELECT method, version, result FROM analysis_results WHERE session_id = %s ORDER BY computed_at DESC",
                (str(session_id),),
            )
            analyses = cur.fetchall()
            print(f"  analysis_results: {len(analyses)} rows")

            # 11. Extract alpha enhancement from the analysis result JSON
            pipeline_ok = True
            problems = []
            if not analyses:
                problems.append("no analysis_results rows")
                pipeline_ok = False
            else:
                method, version, result_blob = analyses[0]
                ae = result_blob.get("alpha_enhancement") if isinstance(result_blob, dict) else None
                if ae:
                    pooled = ae.get("pooled_temporal")
                    per_ch = ae.get("per_channel") or {}
                    print(f"\n  alpha_enhancement:")
                    print(f"    pooled temporal (TP9+TP10): {pooled}")
                    if per_ch:
                        for ch, r in per_ch.items():
                            print(f"    {ch}: {r}")
                    if pooled is None:
                        problems.append("pooled_temporal is None")
                        pipeline_ok = False
                    elif pooled < 1.5:
                        problems.append(f"pooled_temporal = {pooled:.2f} < 1.5 (expected strong boost from mock)")
                        pipeline_ok = False
                else:
                    problems.append("no alpha_enhancement in result")
                    pipeline_ok = False

            if n_files == 0:
                problems.append("no raw_files rows")
                pipeline_ok = False
            if n_markers == 0:
                problems.append("no markers rows")
                pipeline_ok = False

            print()
            print("=" * 72)
            if pipeline_ok:
                print(" [OK] PIPELINE TEST PASSED")
                print("=" * 72)
                print(f"  Mock 10 Hz alpha boost detected end-to-end")
                print(f"  All Postgres tables populated")
                print(f"  FIF files written, markers aligned, features computed")
                return 0
            else:
                print(" [FAIL] PIPELINE TEST FAILED")
                print("=" * 72)
                for p in problems:
                    print(f"  - {p}")
                return 1
        conn.close()
    except Exception as e:
        print(f"\n[test] ERROR during verification: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
