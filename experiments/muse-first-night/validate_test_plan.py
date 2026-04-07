"""Parallel outside-AI validation of the tonight test plan.

Sends the three experiment designs (eyes-closed baseline, music intervals,
rest vs arithmetic) plus the analysis methodology to Grok / GPT-4o / Claude
via API and asks each one to be a strict reviewer.

What we ask for:
    - Are the protocols well-formed?
    - Are the analysis methods (alpha enhancement ratio, pairwise coherence)
      the right choices for the predictions?
    - What confounds are we missing?
    - Are the segment durations correct (long enough to extract signal,
      short enough to avoid fatigue/drift)?
    - What would a real EEG researcher say is wrong with this?
    - Specific, actionable critique only — no enthusiasm.

Saves all responses to k_validation/ as JSON for the audit trail.
"""
from __future__ import annotations

import _load_keys  # noqa: F401  -- populates os.environ from User scope

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

PROMPT = """You are a senior EEG researcher reviewing an experimental plan for a one-evening, one-subject, consumer-grade Muse (4 EEG channels: TP9, AF7, AF8, TP10 at ~256 Hz) recording session that will run tonight. The subject is the researcher himself; he is at work right now and the device just arrived. The pipeline streams via Mind Monitor → OSC → Python on PC and writes CSVs of raw EEG, band powers, and signal quality. We have already verified end-to-end with a synthetic data test (the pipeline correctly recovers a 42x alpha enhancement from a mocked eyes-closed boost).

Three experiments are planned, in this order:

EXPERIMENT 1 — Eyes-closed vs eyes-open baseline (the "hello world")
  Protocol: pre-flight signal-quality gate (~30s, requires 3 contiguous seconds of all-good horseshoe). Then 4 alternating 60-second blocks: open, closed, open, closed.
  Analysis: Welch PSD per segment, alpha-band power (8-13 Hz) per channel, alpha-enhancement ratio = mean(closed alpha) / mean(open alpha), pooled across the temporal channels TP9 + TP10.
  Pass criterion: pooled-temporal alpha enhancement > 1.5x (literature: 1.5-3x is canonical at temporal/parietal sites).
  Total time: ~5 min including pre-flight.

EXPERIMENT 2 — Music intervals (consonance vs dissonance)
  Protocol: pre-flight signal-quality gate. Then 5 stimuli x 2 reps in randomised order. Each block: 20s rest + 20s stimulus. Stimuli are pure stereo sine waves (no harmonics) at A3 = 220 Hz root: octave 2:1, fifth 3:2, major third 5:4, tritone sqrt(2):1, minor second 16:15. Subject sits eyes-closed listening through headphones.
  Analysis: For each stimulus segment, compute pairwise magnitude-squared coherence in the alpha band (8-13 Hz) across all 6 channel pairs, average to a "global alpha coherence index" per stimulus. Compare across stimulus types.
  Hypothesis: Consonant intervals (octave > fifth > third) produce higher global alpha coherence than dissonant intervals (tritone, minor second). This is a tentative test of a universal-resonance prediction; one subject one night is informative not conclusive.
  Total time: ~7 min.

EXPERIMENT 3 — Rest vs mental arithmetic (Yin/Yang contrast)
  Protocol: pre-flight gate. Then a fixed-order block design: 180s eyes-closed rest with slow breathing, then 180s eyes-closed mental arithmetic (silent serial-7 subtraction from 1000). Order is fixed (rest first) for tonight; counterbalancing left for replication.
  Analysis: Pooled temporal alpha, beta, theta band power per condition; pairwise alpha coherence per condition. Predictions: alpha(rest) > alpha(arith), beta(arith) > beta(rest), theta(rest) >= theta(arith), global alpha coherence(rest) > arith.
  Total time: ~7 min.

PIPELINE NOTES:
  - Mind Monitor's horseshoe encoding: 1=good, 2=ok, 4=bad. Pre-flight requires 3 contiguous seconds of all-1s on all four electrodes.
  - Sample rate is estimated from inter-sample intervals (median); end-to-end test showed 247.6 Hz on synthetic data, real Muse is 256 Hz nominal.
  - Welch PSD with nperseg = min(2*fs, segment_length).
  - Coherence via scipy.signal.coherence with same nperseg.
  - All data persisted to CSV with wall-clock timestamps; markers via Session.mark() write a markers.csv that the analysis pipeline uses to slice segments.

WHAT I WANT FROM YOU — be strict and specific. Itemise:

Q1. PROTOCOL DESIGN — Are the durations correct? Is 60s/block in Experiment 1 sufficient to extract a clean alpha-enhancement effect on consumer 4-channel EEG? Are 20s music segments long enough to measure stimulus-locked coherence changes? Are 180s rest/arithmetic blocks the right length, or too short?

Q2. ANALYSIS CHOICES — Is alpha enhancement the right primary metric for E1? Is pairwise magnitude-squared coherence the right choice for E2 and E3, or would PLV (phase-locking value), wPLI, or imaginary coherence be more robust against volume conduction artifacts on a 4-channel headband?

Q3. CONFOUNDS — What are we ignoring that could fake or mask each effect? (Eye movement artifacts in the closed-eye condition? Counting silently activates motor cortex differently than expected? Mind Monitor's band powers are pre-computed and may have their own filtering we don't control?)

Q4. ELECTRODE PLACEMENT — Muse's 4 channels are frontal (AF7, AF8) and temporal (TP9, TP10). Is "alpha enhancement at TP9/TP10" the right pooling, given that classical alpha is most prominent at occipital sites which the Muse cannot reach? Should we be looking at the front+temporal contrast differently?

Q5. STATISTICAL POWER — With 2x60s open and 2x60s closed in E1, what's the realistic effect-size detectability? With 2 reps of 5 stimuli in E2 (n=2 per condition), is anything meaningful actually achievable, or should this be deferred to a multi-night setup?

Q6. PRE-FLIGHT GATE — A 3-second contiguous all-good requirement on Mind Monitor's horseshoe — too strict, too lax, or just right? Does this risk false-rejecting a usable session or false-accepting a flaky one?

Q7. WHAT TO DROP OR ADD — If you had 30 minutes and a tired-from-work subject, would you keep all three experiments, drop one, or insist on something different? What's the highest-leverage hour for a first-ever Muse recording?

Q8. NULL RESULT POSTURE — If E1 fails (ratio <= 1.0), is it more likely a real null, a headband fit issue, a Mind Monitor configuration issue, or a pipeline bug? How would you triage?

Format:
Q1: [verdict + specific recommendations]
Q2: ...
...
Q8: ...
TOP-3 ACTION ITEMS (most important fixes before tonight): [...]
OVERALL: [one paragraph: should we run as designed, run with edits, or rework before tonight?]
Be terse. Catch problems. Null findings are valuable. I am NOT looking for enthusiasm — I want errors and missing pieces."""


def call_openai(prompt):
    import httpx
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return {"error": "OPENAI_API_KEY not set"}
    start = time.time()
    resp = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": "gpt-4o", "messages": [{"role": "user", "content": prompt}], "max_tokens": 3500},
        timeout=180,
    )
    data = resp.json()
    if "choices" in data:
        return {"model": "gpt-4o", "response": data["choices"][0]["message"]["content"], "elapsed_seconds": round(time.time()-start, 2)}
    return {"error": str(data)}


def call_grok(prompt):
    import httpx
    api_key = os.environ.get("XAI_API_KEY", "")
    if not api_key:
        return {"error": "XAI_API_KEY not set"}
    start = time.time()
    resp = httpx.post(
        "https://api.x.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": "grok-3-mini", "messages": [{"role": "user", "content": prompt}], "max_tokens": 3500},
        timeout=180,
    )
    data = resp.json()
    if "choices" in data:
        return {"model": "grok-3-mini", "response": data["choices"][0]["message"]["content"], "elapsed_seconds": round(time.time()-start, 2)}
    return {"error": str(data)}


def call_claude(prompt):
    import anthropic
    client = anthropic.Anthropic()
    start = time.time()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=3500,
        messages=[{"role": "user", "content": prompt}],
    )
    return {"model": "claude-sonnet-4", "response": response.content[0].text if response.content else "", "elapsed_seconds": round(time.time()-start, 2)}


if __name__ == "__main__":
    jobs = [(call_grok, "grok"), (call_openai, "openai"), (call_claude, "claude")]
    results = {}
    print("Launching 3 parallel test-plan validation calls...")
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(fn, PROMPT): tag for fn, tag in jobs}
        for fut in as_completed(futures):
            tag = futures[fut]
            try:
                r = fut.result()
                results[tag] = r
                print(f"  {tag} done in {r.get('elapsed_seconds', '?')}s ({len(r.get('response', ''))} chars)")
            except Exception as e:
                results[tag] = {"error": str(e)}
                print(f"  {tag} ERROR: {e}")

    out = Path(__file__).parent / "k_validation"
    out.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    f = out / f"test_plan_validation_{ts}.json"
    f.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved to {f}")
