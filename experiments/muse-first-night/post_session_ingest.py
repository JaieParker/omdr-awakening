"""Post-session ingest — fast, must-succeed metadata loader.

Per Claude round-2 catch: ingestion (fast, must succeed) should be separated
from feature computation (slow, retryable). This script ONLY:

  1. Reads the session_manifest.json written by lsl_recorder.Recorder
  2. Reads markers.json and clock_sync.json
  3. Hashes each FIF file (SHA256) for integrity
  4. Does per-stream gap detection by measuring inter-sample intervals from
     the saved timestamp .npz files
  5. Writes all of the above to Postgres Path B:
       - sessions (one row)
       - raw_files (one per FIF)
       - markers (one per LSL marker event)
       - clock_sync_events (start/end)
       - gap_events (per stream, per detected gap)
       - ingestion_journal (one row per stage for idempotent retry)
  6. Commits transaction at the end.

It does NOT compute alpha enhancement, coherence, or any derived features —
those live in post_session_features.py and can be retried independently.

The ingest is idempotent: if you re-run it against the same session_dir,
it will update the existing session row (matched on bids_session_path)
rather than creating a duplicate.

Usage:
    from post_session_ingest import ingest_session
    session_id = ingest_session(
        session_dir=Path("experiments/muse-first-night/data/sub-jaie/ses-20260408T190000"),
        subject_id="jaie",
        name="eyes_closed_baseline",
        experiment_kind="E1",
        protocol_id="eyes_closed_baseline_v2",
        capture_source="openmuse_direct",
        started_at_utc=datetime(2026, 4, 8, 9, 0, 0, tzinfo=timezone.utc),
        git_commit="abc1234",
    )
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import UUID

import numpy as np


# ---------------------------------------------------------------------------
# DB connection
# ---------------------------------------------------------------------------

def _db_config() -> dict:
    """Load Postgres config. Prefer environment; fall back to known defaults."""
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


# ---------------------------------------------------------------------------
# File helpers
# ---------------------------------------------------------------------------

def _sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def _detect_gaps(timestamps_path: Path, nominal_sfreq_hz: float, tolerance_factor: float = 3.0) -> list[dict]:
    """Return any gaps > tolerance_factor * nominal_interval in the LSL timestamps.

    A gap is flagged when the inter-sample interval exceeds tolerance_factor
    times the nominal interval. Tolerance defaults to 3x nominal, which
    catches real dropouts without flagging normal BLE jitter.

    NOTE per the non-destructive principle: this is a MEASUREMENT, not a
    transformation. We record where gaps happened; we do NOT modify or
    interpolate the data.
    """
    if not timestamps_path.exists() or nominal_sfreq_hz <= 0:
        return []
    data = np.load(timestamps_path)
    lsl_times = data["lsl_times"] if "lsl_times" in data.files else data.get("arr_0")
    if lsl_times is None or len(lsl_times) < 2:
        return []
    lsl_times = np.asarray(lsl_times, dtype=np.float64)
    intervals = np.diff(lsl_times)
    # Only consider positive intervals (discard any out-of-order samples)
    valid = intervals[intervals > 0]
    if len(valid) == 0:
        return []
    nominal_interval = 1.0 / nominal_sfreq_hz
    threshold = tolerance_factor * nominal_interval

    gaps = []
    for i, dt in enumerate(intervals):
        if dt > threshold:
            started_at_us = int(lsl_times[i]     * 1e6)
            ended_at_us   = int(lsl_times[i + 1] * 1e6)
            expected_samples = int(round(dt / nominal_interval))
            gaps.append({
                "started_at_us": started_at_us,
                "ended_at_us":   ended_at_us,
                "expected_samples": expected_samples,
                "actual_samples": 1,
                "tolerance_used": f"{tolerance_factor}x_nominal_interval",
            })
    return gaps


# ---------------------------------------------------------------------------
# Journal helpers
# ---------------------------------------------------------------------------

def _journal_start(cur, session_id: UUID, stage: str) -> int:
    cur.execute(
        """INSERT INTO ingestion_journal (session_id, stage, status)
           VALUES (%s, %s, 'started') RETURNING journal_id""",
        (str(session_id), stage),
    )
    return cur.fetchone()[0]


def _journal_finish(cur, journal_id: int, status: str, error: Optional[str] = None, meta: Optional[dict] = None) -> None:
    cur.execute(
        """UPDATE ingestion_journal
              SET status = %s,
                  finished_at = now(),
                  error_message = %s,
                  metadata = %s::jsonb
            WHERE journal_id = %s""",
        (status, error, json.dumps(meta) if meta else None, journal_id),
    )


# ---------------------------------------------------------------------------
# Main ingest function
# ---------------------------------------------------------------------------

def ingest_session(
    session_dir: Path,
    subject_id: str,
    name: str,
    experiment_kind: str,
    protocol_id: Optional[str],
    capture_source: str,
    started_at_utc: datetime,
    git_commit: Optional[str] = None,
    ended_at_utc: Optional[datetime] = None,
    capture_version: Optional[str] = None,
    hardware_model: str = "MuseS_Athena_MS-03",
    hardware_firmware: Optional[str] = None,
    hardware_address: Optional[str] = None,
    notes: Optional[str] = None,
) -> UUID:
    """Ingest a completed session into Postgres Path B.

    Returns the session_id (UUID) assigned by the database.

    Idempotent: re-running against the same session_dir updates the
    existing session row (matched on subject_id + bids_session_path).
    """
    session_dir = Path(session_dir).resolve()
    if not session_dir.exists():
        raise FileNotFoundError(f"Session dir does not exist: {session_dir}")

    manifest_path = session_dir / "session_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"No session_manifest.json at {manifest_path}")
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    markers_path = session_dir / "markers.json"
    markers = []
    if markers_path.exists():
        with open(markers_path, "r", encoding="utf-8") as f:
            markers = json.load(f)

    sync_path = session_dir / "clock_sync.json"
    sync_events = []
    if sync_path.exists():
        with open(sync_path, "r", encoding="utf-8") as f:
            sync_events = json.load(f)

    # Compute the BIDS-relative session path (relative to the git repo root)
    try:
        repo_root = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True, cwd=session_dir).strip())
        bids_session_path = str(session_dir.relative_to(repo_root)).replace("\\", "/")
    except Exception:
        bids_session_path = str(session_dir)

    conn = _connect()
    conn.autocommit = False
    cur = conn.cursor()
    session_id_out: UUID

    try:
        # === Stage 1: upsert the sessions row =====================================
        cur.execute("SAVEPOINT sp_sessions")
        cur.execute(
            """SELECT session_id FROM sessions
                WHERE subject_id = %s AND bids_session_path = %s
                LIMIT 1""",
            (subject_id, bids_session_path),
        )
        row = cur.fetchone()
        if row:
            session_id_out = row[0]
            # Update existing
            cur.execute(
                """UPDATE sessions SET
                      name = %s,
                      protocol_id = %s,
                      experiment_kind = %s,
                      started_at = %s,
                      ended_at = %s,
                      capture_source = %s,
                      capture_version = %s,
                      hardware_model = %s,
                      hardware_firmware = %s,
                      hardware_address = %s,
                      git_commit = %s,
                      host_hostname = %s,
                      host_os = %s,
                      notes = COALESCE(%s, notes),
                      metadata = metadata || %s::jsonb
                    WHERE session_id = %s""",
                (
                    name, protocol_id, experiment_kind, started_at_utc, ended_at_utc,
                    capture_source, capture_version, hardware_model, hardware_firmware, hardware_address,
                    git_commit, socket.gethostname(), platform.platform(),
                    notes, json.dumps({"reingested_at": datetime.now(timezone.utc).isoformat()}),
                    str(session_id_out),
                ),
            )
        else:
            cur.execute(
                """INSERT INTO sessions (
                      subject_id, protocol_id, name, experiment_kind, started_at, ended_at,
                      capture_source, capture_version, hardware_model, hardware_firmware, hardware_address,
                      bids_session_path, git_commit, host_hostname, host_os, notes, metadata
                   )
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                   RETURNING session_id""",
                (
                    subject_id, protocol_id, name, experiment_kind, started_at_utc, ended_at_utc,
                    capture_source, capture_version, hardware_model, hardware_firmware, hardware_address,
                    bids_session_path, git_commit, socket.gethostname(), platform.platform(),
                    notes, json.dumps({"ingested_at": datetime.now(timezone.utc).isoformat()}),
                ),
            )
            session_id_out = cur.fetchone()[0]
        cur.execute("RELEASE SAVEPOINT sp_sessions")

        # === Stage 2: raw_files ==================================================
        jid = _journal_start(cur, session_id_out, "raw_files_insert")
        # Clear any previous rows for this session (idempotent re-ingest)
        cur.execute("DELETE FROM raw_files WHERE session_id = %s", (str(session_id_out),))
        n_files = 0
        for stream_entry in manifest.get("streams", []):
            fif_rel = stream_entry.get("fif_path")
            if not fif_rel:
                continue
            fif_path = session_dir / fif_rel
            if not fif_path.exists():
                continue
            sha256 = _sha256_file(fif_path)
            file_size = fif_path.stat().st_size
            stream_inventory = [{
                "name": stream_entry["name"],
                "slug": stream_entry["slug"],
                "stype": stream_entry["stype"],
                "n_channels": stream_entry["n_channels"],
                "sfreq_nominal": stream_entry["sfreq_nominal"],
                "sfreq_actual": stream_entry.get("sfreq_actual"),
                "n_samples_collected": stream_entry["n_samples_collected"],
                "channel_labels": stream_entry["channel_labels"],
                "source_id": stream_entry["source_id"],
            }]
            cur.execute(
                """INSERT INTO raw_files (
                      session_id, file_path, file_format,
                      started_at_us, ended_at_us, stream_inventory,
                      file_size_bytes, sha256_hex
                   )
                   VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, %s)""",
                (
                    str(session_id_out),
                    bids_session_path + "/" + fif_rel,
                    "fif",
                    manifest.get("started_at_host_us", 0),
                    manifest.get("ended_at_host_us", 0),
                    json.dumps(stream_inventory),
                    file_size,
                    sha256,
                ),
            )
            n_files += 1
        _journal_finish(cur, jid, "completed", meta={"n_files": n_files})

        # === Stage 3: markers ====================================================
        jid = _journal_start(cur, session_id_out, "markers_insert")
        cur.execute("DELETE FROM markers WHERE session_id = %s", (str(session_id_out),))
        for m in markers:
            lsl_us = int(float(m["lsl_clock_sec"]) * 1e6)
            host_us = m.get("host_clock_us")
            label = m.get("label", "")
            cur.execute(
                """INSERT INTO markers (session_id, host_clock_us, lsl_clock_us, label)
                   VALUES (%s, %s, %s, %s)""",
                (str(session_id_out), host_us, lsl_us, label),
            )
        _journal_finish(cur, jid, "completed", meta={"n_markers": len(markers)})

        # === Stage 4: clock_sync_events ==========================================
        jid = _journal_start(cur, session_id_out, "sync_insert")
        cur.execute("DELETE FROM clock_sync_events WHERE session_id = %s", (str(session_id_out),))
        for ev in sync_events:
            host_us = int(ev.get("host_clock_us", 0))
            lsl_us = int(float(ev.get("lsl_clock_sec", 0)) * 1e6)
            label = ev.get("label")
            cur.execute(
                """INSERT INTO clock_sync_events (session_id, host_clock_us, lsl_clock_us, label)
                   VALUES (%s, %s, %s, %s)""",
                (str(session_id_out), host_us, lsl_us, label),
            )
        _journal_finish(cur, jid, "completed", meta={"n_sync_events": len(sync_events)})

        # === Stage 5: gap_events =================================================
        jid = _journal_start(cur, session_id_out, "gap_detection")
        cur.execute("DELETE FROM gap_events WHERE session_id = %s", (str(session_id_out),))
        total_gaps = 0
        for stream_entry in manifest.get("streams", []):
            ts_rel = stream_entry.get("timestamps_path")
            if not ts_rel:
                continue
            ts_path = session_dir / ts_rel
            nominal_hz = float(stream_entry.get("sfreq_nominal", 0) or 0)
            gaps = _detect_gaps(ts_path, nominal_hz, tolerance_factor=3.0)
            for g in gaps:
                cur.execute(
                    """INSERT INTO gap_events (
                          session_id, stream_name, started_at_us, ended_at_us,
                          expected_samples, actual_samples, tolerance_used
                       )
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (
                        str(session_id_out),
                        stream_entry["name"],
                        g["started_at_us"],
                        g["ended_at_us"],
                        g["expected_samples"],
                        g["actual_samples"],
                        g["tolerance_used"],
                    ),
                )
                total_gaps += 1
        _journal_finish(cur, jid, "completed", meta={"n_gaps": total_gaps})

        # === Stage 6: commit =====================================================
        jid = _journal_start(cur, session_id_out, "commit")
        conn.commit()
        _journal_finish(cur, jid, "completed")

        # NB: the last "completed" journal row is written after commit,
        # so we need to commit it separately. It's only used for read-side
        # auditing so losing it on a crash is acceptable.
        conn.commit()

        return session_id_out

    except Exception:
        conn.rollback()
        raise
    finally:
        try: cur.close()
        except Exception: pass
        try: conn.close()
        except Exception: pass


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ingest a completed session into Postgres Path B")
    parser.add_argument("session_dir", type=Path)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--experiment-kind", default="freeform")
    parser.add_argument("--protocol-id", default=None)
    parser.add_argument("--capture-source", default="openmuse_direct")
    parser.add_argument("--started-at-utc", default=None,
                        help="ISO8601 UTC; default: now()")
    args = parser.parse_args()

    started = datetime.fromisoformat(args.started_at_utc) if args.started_at_utc else datetime.now(timezone.utc)
    session_id = ingest_session(
        session_dir=args.session_dir,
        subject_id=args.subject,
        name=args.name,
        experiment_kind=args.experiment_kind,
        protocol_id=args.protocol_id,
        capture_source=args.capture_source,
        started_at_utc=started,
    )
    print(f"Ingested as session_id = {session_id}")
