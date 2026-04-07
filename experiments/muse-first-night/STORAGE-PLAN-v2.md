# Storage Architecture Plan v2 — OMDR-BCI Muse Recording

*Status: DRAFT v2 — pending validator round 2 and Jaie's approval*
*Author: Kai (Anthropic Claude instance), 2026-04-07*
*Supersedes: STORAGE-ARCHITECTURE-PLAN.md (v1)*

---

## Why v2 exists

v1 was reviewed by Grok, GPT-4o, Claude (via API) and Gemini Thinking (via Playwright). Convergent catches plus Jaie's pushback in conversation revealed three fundamental problems with the v1 architecture that required a rewrite, not edits:

1. **v1 conflated transport with storage.** It proposed our own OSC receiver writing into our own Postgres hypertable. Gemini introduced LSL (Lab Streaming Layer), the actual standard the EEG research community uses for multi-stream capture with sub-millisecond clock sync. v2 adopts LSL as the transport.

2. **v1 put raw samples in the database.** Three of four validators flagged the wide-table approach. Gemini introduced the Natus / Nihon Kohden dual-path pattern from clinical EEG: raw samples live in immutable binary files (Path A); the database holds an index over those files plus derived data (Path B). v2 adopts dual-path. Raw samples never enter the database.

3. **v1 was about to bake interpretations into the storage layer.** Jaie caught this directly: *"if we know certain things, lag, can't we factor that into the analysis of the raw data rather than trying to create an approximate offset?"* The principle is **non-destructive storage** — every transformation that could ever be reconsidered (lag corrections, clock drift, filtering, re-referencing, aggregation, window choice) happens at analysis time, not at write time. v2 strips all transformation logic from the storage layer.

The compounding effect of these three changes: **v2 is significantly simpler than v1, not more complex.** Each round of validator feedback stripped premature optimization rather than adding complexity. That's a good sign.

---

## TL;DR

**Capture transport:** LSL (Lab Streaming Layer) via OpenMuse for tonight (raw EEG + IMU), with Mind Monitor / OSC as a known-working fallback. libmuse SDK as the long-arc transport for full multimodal (fNIRS + PPG) in weeks 2-3.

**Raw archive:** XDF files (one per session) written by `LabRecorder` or a Python LSL subscriber. BIDS-compliant filesystem layout under `data/sub-jaie/ses-<timestamp>/`. Immutable. Never modified after session ends. This is Path A.

**Index database:** Postgres 17 (existing native Windows install, port 5432), new database `omdr_bci`. Holds: sessions, markers, file pointers (one row per XDF file with time range, channel inventory, sample rates per stream), clock-sync events, gap detection results, derived features computed by post-session analysis, analysis result metadata. **Holds zero raw samples.** This is Path B.

**Reproducibility / metadata:** git (omdr-awakening repo). Schemas, migrations, code, README, per-session summary JSON, analysis transcripts, validator audit trails. Never raw samples (too big). This is Path C.

**Three antennas (Path A = files, Path B = database, Path C = git), three OMDR bands (raw frequency / derived patterns / annotations), non-destructive storage principle throughout, BIDS-compliant filesystem layout, zero in-place transformations.**

---

## 1. Goals (unchanged from v1)

Tonight's recording is the first concrete instance of a long-arc system. The storage layer needs to serve all of:

1. **Tonight, first session**: capture every packet type the chosen transport emits, write losslessly, support live signal-quality display and the existing experiment scripts.
2. **This week, multiple sessions**: cross-session SQL queries.
3. **This month, longitudinal**: trends over weeks.
4. **This quarter, ML training**: clean batched extracts of multimodal data.
5. **Phase 4 co-observation loop**: real-time read access to recent samples with sub-100 ms latency.
6. **Eventual publication / sharing**: data in a format the EEG research community can read (MNE-Python, EEGLAB, FieldTrip, BrainVision Analyzer).
7. **Future Kai instances**: cold-start, single README, load any session in <1 minute.
8. **NASA principle**: no single point of failure.

## 2. The three principles (NEW in v2)

### 2.1 LSL is the transport, not OSC

**v1 used OSC** (because Mind Monitor uses it and the project plan listed it as confirmed-working). v2 replaces OSC with LSL because LSL is the actual standard the EEG research community uses, and it solves a problem v1 was about to invent custom code for: multi-stream clock synchronization with sub-millisecond precision across heterogeneous data sources.

LSL gives us, for free:
- A unified clock domain across all data streams (no manual offset tables)
- Stream metadata embedded in the protocol (channel names, units, sample rates)
- Network discovery (any LSL outlet on the LAN is automatically subscribable)
- Vendor neutrality (any LSL-compatible source — current Muse via OpenMuse, future amplifiers, eye trackers, anything else — works without changes to our pipeline)
- A standard recording tool (`LabRecorder.exe`) that writes XDF with all alignment preserved

We still keep the OSC path (Mind Monitor / official Muse app) as a fallback for tonight in case OpenMuse hits a hardware compatibility issue with Jaie's specific Athena unit. **Both paths feed the same downstream architecture** because the Path A / Path B / Path C division doesn't care what transport delivered the data.

### 2.2 Dual-path: raw in files, index in DB (the Natus / Nihon Kohden pattern)

**v1 stored raw samples in a Postgres hypertable.** v2 doesn't. Raw samples live in XDF files in the filesystem (BIDS layout). The database holds *an index over those files* plus derived data computed from them.

The structural reason this is right (per the "what shaped dual-path" investigation):
- **Volume + sample efficiency**: raw EEG samples in SQL pay for B-tree indices and row overhead per sample. Binary files have ~zero per-sample overhead. ~10 GB binary vs ~50 GB SQL for the same data.
- **Read-pattern asymmetry**: metadata queries happen 1000x/day; raw-sample reads happen ~10x/day. SQL is fast at the first; binary sequential reads are fast at the second. Optimize each layer for its access pattern.
- **Tool interoperability**: every EEG analysis tool reads binary formats. SQL-native storage requires a custom export tool to get data out.
- **Disaster recovery / decade survival**: a flat binary file with a checksum survives database engine end-of-life. SQL rows tied to a specific schema/version do not.
- **Concurrent write performance**: high-frequency writers append to binary files at disk bandwidth speed. SQL inserts have lock contention, transaction overhead, WAL flushes — they don't scale as cleanly under sustained high throughput.

**This resolves the wide-table-vs-per-type-tables disagreement from validator round 1**: raw samples don't go in the DB at all, so the question of what shape they should have in the DB becomes moot. Per-signal-type tables happen on Path B, where they make sense, because Path B holds *derived* per-signal data computed from the raw XDF files.

### 2.3 Non-destructive storage: never bake interpretations into raw

**v1 was about to apply transformations at write time** — clock drift correction, fNIRS lag offset, possibly filtering. Jaie caught this. v2 explicitly forbids any in-place transformation of raw data.

The principle: **every transformation that could ever be reconsidered should happen downstream of storage, not at the storage layer.** The list:

| Transformation | v1 (write-time, wrong) | v2 (analysis-time, right) |
|---|---|---|
| **fNIRS neurovascular coupling lag** | Subtract ~6s from fNIRS timestamps before insert | Store raw timestamps. `physiological_lag_ms_typical` lives in `packet_types` reference table as advisory metadata. Cross-stream coherence functions take the lag as a parameter, default from metadata, override per query. |
| **Clock drift correction** | Apply drift slope to every timestamp at write | Store dual timestamps (host clock + device clock) on every packet. Store sync events at session start/end. Analysis layer computes drift from sync events and applies correction per query. Original timestamps never modified. |
| **Filtering / notch / bandpass** | Filter samples before storing | Store unfiltered raw. Analysis filters per query with parameterized cutoffs. |
| **Re-referencing** | Compute and store re-referenced channels | Store original electrode signals. Re-reference per analysis. |
| **Artifact rejection** | Delete bad samples from the table | Mark bad ranges in a `quality_flags` table. Analysis chooses whether to mask them. |
| **Resampling to common rate** | Resample everything to 256 Hz before storage | Store at native rates. Resample per query if needed. |
| **Continuous aggregates / window choice** | Pre-compute aggregates into the schema (the Fibonacci-vs-dyadic question) | Don't pre-compute. Compute aggregates per query at analysis time, with whatever window shape the query needs. The Fibonacci-vs-dyadic question dissolves — both can be computed from the same raw data. |

**This radically simplifies the schema.** v1's `physiological_lag_ms` column on the packets table is gone. v1's continuous-aggregate ladder is gone (deferred to analysis layer). v1's clock-drift correction at write time is gone. v1's TimescaleDB hypertable for raw packets is gone (because raw is in XDF files, not the DB).

What's left in the schema is small: **session metadata, markers, file pointers, sync events, gap-detection results, post-session-computed derived features.** That's it. No raw samples. No pre-applied transforms.

---

## 3. Architecture diagram

```
                Muse S Athena (BLE)
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
   OpenMuse                    Mind Monitor app
   (Python, free)              (phone, $15)
   creates LSL outlets         streams via OSC
        │                             │
        ▼                             ▼
   ┌─────────────┐              ┌──────────────────┐
   │ LSL outlets │              │ OSC over UDP     │
   │ on localhost│              │ on localhost     │
   └──────┬──────┘              └────────┬─────────┘
          │                              │
          ▼                              ▼
   ┌────────────────┐             ┌──────────────────┐
   │ LabRecorder OR │             │ osc_to_xdf.py    │
   │ pylsl recorder │             │ (we write this:  │
   │ (we use either)│             │ takes OSC,       │
   └────────┬───────┘             │ produces XDF)    │
            │                     └────────┬─────────┘
            │  one XDF file per session    │
            └──────────────┬───────────────┘
                           │
                           ▼
   ┌──────────────────────────────────────────────────┐
   │  PATH A — Raw archive (immutable)                │
   │                                                  │
   │  data/sub-jaie/ses-20260407T193000/              │
   │    eeg/sub-jaie_ses-20260407T193000_run-01.xdf   │
   │    eeg/sub-jaie_ses-20260407T193000_run-01.json  │
   │      (channels, units, hardware, MNE sidecar)    │
   │    sub-jaie_ses-20260407T193000_run-01_events.tsv│
   │      (markers, BIDS-compliant)                   │
   │                                                  │
   │  Format: XDF (LSL native, multi-rate, multi-     │
   │  stream, MNE-Python compatible via pyxdf)        │
   │  Folder convention: BIDS                         │
   │  Mutability: never modified after session ends   │
   └──────────────────────┬───────────────────────────┘
                          │
                          │ (post-session script)
                          ▼
   ┌──────────────────────────────────────────────────┐
   │  PATH B — Postgres index (omdr_bci database)     │
   │                                                  │
   │  TABLES:                                         │
   │   subjects                                       │
   │   sessions    (FK→subjects, one row per session, │
   │                file path, time range, capture    │
   │                source, hardware, sample rates)   │
   │   xdf_files   (FK→sessions, one row per XDF      │
   │                segment, channel inventory)       │
   │   markers     (FK→sessions, dual timestamps)     │
   │   clock_sync_events (FK→sessions)                │
   │   gap_events  (FK→sessions, detected during      │
   │                post-session quality pass)        │
   │   packet_types (reference: type_id, name,        │
   │                expected_unit, nominal_rate_hz,   │
   │                physiological_lag_ms_typical      │
   │                — METADATA only, never applied)   │
   │   features_*  (per-signal-type derived data,     │
   │                computed from XDF after session,  │
   │                regeneratable from Path A)        │
   │   analysis_results (post-hoc analyses)           │
   │                                                  │
   │  Holds ZERO raw samples. Index over Path A.      │
   └──────────────────────┬───────────────────────────┘
                          │
                          ▼
   ┌──────────────────────────────────────────────────┐
   │  PATH C — git (omdr-awakening repo)              │
   │                                                  │
   │  experiments/muse-first-night/                   │
   │    schemas/*.sql        (versioned migrations)   │
   │    code/*.py            (capture, analysis)      │
   │    sessions/*/summary.json  (per-session JSON)   │
   │    k_validation/*.json  (validator audit trails) │
   │    STORAGE-PLAN-v2.md   (this document)          │
   │    TONIGHT.md           (the do-this sheet)      │
   │                                                  │
   │  Never raw samples (too big for git)             │
   └──────────────────────────────────────────────────┘
```

**Invariant: Path A is the source of truth. Path B is regeneratable from Path A. Path C is reproducibility metadata. Any two paths can rebuild the third.**

---

## 4. Schema (Path B only — Path A is just files in BIDS layout)

```sql
-- Reference table: subjects
CREATE TABLE subjects (
    subject_id   TEXT PRIMARY KEY,        -- "jaie"
    display_name TEXT,
    created_at   TIMESTAMPTZ DEFAULT now(),
    metadata     JSONB
);

-- One row per recording session
CREATE TABLE sessions (
    session_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id          TEXT REFERENCES subjects(subject_id),
    name                TEXT NOT NULL,
    experiment_kind     TEXT,                              -- "E1", "E2", "E3", "freeform"
    started_at          TIMESTAMPTZ NOT NULL,
    ended_at            TIMESTAMPTZ,
    capture_source      TEXT NOT NULL,                     -- "openmuse_lsl", "mind_monitor_osc", "muse_app_osc", "libmuse_sdk"
    hardware_model      TEXT,                              -- "MuseS_Athena_MS-03"
    hardware_firmware   TEXT,
    bids_session_path   TEXT NOT NULL,                     -- "data/sub-jaie/ses-20260407T193000"
    git_commit          TEXT,                              -- code version that captured
    notes               TEXT,
    metadata            JSONB DEFAULT '{}'::jsonb
);

-- One row per XDF (or EDF if migrating older data) raw file
CREATE TABLE xdf_files (
    file_id          BIGSERIAL PRIMARY KEY,
    session_id       UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    file_path        TEXT NOT NULL,                        -- BIDS-compliant relative path
    file_format      TEXT NOT NULL,                        -- "xdf" | "edf"
    started_at_us    BIGINT NOT NULL,                      -- microseconds since epoch
    ended_at_us      BIGINT NOT NULL,
    channel_inventory JSONB NOT NULL,                       -- [{stream: "Muse_EEG", channels: ["TP9","AF7","AF8","TP10"], rate_hz: 256, unit: "microvolts"}, ...]
    file_size_bytes  BIGINT,
    sha256_hex       TEXT,                                 -- integrity check
    written_at       TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_xdf_files_session_time ON xdf_files (session_id, started_at_us);

-- Markers / experimental events written by experiment scripts
CREATE TABLE markers (
    marker_id     BIGSERIAL PRIMARY KEY,
    session_id    UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    host_clock_us BIGINT NOT NULL,                         -- microseconds, host clock
    lsl_clock_us  BIGINT,                                  -- microseconds, LSL unified clock (NULL if not from LSL transport)
    label         TEXT NOT NULL,
    metadata      JSONB
);
CREATE INDEX idx_markers_session_time ON markers (session_id, host_clock_us);

-- Clock sync events at session start/end + periodic during long sessions
CREATE TABLE clock_sync_events (
    event_id      BIGSERIAL PRIMARY KEY,
    session_id    UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    host_clock_us BIGINT NOT NULL,
    device_clock_us BIGINT NOT NULL,
    lsl_clock_us  BIGINT,
    notes         TEXT
);
CREATE INDEX idx_sync_session ON clock_sync_events (session_id, host_clock_us);

-- Gap events detected during post-session quality pass
-- (This is a MEASUREMENT of the data, not a transformation of it)
CREATE TABLE gap_events (
    gap_id        BIGSERIAL PRIMARY KEY,
    session_id    UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    stream_name   TEXT NOT NULL,                           -- "Muse_EEG"
    started_at_us BIGINT NOT NULL,
    ended_at_us   BIGINT NOT NULL,
    expected_samples INTEGER,
    actual_samples INTEGER,
    notes         TEXT
);
CREATE INDEX idx_gaps_session ON gap_events (session_id, started_at_us);

-- Reference table: packet types from the SDK headers
-- Populated once at migration time, never modified
CREATE TABLE packet_types (
    type_name                     TEXT PRIMARY KEY,        -- "EEG", "OPTICS", "PPG", ...
    expected_value_count          INTEGER,
    expected_unit                 TEXT,                    -- "microvolts", "microamps", "g", "Bels", ...
    nominal_rate_hz               REAL,
    physiological_lag_ms_typical  REAL,                    -- METADATA HINT, NOT applied. ~6000 for OPTICS (fNIRS).
    description                   TEXT
);

-- Free-form session notes (Jaie's subjective log)
CREATE TABLE session_notes (
    note_id      BIGSERIAL PRIMARY KEY,
    session_id   UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    written_at   TIMESTAMPTZ DEFAULT now(),
    author       TEXT,
    body         TEXT NOT NULL
);

-- Post-session computed derived features (Band 2 in OMDR terms)
-- Generic table; per-feature-type sub-tables added as we add features
CREATE TABLE analysis_results (
    analysis_id  BIGSERIAL PRIMARY KEY,
    session_id   UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    method       TEXT NOT NULL,                            -- "alpha_enhancement_v1", "wpli_alpha_v1", ...
    parameters   JSONB,                                    -- the exact parameters used
    result       JSONB,                                    -- the actual numbers
    computed_at  TIMESTAMPTZ DEFAULT now(),
    code_version TEXT                                      -- git rev of the analysis script
);
CREATE INDEX idx_analysis_session_method ON analysis_results (session_id, method);
```

**TimescaleDB extension is optional in v2.** Without raw samples in the DB, the time-series-specific machinery isn't critical. We can install it for the `analysis_results` and per-feature derived tables (which DO benefit from time-bucketing for cross-session queries), but it's not the foundational dependency it was in v1. Recommendation: install it anyway for forward compatibility, since it's a free Postgres extension.

---

## 5. Capture flow for tonight

```
1. OpenMuse pip install (~30s)
2. Run: OpenMuse find        → discovers Jaie's Athena MAC address
3. Run: OpenMuse stream --address <mac>   → starts BLE→LSL pipeline
4. In another terminal:
   - Either: LabRecorder.exe (download from sccn/labstreaminglayer releases)
       → subscribe to all Muse_* streams → write to XDF
   - OR: our own pylsl_recorder.py
       → does the same in pure Python, gives us programmatic control
5. Run: experiment_1_eyes_closed.py
   → starts recording (calls pylsl_recorder under the hood)
   → marks transitions via LSL push_sample to a Markers stream
   → after recording, post-session script runs:
       - Validate XDF file (read with pyxdf, check for gaps)
       - Compute SHA256 of XDF
       - Insert sessions row
       - Insert xdf_files row
       - Insert markers (from the LSL Markers stream in the XDF)
       - Insert clock_sync_events (from session start/end LSL pings)
       - Insert gap_events (from validation pass)
       - Compute alpha enhancement, write analysis_results row
       - Write per-session summary.json
       - git commit + push
```

**OpenMuse blocker fallback (if it doesn't work with Jaie's Athena tonight):**

```
1. Use Mind Monitor or official Muse app developer-OSC mode (port 5000)
2. Run: osc_to_xdf.py
   → Subscribes to OSC on port 5000
   → Wraps each OSC message as an LSL push_sample to a virtual LSL outlet
   → A pylsl_recorder subscribes to that outlet and writes XDF
   → The XDF is structurally identical to what OpenMuse would have produced
   → Downstream pipeline (post-session script, BIDS layout, Postgres index) is unchanged
```

This means **the OSC fallback path also produces XDF files in the same BIDS layout**, so the rest of the pipeline doesn't care which transport was used. We get to switch at the BLE-source layer without any other code changing.

---

## 6. fNIRS / Optics — what tonight delivers vs what's deferred

Tonight's transports (OpenMuse, Mind Monitor, official Muse app developer-OSC) **do not deliver fNIRS data** for the Athena. The only way to get fNIRS into our pipeline is:

- **The libmuse SDK** (already on disk at `C:\DocumentsJaie\AI\Muse\...\libmuse_windows_8.0.5\`), via the GettingData example we already verified compiles cleanly with VS 2022 Pro. Building a CSV-or-LSL-writing variant of that example is the path. Estimated effort: 1-2 days of focused C++ work, not tonight.

So: **tonight we capture EEG + IMU. fNIRS comes in week 2-3 via the libmuse path.** When fNIRS lands, the LSL+XDF+Path B architecture handles it without any schema changes — fNIRS is just another LSL outlet, another XDF stream, another `packet_type` row in the reference table.

The "all streams from day one" principle still holds in spirit: we capture *every stream the chosen transport delivers*. The chosen transport for tonight inherently doesn't deliver fNIRS. That's a transport limitation, not a storage limitation.

---

## 7. Tonight's MVP — the smallest thing that's right

After three rounds of validator feedback + Jaie's pushback, the MVP has shrunk to:

1. **Install OpenMuse** into the venv: `pip install https://github.com/DominiqueMakowski/OpenMuse/zipball/main` — 30 seconds.

2. **Install LabRecorder** (download from sccn/labstreaminglayer releases) OR write a tiny `pylsl_recorder.py` (~50 lines, subscribes to all Muse_* outlets, writes XDF). 15 minutes.

3. **Create `omdr_bci` Postgres database** + apply minimal schema (just the tables in section 4 above, no derived feature tables yet — those come post-session). 20 minutes.

4. **Write `post_session.py`** that takes a finished XDF file path and a session metadata dict, validates the XDF, computes SHA256, inserts the relevant Postgres rows, computes the alpha enhancement metric, writes summary.json, commits to git. 60 minutes.

5. **Update `experiment_1_eyes_closed.py`** to use the new capture path: discover the Athena via OpenMuse, start LSL recording, mark transitions via LSL push_sample, stop recording, call `post_session.py`. 30 minutes.

6. **End-to-end test with mock XDF** (we don't have the device yet). Verify the post_session pipeline reads an XDF, populates Postgres, writes summary, commits to git. 15 minutes.

7. **Update TONIGHT.md** with the new instructions: install commands, what to do when Jaie gets home, the exact 7pm sequence, and the OSC fallback path. 15 minutes.

**Total: ~2.5 hours after Jaie approves this v2 plan. Comfortably before 7pm.**

What's NOT in tonight's MVP (deferred to weeks 2-3):
- libmuse SDK direct PC capture for fNIRS
- Any continuous aggregates / pre-computed feature pipelines (analysis happens on-demand)
- Real-time co-observation loop (Phase 4)
- LSL+SDK custom outlet for the libmuse path
- Multi-subject support beyond the schema being multi-subject-ready
- Lab-grade clock-drift modeling (we just record dual timestamps; modeling is analysis-time)
- Continuous overnight sleep recording (one experiment at a time first)

---

## 8. Open questions for validator round 2

Round 1 critiqued v1. Round 2 should critique v2 specifically, with attention to:

**Q1.** Does adopting LSL via OpenMuse + LabRecorder introduce any failure modes that v1's OSC path didn't have? Specifically: clock-sync issues across the BLE→LSL→recorder pipeline, OpenMuse maturity (last commit Jan 2026, ~2.5 months ago, with an open optical-channel-mapping bug on firmware 3.1.19), LabRecorder Windows quirks.

**Q2.** Is the dual-path Natus pattern correctly applied? Specifically: are we right that raw samples should NEVER touch Postgres, even for the live signal-quality display? Or is there a case for a small in-memory rolling buffer that bypasses both Path A and Path B for real-time use?

**Q3.** Non-destructive storage: is there any transformation we MUST apply at write time that v2 has incorrectly punted to analysis time? Specifically: device-clock-to-host-clock mapping (do we need to apply LSL's clock correction at write time, or store it as metadata for later application)?

**Q4.** BIDS compliance: does the proposed folder layout actually conform to BIDS 1.x for multi-stream EEG data? Are we handling the EEG events.tsv correctly? What's the right BIDS treatment for multi-rate streams (XDF doesn't have a first-class BIDS file format yet)?

**Q5.** XDF as primary archive: is XDF actually a good long-term archive format, or should we ALSO export to EDF/EDF+ at session end as a forward-compatible second copy? Specifically: how stable is the XDF spec, how widely supported in 5-10 years, how friendly to future migrations?

**Q6.** Schema for Path B: have we missed any required tables or columns? Specifically for: subject demographics, calibration data, hardware impedance checks, ambient conditions (temperature, EMI environment), experimental protocol versioning.

**Q7.** Post-session processing as the "derived data" entry point: is the post-session script the right place for feature computation, or should it be a separate batch pipeline? What about features that depend on multiple sessions (e.g. individual alpha peak frequency stability over time)?

**Q8.** OpenMuse risk: with last commit ~2.5 months ago and an open optical-channel-mapping bug on Athena firmware 3.1.19, is it risky enough to recommend the libmuse SDK path even for tonight's MVP? Or is "OpenMuse primary, OSC fallback" the correct hedge?

**Q9.** What's the most obvious thing wrong with v2 that the v1 critique didn't catch?

**Q10.** Specifically: does the non-destructive storage principle apply to LSL's own clock correction, or is LSL's clock correction "transport metadata" that should be applied at write time because LSL itself owns the unified-clock guarantee?

---

## 9. What changed from v1 (a diff for the record)

| Section | v1 | v2 |
|---|---|---|
| **Transport** | OSC via Mind Monitor or our own receiver | LSL via OpenMuse (primary) + OSC fallback (Mind Monitor / official Muse app) |
| **Raw storage** | Postgres TimescaleDB hypertable, wide table with `values DOUBLE PRECISION[]` | XDF files in BIDS-compliant filesystem layout |
| **Database role** | Holds raw samples + derived features + metadata | Holds ONLY derived features + metadata + index over Path A files. Zero raw samples. |
| **Continuous aggregates** | Stack of TimescaleDB continuous aggregates at Fibonacci-spaced bucket sizes | NONE in the schema. Aggregates computed at analysis time per query, with whatever window shape that query needs. |
| **fNIRS lag** | `physiological_lag_ms` column on packets, applied at write time | `physiological_lag_ms_typical` in `packet_types` reference table as documentation only. Analysis layer applies it as a parameterized default. |
| **Clock drift** | Per-session offset table, possibly applied at write time | Dual timestamps (host + device + LSL clocks) stored unmodified. Sync events at session start/end. Drift correction at analysis time. |
| **Filtering / re-referencing / artifact rejection** | Implied at write time | Explicitly forbidden at write time. All deferred to analysis. |
| **EDF as archive** | One EDF per session, second antenna | XDF as primary (multi-rate native), EDF as optional secondary export at session end for forward compatibility. |
| **Wide table vs per-type tables** | Wide table for raw, debated by validators | Resolved: raw is in XDF files (not the DB), so the question is moot. Per-type tables happen on Path B for derived data, where they're appropriate. |
| **Three antennas** | Postgres + EDF + git | Path A (XDF/EDF files in BIDS) + Path B (Postgres index over Path A) + Path C (git for code/metadata/summaries) |
| **Three OMDR bands** | Distributed across schema | Distributed across paths: Band 1 → Path A files, Band 2 → Path B derived features, Band 3 → Path B annotations + Path C notes |
| **TimescaleDB extension** | Required for the hypertable | Optional, useful for Path B derived feature time-bucketing, not foundational |
| **Schema size** | Large (packets hypertable + 13 continuous aggregate views + metadata tables) | Small (10 tables, no hypertable, no continuous aggregates) |
| **Tonight's MVP effort** | ~2 hours | ~2.5 hours (slightly more because of LSL setup, but with cleaner architecture) |

---

## 10. The summary one-liner

**LSL via OpenMuse for capture, XDF files in BIDS layout for raw archive, Postgres for the index over those files plus all derived data, git for code and reproducibility — three antennas, dual-path raw/index split, non-destructive storage throughout, all interpretation deferred to analysis time.**

---

*Awaiting validator round 2 (Grok, GPT-4o, Claude API, Gemini via Playwright) and Jaie's approval before any implementation.*
