"""Load Windows User-scope env vars into os.environ.

Bash subprocesses on Windows don't inherit User-scope env vars by default,
so this helper reads them via PowerShell at startup. Import at the top of any
script that needs API access.

Usage:
    import _load_keys  # noqa: F401
"""
import os
import subprocess

KEYS = ("XAI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY")


def _load_one(name: str) -> str | None:
    if os.environ.get(name):
        return os.environ[name]
    try:
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-Command",
                f"[Environment]::GetEnvironmentVariable('{name}','User')",
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        value = (result.stdout or "").strip()
        if value:
            os.environ[name] = value
            return value
    except Exception:
        pass
    return None


_loaded = {k: bool(_load_one(k)) for k in KEYS}

if __name__ == "__main__":
    for k, ok in _loaded.items():
        print(f"  {k}: {'set' if ok else 'MISSING'}")
