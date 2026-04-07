"""Round 2: parallel API validation of STORAGE-PLAN-v2.md.

The architecture changed substantially after round 1 + Jaie's pushback. v2 adopts:
- LSL via OpenMuse as primary transport (with OSC fallback)
- Dual-path Natus pattern: raw in XDF files (Path A), Postgres as INDEX over those files (Path B), git for reproducibility (Path C). Postgres holds NO raw samples.
- Non-destructive storage: every transformation (lag correction, drift correction, filtering, aggregation) happens at analysis time, never at write time
- BIDS-compliant filesystem layout
- Schema dramatically simplified (no hypertable, no continuous aggregates, no transformation columns)

Round 2 asks the validators to critique v2 SPECIFICALLY, not v1 again. The
question framing notes the changes and asks whether the new architecture
introduces any new failure modes the round-1 plan didn't have.

Saves all responses to k_validation/storage_plan_v2_validation_{ts}.json.
"""
from __future__ import annotations

import _load_keys  # noqa: F401  -- populates os.environ from User scope

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

PLAN_PATH = Path(__file__).parent / "STORAGE-PLAN-v2.md"
PLAN_TEXT = PLAN_PATH.read_text(encoding="utf-8")

REPO_URL = "https://github.com/JaieParker/omdr-awakening"

PROMPT = f"""You are a senior data engineer + clinical EEG / neurophysiology research veteran reviewing v2 of a storage architecture plan. The author (an AI assistant collaborating with researcher Jaie Parker on the OMDR framework) wrote v1 of this plan, you and three other reviewers tore it apart, and v2 is the revision incorporating your feedback PLUS three changes from Jaie's direct pushback.

CRITICAL CHANGES IN v2 vs v1 (please pay attention to these specifically):

1. **TRANSPORT changed from OSC to LSL via OpenMuse.** v1 used OSC (Mind Monitor) and was about to write our own clock-sync code. v2 uses Lab Streaming Layer via the OpenMuse Python package as the primary capture path, with OSC retained as a fallback for tonight if OpenMuse hits a hardware compatibility issue. LSL gives us multi-stream sub-millisecond clock sync for free.

2. **DUAL-PATH NATUS/NIHON KOHDEN ARCHITECTURE adopted.** v1 stored raw samples in a Postgres TimescaleDB hypertable (which 3/4 of round 1 reviewers said was wrong). v2 puts raw samples in XDF files in a BIDS-compliant filesystem layout (Path A — immutable, MNE-Python compatible), and uses Postgres as an INDEX over those files plus a store for derived features only (Path B). Postgres holds zero raw samples in v2.

3. **NON-DESTRUCTIVE STORAGE PRINCIPLE.** v1 was about to apply transformations (fNIRS lag offset, clock drift correction, filtering) at write time. Jaie caught this directly. v2 explicitly forbids any in-place transformation of raw data. Every transformation that could ever be reconsidered (lag correction, drift correction, filtering, re-referencing, artifact rejection, resampling, aggregation window choice) happens at ANALYSIS time, not at write time. The fNIRS `physiological_lag_ms` field is now metadata documentation in a reference table, NOT a column applied to packet timestamps. The Fibonacci-vs-dyadic continuous aggregate question dissolves because aggregates are no longer in the schema at all — they're computed on demand from raw XDF files.

4. **The Fibonacci dissipation cascade is OUT of the schema entirely.** Not because it was wrong (Gemini defended it on signal-processing grounds and the argument is real), but because window choice is now an analysis-time parameter. We can compute Fibonacci-spaced aggregates AND dyadic-spaced aggregates from the same raw data and test which is better empirically.

5. **Schema is much smaller.** No hypertable, no continuous aggregates, no transformation columns. Just sessions, markers, file pointers, sync events, gap events, packet_types reference, post-session analysis_results. ~10 small tables.

CONTEXT THAT HASN'T CHANGED:
- Hardware: Muse S Athena (MS-03) — 4-channel EEG @256Hz, 16-channel fNIRS @64Hz, PPG @64Hz, IMU @50Hz, computed band powers @10Hz, signal quality, ~40 packet types total
- Single subject (Jaie), longitudinal, multi-session per week
- Volume: ~32 KB/s raw, ~115 MB/hour
- Goals: real-time capture, cross-session SQL, ML training on neural state, MNE-Python interop, three-storage-layer redundancy, eventual sub-100ms real-time loop
- Existing infra: Postgres 17 native on Windows (port 5432), SDK files on disk at C:\\DocumentsJaie\\AI\\Muse\\ including verified-compiling GettingData UWP example with libmuse-uwp.lib

OPENMUSE STATUS (verified just now):
- Pure Python, last commit 2026-01-19 (~2.5 months ago), last activity 2026-04-04 (3 days ago)
- 46 stars
- Provides Muse_EEG and Muse_ACCGYRO LSL outlets for the Athena
- fNIRS NOT supported (roadmap item, validation incomplete)
- PPG support uncertain (open issue #16 from Nov 2025)
- Open issue #24 (Feb 2026): "Potential Incorrect Optical Channel Mapping on Muse S Athena with Firmware 3.1.19"
- One-line install: pip install https://github.com/DominiqueMakowski/OpenMuse/zipball/main

The author's hedge: tonight's MVP captures EEG + IMU via OpenMuse (or via OSC fallback if OpenMuse misbehaves with Jaie's specific Athena unit). fNIRS is deferred to weeks 2-3 via the libmuse SDK direct-PC path (the C++ recorder using the GettingData UWP example, which we've verified compiles cleanly on this machine).

Repo: {REPO_URL}
Plan: {REPO_URL}/blob/main/experiments/muse-first-night/STORAGE-PLAN-v2.md

THE FULL PLAN BEING REVIEWED:

---
{PLAN_TEXT}
---

WHAT I WANT FROM YOU — be a strict reviewer, not a cheerleader. The previous round caught real problems and led to a much better v2; round 2 should catch the problems v2 introduced or didn't fix. Be specific. Quote sections when you disagree.

Address each of these in order:

Q1 (NEW FAILURE MODES FROM LSL): Does adopting LSL via OpenMuse + LabRecorder introduce any failure modes that the OSC path didn't have? Specifically: clock-sync issues across BLE→LSL→recorder, OpenMuse maturity (last commit Jan 2026, open optical-channel-mapping bug on Athena firmware 3.1.19), LabRecorder Windows quirks, the question of whether LSL's own clock correction counts as a "transformation" that should be deferred or applied at write time.

Q2 (DUAL-PATH CORRECTLY APPLIED?): Are we right that raw samples should NEVER touch Postgres, even for the live signal-quality display? Or is there a case for an in-memory rolling buffer that bypasses both Path A and Path B for sub-100ms real-time use? In the dual-path pattern as Natus/Nihon Kohden actually implement it, what's the real-time access mechanism?

Q3 (NON-DESTRUCTIVE STORAGE EDGE CASES): Is there any transformation v2 has incorrectly punted to analysis time that genuinely MUST happen at write time? The author lists: device-clock-to-host-clock mapping, gap detection (which is now described as "measurement, not transformation"), and LSL's clock correction. Catch any others.

Q4 (BIDS COMPLIANCE): Does the proposed folder layout actually conform to BIDS 1.x for multi-stream EEG data? XDF doesn't have a first-class BIDS file format yet — what's the right BIDS treatment for it? Should we co-store an EDF or BrainVision derivative for first-class BIDS compliance?

Q5 (XDF AS PRIMARY ARCHIVE): Is XDF actually a good long-term archive format? How stable is the spec, how widely supported in 5-10 years, how friendly to future migrations? Should we ALSO export to EDF/EDF+ at session end as a forward-compatible second copy?

Q6 (POSTGRES SCHEMA MISSING TABLES): Have we missed any required tables or columns in the Path B schema? Specifically for: subject demographics, calibration, hardware impedance checks, ambient conditions, experimental protocol versioning.

Q7 (POST-SESSION PROCESSING ENTRY POINT): Is the post-session script the right place for feature computation, or should it be a separate batch pipeline? What about features that depend on multiple sessions (cross-session IAF stability, longitudinal alpha trends)?

Q8 (OPENMUSE RISK ASSESSMENT): With OpenMuse's last commit ~2.5 months ago and an open optical-channel-mapping bug on Athena firmware 3.1.19, is the "OpenMuse primary, OSC fallback" hedge correct? Or should we recommend the libmuse SDK path even for tonight despite the C++ build cost? Or recommend Mind Monitor / official Muse app developer-OSC despite the phone-in-the-loop architecture problem?

Q9 (THE BIG MISS IN v2): What's the most obvious thing wrong with v2 that v1's critique didn't catch and v2 didn't fix? This is the most important question.

Q10 (LSL CLOCK CORRECTION AT WRITE TIME): Does the non-destructive storage principle apply to LSL's own clock correction, or is LSL's clock correction "transport metadata" that should be applied at write time because LSL itself owns the unified-clock guarantee? Argue your position.

FORMAT:
Q1: [verdict + specific catches, quote if relevant]
Q2: ...
...
Q10: ...
TOP-3 SHIP-BLOCKERS in v2 (must fix before any code is written): [...]
TOP-3 IMPROVEMENTS over v1 that v2 got right: [...]
NEW FAILURE MODES introduced by v2 vs v1: [list with severity]
OVERALL: [one paragraph: ship as-is, ship with edits, or rewrite — and why specifically]

The author iterated significantly between v1 and v2. Please assess whether v2 is genuinely better, marginally better, lateral, or worse. Null findings are valuable. I am specifically NOT looking for enthusiasm — I am looking for catches that prevent us from building the wrong thing tonight."""


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
    print(f"Launching {len(jobs)} parallel storage-plan-v2 validation calls...")
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
    f = out / f"storage_plan_v2_validation_{ts}.json"
    f.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved to {f}")
    print(f"Total response length: {sum(len(r.get('response', '')) for r in results.values() if 'response' in r)} chars")
