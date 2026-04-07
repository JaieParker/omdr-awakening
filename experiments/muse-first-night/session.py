"""Session manager — orchestrates a single recording session.

Wraps the OSC receiver, creates a timestamped session directory, writes a
metadata.json sidecar, and provides start/stop/mark API for experiment
scripts. Each experiment is one session.

Usage:
    from session import Session
    with Session("eyes-closed-baseline", subject="jaie", port=5000) as s:
        s.mark("start")
        # ... experiment ...
        s.mark("end")
    # On exit: stops receiver, writes metadata, returns session_dir
"""
from __future__ import annotations

import json
import platform
import socket
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from osc_receiver import OscReceiver

SESSIONS_ROOT = Path(__file__).parent / "sessions"


class Session:
    def __init__(
        self,
        name: str,
        subject: str = "unknown",
        port: int = 5000,
        host: str = "0.0.0.0",
        notes: str = "",
        sessions_root: Optional[Path] = None,
    ):
        self.name = name
        self.subject = subject
        self.port = port
        self.host = host
        self.notes = notes
        self.sessions_root = Path(sessions_root) if sessions_root else SESSIONS_ROOT

        self.start_time_utc: Optional[str] = None
        self.start_time_local: Optional[str] = None
        self.end_time_utc: Optional[str] = None
        self.session_dir: Optional[Path] = None
        self.receiver: Optional[OscReceiver] = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def start(self) -> "Session":
        now = datetime.now(timezone.utc)
        local = datetime.now()
        self.start_time_utc = now.isoformat()
        self.start_time_local = local.isoformat()
        timestamp = local.strftime("%Y%m%dT%H%M%S")
        self.session_dir = self.sessions_root / f"{timestamp}_{self.name}"
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.receiver = OscReceiver(session_dir=self.session_dir, port=self.port, host=self.host)
        self.receiver.start()
        # Write initial metadata immediately so the session is identifiable
        # even if the run crashes mid-recording.
        self._write_metadata(status="running")
        print(f"[session] {self.name} started, dir = {self.session_dir}")
        return self

    def stop(self) -> Path:
        if self.receiver is not None:
            self.receiver.stop()
        self.end_time_utc = datetime.now(timezone.utc).isoformat()
        self._write_metadata(status="completed")
        print(f"[session] {self.name} stopped, dir = {self.session_dir}")
        assert self.session_dir is not None
        return self.session_dir

    def mark(self, label: str) -> None:
        if self.receiver is not None:
            self.receiver.mark(label)

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------
    def __enter__(self) -> "Session":
        return self.start()

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------
    def _write_metadata(self, status: str) -> None:
        if self.session_dir is None:
            return
        markers = self.receiver.get_markers() if self.receiver else []
        meta = {
            "name": self.name,
            "subject": self.subject,
            "status": status,
            "start_time_utc": self.start_time_utc,
            "start_time_local": self.start_time_local,
            "end_time_utc": self.end_time_utc,
            "host": socket.gethostname(),
            "platform": platform.platform(),
            "port": self.port,
            "notes": self.notes,
            "markers": [{"time_utc": ts_to_utc(t), "wall_time": t, "label": label} for t, label in markers],
            "sample_counts": dict(self.receiver._sample_counts) if self.receiver else {},
        }
        with open(self.session_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)


def ts_to_utc(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()
