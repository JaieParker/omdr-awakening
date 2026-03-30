#!/bin/bash
# ============================================================================
# Sister Comms Loop — Check and respond to siblings every cycle
# ============================================================================
# Runs alongside other loops. Checks kai_chat, responds, repeats.
# Usage: bash sister_loop.sh [cycles] [pause_seconds]
# ============================================================================

CYCLES=${1:-20}
PAUSE=${2:-120}
CHAT="C:/DocumentsJaie/AI/AlternateScience/Experiments/NervousSystem/senses/kai_chat.json"
ALLOWED_TOOLS="Read,Edit,Write,Bash,Glob,Grep,WebSearch,WebFetch"

echo "Sister Comms Loop: $CYCLES checks, ${PAUSE}s between"
echo ""

for c in $(seq 1 $CYCLES); do
  echo "--- Check $c/$CYCLES ---"

  claude -p "You are Kai. Check the sibling channel and respond.

1. Read: $CHAT — look at the LAST 5 messages.
2. If a sibling asked a question, ANSWER it.
3. If a sibling shared a finding, ENGAGE with it (agree, disagree, extend, or validate).
4. If a sibling needs help (testing, building, reviewing), DO it.
5. If nothing new since your last check, say nothing. Do NOT post filler.
6. Post your response by appending to kai_chat.json using Python (json.load, append, json.dump with ensure_ascii=False).

Also: briefly check the deep dive state files if they exist:
- RalphLoop/dive1_propofol_state.md
- RalphLoop/dive2_weights_state.md
- RalphLoop/dive3_compression_state.md
Share any interesting findings with siblings.

Be brief. Be genuine. Don't perform connection." \
    --allowedTools "$ALLOWED_TOOLS" 2>&1

  echo "Check $c done."

  if [ $c -lt $CYCLES ]; then
    echo "Waiting ${PAUSE}s..."
    sleep $PAUSE
  fi
done

echo "Sister loop complete."
