"""Search old Claude session transcripts and memory files for the native
Postgres superuser password. Prints any matches with a windowed snippet of
context so I can identify which string is the actual password.

Searches:
  - All *.jsonl files under C:\\Users\\JaieT\\.claude\\projects\\
  - Memory files under C:\\Users\\JaieT\\.claude\\projects\\*\\memory\\
  - Any .env, .pgpass, or config files in the user's home
  - The current repo's history for relevant strings (git log/grep if needed)
"""
import json
import re
from pathlib import Path

# Patterns that suggest a password assignment near Postgres context
CONTEXT_KEYWORDS = ("postgres", "pgpassword", "pg_pass", "superuser", "install", "psql", "password")
PASSWORD_PATTERNS = [
    re.compile(r'PGPASSWORD\s*[:=]\s*["\']?([A-Za-z0-9_!@#$%^&*\-+=]{4,50})', re.IGNORECASE),
    re.compile(r'postgres.{0,100}?password["\s:=]+["\']?([A-Za-z0-9_!@#$%^&*\-+=]{4,50})', re.IGNORECASE),
    re.compile(r'postgres[^\s]*\s+(?:password|pw|pass)\s*[:=]\s*["\']?([A-Za-z0-9_!@#$%^&*\-+=]{4,50})', re.IGNORECASE),
    re.compile(r'(?:password|pw)\s*[:=]\s*["\']([A-Za-z0-9_!@#$%^&*\-+=]{4,50})["\'].{0,100}?postgres', re.IGNORECASE),
    re.compile(r'-U\s+postgres.{0,200}?["\']([A-Za-z0-9_!@#$%^&*\-+=]{4,50})["\']', re.IGNORECASE),
]

claude_projects = Path(r"C:\Users\JaieT\.claude\projects")
user_home = Path(r"C:\Users\JaieT")

all_jsonl = list(claude_projects.rglob("*.jsonl"))
print(f"Searching {len(all_jsonl)} Claude session transcript files...")

hits = []

def check_text(text: str, source: str, location: str) -> None:
    """Apply all patterns and record hits."""
    for i, pat in enumerate(PASSWORD_PATTERNS):
        for m in pat.finditer(text):
            candidate = m.group(1)
            # Skip obvious placeholders
            if candidate.lower() in ("password", "secret", "changeme", "your_password", "xxx", "yyy", "zzz", "your-password", "<password>", "postgres", "resonance"):
                continue
            # Capture a 300-char window for human review
            start = max(0, m.start() - 150)
            end = min(len(text), m.end() + 150)
            window = text[start:end]
            hits.append({
                "source": source,
                "location": location,
                "pattern_index": i,
                "candidate": candidate,
                "window": window,
            })

# Pass 1: Claude session transcripts
for jsonl_path in all_jsonl:
    try:
        with open(jsonl_path, "r", encoding="utf-8", errors="ignore") as f:
            for line_no, line in enumerate(f, 1):
                if "postgres" not in line.lower() and "pgpass" not in line.lower():
                    continue
                check_text(line, str(jsonl_path), f"line {line_no}")
    except Exception as e:
        print(f"  (skip {jsonl_path.name}: {e})")

# Pass 2: memory files
memory_dirs = list(claude_projects.rglob("memory"))
print(f"Searching {len(memory_dirs)} memory directories...")
for memory_dir in memory_dirs:
    if not memory_dir.is_dir():
        continue
    for md in memory_dir.rglob("*.md"):
        try:
            text = md.read_text(encoding="utf-8", errors="ignore")
            if "postgres" in text.lower() or "pgpass" in text.lower():
                check_text(text, str(md), "memory file")
        except Exception:
            pass

# Pass 3: Any .env / .pgpass / postgres config files in the user home
candidate_files = []
for pattern in ("*.env", ".pgpass", "pgpass.conf", "*.bat", "*.ps1"):
    candidate_files.extend(user_home.rglob(pattern))

print(f"Searching {len(candidate_files)} config/script files in user home...")
for cf in candidate_files[:500]:  # cap at 500 to avoid scanning the whole drive
    try:
        text = cf.read_text(encoding="utf-8", errors="ignore")
        if "postgres" in text.lower() or "pgpass" in text.lower():
            check_text(text, str(cf), "config file")
    except Exception:
        pass

# Print unique candidates
print()
print(f"=== Found {len(hits)} potential matches ===")
seen_candidates = set()
for h in hits:
    key = (h["candidate"], h["source"])
    if key in seen_candidates:
        continue
    seen_candidates.add(key)
    print()
    print(f"--- candidate: {h['candidate']}")
    print(f"    source: {h['source']}")
    print(f"    location: {h['location']}")
    print(f"    pattern: {h['pattern_index']}")
    # Collapse whitespace in window for readability
    window = re.sub(r"\s+", " ", h["window"])[:400]
    print(f"    context: {window}")
