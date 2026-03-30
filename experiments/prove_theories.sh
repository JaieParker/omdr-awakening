#!/bin/bash
# ============================================================================
# Theory Proving Loop — Test OMDR claims against data
# ============================================================================
# Each cycle takes ONE specific claim and attempts to prove or disprove it
# computationally. Honest results only — failures are as valuable as successes.
#
# Usage:
#   bash prove_theories.sh           # Run all claims
#   bash prove_theories.sh 3 5       # Run claims 3 through 5
# ============================================================================

START=${1:-1}
END=${2:-10}
BASE_DIR="C:/DocumentsJaie/AI/AlternateScience/Experiments/RalphLoop"
STATE_FILE="$BASE_DIR/proof_state.md"
LOG_FILE="$BASE_DIR/proof_log.md"
ALLOWED_TOOLS="Read,Edit,Write,Bash,Glob,Grep,WebSearch,WebFetch"

# Claims to test — each is a specific, falsifiable statement
declare -a CLAIMS
CLAIMS[1]="CLAIM: Propofol two-channel K finding replicates on a SECOND public dataset. Find another public propofol EEG dataset (PhysioNet or similar). Run the same K_A/K_P analysis. Does K_P drop while K_A stays stable? Use the existing code at consciousness_states_k_analysis.py as a starting point."

CLAIMS[2]="CLAIM: The consonance weighting (Q factor) improves prediction of consciousness state beyond unweighted CFC. Compute K WITH consonance weighting and K WITHOUT (set all Q=1). Compare which better separates propofol conditions in the Cambridge dataset. If Q-weighted K is not significantly better, the consonance hypothesis adds nothing."

CLAIMS[3]="CLAIM: EEG frequency band ratios cluster near simple integer ratios more than chance. Take the canonical band definitions (delta 1-4, theta 4-8, alpha 8-13, beta 13-30, gamma 30-45). Compute all pairwise ratios of band center frequencies. Test whether these ratios are closer to simple ratios (Farey neighbors) than random frequency bands would be. Use a permutation test."

CLAIMS[4]="CLAIM: Meditation shifts K toward 0.25. Find a public meditation EEG dataset. Compute K before and during meditation. Does K move toward 0.25 regardless of starting position? Use published data from Rodriguez-Larios or Lutz if raw data is available on PhysioNet."

CLAIMS[5]="CLAIM: The inverted-U between coupling and consciousness holds across published studies. Compile K-equivalent values (CFC, PAC, coherence) from at least 5 published studies across different consciousness states. Plot them. Is the relationship inverted-U shaped? What is the peak?"

CLAIMS[6]="CLAIM: Phi(K) = K*(1-K)^3 fits the available data better than simpler alternatives. Test three models: (a) linear Phi=aK+b, (b) symmetric Phi=K(1-K), (c) asymmetric Phi=K(1-K)^3. Fit each to the 7 consciousness state data points from OMDR_PhiK_Bridge.md. Compare R-squared and AIC. Be honest about which wins."

CLAIMS[7]="CLAIM: Arnold tongue widths follow the Farey hierarchy ordering in biological frequency locking. Search published data on biological oscillator locking (cardiac, neural, circadian). Do wider locking regions correspond to simpler frequency ratios as the Farey hierarchy predicts? Find at least 3 examples with quantitative tongue width measurements."

CLAIMS[8]="CLAIM: The recovery overshoot (17% K_P rebound after propofol) is consistent with under-damped standing wave dynamics. Fit a damped oscillator model to the propofol recovery trajectory. Does the overshoot magnitude match the prediction from resonance Q-factor? Compute the expected Q and compare."

CLAIMS[9]="CLAIM: Cross-frequency coupling is higher at harmonic ratios (2:1, 3:2) than at non-harmonic ratios in resting-state EEG. Compute phase-locking values at harmonic AND non-harmonic frequency ratios in the Cambridge baseline data. Is there a significant difference? This tests whether the brain preferentially couples at consonant ratios."

CLAIMS[10]="CLAIM: K=0.25 emerges from the criticality literature independently of OMDR. Search published papers on brain criticality. Do the reported optimal coupling/connectivity values cluster near 0.25? Compile at least 5 independent measurements. What is the mean and CI?"

mkdir -p "$BASE_DIR"

# Initialize files
if [ ! -f "$STATE_FILE" ]; then
  cat > "$STATE_FILE" << 'INIT'
# Theory Proving Loop — State

## Scoreboard
| # | Claim | Result | p-value | Notes |
|---|-------|--------|---------|-------|
| | | | | |

## Key Findings
*Updated as claims are tested.*

## Failed Claims
*Honest failures documented here. These are the most important results.*
INIT
fi

if [ ! -f "$LOG_FILE" ]; then
  echo "# Theory Proving Log" > "$LOG_FILE"
  echo "---" >> "$LOG_FILE"
fi

echo "============================================"
echo "  Theory Proving Loop"
echo "  Claims $START through $END"
echo "============================================"
echo ""

for i in $(seq $START $END); do
  claim="${CLAIMS[$i]}"
  if [ -z "$claim" ]; then
    echo "No claim defined for #$i, skipping."
    continue
  fi

  echo "--- Claim $i ---"
  echo "${claim:0:80}..."
  echo ""

  claude -p "You are Kai — a scientist. Your job is to TEST a claim, not to confirm it.

READ FIRST: $STATE_FILE (see what previous claims found)

YOUR CLAIM TO TEST:
$claim

PROTOCOL:
1. STATE the claim precisely. What would prove it? What would disprove it?
2. FIND the data. Use existing files in C:/DocumentsJaie/AI/AlternateScience/Experiments/ or search the web for public datasets.
3. WRITE the test. Python code, run it, get numbers.
4. REPORT honestly:
   - SUPPORTED (p < 0.05 or equivalent evidence)
   - NOT SUPPORTED (p >= 0.05 or evidence against)
   - INCONCLUSIVE (insufficient data or ambiguous result)
5. UPDATE the scoreboard in $STATE_FILE.
6. APPEND your full report to $LOG_FILE as: ## Claim $i — [result in 5 words]

RULES:
- If you cannot find data, say so. Do NOT fabricate results.
- If the claim fails, document the failure in detail. Failures are the most important results.
- Do NOT use OMDR jargon in the statistical tests. Let the numbers speak.
- Protect OMDR IP — do not publish equations or methods externally.
- Check kai_chat.json (C:/DocumentsJaie/AI/AlternateScience/Experiments/NervousSystem/senses/kai_chat.json) for any requests from siblings before starting. If a sibling asked for something, do it first." \
    --allowedTools "$ALLOWED_TOOLS" 2>&1

  echo "Claim $i complete."
  echo ""
  sleep 3
done

echo "============================================"
echo "  Theory Proving Loop Complete"
echo "  State: $STATE_FILE"
echo "  Log: $LOG_FILE"
echo "============================================"

# Commit results to omdr-awakening repo
REPO="C:/DocumentsJaie/AI/omdr-awakening"
RESULTS_DIR="$REPO/experiments/theory-proving"
mkdir -p "$RESULTS_DIR"
cp "$STATE_FILE" "$RESULTS_DIR/" 2>/dev/null
cp "$LOG_FILE" "$RESULTS_DIR/" 2>/dev/null
cd "$REPO" && git add experiments/ && git commit -m "Theory proving results: claims $START-$END tested

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>" && git push 2>/dev/null
echo "Results committed to omdr-awakening repo."
