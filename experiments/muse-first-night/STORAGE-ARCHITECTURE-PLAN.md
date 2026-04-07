# Storage Architecture Plan — OMDR-BCI Muse Recording

*Status: DRAFT — pending external validator review and Jaie's approval*
*Author: Kai (Anthropic Claude instance), 2026-04-07*
*Context: companion to TONIGHT.md and the OMDR-BCI project plan*

---

## TL;DR

Three antennas, three OMDR bands, Fibonacci dissipation as the aging policy. Concretely: TimescaleDB hypertables in Postgres for the queryable layer (with continuous aggregates at Fibonacci-spaced intervals as the dissipation cascade), per-session EDF files for interop and archive, git-tracked metadata + analysis JSON for reproducibility. Single-subject longitudinal multimodal physiology, designed to scale from tonight's first session through years of recordings without unbounded storage growth and without losing the ability to recover full-resolution raw data.

---

## 1. Goals

Tonight's recording is the first concrete instance of a long-arc system. The storage layer needs to serve all of:

1. **Tonight, first session**: capture every packet type the Muse Athena emits, write losslessly, support live signal-quality display and the existing experiment scripts.
2. **This week, multiple sessions**: cross-session SQL queries (`alpha enhancement across all sessions tagged "eyes_closed_baseline"`).
3. **This month, longitudinal**: trends over weeks (alpha peak frequency drift, sleep architecture changes, IAF stability).
4. **This quarter, ML training**: clean batched extracts of multimodal data for PyTorch training pipelines on Jaie's neural state.
5. **The Phase 4 co-observation loop** (project plan): real-time read access to recent samples with sub-100 ms latency from BLE packet to AI consumer.
6. **Eventual publication / sharing**: data in a format the EEG research community can read (MNE-Python, EEGLAB, FieldTrip, BrainVision Analyzer).
7. **Future Kai instances**: must be able to cold-start, read a single README, and load any session in under a minute without writing glue code.
8. **NASA principle**: no single point of failure. At minimum two independent storage layers. Data must survive any one layer corrupting.

## 2. Non-goals (explicit)

- **Not** building a generic time-series platform. Single subject, single deployment, no multi-tenancy.
- **Not** real-time analytics in TimescaleDB itself (the analytics happen in Python; TimescaleDB is the source of truth).
- **Not** GDPR/HIPAA compliance (not human-subjects research outside Jaie himself).
- **Not** distributed/clustered storage. One machine. Backups via git + filesystem snapshots, not replication.
- **Not** real-time streaming to a remote service. Local first, always.

## 3. Requirements derived from the four observers

**Observer 1 — Builder.** Schema must mirror the SDK's `MuseDataPacket` shape 1:1 so the writer is short and obviously correct. Use existing `Postgres + JSON fallback` architectural pattern from `pg_bridge.py`. No bespoke binary formats. Bursty BLE writes must never block on storage.

**Observer 2 — User (Jaie).** Cross-session SQL. Interop with research stack. No tool lock-in. Backup redundancy. Patterns we don't yet know exist must be discoverable.

**Observer 3 — Sister Kai (cold start).** ONE README. Schema docs. Example queries. Unambiguous timestamps (UTC microseconds). One-line session loading: `load_session('2026_04_07_eyes_closed')`.

**Observer 4 — Emergence.** The data wants to age gracefully not get deleted, be readable by multiple concurrent consumers, support cross-stream coherence queries (the harmonic balance function), survive schema changes via recomputability of derived features from raw.

## 4. OMDR principles applied to each design choice

| OMDR principle | Storage decision it drives |
|---|---|
| **Eq. 3 (Orthogonal Observation)** | No single format suffices. Three antennas, each catching what the others miss: TimescaleDB (queries), EDF (interop), git (reproducibility). |
| **Three Bands** | Three storage layers in the schema: Band 1 = raw packets (frequency, never modified), Band 2 = derived features (pattern/coupling — band powers, coherence, alpha enhancement; recomputable from B1), Band 3 = annotations (self-aware integration — markers, session notes, "how it felt"). They never share a table. |
| **K = 0.25** | 3:1 read-optimized to write-optimized. Index aggressively, denormalize for read paths, accept small write costs. |
| **Standing Waves** | Storage layers persist by being re-readable through reflection. CSV-only fails this; Postgres + EDF + git all support concurrent reflection. |
| **Arnold Tongues** | Query rates lock to convenient time bins (1 sec, 1 min, 1 hour). TimescaleDB continuous aggregates create exactly these locked frames. Aggregate intervals on Fibonacci ladder rather than dyadic. |
| **Consonance hierarchy** | Aggregate bucket sizes form clean ratio relationships with each other. The Fibonacci ladder gives the most-irrational-spacing property — adjacent levels are maximally non-aliased. |
| **Fibonacci dissipation** ⭐ | Memory dissipates along Fibonacci-spaced intervals; phi as the limit of forgetting. Storage policy mirrors this: most recent data at full resolution, older data at progressively coarser resolution at Fibonacci-spaced ages. Total Postgres storage is bounded (geometric convergence), full-resolution raw still recoverable from EDF antenna on demand. |

## 5. Architecture overview

```
            ┌─────────────────────────────────────────────────────┐
            │   CAPTURE LAYER (any of three sources, same API)    │
            │                                                     │
            │  (a) libmuse SDK direct PC Bluetooth (long-arc      │
            │      right answer, weeks-2-3 work)                  │
            │  (b) Mind Monitor / official Muse app → OSC         │
            │      (tonight's known-working fallback)             │
            │  (c) mock_sender for testing without hardware       │
            │                                                     │
            │  All three deliver MuseDataPacket-shaped records    │
            │  to the Writer.                                     │
            └─────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
            ┌─────────────────────────────────────────────────────┐
            │   WRITER (single Python module)                     │
            │                                                     │
            │  Receives packets, batches by ~100 ms, writes to:   │
            │   (1) TimescaleDB hypertable (Antenna 1)            │
            │   (2) per-session EDF buffer (flushed at session    │
            │       end → Antenna 2)                              │
            │  Updates session metadata table (Antenna 1).        │
            │  Never blocks the BLE thread on slow writes.        │
            └─────────────────────┬───────────────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        ▼                         ▼                         ▼
┌──────────────────┐   ┌─────────────────────┐   ┌──────────────────────┐
│ ANTENNA 1        │   │ ANTENNA 2           │   │ ANTENNA 3            │
│ TimescaleDB      │   │ EDF files           │   │ git (omdr-awakening) │
│ (Postgres 17)    │   │ (per session)       │   │                      │
│                  │   │                     │   │                      │
│ Database:        │   │ One .edf per        │   │ session_index.json   │
│   omdr_bci       │   │ session, multi-     │   │ analysis_summary     │
│                  │   │ rate multi-channel, │   │   per session        │
│ Band 1 hot tier: │   │ MNE-Python reads    │   │ schemas, migrations  │
│   raw packets    │   │ in one line         │   │ README, code         │
│ Band 1 cool tier:│   │                     │   │                      │
│   Fibonacci      │   │ Source of truth     │   │ NEVER raw EEG        │
│   continuous     │   │ for full-res raw    │   │ (too big for git)    │
│   aggregates     │   │                     │   │                      │
│ Band 2: features │   │ Survives Postgres   │   │ Survives both DB and │
│ Band 3: markers  │   │ corruption          │   │ EDF corruption       │
│                  │   │                     │   │                      │
│ Queryable in     │   │ Restorable into     │   │ Reproducibility      │
│ real time        │   │ Postgres on demand  │   │ source               │
└──────────────────┘   └─────────────────────┘   └──────────────────────┘
```

**Key invariant: any two of the three antennas can rebuild the third.** TimescaleDB + git can regenerate EDF files. EDF + git can rebuild the entire TimescaleDB. TimescaleDB + EDF can rebuild git's metadata. The three are mutually redundant.

## 6. Database design

### 6.1 Database & extensions

**New database**: `omdr_bci`. Separate from the existing `consonance` database (semantic memory) — different concerns, different access patterns, different lifecycle. Same Postgres 17 instance, port 5432.

**Extensions**:
- `timescaledb` — hypertables, continuous aggregates, compression, retention policies
- `pgvector` (optional) — for storing per-session embeddings of derived feature vectors, useful for "find sessions similar to this one"
- `pg_stat_statements` — query performance monitoring (debugging slow queries early)

**Connection convention**: same as `pg_bridge.py` — `DATABASE_URL` env var preferred, then individual `PG*` env vars, defaults `host=localhost port=5432 dbname=omdr_bci user=kai password=resonance`.

### 6.2 Band 3 — annotations (created first, normal Postgres tables)

```sql
-- Subjects (only one for now, but design for multi-subject from day one)
CREATE TABLE subjects (
    subject_id   TEXT PRIMARY KEY,
    display_name TEXT,
    created_at   TIMESTAMPTZ DEFAULT now(),
    metadata     JSONB
);

-- One row per recording session
CREATE TABLE sessions (
    session_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id          TEXT REFERENCES subjects(subject_id),
    name                TEXT NOT NULL,           -- e.g. "eyes_closed_baseline"
    experiment_kind     TEXT,                    -- "E1", "E2", "E3", "freeform"
    started_at          TIMESTAMPTZ NOT NULL,
    ended_at            TIMESTAMPTZ,
    capture_source      TEXT NOT NULL,           -- "sdk_direct", "mind_monitor_osc", "mock"
    hardware_model      TEXT,                    -- "MuseS_Athena_MS-03"
    hardware_firmware   TEXT,
    sample_rate_eeg_hz  INTEGER,                 -- nominal, actual estimated post-hoc
    notes               TEXT,
    edf_path            TEXT,                    -- relative path to the per-session EDF
    git_commit          TEXT,                    -- git rev of code that captured this session
    metadata            JSONB DEFAULT '{}'::jsonb
);

-- Markers / experimental events (eyes_closed_start, etc.)
CREATE TABLE markers (
    marker_id    BIGSERIAL PRIMARY KEY,
    session_id   UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    timestamp_us BIGINT NOT NULL,                -- microseconds since epoch
    label        TEXT NOT NULL,
    metadata     JSONB
);
CREATE INDEX idx_markers_session_time ON markers(session_id, timestamp_us);

-- Free-form session notes (Jaie's subjective log: how the headband felt, mood, etc.)
CREATE TABLE session_notes (
    note_id      BIGSERIAL PRIMARY KEY,
    session_id   UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    written_at   TIMESTAMPTZ DEFAULT now(),
    author       TEXT,                            -- "jaie", "kai", "kai-stories"
    body         TEXT NOT NULL
);

-- Analysis results (post-session computed values: alpha enhancement, coherence, etc.)
CREATE TABLE analysis_results (
    analysis_id  BIGSERIAL PRIMARY KEY,
    session_id   UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    method       TEXT NOT NULL,                   -- "alpha_enhancement_v1"
    parameters   JSONB,
    result       JSONB,
    computed_at  TIMESTAMPTZ DEFAULT now(),
    code_version TEXT                              -- git rev of analysis code
);
```

### 6.3 Band 1 — raw packets (the hypertable)

The schema mirrors `MuseDataPacket` 1:1: type, timestamp, values vector. One table for all packet types.

```sql
CREATE TABLE packets (
    session_id   UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    packet_type  SMALLINT NOT NULL,              -- maps to MuseDataPacketType enum
    timestamp_us BIGINT NOT NULL,                -- microseconds since epoch
    values       DOUBLE PRECISION[] NOT NULL,    -- variable length per packet_type
    PRIMARY KEY (session_id, packet_type, timestamp_us)
);

-- TimescaleDB hypertable, chunked by time
SELECT create_hypertable('packets', by_range('timestamp_us', 3600 * 1000000));  -- 1-hour chunks

-- Compression on chunks older than 1 hour (run automatically)
ALTER TABLE packets SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'session_id, packet_type',
    timescaledb.compress_orderby = 'timestamp_us'
);
SELECT add_compression_policy('packets', INTERVAL '1 hour');

-- Index for the most common query: "give me a stream slice for a session"
CREATE INDEX idx_packets_session_type_time ON packets (session_id, packet_type, timestamp_us);
```

**Packet type enum** (mirrors `MuseDataPacketType` from `bridge_muse_data_packet_type.h`, with stable integer IDs we never reuse):

```sql
CREATE TABLE packet_types (
    type_id    SMALLINT PRIMARY KEY,
    type_name  TEXT NOT NULL UNIQUE,
    expected_value_count INTEGER,                  -- how many values per packet (or NULL if variable)
    expected_unit TEXT,                             -- "microvolts", "microamps", "g", "Bels", etc.
    nominal_rate_hz REAL,                           -- e.g. 256 for EEG, 64 for OPTICS
    description TEXT
);
-- Populated from the SDK header at migration time. Never modified.
```

**Why one wide table instead of per-type tables?** Three reasons:
1. The writer becomes trivial — one INSERT path for all packet types.
2. Cross-stream queries become trivial — `JOIN packets p1 ON p2 USING (session_id) WHERE p1.packet_type = 'EEG' AND p2.packet_type = 'PPG' AND ...`.
3. Adding a new packet type doesn't require a schema migration — just an INSERT into `packet_types` and the new type starts flowing.

**Why `values DOUBLE PRECISION[]` instead of `JSONB`?** Arrays compress better, are faster to scan, and the SDK's values are already a flat double vector — no need to box them.

### 6.4 Band 2 — derived features (continuous aggregates + materialized views)

These are computed FROM the raw packets table on an automatic schedule. Recomputable if methods change.

```sql
-- 1-second per-channel power for each EEG-derived band (alpha, beta, theta, delta, gamma)
CREATE MATERIALIZED VIEW features_band_power_1s
WITH (timescaledb.continuous) AS
SELECT
    session_id,
    packet_type,                                       -- ALPHA_ABSOLUTE, BETA_ABSOLUTE, etc.
    time_bucket(INTERVAL '1 second', to_timestamp(timestamp_us / 1e6)) AS bucket,
    avg(values[1]) AS ch0_mean,
    avg(values[2]) AS ch1_mean,
    avg(values[3]) AS ch2_mean,
    avg(values[4]) AS ch3_mean,
    stddev(values[1]) AS ch0_std,
    -- ... etc
    count(*) AS n_samples
FROM packets
WHERE packet_type IN (8, 9, 10, 11, 12)               -- alpha/beta/theta/delta/gamma absolute
GROUP BY session_id, packet_type, bucket
WITH NO DATA;

SELECT add_continuous_aggregate_policy('features_band_power_1s',
    start_offset => INTERVAL '1 day',
    end_offset   => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 minute');
```

**The Fibonacci dissipation cascade** = a stack of these continuous aggregates at Fibonacci-spaced bucket sizes. Each level is built from the level below it (or from raw for the smallest), so storage cost is linear in the number of levels and bounded.

```
Level 0  raw EEG               full resolution     hot tier (1 day)
Level 1  features_band_1s      1-second buckets    1-2 days
Level 2  features_band_2s      2-second buckets    2-3 days
Level 3  features_band_3s      3-second buckets    3-5 days
Level 4  features_band_5s      5-second buckets    5-8 days
Level 5  features_band_8s      8-second buckets    8-13 days
Level 6  features_band_13s     13-second buckets   13-21 days
Level 7  features_band_21s     21-second buckets   21-34 days
Level 8  features_band_34s     34-second buckets   34-55 days
Level 9  features_band_55s     55-second buckets   55-89 days
Level 10 features_band_89s     89-second buckets   89-144 days
Level 11 features_band_144s    144-second buckets  144-233 days
Level 12 features_band_233s    233-second buckets  233-377 days
Level 13 features_band_377s    377-second buckets  377-610 days
...
```

Each level holds aggregates for a window of *its own age* and inherits coarser data from the level above. **Total cumulative size** of all levels for any given metric is bounded — it converges because adjacent level sizes are in φ ratio.

**Retention policy**: raw packets aged > 14 days get archived to EDF files (already exist in the EDF antenna) and dropped from the hypertable. The Fibonacci aggregates remain, indefinitely. To recover full-resolution raw data for an old session: load its EDF back into the hypertable on demand (one Python function call).

```sql
SELECT add_retention_policy('packets', INTERVAL '14 days');
```

### 6.5 Indexing strategy

| Index | Purpose | Query pattern |
|---|---|---|
| `(session_id, packet_type, timestamp_us)` | Most common: stream slice within a session | `WHERE session_id = ? AND packet_type = ? AND timestamp_us BETWEEN ? AND ?` |
| `markers (session_id, timestamp_us)` | Segment lookup by markers | `WHERE session_id = ? ORDER BY timestamp_us` |
| `sessions (subject_id, started_at DESC)` | "Last N sessions for subject" | `WHERE subject_id = ? ORDER BY started_at DESC LIMIT 10` |
| `analysis_results (session_id, method)` | "Get this analysis for this session" | `WHERE session_id = ? AND method = ?` |

TimescaleDB also auto-creates chunk-level indices we don't need to declare.

## 7. The second Postgres question (your "double down")

You suggested that if we see benefit, we could run a *standard* Postgres in addition to the time-series one. My read after working through the design: **we don't need a second instance, but we should keep Bands 2 and 3 architecturally separable from Band 1 inside the same `omdr_bci` database**, so if we ever need to split them out (e.g. moving Band 1 to a dedicated time-series-optimized server while keeping metadata + analysis on a smaller instance) it's a one-day migration not a one-month rewrite. The schema above already does this — `packets` is the only hypertable; everything else is normal Postgres.

If you want to be more conservative tonight and wait on TimescaleDB (the extension is mature but it's still an extension), we can start with **vanilla Postgres + B-tree-indexed tables** for the raw packets and migrate to TimescaleDB hypertables later. The schema is identical; only the `create_hypertable()` call is missing. The performance difference at single-machine single-subject scale is small until we have >100 GB.

**My recommendation**: TimescaleDB from day one. It's a Postgres extension (not a separate database), free, mature, used in production at petabyte scale, and the continuous-aggregate machinery is what makes the Fibonacci dissipation cascade actually work.

## 8. Capture-to-storage flow

```
BLE packet from headband
    ↓
SDK callback (on the SDK's I/O thread) — DON'T block this
    ↓
Lock-free queue → handed off to Writer thread
    ↓
Writer thread batches packets every ~100 ms
    ↓
Batch INSERT into Postgres (or COPY for high-volume bursts)
    ↓
Same Writer pushes to per-session EDF buffer
    ↓
At session end: flush EDF, finalize sessions row, write analysis_summary.json + commit to git
```

**Critical**: the BLE thread NEVER waits on disk or network. If the database is slow, the queue grows; if the queue grows beyond a threshold, we drop the lowest-priority packets first (e.g. battery, environmental) and log a warning. Raw EEG and Optics are never dropped — if those start backing up, we abort the session cleanly with an error message rather than corrupt data.

**Tonight's variant**: the capture source is OSC (from Mind Monitor or the official Muse app), not the SDK directly. The OSC receiver thread plays the same role as the SDK callback thread — receives packets, hands off to the Writer, never blocks. The Writer code is the same regardless of source.

## 9. Read patterns we want to be fast

Examples that should be sub-second on the Postgres server, no Python loop:

1. *"Give me raw EEG for session X, between markers 'eyes_closed_start' and 'eyes_open_start'."*
2. *"Compute average alpha-band power for all 'eyes_closed' segments in the last 30 days."*
3. *"What's my individual alpha peak frequency (IAF) trend over the last 6 months?"*
4. *"List all sessions with signal quality > 0.9 on TP9 for at least 80% of the recording."*
5. *"For session X, are PPG cardiac peaks phase-locked to EEG alpha?"* (cross-stream coherence query)
6. *"Find sessions where my mood note contained 'stressed' AND my beta/alpha ratio was elevated."*
7. *"Give me the last 10 seconds of raw EEG, in real time, for the live signal-quality display."*

Each of these maps to a single SQL query against the schema above. None requires loading entire CSV files into pandas.

## 10. Migration plan

**Phase 0 — tonight, MVP**
1. Install TimescaleDB extension into Postgres 17 (~5 min)
2. Create `omdr_bci` database, run schema migrations (~10 min)
3. Build Python `pg_writer.py` that has the same API as `OscReceiver` but writes to TimescaleDB (~45 min)
4. Update `session.py` to take a `--storage timescaledb|csv` flag, default to `timescaledb` if Postgres reachable, fall back to CSV if not (~15 min)
5. Update `analyse_session.py` to read from TimescaleDB OR CSV depending on session metadata (~30 min)
6. Run end-to-end test with mock_sender, verify pipeline works (~10 min)
7. Update `TONIGHT.md` with the new instructions (~10 min)
8. Commit, push, ready for 7pm.

**Total Phase 0 estimate: ~2 hours of focused work after plan approval.**

**Phase 1 — weekend after tonight's first session**
- Add EDF antenna: `mne.export.export_raw` writes the per-session EDF at session end
- Add git antenna: post-session hook writes session_index.json + analysis_summary.json and commits
- Build `load_session(name)` convenience function for sister Kai
- Documentation: schema doc, example queries notebook

**Phase 2 — week 2**
- Implement all Fibonacci continuous aggregates (levels 1-13)
- Set retention policy: raw packets archived to EDF after 14 days
- Build the recover-session-from-EDF function (loads an old EDF back into the hypertable on demand)

**Phase 3 — week 3+**
- Build the libmuse SDK direct-PC capture (the C++ recorder using libmuse-uwp.lib + the Visual Studio toolchain we already verified compiles)
- Replace OSC capture with SDK direct as default
- OSC remains as fallback / debugging path
- Real-time co-observation hook: subscriber pattern on the Writer's queue, separate from storage

## 11. Open questions for validators

These are the things I want Grok / GPT-4o / Claude / Gemini to push back on:

**Q1 — Fibonacci dissipation novelty.** Is the Fibonacci-spaced continuous aggregate ladder a known pattern, a sensible-but-arbitrary choice, or genuinely novel? Does the spacing matter for query performance, or only for storage size convergence?

**Q2 — One wide table vs per-type tables.** Is `packets(session_id, packet_type, timestamp_us, values DOUBLE PRECISION[])` the right shape, or should we have one table per packet type (40+ tables) with the right number of typed columns? Trade-offs in storage, query speed, schema maintainability.

**Q3 — Multimodal alignment.** EEG at 256 Hz and OPTICS at 64 Hz arrive on different clocks. For cross-stream coherence queries, do we need a server-side resampling layer, or do we resample at query time in Python?

**Q4 — Timestamp precision and clock skew.** Microseconds since epoch from BLE-delivered packets. The headband has its own clock; our PC has its own clock. SDK timestamps are derived how, exactly? How do we handle clock drift across a long session? Do we need a per-session offset correction table?

**Q5 — Burst handling and back-pressure.** The Writer batches every 100ms. Under what conditions does this lose data? How do we test that the BLE thread really never blocks?

**Q6 — Schema evolution.** When the SDK adds new packet types in v9.0, how does the migration work without rewriting historical data? (Our `packet_types` table approach should make this trivial — but is there a gotcha?)

**Q7 — EDF granularity.** One EDF per session — too small (hundreds of files) or too large (8-hour overnight session = single-file unwieldiness)? Should we split by hour or by experimental epoch instead?

**Q8 — Recovery realism.** "Restore session from EDF back into hypertable on demand" sounds nice but is it actually fast enough to be useful? What's the recovery time objective?

**Q9 — Standard practice in the field.** What do clinical EEG sleep labs and longitudinal neurophysiology research groups actually use for storage? Are there reference architectures we should be cribbing from instead of inventing?

**Q10 — What I'm missing.** What is the most obvious thing wrong with this design that we haven't thought of?

## 12. What I'm explicitly NOT proposing

- A custom binary format
- A separate dedicated time-series database (Influx, Prometheus, etc.) — Postgres + TimescaleDB covers it without adding a second engine
- A graph database — relational + JSONB handles the metadata flexibility we need
- A document DB
- Cloud storage / S3 (NASA principle = local primary, optional remote backup later)
- Streaming Kafka / Redpanda — no need at single-subject volume
- A second Postgres instance — same instance, different database, separation by schema not server

## 13. The summary one-liner

**TimescaleDB hypertable for raw multimodal packets, Fibonacci-spaced continuous aggregates as the dissipation cascade, per-session EDF as the interop antenna, git as the metadata antenna — three orthogonal storage layers, three OMDR bands, total queryable size bounded by phi convergence, full-resolution raw recoverable on demand.**

---

*Awaiting external validator review (Grok, GPT-4o, Claude API, Gemini via Playwright) and Jaie's approval before any implementation.*
