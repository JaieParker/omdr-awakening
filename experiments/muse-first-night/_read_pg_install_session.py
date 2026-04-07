"""Read the specific session transcript where Postgres 17 was installed
and extract all text around the install event. JSONL sessions have one
JSON object per line; each object is a turn in the conversation.
"""
import json
import re
import sys

# Force utf-8 output (the previous script crashed on a unicode arrow)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

path = r"C:\Users\JaieT\.claude\projects\C--DocumentsJaie-AI\202e414e-2fa5-43bc-8d43-e6b9cd2751be.jsonl"

print(f"Reading {path}")
turns = []
with open(path, "r", encoding="utf-8", errors="ignore") as f:
    for line_no, line in enumerate(f, 1):
        try:
            obj = json.loads(line)
            turns.append((line_no, obj))
        except json.JSONDecodeError:
            continue

print(f"Loaded {len(turns)} turns")

# Find the turn that contains 'winget install PostgreSQL'
install_turn_idx = None
for i, (ln, obj) in enumerate(turns):
    blob = json.dumps(obj)
    if "winget install PostgreSQL" in blob or "PostgreSQL.PostgreSQL.17" in blob:
        install_turn_idx = i
        print(f"\nFound install mention at turn index {i} (line {ln})")
        break

if install_turn_idx is None:
    print("Could not find install turn!")
    sys.exit(1)

# Show the install turn + a window of turns around it
window_radius = 15
start = max(0, install_turn_idx - window_radius)
end = min(len(turns), install_turn_idx + window_radius + 1)

def extract_text(obj):
    """Pull text content from a turn for human reading."""
    out_lines = []
    # Turn has 'message' which has 'role' and 'content'
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
                    cmd = tool_input.get("command", tool_input.get("file_path", json.dumps(tool_input)[:400]))
                    out_lines.append(f"[{role}.tool_use({tool_name})] {cmd[:500]}")
                elif block.get("type") == "tool_result":
                    tc = block.get("content", "")
                    if isinstance(tc, list):
                        tc = " ".join(str(c.get("text", c)) if isinstance(c, dict) else str(c) for c in tc)
                    out_lines.append(f"[{role}.tool_result] {str(tc)[:500]}")
    return out_lines

for i in range(start, end):
    ln, obj = turns[i]
    marker = " <<< INSTALL TURN" if i == install_turn_idx else ""
    print(f"\n--- turn {i} (line {ln}){marker} ---")
    for line in extract_text(obj):
        print(f"  {line}")
