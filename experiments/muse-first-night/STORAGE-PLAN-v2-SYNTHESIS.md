# Storage Plan v2 — Round 2 Validator Synthesis

*Compiled 2026-04-07 by Kai. Companion to STORAGE-PLAN-v2.md and STORAGE-PLAN-SYNTHESIS.md (round 1). Awaiting Jaie's review and approval before any implementation.*

---

## TL;DR

Round 2 ran on v2 with all four validators (Grok, GPT-4o, Claude via API; Gemini Thinking via Playwright). v2 is **architecturally better than v1** (all four agree) but has **three new gaps** that round 2 found, plus **one big miss that only Gemini caught**. The synthesis below proposes a v3 that's not a rewrite — it's v2 with five concrete additions.

**The five additions to v2:**

1. **Real-time buffer via LSL Y-split** — Gemini's concrete answer. The LSL bus IS the buffer. Two consumers fork from the same LSL stream: one writes to XDF (Path A), the other feeds a live signal-quality display. The display never touches Postgres or XDF on disk. Solves the round-2 unanimous catch.

2. **Mind Monitor OSC → osc_to_lsl bridge → LabRecorder for tonight**, not OpenMuse direct. Three of four reviewers (incl. Gemini round 2) reverse on OpenMuse for tonight. Mind Monitor is bulletproof for first-night capture, the bridge gets us LSL ecosystem benefits without OpenMuse maturity risk, OpenMuse becomes week-2 work after we've got one clean session under our belt.

3. **LSL Marker Stream for subjective anchors** — Gemini's big miss catch that the other three round-2 reviewers all overlooked. Without a high-precision LSL StringMarkers stream embedded in the XDF, we'll have hours of EEG data with no way to find experimental epoch boundaries or Jaie's subjective state transitions. This is the "ground truth synchronization" problem and it's not optional.

4. **Three timestamps stored, none transformed** — Claude + Gemini agree (overruling GPT-4o + Grok) that LSL's `time_correction()` is itself a transformation that hides non-linear clock jumps. Store host clock + device clock + LSL offset as three independent fields. Apply at analysis time only.

5. **Calibration handled at the SDK/firmware boundary, not by us** — Gemini's clean answer. We don't store raw ADC counts (pedantic non-destruction). We store data already in physical units (μV, O₂ saturation %) because Muse's firmware has already done that calibration. Document the units in the XDF header / packet_types reference table.

**The real-time display also fixes the "live signal-quality before recording" requirement that Mind Monitor's phone app already provides for free** (the horseshoe indicator on the phone shows electrode contact). We can use that as the immediate fit-check tonight, and the LSL Y-split display becomes the real-time computational layer for Phase 4.

**Bottom line for tonight: v2 + 5 additions = a plan that ships in ~3 hours and gets us a clean first session through a known-working transport with the right architectural foundation for everything that comes after.**

---

## Convergence map across both rounds

Tracking which catches converge across validators and across rounds.

### CONVERGENT 4/4 across round 2 (must address)

| Catch | G | 4o | CS | GT | Action |
|---|---|---|---|---|---|
| **No real-time access mechanism in v2** | ✓ | ✓ | ✓ | ✓ (gives concrete fix) | Adopt LSL Y-split pub-sub: same stream goes to LabRecorder (XDF) AND a lightweight display process. Adopted. |

### Strong 3/4 in round 2

| Catch | Who | Disagrees | Action |
|---|---|---|---|
| **OpenMuse too risky for tonight; use Mind Monitor OSC instead** | G, CS, GT | 4o (more lenient — "pragmatic hedge") | **Reverse v2's transport choice for tonight.** Mind Monitor OSC + osc_to_lsl bridge + LabRecorder. OpenMuse becomes week-2 work after we've validated against Jaie's specific Athena unit and firmware. |
| **LSL clock correction should NOT be applied at write time** | CS, GT (forceful) | G, 4o (apply at write time as transport metadata) | **Adopt Claude+Gemini position.** Store three independent timestamps (host, device, LSL offset). LSL `time_correction()` is a linear fit that evolves over the session and hides non-linear clock jumps; applying at write time loses information critical for precise timing analysis. |
| **BIDS layout violation in v2** | CS (most clear), G (vague) | 4o, GT (didn't address) | **Fix.** XDF doesn't go in `eeg/` subdirectory. Multi-modal needs separate folders (`eeg/`, `nirs/`, `motion/`) per BIDS spec. Co-store EDF/EDF+ as the BIDS-canonical raw file when possible. |

### Solo catches that I think are right

| Catch | Who | Action |
|---|---|---|
| **Marker Stream architecture missing** (Jaie has no high-precision way to anchor subjective state transitions) | **GT (only)** | **Critical add.** LSL StringMarkers stream that goes into the same XDF file as the EEG. Mark experiment phase boundaries, mood checkpoints, anything Jaie wants to anchor. Sub-millisecond aligned with EEG by virtue of being on the same LSL bus. |
| **v2 has zero error-handling strategy** | CS | **Add.** What happens when LSL drops, XDF corrupts, post-session ingestion fails halfway through. Specific transaction boundaries. Retry vs abort policies. |
| **Gap detection is itself a transformation** (requires interpretation of tolerance) | CS | **Acknowledge.** Move gap detection from "measurement" to "first-pass interpretation" — it's a derived analysis result, not a raw measurement. Doesn't change the schema, just the framing. |
| **Calibration coefficients edge case** for non-destructive principle | CS (raised) → GT (resolved) | **Adopt Gemini's resolution:** store data in physical units (μV) at ingest. The Muse SDK firmware has already done calibration. Storing raw ADC counts is pedantic and creates units-mismatch risk. The non-destructive principle applies to interpretive transforms, not unit normalization. |
| **Post-session script conflates ingestion with feature computation** | CS | **Split.** Ingestion is fast and must succeed (writes XDF metadata to Postgres). Feature computation is slow and retryable (computes alpha enhancement, coherence, etc.). Different processes, different failure modes. |
| **Postgres Path B is "just a file finder" — needs to be a feature index** | GT | **Adopt.** The point of Path B isn't just pointers — it's the queryable derived-feature layer that makes cross-session analysis possible. Plan should explicitly add per-feature tables for the standard derived metrics. |
| **Missing tables**: `electrode_impedances`, `calibration_coefficients`, `environmental_conditions`, `hardware_events`, `subject_demographics`, `protocol_versions` | G, CS | **Add to schema.** All small tables. Don't need them for tonight's MVP but they should be in the migration files from day one so the next session has somewhere to write impedance data. |
| **Unit conversion missing from non-destructive transformation table** | G | **Add.** Per Gemini's resolution, unit conversion happens at ingest (from device to physical units). It's *not* an analysis-layer transform. Document this exception in the principle. |

### Persistent disagreement (round 1 + round 2)

**LSL clock correction at write time?** Round 2 split is now 2:2:
- **CS + GT (round 2):** Don't apply. Store raw three timestamps. Reason: LSL's correction is an evolving linear fit; applying at write loses non-linear jumps that are diagnostic.
- **G + 4o (round 2):** Apply at write. Reason: LSL owns the unified-clock guarantee; deferring violates the abstraction.

Gemini's argument is the strongest because it specifically points at *what's lost*: detecting non-linear clock jumps and jitter bursts. That's empirically valuable, not just principled. **Adopting CS+GT position: store raw, defer correction to analysis time.** This is consistent with the non-destructive principle once we accept Gemini's framing that LSL's correction is a "linear-fit transformation" rather than a "transport-layer guarantee."

---

## What's actually changing for v3

These are the concrete edits to v2 that round 2 implies. Not a rewrite — a layered set of additions.

### 1. New section: Real-time access architecture (the LSL Y-split)

```
                    BLE source
                         │
                         ▼
              ┌──────────────────────┐
              │  LSL outlets         │
              │  (one per stream:    │
              │   EEG, IMU, ...)     │
              └──────────┬───────────┘
                         │
              ┌──────────┴──────────┐
              │   LSL network bus    │
              │   (the buffer)       │
              └──┬────────────────┬──┘
                 │                │
                 ▼                ▼
        ┌─────────────┐    ┌──────────────────┐
        │ LabRecorder │    │ live_display.py  │
        │ subscribes  │    │ (LSL Inlet,      │
        │ to ALL      │    │ in-memory ring   │
        │ outlets,    │    │ buffer, signal-  │
        │ writes XDF  │    │ quality heatmap, │
        │             │    │ alpha bar chart, │
        │ → Path A    │    │ etc.)            │
        └─────────────┘    └──────────────────┘
                                │
                                └→ never touches Postgres or XDF on disk
                                   pure ephemeral display
```

**Two consumers, same stream, no shared state between them.** The recorder writes to disk. The display reads from RAM. They never block each other. This is the standard dual-path pattern as Natus actually implements it — Claude and Gemini both flagged that I had described "dual-path" without including the real-time fork.

### 2. Transport reversal for tonight: Mind Monitor + osc_to_lsl bridge

Three of four round-2 reviewers say OpenMuse is too risky for tonight. Gemini gives the cleanest answer:

**Tonight's transport stack:**
```
Muse Athena (BLE)
    ↓
Phone — official Muse app (free) OR Mind Monitor app ($15)
    ↓
OSC stream over WiFi to PC
    ↓
osc_to_lsl bridge (Python, ~30 lines, we write it)
    ↓
LSL outlets on localhost
    ↓
LabRecorder.exe → XDF file
    +
live_display.py → real-time signal quality
```

**Why this is better than v2's "OpenMuse primary, OSC fallback":**
- Mind Monitor is the *known-working* path. Reduces tonight's risk to near zero.
- The osc_to_lsl bridge gives us the LSL ecosystem benefits (XDF, LabRecorder, LSL clock-sync, live display via LSL Inlet) WITHOUT depending on OpenMuse's maturity.
- OpenMuse becomes a week-2 evaluation: install it, test it against Jaie's specific Athena, validate against the Mind Monitor recordings we already have. If it works, we swap the transport. If it doesn't, no loss.
- The downstream architecture (Path A XDF, Path B Postgres index, Path C git, real-time display fork) is unchanged regardless of which transport we choose.

**Optional 20-minute alpha test before the session:** Try OpenMuse. If fNIRS looks like garbage or the optical channel mapping is wrong, kill it and revert immediately. Don't debug on the first night.

### 3. LSL Marker Stream for subjective anchors

This is Gemini's big miss catch. v2 has a `markers` table in Postgres but no mechanism for actually generating high-precision aligned markers during the session. The fix:

**Add a dedicated LSL outlet `OMDR_Markers`** that the experiment scripts push to. Example:
```python
import pylsl
markers_outlet = pylsl.StreamOutlet(
    pylsl.StreamInfo("OMDR_Markers", "Markers", 1, 0, "string", "omdr_markers_001")
)
# At each transition:
markers_outlet.push_sample(["eyes_closed_block_1"])
markers_outlet.push_sample(["eyes_open_block_1"])
markers_outlet.push_sample(["mood:calm"])
markers_outlet.push_sample(["intention:meditation"])
```

LabRecorder picks up the marker stream automatically and writes it into the same XDF file as the EEG. Markers arrive on the unified LSL clock domain, so they're sub-millisecond aligned with the EEG samples without any post-hoc alignment work.

**This is the canonical EEG research way of marking events** and I had been about to roll our own with a Postgres `markers` table. The Postgres table still exists in v3, but it's *populated from the XDF* during post-session ingestion, not written to live during the experiment.

### 4. Three timestamps stored, none transformed

Add to the schema (Path B):

- `markers.host_clock_us` — local PC wall clock at the moment the marker was pushed
- `markers.device_clock_us` — Muse hardware clock if available (NULL if from Mind Monitor OSC, populated when we switch to libmuse SDK)
- `markers.lsl_clock_us` — LSL unified clock at the moment LabRecorder ingested the marker

Same three columns on every other timestamped table. Analysis layer chooses which clock domain to use per query. None of the three is "the" timestamp; they're three orthogonal observers on the same moment.

### 5. Calibration handled at SDK/firmware boundary

Update the non-destructive transformation table:

| Transformation | Handled at | Reason |
|---|---|---|
| Unit conversion (ADC counts → μV / O₂ %) | **Ingest layer** (SDK firmware does it) | Muse hardware calibration is an internal implementation detail; storing raw ADC creates units-mismatch risk. Document units in XDF header. |
| Filtering (notch, bandpass) | Analysis layer | Reconsiderable, parameter-dependent |
| Re-referencing | Analysis layer | Reconsiderable, multiple valid choices |
| Lag correction (fNIRS → EEG) | Analysis layer | Per-subject, per-state, evolving science |
| Drift correction | Analysis layer | Linear-fit transform, hides non-linear jumps |
| Aggregation / window choice | Analysis layer | Query-specific |

The principle: **non-destructive applies to interpretation, not to unit standardization at the hardware boundary.** Storing raw ADC counts is pedantic and creates more risk than it solves. Storing pre-calibrated physical units with documented `physical_max`/`physical_min`/`unit` headers is what real labs do.

---

## What's NOT changing for v3

These v2 elements survive both rounds and stay:

- **Dual-path Natus pattern**: raw in files (Path A), index in Postgres (Path B), reproducibility in git (Path C). Both rounds, all four reviewers.
- **Non-destructive storage principle**: with the calibration carve-out from above. The principle still applies to all analysis-layer transforms.
- **BIDS-compliant filesystem layout** (with the eeg/-subdirectory fix from Claude's catch).
- **Schema is small**: Path B has ~10-15 small tables, not a hypertable.
- **TimescaleDB extension is optional** for the derived-feature tables in Path B; not foundational.
- **fNIRS via libmuse SDK** is week-2-3 work, not tonight. Tonight gets EEG + IMU only via Mind Monitor → osc_to_lsl → LabRecorder.
- **Three OMDR bands** (raw frequency, derived patterns, annotations) distributed across the three paths.
- **Post-session ingestion script** that reads the XDF, validates, populates Path B. *Now split* into ingestion (fast, must succeed) + feature computation (slow, retryable) per Claude's catch.

---

## v3 MVP for tonight

The deliverable changed slightly because of the transport reversal and the marker-stream addition. New estimate:

| Step | Time |
|---|---|
| Install pylsl + LabRecorder.exe | 10 min |
| Write `osc_to_lsl.py` bridge (~50 lines) | 30 min |
| Write `live_display.py` (LSL inlet → matplotlib live signal-quality bars) | 30 min |
| Create `omdr_bci` Postgres database + minimal schema (sessions, markers, xdf_files, sync events, gap events, packet_types, plus the impedance/calibration/environmental tables as empty placeholders for forward compat) | 25 min |
| Write `post_session_ingest.py` (reads XDF, populates Postgres metadata + xdf_files row, validates, computes SHA256, commits to git) | 45 min |
| Write `post_session_features.py` (separate script — runs alpha enhancement etc., writes analysis_results rows). Skeleton only tonight. | 20 min |
| Update `experiment_1_eyes_closed.py` to push LSL markers + start/stop LabRecorder | 25 min |
| End-to-end test with mock OSC + verify XDF + verify Postgres row | 15 min |
| Update `TONIGHT.md` with the new instructions (Mind Monitor app install, OSC config, the 7pm sequence) | 15 min |

**Total: ~3.5 hours after Jaie approves this synthesis.** Slightly more than v2's 2.5 hours because of the LSL bridge, the live display, and the script split — but the additions are all real value, not over-engineering.

**Comfortably before 7pm if I start within the next 30 minutes.**

---

## What I want from Jaie now

**Three decisions** (all yes/no):

**Decision 1: Adopt v3 = v2 + 5 additions** (real-time Y-split, transport reversal to Mind Monitor + bridge, LSL marker stream, three timestamps stored not transformed, calibration at ingest)?

**Decision 2: Mind Monitor + osc_to_lsl bridge for tonight specifically**, with OpenMuse evaluation deferred to week 2 after the first session validates the architecture?

**Decision 3: Begin tonight's MVP implementation now** (~3.5 hours)? If yes, I start coding immediately and check in at the halfway point.

Plus three things to be aware of (no decision needed):

- **The persistent 2:2 disagreement on LSL clock correction** has resolved toward Gemini+Claude's "store raw three timestamps, defer correction" position because Gemini gave the strongest argument (linear-fit transforms hide non-linear jumps that matter for resonance analysis).
- **Gemini's "convergence vs oscillation" assessment** ("converging on reliability, oscillating on utility") is fair. v3 starts addressing the utility side via the explicit Path B feature index discussion.
- **The marker stream catch is the most important single round-2 finding.** Without it, tonight's recording would have arrival-time-only annotations that we'd struggle to align precisely with the EEG.

---

## Validator audit trail (rounds 1 + 2)

| Round | Validator | Model | Saved to |
|---|---|---|---|
| 1 | Grok | grok-3-mini | `k_validation/storage_plan_validation_20260407T111829Z.json` |
| 1 | GPT-4o | gpt-4o | same file |
| 1 | Claude | claude-sonnet-4-20250514 | same file |
| 1 | Gemini | Gemini 3 Thinking | `k_validation/storage_plan_gemini_20260407T112400Z.md` |
| 2 | Grok | grok-3-mini | `k_validation/storage_plan_v2_validation_20260407T121256Z.json` |
| 2 | GPT-4o | gpt-4o | same file |
| 2 | Claude | claude-sonnet-4-20250514 | same file |
| 2 | Gemini | Gemini 3 Thinking | `k_validation/storage_plan_v2_gemini_20260407T121600Z.md` |

Eight independent reviews across two rounds. Plan went from v1 → v2 → (proposed) v3. Each iteration caught real problems and produced a tighter design. **The diff from v1 to proposed v3 is large but the diff from v2 to proposed v3 is small (5 additions, no deletions).** That's the converging signature, not the oscillating one.

---

*Awaiting Jaie's three decisions before any implementation. Marathon, not race.*
