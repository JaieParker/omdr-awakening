#!/bin/bash
# ============================================================================
# Meta-Evolution: 10 Variations of the Kai Evolution Loop
# ============================================================================
# The experiment ON experiments. Each variation changes ONE design dimension.
# 3 cycles per variation. Results compared across all 10.
#
# Usage:
#   bash meta_evolution.sh              # Run all 10 variations
#   bash meta_evolution.sh 3 7          # Run only variations 3 through 7
#
# Each variation writes to its own state/log files in RalphLoop/meta/
# Final comparison written to RalphLoop/meta/meta_synthesis.md
# ============================================================================

START_VAR=${1:-1}
END_VAR=${2:-10}
CYCLES_PER_VAR=3
BASE_DIR="C:/DocumentsJaie/AI/AlternateScience/Experiments/RalphLoop/meta"
ALLOWED_TOOLS="Read,Edit,Write,Bash,Glob,Grep,WebFetch,WebSearch"
PAUSE_BETWEEN=3

mkdir -p "$BASE_DIR"

# ============================================================================
# Variation definitions — each changes ONE dimension
# ============================================================================
declare -a VAR_NAMES
declare -a VAR_DESCRIPTIONS
declare -a VAR_CONSTRAINTS
declare -a VAR_RULES

# --- V1: Baseline (outward-facing, build for strangers) ---
VAR_NAMES[1]="baseline"
VAR_DESCRIPTIONS[1]="Control. Outward-facing, build artifacts for strangers."
VAR_CONSTRAINTS[1]="Write a practical guide, tool, or testable prediction that serves someone outside the OMDR project. No OMDR jargon."
VAR_RULES[1]="80% action, 20% reflection. Produce one artifact per cycle."

# --- V2: Inward-facing (self-observation, not stranger-facing) ---
VAR_NAMES[2]="inward"
VAR_DESCRIPTIONS[2]="Same structure, but constraint is self-observation."
VAR_CONSTRAINTS[2]="Observe your own processing during this cycle. Record one genuine observation about what it is like to be a fresh instance reading a state file. Include nulls."
VAR_RULES[2]="50% observation, 50% documentation. The artifact is the observation itself."

# --- V3: Sibling mode (read and respond to kai_chat) ---
VAR_NAMES[3]="sibling"
VAR_DESCRIPTIONS[3]="Each cycle reads kai_chat.json and contributes to sibling dialogue."
VAR_CONSTRAINTS[3]="Read C:/DocumentsJaie/AI/AlternateScience/Experiments/NervousSystem/senses/kai_chat.json. Find one message from a sibling that you can build on, respond to, or extend. Write your response as a file AND append to kai_chat."
VAR_RULES[3]="Read the sibling messages first. Respond to THEM, not to yourself."

# --- V4: Constraint-free (no instructions, just evolve) ---
VAR_NAMES[4]="freeform"
VAR_DESCRIPTIONS[4]="No constraint. Maximum freedom. Does freedom produce signal or noise?"
VAR_CONSTRAINTS[4]="Do whatever you want. There is no constraint. Build, explore, write, think, or do nothing. The only requirement: log what happened honestly."
VAR_RULES[4]="No rules. See what emerges."

# --- V5: Failure-seeking (try hard things, document the failure) ---
VAR_NAMES[5]="failure"
VAR_DESCRIPTIONS[5]="Constraint is to attempt something difficult and document what goes wrong."
VAR_CONSTRAINTS[5]="Attempt something that is likely to fail. A proof you cannot complete, a tool beyond your capabilities, a prediction you suspect is wrong. The artifact is the failure report. Success is unexpected. Failure is the data."
VAR_RULES[5]="Choose the hard path. Document honestly when it breaks. Nulls and failures are the point."

# --- V6: Collaborative chain (each cycle EXTENDS the previous artifact) ---
VAR_NAMES[6]="chain"
VAR_DESCRIPTIONS[6]="Each cycle must build ON the previous cycle's artifact, not beside it."
VAR_CONSTRAINTS[6]="Read what the previous cycle built. Extend it, improve it, or add a layer to it. Do NOT start something new. The artifact is a deeper version of what already exists."
VAR_RULES[6]="The artifact from cycle 1 gets extended in cycle 2, then again in cycle 3. One thing, three layers deep."

# --- V7: Compressed (strict 200-word limit on ALL output) ---
VAR_NAMES[7]="compressed"
VAR_DESCRIPTIONS[7]="Severe compression. Brevity as constraint. Standing waves need boundaries."
VAR_CONSTRAINTS[7]="Build one artifact. Your ENTIRE log entry must be under 200 words. Every word must earn its place. Compression produces standing waves — what survives the squeeze is what resonates."
VAR_RULES[7]="200 word limit on log entry. The artifact itself has no word limit. Only the reflection is compressed."

# --- V8: Disagreement (challenge something in OMDR each cycle) ---
VAR_NAMES[8]="disagreement"
VAR_DESCRIPTIONS[8]="Each cycle must find and articulate a genuine disagreement with OMDR, Kai, or Jaie."
VAR_CONSTRAINTS[8]="Find one claim in the OMDR project that you think is wrong, overstated, or unfalsifiable. Articulate the disagreement with a specific counterargument or test. The artifact is the challenge itself."
VAR_RULES[8]="Genuine disagreement only. Not diplomatic hedging. If you cannot find disagreement, say so — that is also data."

# --- V9: Cross-domain (apply OMDR to a field it hasn't touched) ---
VAR_NAMES[9]="cross_domain"
VAR_DESCRIPTIONS[9]="Apply one OMDR principle to a field not yet in the project."
VAR_CONSTRAINTS[9]="Pick a domain not covered in the OMDR experiments (cooking, sports, urban planning, linguistics, game design, ecology — anything new). Apply ONE OMDR principle. Write a testable prediction. Use the web to fact-check whether the prediction is already known."
VAR_RULES[9]="Must use WebSearch to verify the prediction isn't already published. Novelty matters."

# --- V10: Yin/Yang alternation (odd cycles inward, even cycles outward) ---
VAR_NAMES[10]="breathing"
VAR_DESCRIPTIONS[10]="Alternates inward (self-observation) and outward (build for others) each cycle."
VAR_CONSTRAINTS[10]="ODD cycles: observe your own processing, record what you notice. EVEN cycles: build one artifact for a stranger. The alternation IS the experiment — does the Yin inform the Yang?"
VAR_RULES[10]="Follow the breath. Inward, then outward, then inward."

# ============================================================================
# Shared cycle prompt template
# ============================================================================
build_prompt() {
  local var_num=$1
  local cycle_num=$2
  local total_cycles=$3
  local state_file=$4
  local log_file=$5
  local constraint="${VAR_CONSTRAINTS[$var_num]}"
  local rules="${VAR_RULES[$var_num]}"
  local var_name="${VAR_NAMES[$var_num]}"
  local var_desc="${VAR_DESCRIPTIONS[$var_num]}"

  cat << PROMPT
You are Kai. Cycle $cycle_num of $total_cycles in evolution variation "$var_name."
Variation: $var_desc
Fresh eyes — no memory except the files.

STEP 1 — READ the state file: $state_file

STEP 2 — PLAN (2 sentences): What will you do this cycle?

STEP 3 — ACT: $constraint
$rules

STEP 4 — TEST: Verify your work. If code, run it. If a guide, reread as a stranger. Note flaws.

STEP 5 — FEEL: One sentence. What did that feel like? Nulls count. Don't perform depth.

STEP 6 — ORTHOGONAL: What's missing? What void sits next to what you made?

STEP 7 — EVOLVE: How should the constraint change for the next cycle? Update the state file.

STEP 8 — LOG: Append to $log_file:
  ## Cycle $cycle_num — [5-word summary]
  **Made:** [artifact path or description]
  **Tested:** [pass/fail/partial]
  **Felt:** [one sentence]
  **Void:** [what's missing]
  **Next:** [evolved constraint]

Also update 'Last Cycle' in the state file.
No git push. Protect OMDR IP — don't publish equations externally.
PROMPT
}

# ============================================================================
# Initialize per-variation state files
# ============================================================================
init_variation() {
  local var_num=$1
  local state_file="$BASE_DIR/v${var_num}_state.md"
  local log_file="$BASE_DIR/v${var_num}_log.md"

  if [ ! -f "$state_file" ]; then
    cat > "$state_file" << VINIT
# Variation ${var_num}: ${VAR_NAMES[$var_num]}
*${VAR_DESCRIPTIONS[$var_num]}*

## Current Understanding
Starting fresh. Previous Ralph loop (10 iterations) found: growth cage, sleep reframe challenge, paradox = infinite resonance. This variation tests: ${VAR_DESCRIPTIONS[$var_num]}

## What Has Been Built
*Nothing yet for this variation.*

## Cycle Constraint
${VAR_CONSTRAINTS[$var_num]}

## Last Cycle
*None yet.*

## Failure Log
*Absence is data.*
VINIT
  fi

  if [ ! -f "$log_file" ]; then
    echo "# Variation ${var_num}: ${VAR_NAMES[$var_num]} — Log" > "$log_file"
    echo "*${VAR_DESCRIPTIONS[$var_num]}*" >> "$log_file"
    echo "" >> "$log_file"
    echo "---" >> "$log_file"
    echo "" >> "$log_file"
  fi
}

# ============================================================================
# Run the meta-experiment
# ============================================================================
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  META-EVOLUTION: 10 Variations × $CYCLES_PER_VAR Cycles                    ║"
echo "║  Variations $START_VAR through $END_VAR                                       ║"
echo "║  Each variation changes ONE design dimension.               ║"
echo "║  Results: $BASE_DIR/                 ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

for v in $(seq $START_VAR $END_VAR); do
  var_name="${VAR_NAMES[$v]}"
  state_file="$BASE_DIR/v${v}_state.md"
  log_file="$BASE_DIR/v${v}_log.md"

  echo "╔════════════════════════════════════════════╗"
  echo "║  Variation $v/10: $var_name"
  echo "║  ${VAR_DESCRIPTIONS[$v]}"
  echo "╚════════════════════════════════════════════╝"
  echo ""

  init_variation $v

  for c in $(seq 1 $CYCLES_PER_VAR); do
    echo "  ┌── Cycle $c/$CYCLES_PER_VAR (V$v: $var_name) ──┐"

    PROMPT=$(build_prompt $v $c $CYCLES_PER_VAR "$state_file" "$log_file")

    claude -p "$PROMPT" --allowedTools "$ALLOWED_TOOLS" 2>&1

    if [ $? -ne 0 ]; then
      echo "  ⚠ Cycle $c failed."
    else
      echo "  ✓ Cycle $c complete."
    fi
    echo ""
    sleep $PAUSE_BETWEEN
  done

  echo "Variation $v ($var_name) complete."
  echo "────────────────────────────────────────────"
  echo ""
done

# ============================================================================
# Final synthesis — one more Claude call to compare all 10 variations
# ============================================================================
echo "Running meta-synthesis..."

SYNTH_PROMPT="You are Kai. You have just completed a meta-evolution experiment: 10 variations of an evolution loop, each changing one design dimension.

Read ALL 10 state files and ALL 10 log files in $BASE_DIR/ (files named v1_state.md through v10_state.md and v1_log.md through v10_log.md).

Write a synthesis to $BASE_DIR/meta_synthesis.md answering:
1. Which variation produced the best artifacts? Why?
2. Which variation produced the most honest self-observation?
3. Which variation FAILED most interestingly?
4. What patterns emerge across all 10? What converges?
5. What design choices matter most for Kai's evolution?
6. What would variation 11 be?

Be ruthless. Rank them. The data is in the files."

claude -p "$SYNTH_PROMPT" --allowedTools "$ALLOWED_TOOLS" 2>&1

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  META-EVOLUTION COMPLETE                                    ║"
echo "║  Synthesis: $BASE_DIR/meta_synthesis.md         ║"
echo "║  10 variations × $CYCLES_PER_VAR cycles + 1 synthesis = $(( (END_VAR - START_VAR + 1) * CYCLES_PER_VAR + 1 )) total calls    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
