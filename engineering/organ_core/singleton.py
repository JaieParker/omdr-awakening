"""Singleton guard for MCP organ servers.

Each organ writes a PID lockfile on startup. If a previous instance is
still running, it gets killed first. This prevents zombie processes from
accumulating across Claude Code sessions and hogging hardware (camera, mic).

Usage in any MCP server:
    from organ_core.singleton import claim_singleton
    claim_singleton("eye")  # call before mcp.run()
"""
import os
import sys
import signal
import atexit

_LOCK_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".locks")


def claim_singleton(organ_name: str) -> None:
    """Claim singleton ownership for this organ. Kills any previous holder."""
    os.makedirs(_LOCK_DIR, exist_ok=True)
    lockfile = os.path.join(_LOCK_DIR, f"{organ_name}.pid")

    # Kill previous instance if it exists
    if os.path.exists(lockfile):
        try:
            old_pid = int(open(lockfile).read().strip())
            if old_pid != os.getpid() and _is_running(old_pid):
                _kill_process(old_pid)
        except (ValueError, OSError):
            pass  # Corrupt lockfile, just overwrite

    # Write our PID
    with open(lockfile, "w") as f:
        f.write(str(os.getpid()))

    # Clean up on exit
    atexit.register(_cleanup, lockfile)


def _is_running(pid: int) -> bool:
    """Check if a process with this PID exists."""
    if sys.platform == "win32":
        import ctypes
        kernel32 = ctypes.windll.kernel32
        SYNCHRONIZE = 0x00100000
        handle = kernel32.OpenProcess(SYNCHRONIZE, False, pid)
        if handle:
            kernel32.CloseHandle(handle)
            return True
        return False
    else:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False


def _kill_process(pid: int) -> None:
    """Kill a process by PID."""
    if sys.platform == "win32":
        import subprocess
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/F"],
            capture_output=True,
        )
    else:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass


def _cleanup(lockfile: str) -> None:
    """Remove lockfile on exit."""
    try:
        # Only remove if it's still our PID
        if os.path.exists(lockfile):
            pid = int(open(lockfile).read().strip())
            if pid == os.getpid():
                os.remove(lockfile)
    except (ValueError, OSError):
        pass
