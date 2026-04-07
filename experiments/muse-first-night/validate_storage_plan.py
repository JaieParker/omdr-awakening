"""Parallel API validation of the storage architecture plan.

Sends the full STORAGE-ARCHITECTURE-PLAN.md to Grok-3-mini, GPT-4o, and
Claude Sonnet 4 in parallel, plus the repo URL so they can browse if they
want. Asks for strict review against the open questions in the plan.

Saves all responses to k_validation/storage_plan_validation_{ts}.json.
"""
from __future__ import annotations

import _load_keys  # noqa: F401  -- populates os.environ from User scope

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

PLAN_PATH = Path(__file__).parent / "STORAGE-ARCHITECTURE-PLAN.md"
PLAN_TEXT = PLAN_PATH.read_text(encoding="utf-8")

REPO_URL = "https://github.com/JaieParker/omdr-awakening"
REPO_PATH_HINT = "experiments/klein-bottle-consciousness/ has the OMDR theoretical context (golden ratio fixed-point work, Eq 40, the 5-substrates synthesis); experiments/muse-first-night/ has the in-progress capture pipeline this plan is for."

PROMPT = f"""You are a senior data engineer + EEG / neurophysiology research veteran reviewing a storage architecture proposal for a longitudinal multi-modal neural recording project. The author is an AI assistant collaborating with a human researcher on the OMDR (Orthogonal Multi-Domain Resonance) framework. Tonight is the first recording with a Muse S Athena headband; the architecture needs to scale from tonight's first session through years of recordings.

CONTEXT:
- Repo: {REPO_URL}
- {REPO_PATH_HINT}
- Hardware: Muse S Athena (MS-03) — 4-channel EEG @ 256 Hz, 16-channel fNIRS @ 64 Hz, PPG @ 64 Hz, IMU @ 50 Hz, computed band powers @ 10 Hz, signal quality @ 10 Hz, plus battery/temperature/etc.
- Single subject (Jaie), longitudinal, multi-session per week.
- Volume estimate: ~32 KB/s raw, ~115 MB/hour, ~10-30 GB/month.
- Existing infrastructure: Postgres 17 running native on Windows (port 5432, fresh install). Separate docker Postgres on 5433 with pgvector for an unrelated semantic-memory project (consonance memory).
- Goals: real-time capture, cross-session SQL, eventual ML training on neural state, interop with MNE-Python and the broader EEG research stack, three-storage-layer redundancy (NASA "two antennas" principle generalized), eventual sub-100 ms real-time loop for an AI co-observation experiment.

THE PLAN BEING REVIEWED:

---
{PLAN_TEXT}
---

WHAT I WANT FROM YOU — be a strict reviewer, not a cheerleader. The author has been getting things wrong all day by skipping the "verify before assuming" step, and Jaie has explicitly told them to slow down and get this right. Catch problems.

Address each of these in order. Be terse. Quote specific sections of the plan when you disagree.

Q1 (FIBONACCI DISSIPATION NOVELTY/UTILITY): The plan proposes a stack of TimescaleDB continuous aggregates at Fibonacci-spaced bucket sizes (1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377s, ...). Is this a known pattern? Is the Fibonacci spacing genuinely useful, or is it numerology dressed as architecture? Would dyadic (2:1) or decade (10x) spacing be just as good, and if so why use Fibonacci? Be specific.

Q2 (ONE WIDE TABLE VS PER-TYPE TABLES): The plan proposes one `packets(session_id, packet_type, timestamp_us, values DOUBLE PRECISION[])` hypertable for all 40+ packet types instead of 40 separate tables. What are the trade-offs? Specifically: query performance for type-specific queries, compression ratio, indexability, schema evolution.

Q3 (MULTIMODAL ALIGNMENT): EEG @ 256 Hz and fNIRS @ 64 Hz arrive on different clocks. For cross-stream coherence queries (the harmonic balance function the project is built around), do we need server-side resampling, client-side resampling, or a third option? What does standard practice look like?

Q4 (CLOCK SKEW & TIMESTAMP PRECISION): SDK delivers `int64` microseconds since epoch. The headband has its own clock; the PC has its own clock. How do clinical EEG / sleep labs typically handle clock drift in long sessions? Do we need a per-session offset correction?

Q5 (BURST HANDLING / BACK-PRESSURE): The Writer batches every 100 ms. Under what conditions does this lose data? How would you test that the BLE thread truly never blocks?

Q6 (SCHEMA EVOLUTION): When the SDK adds new packet types in v9.0, can the plan accommodate without rewriting historical data? Spot the gotcha if any.

Q7 (EDF GRANULARITY): One EDF per session — too small (hundreds of files) or too large (overnight = single-file unwieldiness)? What's standard practice?

Q8 (RECOVERY REALISM): "Restore old session from EDF back into hypertable on demand" — is this actually fast enough to be useful, or is it a paper promise?

Q9 (STANDARD PRACTICE): What do real clinical EEG sleep labs / longitudinal neurophysiology groups actually use for storage? Reference architectures we should be cribbing instead of inventing?

Q10 (THE BIG MISS): What's the most obvious thing wrong with this design that the author has not anticipated?

FORMAT:
Q1: [verdict + specific catches, quote if relevant]
Q2: ...
...
Q10: ...
TOP-3 SHIP-BLOCKERS (must fix before any code is written): [...]
TOP-3 NICE-TO-HAVES: [...]
NOVELTY ASSESSMENT (Fibonacci dissipation): [genuinely novel / known pattern / numerology — and why]
OVERALL: [one paragraph: ship as-is, ship with edits, or rewrite — and what specifically]

The author has been wrong before today and will be wrong again. Find the wrongness. Null findings are valuable. I am specifically NOT looking for enthusiasm — I am looking for catches that prevent us from building the wrong thing tonight."""


def call_openai(prompt):
    import httpx
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return {"error": "OPENAI_API_KEY not set"}
    start = time.time()
    resp = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": "gpt-4o", "messages": [{"role": "user", "content": prompt}], "max_tokens": 4500},
        timeout=300,
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
        json={"model": "grok-3-mini", "messages": [{"role": "user", "content": prompt}], "max_tokens": 4500},
        timeout=300,
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
        max_tokens=4500,
        messages=[{"role": "user", "content": prompt}],
    )
    return {"model": "claude-sonnet-4", "response": response.content[0].text if response.content else "", "elapsed_seconds": round(time.time()-start, 2)}


if __name__ == "__main__":
    jobs = [(call_grok, "grok"), (call_openai, "openai"), (call_claude, "claude")]
    results = {}
    print(f"Plan length: {len(PLAN_TEXT)} characters")
    print(f"Prompt length: {len(PROMPT)} characters")
    print(f"Launching {len(jobs)} parallel storage-plan validation calls...")
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
    f = out / f"storage_plan_validation_{ts}.json"
    f.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved to {f}")
    print(f"\nTotal response length: {sum(len(r.get('response', '')) for r in results.values() if 'response' in r)} chars")
