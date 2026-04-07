-- =====================================================================
-- OMDR-BCI Storage v3 — Reference Data
-- =====================================================================
-- Seeds the reference tables with values observed from Jaie's specific
-- Muse S Athena (MAC 00:55:DA:BB:D9:53, firmware 3.1.15) during the
-- 2026-04-07 connectivity validation.
--
-- Source of truth: CONNECTIVITY-VALIDATION.md + connectivity_deep_probe.json
-- =====================================================================

-- Subject: Jaie
INSERT INTO subjects (subject_id, display_name, birth_year, handedness, notes)
VALUES ('jaie', 'Jaie Parker', NULL, 'U', 'Primary subject for the OMDR-BCI project. Athena owner.')
ON CONFLICT (subject_id) DO NOTHING;

-- =====================================================================
-- STREAM TYPES — the four streams observed on the Athena
-- =====================================================================

-- Muse-EEG: 4 standard Muse 2 sites + 4 auxiliary channels
INSERT INTO stream_types (
    stream_name, stream_kind, nominal_n_channels, nominal_sfreq_hz,
    channel_labels, channel_units, physiological_lag_ms_typical, description
) VALUES (
    'Muse-EEG', 'eeg', 8, 256.0,
    ARRAY['EEG_TP9', 'EEG_AF7', 'EEG_AF8', 'EEG_TP10', 'AUX_1', 'AUX_2', 'AUX_3', 'AUX_4'],
    ARRAY['microvolt', 'microvolt', 'microvolt', 'microvolt', 'microvolt', 'microvolt', 'microvolt', 'microvolt'],
    0.0,  -- EEG is an electrical signal; no physiological lag relative to itself
    'Raw EEG from Muse S Athena. Channels 1-4 are the classical Muse 2 sites (TP9, AF7, AF8, TP10); channels 5-8 are auxiliary electrodes introduced on the Athena (MS-03). Forehead sites (AF7, AF8) typically have best contact; ear sites (TP9, TP10) require dampening for good electrode contact. Anti-alias lowpass at 128 Hz (Nyquist).'
)
ON CONFLICT (stream_name) DO NOTHING;

-- Muse-OPTICS: hybrid fNIRS + PPG + ambient light reference
INSERT INTO stream_types (
    stream_name, stream_kind, nominal_n_channels, nominal_sfreq_hz,
    channel_labels, channel_units, channel_wavelengths_nm,
    physiological_lag_ms_typical, description
) VALUES (
    'Muse-OPTICS', 'optics', 16, 64.0,
    ARRAY[
        'OPTICS_LO_NIR', 'OPTICS_RO_NIR', 'OPTICS_LO_IR',  'OPTICS_RO_IR',
        'OPTICS_LI_NIR', 'OPTICS_RI_NIR', 'OPTICS_LI_IR',  'OPTICS_RI_IR',
        'OPTICS_LO_RED', 'OPTICS_RO_RED', 'OPTICS_LO_AMB', 'OPTICS_RO_AMB',
        'OPTICS_LI_RED', 'OPTICS_RI_RED', 'OPTICS_LI_AMB', 'OPTICS_RI_AMB'
    ],
    ARRAY[
        'microamp', 'microamp', 'microamp', 'microamp',
        'microamp', 'microamp', 'microamp', 'microamp',
        'microamp', 'microamp', 'microamp', 'microamp',
        'microamp', 'microamp', 'microamp', 'microamp'
    ],
    ARRAY[
        730.0, 730.0, 850.0, 850.0,        -- LO_NIR, RO_NIR, LO_IR, RO_IR  (fNIRS outer pair)
        730.0, 730.0, 850.0, 850.0,        -- LI_NIR, RI_NIR, LI_IR, RI_IR  (fNIRS inner pair)
        660.0, 660.0, NULL, NULL,           -- LO_RED, RO_RED, LO_AMB, RO_AMB (PPG outer + ambient ref)
        660.0, 660.0, NULL, NULL            -- LI_RED, RI_RED, LI_AMB, RI_AMB (PPG inner + ambient ref)
    ]::REAL[],
    6000.0,  -- neurovascular coupling lag: hemodynamic response lags EEG electrical activity by ~5-8s (advisory, not applied)
    'Hybrid fNIRS + PPG from Muse S Athena. 2 hemispheres (L/R) x 2 optode pairs (Outer/Inner) x 4 wavelengths (NIR ~730nm, IR ~850nm, RED ~660nm, AMBient). NIR+IR pairs are the fNIRS brain hemodynamics channels (deoxy-Hb via NIR differential, oxy-Hb via IR differential). RED+IR pairs are the pulse-oximetry PPG channels. AMBient channels are ambient-light reference for noise subtraction. Wavelengths above are inferred from standard Muse hardware documentation; exact values may differ slightly per firmware revision. Anti-alias lowpass at 32 Hz. NOTE: physiological_lag_ms_typical = 6000 is advisory only, stored for analysis-layer hint; cross-stream coherence queries should take it as a default parameter but NEVER apply it at write time. Per-subject empirical lag may differ.'
)
ON CONFLICT (stream_name) DO NOTHING;

-- Muse-ACCGYRO: standard 6-axis IMU
INSERT INTO stream_types (
    stream_name, stream_kind, nominal_n_channels, nominal_sfreq_hz,
    channel_labels, channel_units, physiological_lag_ms_typical, description
) VALUES (
    'Muse-ACCGYRO', 'accgyro', 6, 52.0,
    ARRAY['ACC_X', 'ACC_Y', 'ACC_Z', 'GYRO_X', 'GYRO_Y', 'GYRO_Z'],
    ARRAY['g', 'g', 'g', 'deg/s', 'deg/s', 'deg/s'],
    0.0,
    '6-axis IMU: 3-axis accelerometer (units of gravity, 1g = 9.81 m/s^2) + 3-axis gyroscope (degrees/second). Z axis measures gravity, expect ~-1.0g when the head is upright. Anti-alias lowpass at 26 Hz.'
)
ON CONFLICT (stream_name) DO NOTHING;

-- Muse-BATTERY: single channel, very slow
INSERT INTO stream_types (
    stream_name, stream_kind, nominal_n_channels, nominal_sfreq_hz,
    channel_labels, channel_units, physiological_lag_ms_typical, description
) VALUES (
    'Muse-BATTERY', 'battery', 1, 0.2,
    ARRAY['BATTERY_PERCENT'],
    ARRAY['percent'],
    0.0,
    'Battery state-of-charge percentage (0-100). Updated every 5 seconds. Not a physiological signal; used for session health monitoring and to populate session.battery_start_pct / battery_end_pct at ingestion time.'
)
ON CONFLICT (stream_name) DO NOTHING;

-- =====================================================================
-- PROTOCOLS
-- =====================================================================

-- Experiment 1: eyes-closed baseline (the canonical alpha-enhancement test)
INSERT INTO protocols (protocol_id, name, description, version, definition)
VALUES (
    'eyes_closed_baseline_v2',
    'Eyes closed vs eyes open baseline',
    'Alternating 60-second blocks of eyes-open and eyes-closed. Canonical EEG alpha-enhancement test: alpha-band (8-13 Hz) power should be 1.5-3x higher at posterior sites during eyes-closed. With the Athena''s 8-channel layout we also examine frontal (AF7, AF8) and temporal (TP9, TP10) sites. Tomorrow''s first session.',
    '2.0.0',
    '{
        "experiment_kind": "E1",
        "blocks": [
            {"label": "eyes_open_1",   "duration_s": 60},
            {"label": "eyes_closed_1", "duration_s": 60},
            {"label": "eyes_open_2",   "duration_s": 60},
            {"label": "eyes_closed_2", "duration_s": 60},
            {"label": "eyes_open_3",   "duration_s": 60},
            {"label": "eyes_closed_3", "duration_s": 60}
        ],
        "total_duration_s": 360,
        "required_streams": ["Muse-EEG"],
        "optional_streams": ["Muse-OPTICS", "Muse-ACCGYRO", "Muse-BATTERY"],
        "quality_gate": {
            "min_contiguous_good_seconds": 5,
            "strict_channels": ["EEG_AF7", "EEG_AF8"],
            "lenient_channels": ["EEG_TP9", "EEG_TP10"],
            "lenient_mode_after_seconds": 30
        },
        "pre_recording_protocol": [
            "Dampen behind the ears (TP9, TP10 electrode sites) with water or electrolyte gel",
            "Verify forehead contact by adjusting headband position",
            "Sit upright, minimize head movement",
            "Close eyes only during eyes-closed blocks; relax eyes open during open blocks"
        ]
    }'::jsonb
)
ON CONFLICT (protocol_id) DO NOTHING;

-- =====================================================================
-- END OF REFERENCE DATA
-- =====================================================================
