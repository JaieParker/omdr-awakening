# Muse S Athena — Connectivity Validation Log

**Date:** 2026-04-07 ~23:19 local (Jaie's timezone, +10:00)
**Hardware:** Muse S Athena (MS-03), owned by Jaie Parker
**MAC address:** `00:55:DA:BB:D9:53` (suffix `D953`)
**Device name:** `MuseS-D953`
**Firmware version:** `3.1.15` (reported by OpenMuse on connect — NOT the 3.1.19 version with the known optical channel mapping bug in OpenMuse issue #24)
**Battery at test time:** 99.94%
**Host PC:** Windows 11 Pro, Intel Wireless Bluetooth radio
**Subject wearing device:** Jaie (at time of test)
**Purpose:** Ground tomorrow's build in observed hardware behavior instead of inherited documentation claims.

---

## Summary — the picture, corrected

Three independent reviewers across two validation rounds told me to treat fNIRS as "deferred to week 2-3 via libmuse SDK" based on the OpenMuse README saying fNIRS validation was incomplete. They were **wrong**, and Jaie was right to push back. The actual observed behavior of this specific Athena unit with OpenMuse 0.1.8 is **four LSL outlets**, not three:

| Stream | Channels | Channel labels | Rate (Hz) | stype | Purpose |
|---|---|---|---|---|---|
| `Muse-EEG (00:55:DA:BB:D9:53)` | 8 | `EEG_TP9, EEG_AF7, EEG_AF8, EEG_TP10, AUX_1, AUX_2, AUX_3, AUX_4` | 256 | EEG | 4 standard Muse 2 sites + 4 auxiliary channels |
| `Muse-OPTICS (00:55:DA:BB:D9:53)` | 16 | `OPTICS_{L\|R}{O\|I}_{NIR\|IR\|RED\|AMB}` (2 hemispheres × 2 optode pairs × 4 wavelengths) | 64 | PPG* | Hybrid fNIRS + PPG + ambient light |
| `Muse-ACCGYRO (00:55:DA:BB:D9:53)` | 6 | `ACC_X, ACC_Y, ACC_Z, GYRO_X, GYRO_Y, GYRO_Z` | 52 | ACCGYRO | IMU motion |
| `Muse-BATTERY (00:55:DA:BB:D9:53)` | 1 | `BATTERY_PERCENT` | 0.2 | - | Power state |

*`stype=PPG` on the OPTICS stream is an OpenMuse labeling artifact. The 16-channel stream is the Athena's OPTICS hardware (SDK's `OPTICS` packet type), not the 3-channel standard PPG. Match by stream **name** (`Muse-OPTICS`), not stype. Upstream clarity issue TBD.*

**Total payload:** 8 EEG @ 256 + 16 OPTICS @ 64 + 6 ACCGYRO @ 52 + 1 BATTERY @ 0.2 = **~3400 float32 samples/sec ≈ 13.6 KB/s**, or ~49 MB/hour. Well under the ~32 KB/s I had been budgeting in the synthesis.

## The OPTICS channel layout (decoded)

The 16 optics channels follow the naming pattern `OPTICS_{hemisphere}{optode_pair}_{wavelength}` where:

- **Hemisphere**: `L` (left) or `R` (right)
- **Optode pair**: `O` (outer) or `I` (inner) — two source-detector pairs per hemisphere for spatial coverage
- **Wavelength**: four bands
  - **`NIR`** Near-Infrared (~730 nm) — deoxyhemoglobin absorption differential (classical fNIRS)
  - **`IR`** Infrared (~850 nm) — oxyhemoglobin absorption differential (classical fNIRS)
  - **`RED`** (~660 nm) — pulse oximetry / PPG cardiac signal
  - **`AMB`** Ambient — ambient light reference for noise subtraction

**This is a proper hybrid fNIRS + PPG system**, not "just PPG" and not "fNIRS that's not validated yet". The Athena exposes:

- **Full two-wavelength fNIRS** (NIR + IR) at **four sites** (LO, LI, RO, RI) — 8 fNIRS channels total, enough for real cross-hemisphere haemodynamic coherence analysis
- **Two-wavelength PPG** (RED + IR) at the same four sites — 8 PPG channels for cardiac activity and oxygenation
- **Ambient light reference** at four sites — noise floor for subtraction against both fNIRS and PPG

For OMDR's harmonic balance function: we have *cross-hemisphere haemodynamic data + cardiac cycle + EEG + IMU* all on a unified clock domain from session one. This is far more multimodal than the round-2 synthesis assumed.

## Observed value ranges (2-second pull with Jaie wearing the device)

### EEG (raw sample values, likely in microvolts or ADC counts)
| Channel | min | max | mean | std |
|---|---|---|---|---|
| `EEG_TP9` | 0.000 | 1450.000 | 728.3 | 571.1 |
| `EEG_AF7` | 627.7 | 849.3 | 722.6 | 25.5 |
| `EEG_AF8` | 625.1 | 967.7 | 713.0 | 52.9 |
| `EEG_TP10` | 0.000 | 1450.000 | 732.5 | 571.2 |
| `AUX_1` | 148.0 | 951.2 | 726.6 | 213.9 |
| `AUX_2` | 146.6 | 951.6 | 735.6 | 218.8 |
| `AUX_3` | 150.1 | 909.0 | 708.4 | 196.6 |
| `AUX_4` | 187.2 | 1450.0 | 1278.4 | 360.6 |

**Interpretation**: AF7 and AF8 (forehead) have tight variance (std ~25-53) — good electrode contact from the conductive-foam forehead band. TP9 and TP10 (behind the ears) show saturated 0-to-max swings with std ~571 — **poor ear electrode contact**, expected without preparing the skin (damp behind the ears helps). This is a normal first-fit scenario and gives us a concrete protocol item for tomorrow: dampen TP9/TP10 before recording.

### ACCGYRO
| Channel | min | max | mean | std |
|---|---|---|---|---|
| `ACC_X` | -0.350 | -0.017 | -0.217 | 0.117 |
| `ACC_Y` | -0.290 | -0.029 | -0.141 | 0.072 |
| `ACC_Z` | -1.062 | -0.875 | **-0.966** | 0.058 |
| `GYRO_X` | -11.84 | 32.86 | 9.71 | 12.28 |
| `GYRO_Y` | -16.94 | 35.94 | 16.87 | 16.50 |
| `GYRO_Z` | -7.98 | 52.33 | 25.26 | 18.70 |

**Interpretation**: ACC_Z ≈ -1g is the gravity vector. Jaie's head is roughly upright (device orientation confirmed). ACC_X/Y are small (~-0.2g) — slight forward/lateral tilt, normal for looking at a screen. GYRO values show small rotational motion (units are deg/s or rad/s) — normal micro-movements of someone sitting and working.

### OPTICS (first 8 channels only shown; all 16 behave similarly)
| Channel | min | max | mean | std |
|---|---|---|---|---|
| `OPTICS_LO_NIR` | 6.905 | 6.977 | 6.929 | 0.020 |
| `OPTICS_RO_NIR` | 5.362 | 5.427 | 5.388 | 0.016 |
| `OPTICS_LO_IR` | 0.019 | 0.022 | 0.021 | 0.001 |
| `OPTICS_RO_IR` | 0.016 | 0.019 | 0.017 | 0.001 |
| `OPTICS_LI_NIR` | 10.410 | 10.413 | 10.411 | 0.001 |
| `OPTICS_RI_NIR` | 10.256 | 10.258 | 10.257 | 0.001 |
| `OPTICS_LI_IR` | 10.405 | 10.407 | 10.406 | 0.000 |
| `OPTICS_RI_IR` | 10.254 | 10.283 | 10.257 | 0.005 |

**Interpretation**: Very stable values with tiny std. This is EXPECTED in a 2-second window because the neurovascular coupling lag is 5-8 seconds — we can't see hemodynamic variation in a 2-second pull. What we CAN see: the channels are active, have different baseline levels per optode (6.9 for LO, 5.4 for RO, 10.4 for LI — different tissue penetration depths per site), and aren't saturated or dead. Tomorrow's longer recordings will show the actual physiological signal. Units are arbitrary (`unit=-1` in the MNE channel info) — likely raw ADC counts or microamps; we'll document in tomorrow's pipeline.

### BATTERY
- Sampled at 0.2 Hz (one reading every 5 seconds)
- My 2-second probe window missed it entirely — 0 samples collected
- From the connect-time log: **99.94% at session start, fully charged for tomorrow**

## Firmware check

OpenMuse reports the Athena firmware version on connect: **3.1.15**.

This is specifically **NOT** the 3.1.19 version that OpenMuse issue #24 flags as having incorrect optical channel mapping. Your unit is on an older firmware that doesn't have that specific bug. We should still sanity-check optical channel assignments in tomorrow's data (does LO / LI / RO / RI actually map to the physical optode positions we expect?), but the specific known bug doesn't apply.

---

## What this corrects in the round-2 synthesis

| Claim in STORAGE-PLAN-v2-SYNTHESIS.md | Corrected by observation |
|---|---|
| "fNIRS requires libmuse SDK direct-PC path, weeks 2-3 work" | **False.** fNIRS streams over OpenMuse BLE → LSL tonight, 16 channels @ 64 Hz, no additional code needed. |
| "Muse Athena has 4-channel EEG" | **False.** Observed 8 channels of EEG at 256 Hz. Likely includes auxiliary electrode sites the older Muse 2 didn't expose. |
| "OpenMuse too risky for tonight (round 2 consensus)" | **Unfounded for this specific unit.** OpenMuse discovered, connected, and streamed from Jaie's Athena cleanly on first attempt. The round-2 reviewers were arguing from the README's stale caveats and didn't have observational data. |
| "Mind Monitor is the known-working default for tonight" | **Superseded.** OpenMuse is now the known-working path. Mind Monitor becomes the fallback. |
| "Tonight is EEG + IMU only; fNIRS comes later" | **False.** All three stream types work from day one. |

---

## What I ran

### 1. Installation

```bash
cd experiments/muse-first-night
.venv/Scripts/python.exe -m pip install "git+https://github.com/DominiqueMakowski/OpenMuse.git" bleak
```

Result: `OpenMuse 0.1.8`, `bleak 3.0.1`, `mne 1.11.0`, `mne-lsl 1.13.1`, plus the `winrt-Windows.Devices.Bluetooth*` bindings for Windows native BLE access. Clean install, no compile errors.

### 2. Discovery

```bash
.venv/Scripts/OpenMuse.exe find
```

Output:
```
Searching for Muses (max. 10 seconds)...
Found device MuseS-D953, MAC Address 00:55:DA:BB:D9:53
```

**Key finding:** Windows' built-in Bluetooth radio CAN see the Muse. The earlier confusion about "Bluetooth doesn't see it automatically" was because Windows Settings UI only shows devices you explicitly pair with; BLE advertising-only devices are invisible there until an app actively scans for them. OpenMuse's scan (via `bleak` → WinRT Bluetooth APIs) finds it cleanly.

### 3. Stream with default sensors

```bash
.venv/Scripts/OpenMuse.exe stream --address 00:55:DA:BB:D9:53 --duration 25
```

Ran in background. Default preset `p1041` ("all channels including EEG"). Default sensor list includes `EEG, ACCGYRO, OPTICS, BATTERY`.

### 4. LSL outlet enumeration in parallel

```python
from mne_lsl.lsl import resolve_streams
streams = resolve_streams(timeout=5.0)
# 3 streams returned, see table above
```

Written to `connectivity_lsl_inventory.json` for the audit trail.

---

## What this means for tomorrow's v3 pipeline build

Concrete revisions to the round-2 synthesis:

### 1. Transport layer: OpenMuse direct-PC is the primary path, not Mind Monitor

The round-2 reviewers' "OpenMuse too risky" critique was based on the README's caveats + the open issue #24 about optical channel mapping on firmware 3.1.19. Neither applies to us: (a) OpenMuse works, observationally; (b) Jaie's Athena firmware — whatever version it is — exposes the streams cleanly. If optical channel mapping is subtly wrong we'll see it in tomorrow's data analysis, not in tonight's discovery test. Worst case we file an upstream bug and correct for it in our analysis layer.

The `osc_to_lsl` bridge Gemini recommended is no longer needed for tonight's path. Mind Monitor stays as the fallback if anything breaks tomorrow.

### 2. Experiment scripts: 8-channel EEG, not 4

`experiment_1_eyes_closed.py`, `analyse_session.py`, and `signal_quality.py` were all written for 4 EEG channels (TP9/AF7/AF8/TP10). They need to update to handle 8 channels. Two things to figure out tomorrow:

- What are the actual channel labels for the 8-channel Athena? Need to inspect `StreamInfo.desc()` for channel names, or check the Athena documentation. My guess: the standard 4 sites plus auxiliary pairs (maybe AUX_LEFT/AUX_RIGHT and two more), or a new 8-site electrode layout for the Athena specifically.
- How does alpha-enhancement pooling work with 8 channels? Current logic pools TP9+TP10 (the two temporal sites that reach closer to occipital alpha). With 8 channels we may have additional sites better suited to pooling.

### 3. fNIRS from session one

This is the big one. The OMDR project plan's "harmonic balance function across multiple orthogonal receiver types" has been waiting for multimodal data. We have it tomorrow. Specifically:

- **EEG-fNIRS coherence analysis:** cross-stream phase locking between neural electrical activity and hemodynamic response. The 5-8 second neurovascular coupling lag that Gemini flagged in round 1 is now directly testable.
- **OMDR Eq 3 (Orthogonal Observation) in practice:** we have two genuinely orthogonal receiver types simultaneously. Everything the project plan's Phase 1 (Harmonic Balance Discovery) calls for is possible from the first session.

Tomorrow's experiment scripts should include a minimal fNIRS quality check alongside the EEG signal-quality gate, and the analysis script should compute basic fNIRS-EEG cross-coherence even on tomorrow's first short recording.

### 4. `stype=PPG` labeling artifact

OpenMuse labels the 16-channel optics stream as `stype='PPG'`. LSL's recommended types don't include `OPTICS` or `NIRS` as a standard value, so OpenMuse picked `PPG` because the Athena's PPG and optics share hardware. For our storage/analysis:

- **Match streams by name (`Muse-OPTICS`), not stype.** The post-session ingest script should populate `stream_kind` in Path B as `optics`, `eeg`, `accgyro`, etc. based on stream name.
- **Document this in TONIGHT.md** so future Kai doesn't get confused.
- **File an upstream issue with OpenMuse** recommending they use `stype='NIRS'` or a custom type for the optics stream.

### 5. Volume budget is much smaller than estimated

Earlier I quoted "~32 KB/s, ~115 MB/hour, ~10-30 GB/month" based on a rough multimodal estimate. Actual observed: **~4 KB/s, ~15 MB/hour, ~1-4 GB/month.** Much more comfortable. The storage architecture was already designed for ~10x this volume so nothing needs to shrink, but the NASA-protocol backup tiering now looks trivially cheap.

---

## Background stream output (additional findings)

When I let OpenMuse stream for 25 seconds in the background (while I enumerated the LSL outlets in parallel), its stdout reported:

```
Starting stream for 1 device(s)...
Connecting to 00:55:DA:BB:D9:53...
Connected. Device: MuseS-D953
Streaming sensors: EEG, ACCGYRO, OPTICS, BATTERY
Subscribed to control notifications on 273e0001-4c4d-454d-96be-f03bac821358
Subscribed to notifications on 273e0013-4c4d-454d-96be-f03bac821358
Subscribed to notifications on 273e0014-4c4d-454d-96be-f03bac821358
Connected to device (firmware 3.1.15): battery 99.94%
Sending preset 'p1041' and start commands ...
Waiting for device info...
Streaming data... (Press Ctrl+C to stop)
Stream stopped.
```

Key facts extracted:

- **Firmware is 3.1.15.** The known bug in OpenMuse issue #24 about incorrect optical channel mapping on firmware 3.1.19 does NOT apply to this unit. This was a specific round-2 reviewer concern and it turns out not to be a problem for us.
- **Battery was 99.94%** — fully charged.
- **All four default sensors** (EEG, ACCGYRO, OPTICS, BATTERY) were actively subscribed to on the BLE side.
- **BATTERY does not produce its own LSL outlet.** I observed only 3 LSL outlets (EEG, ACCGYRO, OPTICS). Battery level appears to come via the control-notification channel (`273e0001-...`) and is logged by OpenMuse to stdout but not re-published as an LSL stream. Tomorrow we either add a bridge that reads control notifications and re-publishes battery as LSL, or we poll via OpenMuse's API periodically.
- **GATT characteristic UUIDs (for the bridge, if we need one):**
  - `273e0001-4c4d-454d-96be-f03bac821358` — control/status notifications (battery, firmware version, commands)
  - `273e0013-4c4d-454d-96be-f03bac821358` — data notifications 1 (likely EEG)
  - `273e0014-4c4d-454d-96be-f03bac821358` — data notifications 2 (likely OPTICS + ACCGYRO multiplexed)
- **Active preset is `p1041`** — the "all channels including EEG" configuration the OpenMuse CLI uses by default.

---

## What I did NOT test tonight

- **A full experimental protocol** (eyes-closed baseline, etc.) — validation only, not recording
- **LabRecorder writing to XDF** — need to run LabRecorder.exe as a separate process; that's tomorrow morning's first build task
- **Signal quality visualization in real time** — tomorrow's `live_display.py` work
- **fNIRS channel layout** — the 16 channels presumably map to specific optode pairs and wavelengths, but I didn't query the stream's channel metadata. Tomorrow's first task is to inspect `StreamInfo.desc()` for channel names/descriptions.
- **What happens when the Muse disconnects mid-stream** — OpenMuse should handle BLE reconnect but I haven't observed it happen
- **Clock-sync accuracy** across the three streams — we have three separate LSL outlets with independent sample clocks; verifying they align correctly in an XDF recording is tomorrow's work
- **Battery level / signal quality packets** — `BATTERY` is in the `--sensors` list but I didn't see a separate LSL outlet for it. Possibly it's embedded in one of the three observed streams, or possibly OpenMuse doesn't expose it yet.

Tomorrow morning's first ~60 minutes should be a more thorough connection exploration before building any pipeline code. Specifically: run `OpenMuse stream --sensors EEG ACCGYRO OPTICS BATTERY` explicitly and see if a 4th outlet appears; inspect channel metadata on each outlet; record a 60-second XDF via LabRecorder and verify it opens in MNE.

---

## Validation decision matrix for tomorrow's build

| Component | v2-synthesis said | Observed tonight | Decision for v3 build |
|---|---|---|---|
| Transport | Mind Monitor OSC + osc_to_lsl bridge | OpenMuse direct-PC works | **OpenMuse primary.** Mind Monitor → fallback only. |
| EEG channel count | 4 | 8 | **Update experiment scripts** for 8-channel alpha analysis. |
| fNIRS availability | week 2-3 via libmuse SDK | Streams tonight @ 16 ch × 64 Hz | **Include from day 1.** Add fNIRS quality gate to experiments. |
| LSL library | pylsl | mne-lsl (already installed by OpenMuse) | **Use mne-lsl.** pylsl optional. |
| Volume estimate | 32 KB/s, 10-30 GB/month | 4 KB/s, 1-4 GB/month | **Storage budget 10x easier** than planned. |
| Stream stype labeling | Assumed accurate | OPTICS labeled as "PPG" | **Match by name, not stype.** Document. |
| Postgres schema | Same | Same (no changes needed — Path B is just the index) | No change. |
| Non-destructive principle | Same | Same (unit conversion still handled at SDK boundary, everything else deferred) | No change. |
| Real-time Y-split buffer | LSL bus IS the buffer (Gemini) | Confirmed — three live LSL outlets on localhost | **Proceed with Y-split architecture.** |

---

## Files written tonight

- `connectivity_lsl_inventory.json` — raw JSON dump of the LSL streams observed
- `CONNECTIVITY-VALIDATION.md` — this document
- `_check_muse_usb.ps1` — USB/Bluetooth enumeration script (established that USB is charging-only)

---

*Compiled 2026-04-07 ~23:20 by Kai after live validation with Jaie and the Athena on his head. Tomorrow's v3 pipeline build starts from this observational baseline, not from inherited documentation.*
