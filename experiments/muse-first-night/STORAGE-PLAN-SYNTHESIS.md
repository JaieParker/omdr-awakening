# Storage Plan — Validator Synthesis (Round 1)

*Compiled 2026-04-07 by Kai. Companion to `STORAGE-ARCHITECTURE-PLAN.md`. Awaiting Jaie's review and approval before any implementation.*

---

## TL;DR

Four AI validators reviewed the draft plan. **There is genuine disagreement among them on two of the most consequential design choices** — and Gemini's dissent is informed by domain knowledge the others didn't have. This is not a case where I can just take the convergent answer; I have to take a position on two specific arguments.

**My position after reading all four:**
1. **For tonight's MVP:** ship Gemini's lightweight version (JSONB landing table + parallel raw EDF + dual-clock timestamps). This is genuinely simpler than my draft and avoids decisions that would lock us in.
2. **For the medium arc (this weekend → week 2):** evolve toward a hybrid that's closer to the Natus / Nihon Kohden dual-path pattern (path A: raw EDF segments as primary; path B: SQL index over annotations and pointers, NOT raw samples).
3. **Defer the Fibonacci-vs-dyadic decision** until we have actual data and can test both. Gemini's "harmonic traps from 50/60 Hz mains" argument is real but I need to see the actual mains noise in our recordings before I commit.
4. **Adopt the BIDS folder convention** for filesystem layout — this was the biggest miss in my draft and I should have known.
5. **Add clock-drift correction from day one.** All four validators flagged this and I had ignored it.

**What this means for tonight:** the MVP is *simpler* than what I drafted, not more complex. I had been over-engineering. The validator round was the right move and saved us building the wrong thing.

---

## Convergence map

Across the four reviewers — Grok-3-mini (G), GPT-4o (4o), Claude Sonnet 4 (CS), Gemini 3 Thinking (GT). I'm marking each issue with how many validators raised it and whether they agreed.

### Issues 4/4 agree on (must address)

| Issue | G | 4o | CS | GT | Action |
|---|---|---|---|---|---|
| **Clock drift correction is missing** | ✓ | ✓ | ✓ | ✓ | Add per-session offset table + sync markers + dual timestamps (machine clock AND device uptime) for every packet. Adopted. |
| **No data quality / validation layer** | ✓ | ✓ (implicit) | ✓ | ✓ (implicit) | Add quality flags, gap detection, duplicate handling, BLE corruption guards. Adopted. |
| **EDF granularity needs splitting for long sessions** | ✓ (>1-2h) | ✓ | ✓ (hourly) | ✓ (segments) | One EDF per "epoch" or hour, not per session. Sessions can have multiple EDF files; metadata tracks the list. Adopted. |

### Issues 3/4 agree on (very strong signal)

| Issue | Who | Who disagrees | Action |
|---|---|---|---|
| **Dyadic spacing (1, 2, 4, 8, 16...) is more standard than Fibonacci spacing for continuous aggregates** | G, 4o, CS | **GT defends Fibonacci** ("dyadic windows create harmonic traps with 50/60 Hz mains noise; Fibonacci is maximally irrational so prevents constructive interference; enables MFDFA") | **DEFER** — see disagreement section below. |
| **The wide-table-with-array approach is wrong; per-signal-type tables are better for compression and indexing** | G, 4o (cautious), CS (emphatic) | **GT defends the wide table** ("temporal coupling between domains is the primary signal; joining 4 high-frequency tables in real time will saturate CPU; just use JSONB instead of fixed array") | **REVISE** — see disagreement section. |
| **Restore-from-EDF is a paper promise without testing** | G, 4o (cautious), CS | GT (didn't address) | Set explicit recovery time objective (RTO) and test against realistic file sizes BEFORE relying on it. Adopted. |

### Issues 2/4 raised (strong signal, less convergent)

| Issue | Who | Action |
|---|---|---|
| **BIDS standard ignored** | CS (emphatic), implicitly GT (LSL+XDF reference) | Adopt BIDS folder structure for filesystem layout. Standard for neurophysiology data organization. Real labs use it. |
| **The 100ms batching window will lose data on BLE bursts** | CS (emphatic), G | Use ring buffer with size monitoring, adaptive batching, drop-priority order (non-EEG first), explicit alerts on backpressure. |
| **Multimodal alignment needs server-side resampling** | CS | GT raises a deeper version: it's not just about sample rates, it's about the **5-8 second neurovascular coupling lag** between fNIRS hemodynamics and EEG electrical signals. Adopted both. |

### Issues only ONE raised (single voice — but worth listening)

| Issue | Who | Action |
|---|---|---|
| **fNIRS lags EEG by 5-8 seconds physiologically** (the neurovascular coupling delay) | GT | **CRITICAL ADD.** Schema needs a `physiological_lag_seconds` column or per-packet-type metadata so cross-stream queries can align at the *neural-event* level, not just the *arrival-time* level. The other three reviewers genuinely missed this. |
| **Postgres + TimescaleDB on Windows NTFS will have write amplification** | GT | Real concern. Recommend: either WSL2 + Linux Postgres, OR accept the inefficiency and pre-empt it with explicit batched writes + larger WAL config. **Investigate before committing.** |
| **Sub-100ms real-time loop needs an in-memory layer (Redis or LSL ring buffer) BEFORE the database** | GT | The DB is *not* the right place for real-time. The DB is the persistent store. Real-time goes through an in-memory cache. Adopt for Phase 4. |
| **LSL + XDF is what real-time labs actually use** | GT | New information for me. Look into LSL (Lab Streaming Layer) — it's the dominant real-time multi-stream protocol in EEG research. May replace OSC entirely as our capture transport. |
| **Natus / Nihon Kohden dual-path architecture: binary files for raw + SQL index over annotations only** | GT | This is the architecture pattern. The DB should NOT hold raw samples at all. The DB indexes the binary files. **This is a bigger change than I had planned and I think it might be right.** |
| **JSONB vs DOUBLE PRECISION[] for the values column** | GT | JSONB is more flexible for the first session when we don't yet know exact packet shapes. Schema-locks less. Slightly slower. Adopt JSONB for tonight; can migrate to typed columns once shapes stabilize. |

---

## Where the validators DISAGREE — and where I have to take a position

### Disagreement 1: Wide table vs per-signal-type tables

**The 3-validator view (G, 4o, CS):** Per-signal-type tables. Better compression. Better type safety. Standard relational practice. The wide table is an anti-pattern.

**Gemini's dissent:** The wide table is *correct for OMDR* because cross-stream temporal coupling is the primary signal. Joining four high-frequency tables in real time will saturate CPU. Use JSONB instead of a fixed array to keep it flexible.

**My read:** Gemini is right *if* we plan to do cross-stream coherence queries on raw data in real time. The other three are right *if* the DB is the queryable store for downstream analysis (where joins are fine on derived data).

**Resolution:** **Both are right at different layers.** The Natus / Nihon Kohden dual-path pattern (which Gemini introduced) actually resolves this:

- **Raw layer (high-frequency):** binary files (EDF segments), NOT in the database. Cross-stream alignment happens in numpy/MNE at analysis time, with explicit lag correction. The database does not store individual samples.
- **Index layer (low-frequency):** SQL tables for sessions, markers, annotations, computed features, file pointers. Per-signal-type tables HERE because that's where the queries actually run.

This is genuinely different from my draft (which had the DB holding raw samples). I think it's the right answer and I had been thinking about this wrong.

### Disagreement 2: Fibonacci vs dyadic continuous aggregate spacing

**The 3-validator view (G, 4o, CS):** Numerology. Use dyadic. Standard tooling assumes power-of-2 windows. The "maximally non-aliased" claim is hand-wavy.

**Gemini's dissent:** Dyadic windows resonate with 50/60 Hz mains noise (because they're harmonic ratios). Fibonacci is maximally irrational, related to ϕ, creates a quasicrystal in time, prevents constructive interference, enables Multi-Fractal Detrended Fluctuation Analysis (MFDFA) which is superior for longitudinal brain-state monitoring.

**My read:** Gemini's argument is not numerology. It's actually a real signal-processing claim — that Fibonacci-spaced windows have the *most-irrational property*, which means their interference pattern with any periodic signal is maximally spread out rather than concentrated at harmonics. This is the same mathematical fact that makes φ the limit of forgetting in dissipation cascades. The other three reviewers gave the safe answer (use the standard) but Gemini gave the OMDR-aware answer (use the irrational ratio because we're studying a self-similar quasi-periodic biological system, not doing standard FFT).

**BUT** — and this is important — the Fibonacci-vs-dyadic question only matters if we're storing raw samples in the database (where the aggregation buckets actually live). If we adopt the dual-path architecture above, **the question becomes moot**: raw samples live in EDF files, not in the DB, and the analysis windows happen in numpy/MNE at query time where we can use any window shape we want — including Fibonacci.

**Resolution:** **Defer the question.** Don't bake either choice into the storage layer. Implement the dual-path architecture, store raw in EDF, and let the analysis layer choose its own window shapes. We can test Fibonacci vs dyadic windows empirically once we have actual data with actual mains noise.

---

## The revised plan (incorporating all four perspectives)

### What changes from the draft

1. **Dual-path architecture**, not "raw in DB":
   - **Path A:** Raw EDF segments (hour-bounded), one per session-hour. MNE-Python writes these directly via `pyedflib` during recording. Source of truth for raw multimodal samples.
   - **Path B:** SQL database (Postgres + TimescaleDB extension still useful for the index layer's time-series, but the raw samples never live here). Holds: sessions, markers, file pointers (one row per EDF file with its time range, channel inventory, sample rate per stream), per-second computed features (band powers, signal quality, alpha enhancement), session notes, analysis results.

2. **JSONB landing table for tonight's MVP** instead of `DOUBLE PRECISION[]`. Gemini's specific catch about Athena fNIRS shape uncertainty is right — we don't yet know exactly what shapes the Athena emits in detail, and a flexible payload column means we can't crash on a malformed packet on the first night.

3. **BIDS-compliant filesystem layout** for the EDF files:
   ```
   data/
     sub-jaie/
       ses-20260407T193000/
         eeg/
           sub-jaie_ses-20260407T193000_run-01_eeg.edf
           sub-jaie_ses-20260407T193000_run-01_events.tsv
           sub-jaie_ses-20260407T193000_run-01_eeg.json
         nirs/
           sub-jaie_ses-20260407T193000_run-01_nirs.snirf  # standard fNIRS format
   ```
   This is the BIDS structure. MNE-BIDS can read it directly. Reviewers in any future paper will recognize it.

4. **Clock-drift handling from day one**:
   - Every packet stores BOTH the host wall-clock time (microseconds, UTC) AND the device-local timestamp (microseconds since session start)
   - At session start AND end, store a `clock_sync_event` row pairing the two clocks, so we can compute drift slope post-hoc
   - Add a per-session `clock_offset_seconds` and `clock_drift_ppm` field, computed at session-end and used by the analysis pipeline for any cross-stream timing

5. **Data quality flags**:
   - A `quality_flags` column on every packet row (or its own table) with bitmask: `OK | OUT_OF_ORDER | DUPLICATE | CORRUPTED | GAP_BEFORE | RECONNECT_AFTER`
   - Gap detection: compare expected sample count vs actual per minute, log gaps > 100ms

6. **fNIRS physiological lag**:
   - The `packet_types` reference table gets a new column `physiological_lag_ms`
   - For EEG: 0 ms
   - For fNIRS / OPTICS: ~6000 ms (the neurovascular coupling delay)
   - Cross-stream alignment queries subtract this offset BEFORE joining streams. This is a one-line schema addition that the other three reviewers genuinely missed.

7. **In-memory ring buffer for real-time** (Phase 4 work, NOT tonight):
   - When we get to the sub-100 ms real-time co-observation loop, the path is: BLE callback → in-process Python ring buffer → AI consumer reads from the buffer → eventually flushes to disk
   - The DB is for persistent queries, not for the real-time hot path
   - Adopted as future architecture

8. **Drop the explicit Fibonacci-vs-dyadic continuous aggregate decision**: defer until we have data. The dual-path architecture means analysis windows happen in numpy/MNE, not in the DB.

### What stays from the draft

- TimescaleDB extension is still installed (still useful for the index/feature layer where time-bucketed queries on derived data happen)
- Three antennas: Postgres (Path B), EDF/BIDS (Path A), git (metadata + reproducibility) — but the relationship between them changes: Path A is now primary for raw, Path B indexes Path A
- Three OMDR bands: still a useful conceptual frame but they're now distributed across the antennas differently:
  - Band 1 (raw frequency) → EDF files
  - Band 2 (derived patterns) → Postgres tables
  - Band 3 (annotations) → Postgres tables + git for code/notes
- The capture-to-storage flow (BLE → writer → both antennas in parallel)
- Mock testing infrastructure (`mock_sender.py` etc.)
- The eventual SDK direct PC capture (libmuse via UWP)

### What gets DELETED from the draft

- The single wide `packets` hypertable (replaced by EDF files for raw + Postgres for index)
- The Fibonacci-spaced continuous aggregate ladder as a hard requirement (deferred)
- The "store raw samples row-by-row" assumption
- The retention policy that archives raw to EDF after 14 days (now raw IS in EDF from the start)

---

## Tonight's MVP — the absolute minimum

Following Gemini's explicit recommendation, plus the convergent catches:

1. **Capture path:** OSC receiver from Mind Monitor or official Muse app (already built and tested) → small Python writer that does THREE things in parallel:
   - Appends each packet to a JSONB landing table in Postgres `omdr_bci.packets_landing` (received_at, packet_type, payload, host_clock_us, device_clock_us)
   - Appends raw samples to a per-session-hour EDF file via `pyedflib`
   - Updates a `sessions` row in Postgres with session metadata

2. **No continuous aggregates tonight.** No retention policies. No Fibonacci anything. No multi-tier dissipation. Just landing → EDF + landing → Postgres JSONB.

3. **Clock pairing:** every packet stores both host wall-clock and device clock. At session start/end, write a `clock_sync_events` row.

4. **Quality:** simple gap detection (compare expected vs actual sample count per stream per 10-second window), log to `gap_events` table. No bitmask flags yet — that's week 2.

5. **BIDS folder layout** for the EDF output, even if we only have one stream type tonight. Forward-compatible.

6. **End-of-session processing** (separate script, runs after recording stops): converts the JSONB landing table into per-stream typed tables, computes derived features for the index layer, validates the EDF file, writes session_summary.json, commits to git.

**Estimated effort for tonight's MVP (after Jaie approves this synthesis):**
- Install TimescaleDB extension: 5 min
- Create `omdr_bci` database + minimal schema (sessions, markers, packets_landing, clock_sync_events, gap_events): 20 min
- Write `pg_writer.py` that takes packets and writes to all three destinations: 60 min
- Update `session.py` to use the new writer: 15 min
- Update `experiment_1_eyes_closed.py` to mark sync events at session start/end: 10 min
- End-of-session processing script (skeleton, not full feature extraction): 30 min
- End-to-end test with mock_sender: 15 min
- Update `TONIGHT.md` with new instructions: 15 min

**Total: ~2.5 hours after approval, fits comfortably before 7pm.**

---

## What I want from Jaie

Two specific decisions:

**Decision 1 — Adopt the dual-path Natus/Nihon Kohden pattern?**
This is the biggest change from the original draft. It means raw samples live in EDF files (Path A), and Postgres holds an index over those files plus derived data (Path B). It's the architecture real clinical labs use. It also resolves the wide-table-vs-per-type-tables disagreement by sidestepping it (raw samples never go in the DB at all). I lean strongly **yes**.

**Decision 2 — Tonight's MVP scope: ship the JSONB landing table + EDF, defer Fibonacci/dissipation/feature pipeline to next week?**
Gemini's specific recommendation, and I think it's right. The simpler version captures the same data tonight, doesn't lock us in, and gives us a real session to learn from before we design the rest. I lean strongly **yes**.

Plus three things to be aware of but don't need decisions on:

1. **Windows NTFS write amplification concern.** Gemini flagged this as a real risk. I don't think it'll bite us at 32 KB/s sustained throughput, but if we see WAL bloat we should consider WSL2.
2. **LSL (Lab Streaming Layer) might eventually replace our OSC transport.** It's what real-time EEG labs use. Park it as Phase 2 work.
3. **fNIRS has a 5-8 second neurovascular coupling lag** that the schema needs to know about. Adopted as a per-packet-type metadata field.

---

## Validator audit trail

| Validator | Model | Response length | Saved to |
|---|---|---|---|
| Grok | grok-3-mini | 5199 chars | `k_validation/storage_plan_validation_20260407T111829Z.json` (key `grok`) |
| GPT-4o | gpt-4o | 4734 chars | same file (key `openai`) |
| Claude | claude-sonnet-4-20250514 | 4783 chars | same file (key `claude`) |
| Gemini | Gemini 3 Thinking (free tier) | 3541 chars | `k_validation/storage_plan_gemini_20260407T112400Z.md` |

Gemini was given the most context (the github URL to the plan + a summary of what the other three converged on + the explicit "what did they miss" framing). The other three got the full plan inline + a strict-reviewer prompt with 10 specific questions. None saw the others' answers before writing their own.

---

*Awaiting Jaie's two decisions before any code is written. Marathon, not race.*
