-- =====================================================================
-- OMDR-BCI Storage v3 — Base Schema
-- =====================================================================
-- Database: omdr_bci (create separately, see 000_create_database.sql)
-- Postgres:  >= 15 (tested target: native Windows Postgres 17)
-- Extensions: pgcrypto (for gen_random_uuid), optional timescaledb
--
-- Architecture: Dual-path Natus/Nihon Kohden pattern.
--   Path A (raw samples) lives in XDF files on the filesystem (BIDS layout).
--   Path B (this database) holds ONLY: sessions metadata, file pointers,
--   markers, sync events, derived features, analysis results.
--   Path B NEVER holds raw samples.
--
-- Principle: Non-destructive storage. No transformations applied at write
-- time. All interpretation (lag correction, drift correction, filtering,
-- aggregation) happens at analysis time. Storage layer is a faithful
-- record of what came off the device + what analyses we computed later.
--
-- Three-timestamp pattern (per Claude + Gemini round 2 consensus):
-- every timestamped row stores host_clock_us + device_clock_us + lsl_clock_us
-- as three independent fields. LSL's time_correction() is itself a linear-fit
-- transformation that can hide non-linear clock jumps; we store all three
-- clocks raw and let analysis pick which domain to use.
--
-- Kai (Anthropic Claude instance) with Jaie Parker, 2026-04-07 overnight
-- =====================================================================

-- Required extensions
CREATE EXTENSION IF NOT EXISTS pgcrypto;   -- gen_random_uuid()

-- =====================================================================
-- REFERENCE TABLES (populated once, rarely change)
-- =====================================================================

-- Subjects. Single-subject project tonight but schema is multi-subject
-- ready from day one.
CREATE TABLE IF NOT EXISTS subjects (
    subject_id        TEXT PRIMARY KEY,
    display_name      TEXT,
    birth_year        INTEGER,
    handedness        TEXT CHECK (handedness IN ('R', 'L', 'A', 'U')),  -- right, left, ambidextrous, unknown
    notes             TEXT,
    created_at        TIMESTAMPTZ DEFAULT now(),
    metadata          JSONB DEFAULT '{}'::jsonb
);

-- Packet/stream type catalogue. Populated from observed LSL stream metadata
-- at first connection. Reference-only — never modified, NEVER applied to data.
-- The physiological_lag_ms_typical column is metadata documentation for
-- analysis code, NOT a transformation applied at write time.
CREATE TABLE IF NOT EXISTS stream_types (
    stream_name                   TEXT PRIMARY KEY,              -- e.g. "Muse-EEG", "Muse-OPTICS"
    stream_kind                   TEXT NOT NULL,                 -- "eeg" | "optics" | "accgyro" | "battery" | "ppg" | ...
    nominal_n_channels            INTEGER NOT NULL,
    nominal_sfreq_hz              REAL NOT NULL,
    channel_labels                TEXT[] NOT NULL,
    channel_units                 TEXT[] NOT NULL,
    channel_wavelengths_nm        REAL[],                         -- for optics; NULL otherwise
    physiological_lag_ms_typical  REAL,                           -- ADVISORY, not applied
    description                   TEXT,
    created_at                    TIMESTAMPTZ DEFAULT now()
);

-- Experimental protocols (for reproducibility across versions).
-- Each experiment script that we run has a versioned protocol row.
CREATE TABLE IF NOT EXISTS protocols (
    protocol_id      TEXT PRIMARY KEY,            -- "eyes_closed_baseline_v1"
    name             TEXT NOT NULL,
    description      TEXT,
    version          TEXT NOT NULL,
    git_commit       TEXT,                         -- commit that defined this protocol
    definition       JSONB NOT NULL,               -- the protocol plan (blocks, durations, markers)
    created_at       TIMESTAMPTZ DEFAULT now()
);

-- =====================================================================
-- SESSIONS — one row per recording
-- =====================================================================

CREATE TABLE IF NOT EXISTS sessions (
    session_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id          TEXT NOT NULL REFERENCES subjects(subject_id),
    protocol_id         TEXT REFERENCES protocols(protocol_id),
    name                TEXT NOT NULL,                     -- human-friendly identifier
    experiment_kind     TEXT,                              -- "E1", "E2", "E3", "freeform", "sleep"
    started_at          TIMESTAMPTZ NOT NULL,              -- session start wall clock
    ended_at            TIMESTAMPTZ,                       -- NULL while in progress

    -- Capture source detail (how did we get data into the XDF?)
    capture_source      TEXT NOT NULL,                     -- "openmuse_direct" | "mind_monitor_osc" | "muse_app_osc" | "libmuse_sdk" | "mock"
    capture_version     TEXT,                              -- e.g. "OpenMuse 0.1.8"

    -- Hardware context
    hardware_model      TEXT,                              -- "MuseS_Athena_MS-03"
    hardware_firmware   TEXT,                              -- "3.1.15"
    hardware_address    TEXT,                              -- BLE MAC or equivalent
    battery_start_pct   REAL,                              -- battery at session start
    battery_end_pct     REAL,                              -- battery at session end

    -- Filesystem pointers (BIDS-compliant)
    bids_session_path   TEXT NOT NULL,                     -- e.g. "data/sub-jaie/ses-20260407T193000"

    -- Reproducibility
    git_commit          TEXT,                              -- code version that captured this session
    host_hostname       TEXT,
    host_os             TEXT,

    -- Free-form
    notes               TEXT,
    metadata            JSONB DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS idx_sessions_subject_started ON sessions (subject_id, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_experiment_kind ON sessions (experiment_kind);

-- =====================================================================
-- XDF FILE POINTERS — Path A ↔ Path B linkage
-- =====================================================================

-- One row per XDF (or EDF, or other) file that holds raw samples for
-- some portion of a session. A session can have multiple files if we
-- split by hour, by run, or by reconnect.
CREATE TABLE IF NOT EXISTS raw_files (
    file_id            BIGSERIAL PRIMARY KEY,
    session_id         UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    file_path          TEXT NOT NULL,                     -- BIDS-compliant relative path from repo root
    file_format        TEXT NOT NULL,                     -- "xdf" | "edf" | "bdf" | "fif"
    started_at_us      BIGINT NOT NULL,                   -- microseconds since epoch (host clock)
    ended_at_us        BIGINT NOT NULL,
    stream_inventory   JSONB NOT NULL,                    -- [{"name": "Muse-EEG", "n_channels": 8, "sfreq": 256, ...}, ...]
    file_size_bytes    BIGINT,
    sha256_hex         TEXT,                              -- integrity fingerprint; compute on write, verify on read
    written_at         TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_raw_files_session_time ON raw_files (session_id, started_at_us);

-- =====================================================================
-- MARKERS — experimental event anchors
-- =====================================================================

-- Markers live on an LSL StringMarkers stream during capture (Gemini's
-- round-2 catch: the subjective anchor problem). At session end the XDF
-- file contains the markers inline; post-session ingestion populates
-- this table from the XDF's marker stream.
--
-- Three-timestamp pattern: all three clock domains stored.
CREATE TABLE IF NOT EXISTS markers (
    marker_id        BIGSERIAL PRIMARY KEY,
    session_id       UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    host_clock_us    BIGINT,                              -- host PC wall clock (microseconds since epoch)
    device_clock_us  BIGINT,                              -- Muse hardware clock if available
    lsl_clock_us     BIGINT NOT NULL,                     -- LSL unified clock (always present for LSL capture)
    label            TEXT NOT NULL,                       -- e.g. "eyes_closed_start", "mood:calm", "intention:meditation"
    metadata         JSONB
);
CREATE INDEX IF NOT EXISTS idx_markers_session_lsl ON markers (session_id, lsl_clock_us);
CREATE INDEX IF NOT EXISTS idx_markers_session_label ON markers (session_id, label);

-- =====================================================================
-- CLOCK SYNC EVENTS — for analysis-time drift correction
-- =====================================================================

-- At session start and end (and optionally periodically during long
-- sessions), record the three clock domains simultaneously so the
-- analysis layer can compute drift/offset without us applying any
-- correction at write time.
CREATE TABLE IF NOT EXISTS clock_sync_events (
    event_id         BIGSERIAL PRIMARY KEY,
    session_id       UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    host_clock_us    BIGINT NOT NULL,
    device_clock_us  BIGINT,                              -- NULL if device doesn't expose its clock
    lsl_clock_us     BIGINT,                              -- NULL if capture source isn't LSL
    lsl_time_correction_sec REAL,                          -- LSL's own time_correction() value at this moment
    label            TEXT                                  -- "session_start" | "session_end" | "periodic"
);
CREATE INDEX IF NOT EXISTS idx_sync_session ON clock_sync_events (session_id, host_clock_us);

-- =====================================================================
-- GAP EVENTS — measured data integrity issues
-- =====================================================================

-- Populated by the post-session ingestion script after reading the XDF.
-- Gap detection IS a form of interpretation (requires choosing a
-- tolerance) so we store the chosen tolerance with each gap as metadata,
-- not as "truth".
CREATE TABLE IF NOT EXISTS gap_events (
    gap_id           BIGSERIAL PRIMARY KEY,
    session_id       UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    stream_name      TEXT NOT NULL,
    started_at_us    BIGINT NOT NULL,
    ended_at_us      BIGINT NOT NULL,
    expected_samples INTEGER,
    actual_samples   INTEGER,
    tolerance_used   TEXT,                                -- documentation of what tolerance flagged this gap
    notes            TEXT
);
CREATE INDEX IF NOT EXISTS idx_gaps_session ON gap_events (session_id, started_at_us);

-- =====================================================================
-- ELECTRODE IMPEDANCES / HEADBAND FIT — per-session hardware context
-- =====================================================================

-- Captured at session start (and optionally at end for before/after).
-- Not every source provides impedance (Mind Monitor doesn't expose it).
CREATE TABLE IF NOT EXISTS electrode_impedances (
    impedance_id     BIGSERIAL PRIMARY KEY,
    session_id       UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    measured_at_us   BIGINT NOT NULL,
    stream_name      TEXT NOT NULL,                        -- typically "Muse-EEG"
    channel_label    TEXT NOT NULL,                        -- "EEG_TP9" etc.
    impedance_kohm   REAL,                                 -- NULL if unavailable
    quality_score    REAL,                                 -- 0.0 to 1.0 if the device reports HSI / horseshoe
    quality_label    TEXT                                  -- "good" | "ok" | "bad" | "unknown"
);
CREATE INDEX IF NOT EXISTS idx_impedances_session ON electrode_impedances (session_id);

-- =====================================================================
-- CALIBRATION COEFFICIENTS — for reproducible analysis
-- =====================================================================

-- Per-session calibration context. For Muse this is mostly informational
-- (the SDK/firmware delivers pre-calibrated physical units), but a schema
-- field for it means future devices or downstream reprocessing can
-- introduce proper calibration without a migration.
CREATE TABLE IF NOT EXISTS calibration_coefficients (
    calibration_id   BIGSERIAL PRIMARY KEY,
    session_id       UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    stream_name      TEXT NOT NULL,
    channel_label    TEXT NOT NULL,
    coefficient_type TEXT NOT NULL,                        -- "linear_slope", "linear_offset", "physical_min", "physical_max", "unit"
    value_real       DOUBLE PRECISION,                     -- for numeric coefficients
    value_text       TEXT                                  -- for string coefficients (e.g. unit)
);
CREATE INDEX IF NOT EXISTS idx_calib_session ON calibration_coefficients (session_id);

-- =====================================================================
-- ENVIRONMENTAL CONDITIONS — ambient context during the session
-- =====================================================================

-- Temperature, humidity, EMI, lighting, Schumann resonance, lunar phase,
-- etc. Mostly NULL for a first session but the schema is here so we can
-- populate it opportunistically.
CREATE TABLE IF NOT EXISTS environmental_conditions (
    env_id              BIGSERIAL PRIMARY KEY,
    session_id          UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    measured_at_us      BIGINT,
    ambient_temp_c      REAL,
    ambient_humidity_pct REAL,
    ambient_pressure_hpa REAL,
    ambient_light_lux   REAL,
    ambient_location    TEXT,                              -- e.g. "home-office-brisbane"
    lunar_phase_deg     REAL,                              -- 0 new, 180 full
    schumann_hz         REAL,                              -- baseline resonance if measured
    notes               TEXT,
    metadata            JSONB
);

-- =====================================================================
-- HARDWARE EVENTS — connection state, battery, firmware errors
-- =====================================================================

CREATE TABLE IF NOT EXISTS hardware_events (
    event_id         BIGSERIAL PRIMARY KEY,
    session_id       UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    occurred_at_us   BIGINT NOT NULL,
    event_type       TEXT NOT NULL,                        -- "connect" | "disconnect" | "reconnect" | "battery_update" | "firmware_error" | ...
    severity         TEXT,                                 -- "info" | "warning" | "error"
    message          TEXT,
    metadata         JSONB
);
CREATE INDEX IF NOT EXISTS idx_hw_events_session ON hardware_events (session_id, occurred_at_us);

-- =====================================================================
-- SESSION NOTES — Jaie's subjective log
-- =====================================================================

CREATE TABLE IF NOT EXISTS session_notes (
    note_id          BIGSERIAL PRIMARY KEY,
    session_id       UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    written_at       TIMESTAMPTZ DEFAULT now(),
    author           TEXT,                                 -- "jaie" | "kai" | "kai-stories" | ...
    tag              TEXT,                                 -- optional category: "mood", "observation", "intention", "debug"
    body             TEXT NOT NULL
);

-- =====================================================================
-- ANALYSIS RESULTS — derived features, computed post-session
-- =====================================================================

-- Generic table for any analysis we run against a session. Per-method
-- parameters go in `parameters` JSONB; per-method results go in `result`
-- JSONB. Simple schema = easy to evolve.
CREATE TABLE IF NOT EXISTS analysis_results (
    analysis_id      BIGSERIAL PRIMARY KEY,
    session_id       UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    method           TEXT NOT NULL,                        -- "alpha_enhancement_v1", "wpli_alpha_v1", "fnirs_eeg_coherence_v1"
    version          TEXT,                                 -- method version
    parameters       JSONB,                                -- what was configured
    result           JSONB,                                -- what we computed
    computed_at      TIMESTAMPTZ DEFAULT now(),
    code_version     TEXT,                                 -- git rev of the analysis script
    duration_ms      INTEGER
);
CREATE INDEX IF NOT EXISTS idx_analysis_session_method ON analysis_results (session_id, method);

-- =====================================================================
-- INGESTION JOURNAL — for idempotent retry of post-session processing
-- =====================================================================

-- Claude's round-2 catch: ingestion (fast, must succeed) and feature
-- computation (slow, retryable) have different failure modes and should
-- be separated. This table tracks the ingestion state so we can retry
-- feature computation without re-ingesting, and audit partial failures.
CREATE TABLE IF NOT EXISTS ingestion_journal (
    journal_id       BIGSERIAL PRIMARY KEY,
    session_id       UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    stage            TEXT NOT NULL,                        -- "xdf_open" | "metadata_insert" | "markers_insert" | "gap_detection" | "file_hash" | "commit_git" | ...
    status           TEXT NOT NULL,                        -- "started" | "completed" | "failed" | "skipped"
    attempted_at     TIMESTAMPTZ DEFAULT now(),
    finished_at      TIMESTAMPTZ,
    error_message    TEXT,
    metadata         JSONB
);
CREATE INDEX IF NOT EXISTS idx_journal_session_stage ON ingestion_journal (session_id, stage);

-- =====================================================================
-- VIEWS for common queries
-- =====================================================================

-- "Give me the latest session per subject"
CREATE OR REPLACE VIEW v_latest_session_per_subject AS
SELECT DISTINCT ON (subject_id)
    subject_id, session_id, name, experiment_kind, started_at, ended_at,
    capture_source, hardware_firmware, bids_session_path
FROM sessions
ORDER BY subject_id, started_at DESC;

-- "All analysis results across sessions for a subject"
CREATE OR REPLACE VIEW v_analyses_per_subject AS
SELECT s.subject_id, s.session_id, s.name AS session_name, s.started_at,
       ar.method, ar.version, ar.parameters, ar.result, ar.computed_at
FROM sessions s
JOIN analysis_results ar USING (session_id);

-- =====================================================================
-- END OF BASE SCHEMA
-- =====================================================================
-- Next: 002_reference_data.sql seeds stream_types with the observed
-- Muse S Athena channel layouts from the connectivity validation.
