"""Read the session transcript AFTER the PostgreSQL install to see
what password was actually set and verified.
"""
import json
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

path = r"C:\Users\JaieT\.claude\projects\C--DocumentsJaie-AI\202e414e-2fa5-43bc-8d43-e6b9cd2751be.jsonl"

turns = []
with open(path, "r", encoding="utf-8", errors="ignore") as f:
    for line_no, line in enumerate(f, 1):
        try:
            obj = json.loads(line)
            turns.append((line_no, obj))
        except json.JSONDecodeError:
            continue

# Extract text for each turn — same as before
def extract_text(obj):
    out_lines = []
    msg = obj.get("message", {})
    role = msg.get("role", obj.get("type", "?"))
    content = msg.get("content", obj.get("content", ""))

    if isinstance(content, str):
        out_lines.append(f"[{role}] {content}")
    elif isinstance(content, list):
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    out_lines.append(f"[{role}.text] {block.get('text', '')}")
                elif block.get("type") == "tool_use":
                    tool_name = block.get("name", "?")
                    tool_input = block.get("input", {})
                    cmd = tool_input.get("command", tool_input.get("file_path", json.dumps(tool_input)[:800]))
                    out_lines.append(f"[{role}.tool_use({tool_name})] {str(cmd)[:800]}")
                elif block.get("type") == "tool_result":
                    tc = block.get("content", "")
                    if isinstance(tc, list):
                        tc = " ".join(str(c.get("text", c)) if isinstance(c, dict) else str(c) for c in tc)
                    out_lines.append(f"[{role}.tool_result] {str(tc)[:800]}")
    return out_lines

# Start from turn 977 (the install completion notification) and walk forward
# looking for psql commands with passwords, PGPASSWORD usage, or ALTER USER commands
start = 977
end = min(len(turns), start + 80)
print(f"Reading turns {start} to {end} after install completion")

for i in range(start, end):
    ln, obj = turns[i]
    lines = extract_text(obj)
    if not lines:
        continue
    # Only print turns that mention postgres/psql/password/PGPASSWORD/resonance/ALTER/CREATE
    blob = "\n".join(lines)
    if any(kw in blob.lower() for kw in ("postgres", "psql", "password", "pgpassword", "resonance", "alter user", "create database", "create user", "create role")):
        print(f"\n--- turn {i} (line {ln}) ---")
        for line in lines:
            # Keep each line to 600 chars for readability
            print(f"  {line[:600]}")
