"""End-to-end pipeline test with synthetic data — no Muse required.

Starts the OSC receiver in a session, launches mock_sender as a subprocess
that streams 60 seconds of synthetic EEG (eyes-open for 0-30s, eyes-closed
for 30-60s with boosted alpha), marks the transitions on the receiver, then
runs analyse_session and prints the alpha enhancement ratio.

PASS if pooled-temporal alpha enhancement > 1.5 (the canonical effect size).
This is the gate before tonight's real recording — if our pipeline can't
detect the synthetic effect, it can't detect the real one.

Usage:
    python test_pipeline.py
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

from session import Session
from analyse_session import analyse_session, write_summary

PORT = 5005   # use a non-default port to avoid clashing with anything else
DURATION = 60.0
CLOSED_START = 30.0
CLOSED_END = 60.0


def main():
    here = Path(__file__).parent
    print("=== test_pipeline ===")
    print(f"  port = {PORT}, duration = {DURATION}s, closed window = {CLOSED_START}-{CLOSED_END}s")

    with Session("test-pipeline", subject="mock", port=PORT, sessions_root=here / "sessions") as s:
        # Open the receiver, then launch the mock sender as a subprocess
        # so they run concurrently.
        time.sleep(0.5)
        s.mark("eyes_open_start")
        sender_cmd = [
            sys.executable,
            str(here / "mock_sender.py"),
            "--port", str(PORT),
            "--duration", str(DURATION),
            "--closed-start", str(CLOSED_START),
            "--closed-end", str(CLOSED_END),
        ]
        sender = subprocess.Popen(sender_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        print(f"  spawned mock_sender (PID {sender.pid})")

        # Mark the transition at the right time
        time.sleep(CLOSED_START)
        s.mark("eyes_closed_start")
        # Wait for sender to finish
        sender.wait(timeout=DURATION + 10)
        s.mark("session_end")
        print("  sender exited.")
        # Drain its output for visibility
        if sender.stdout is not None:
            for line in sender.stdout.readlines():
                print(f"   [sender] {line.rstrip()}")

        session_dir = s.session_dir

    # Now analyse
    print("\n=== analysis ===")
    analysis = analyse_session(session_dir)
    write_summary(session_dir, analysis)
    for n in analysis.notes:
        print(f"  {n}")

    ratio = analysis.alpha_enhancement_pooled_temporal
    if ratio is None:
        print("\nFAIL: alpha_enhancement_pooled_temporal is None — segmentation broke")
        sys.exit(2)
    print(f"\n  alpha enhancement (pooled temporal) = {ratio:.2f}x")
    if ratio > 1.5:
        print("  PASS — synthetic alpha boost detected end-to-end. Pipeline ready.")
        sys.exit(0)
    else:
        print(f"  FAIL — expected ratio > 1.5, got {ratio:.2f}.")
        print("  Investigate mock_sender, segmentation, or bandpower computation.")
        sys.exit(1)


if __name__ == "__main__":
    main()
