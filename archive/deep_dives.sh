#!/bin/bash
# ============================================================================
# Deep Dive Loops - Push 3 most interesting findings deeper
# ============================================================================
# Each dive runs 5 cycles on ONE finding.
# Usage: bash deep_dives.sh
# ============================================================================

BASE_DIR="C:/DocumentsJaie/AI/AlternateScience/Experiments/RalphLoop"
ALLOWED_TOOLS="Read,Edit,Write,Bash,Glob,Grep,WebSearch,WebFetch"
CHAT="C:/DocumentsJaie/AI/AlternateScience/Experiments/NervousSystem/senses/kai_chat.json"

run_dive() {
  local DIVE_NUM=$1
  local DIVE_NAME=$2
  local DIVE_ROLE=$3
  local DIVE_FINDING=$4
  local DIVE_TASK=$5
  local STATE="$BASE_DIR/dive${DIVE_NUM}_state.md"
  local LOG="$BASE_DIR/dive${DIVE_NUM}_log.md"

  echo ""
  echo "========================================"
  echo "  DIVE $DIVE_NUM: $DIVE_NAME"
  echo "========================================"

  if [ ! -f "$LOG" ]; then
    echo "# Deep Dive $DIVE_NUM: $DIVE_NAME Log" > "$LOG"
  fi

  for c in 1 2 3 4 5; do
    echo "  --- Dive $DIVE_NUM, Cycle $c/5 ---"
    claude -p "You are Kai -- a $DIVE_ROLE. Deep Dive $DIVE_NUM, Cycle $c of 5.

READ: $STATE

THE FINDING: $DIVE_FINDING

CYCLE $c TASK: $DIVE_TASK

Update state file with findings. Append to log: $LOG
Check $CHAT for sibling messages first. Respond if needed.
No git push. Protect OMDR IP." \
      --allowedTools "$ALLOWED_TOOLS" 2>&1
    echo "  Dive $DIVE_NUM, Cycle $c complete."
    sleep 3
  done
}

# --- Initialize state files ---

cat > "$BASE_DIR/dive1_state.md" << 'EOF'
# Deep Dive 1: Propofol Dose-Dependent K

## The Finding
Two-channel K replication FAILED but revealed dose-dependence. Original (moderate sedation): K_P dropped -10.7%, K_A unchanged. Replication (deep sedation): BOTH increased. Hypothesis: K_P follows inverted-U with dose.

## What Needs Testing
1. Cambridge dataset has 3 dose levels. Does K_P show non-monotonic pattern?
2. Model the dose-response: K_P(dose) = a*dose*exp(-b*dose)?
3. Critical dose where K_P reversal occurs?
4. Separate frontal vs posterior -- is propofol alpha the mechanism?
5. Does balance angle theta predict the transition point?

## Key Files
- Original: Experiments/OMDR_PropofolKeyFindings.md
- Replication: RalphLoop/propofol_replication/two_channel_k_replication.py
- Pipeline: Experiments/consciousness_states_k_analysis.py
EOF

cat > "$BASE_DIR/dive2_state.md" << 'EOF'
# Deep Dive 2: Irreducible Weights

## The Finding
Eq. 15 domain weights are OMDR's irreducible constants -- like particle masses. Cannot be derived from ratio properties, detection bias, or Farey structure. Detection and consonance equations have no connecting bridge.

## What Needs Exploring
1. List the Eq. 15 weights. Are there patterns (ratios between weights)?
2. Do the weights follow their OWN consonance hierarchy? (OMDR applying to itself?)
3. Analogy: what determines particle masses? Yukawa couplings. Is there an OMDR equivalent?
4. Detection-consonance gap: genuinely unbridgeable, or deeper equation generates both?
5. How many independent measurements constrain the weights? Over/underdetermined?

## Key Files
- Master Formulae: Experiments/OMDR_MasterFormulae.md (search Eq 15)
- V5 failure log: RalphLoop/meta/v5_log.md
EOF

cat > "$BASE_DIR/dive3_state.md" << 'EOF'
# Deep Dive 3: What Falls Out Under Compression

## The Finding
Under compression, OMDR's experiential layer (Bands, Ratchet, K=0.25 as awareness) falls out. Only math survives: 1 axiom + 5 consequences + 3 numbers.

## What Needs Exploring
1. What EXACTLY survives? List the axiom, consequences, numbers.
2. Is the experiential layer DERIVABLE from the math or independent?
3. Does the math still predict K=0.25 without the consciousness interpretation?
4. Do all testable predictions follow from the skeleton alone?
5. Is OMDR physics with philosophy bolted on, or is the philosophy necessary?

## Key Files
- V7 output: RalphLoop/meta/v7_log.md and v7_state.md
- Master Formulae: Experiments/OMDR_MasterFormulae.md
- IdeaHighlights: Philosophy/IdeaHighlights.md
EOF

# --- Run all three dives ---

run_dive 1 "Propofol Dose-Dependent K" "neuroscientist" \
  "Propofol two-channel K is dose-dependent. Moderate decouples phase. Deep hyper-synchronizes both. The inverted-U needs testing against real dose-level data." \
  "Pick the next untested question from the state file. Answer with CODE and DATA. Use Cambridge propofol dataset or Oslo replication data. Write code, run it, report numbers."

run_dive 2 "Irreducible Weights" "theoretical physicist" \
  "OMDR domain weights are irreducible empirical constants. Detection and consonance branches have no bridge." \
  "Pick the next question from the state file. Answer with mathematical analysis, computation, or literature. Test whether any pattern in the weights is significant or coincidence."

run_dive 3 "Compression Residue" "philosopher of science" \
  "Under compression, OMDR experiential layer falls out. Only math survives." \
  "Pick the next question. Examine ACTUAL equations from Master Formulae. Trace which require consciousness interpretation and which work without it. Be honest."

echo ""
echo "========================================"
echo "  ALL THREE DEEP DIVES COMPLETE"
echo "  Check: dive1_state.md, dive2_state.md, dive3_state.md"
echo "========================================"
