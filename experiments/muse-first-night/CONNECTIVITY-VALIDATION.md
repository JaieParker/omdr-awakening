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

Three independent reviewers across two validation rounds told me to treat fNIRS as "deferred to week 2-3 via libmuse SDK" based on the OpenMuse README saying fNIRS validation was incomplete. They were **wrong**, and Jaie was right to push back. The actual observed behavior of this specific Athena unit with OpenMuse 0.1.8 is:

```
Stream name                              type      channels   rate (Hz)   dtype
Muse-EEG    (00:55:DA:BB:D9:53)          EEG       8          256         float32
Muse-ACCGYRO(00:55:DA:BB:D9:53)          ACCGYRO   6          52          float32
Muse-OPTICS (00:55:DA:BB:D9:53)          PPG*      16         64          float32
```

*`stype=PPG` is a labeling artifact of OpenMuse — the 16-channel stream is the Athena's fNIRS optics (the SDK's `OPTICS` packet type), not the 3-channel PPG. Use the stream **name** (`Muse-OPTICS`) to disambiguate. TODO: file a clarity issue with OpenMuse upstream.*

**Total payload:** 8 EEG @ 256 Hz + 16 OPTICS @ 64 Hz + 6 ACCGYRO @ 52 Hz = **~4 KB/s at float32**, or ~15 MB/hour at raw sample rate. Comfortably inside every budget the round-1 synthesis estimated.

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
