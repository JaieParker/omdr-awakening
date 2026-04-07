# Tonight — 19:00 Muse first-session action sheet (v3)

*For Jaie. The one-page thing to read when you sit down to record.*

**Last updated:** 2026-04-08 (overnight build by Kai after eight validator passes and a live connectivity test)
**Status:** v3 pipeline complete, end-to-end tested on synthetic data with a 51x alpha-enhancement detection. Postgres live. Schemas applied. Experiment + ingest + features scripts working. Live signal-quality display ready. **We are GO for 19:00.**

---

## The 5 things you actually do at 19:00

### 0. Sit down at your desk with the Muse powered on and the USB cable unplugged

The Muse charges via USB but **streams only over Bluetooth**. Leave the cable out during recording.

### 1. Dampen the ear electrodes (≈20 seconds)

The temporal sites (TP9 behind left ear, TP10 behind right ear) don't get good contact when dry — validated last night, your TP9/TP10 showed saturated 0-1450 swings while the forehead (AF7/AF8) stayed clean. Dab a small amount of water (or saline, or electrode gel if you have any) onto the pads that sit behind the ears before putting the headband on.

### 2. Open THREE terminals (or three tabs in Windows Terminal)

```powershell
# All three start in the same folder:
cd C:\DocumentsJaie\AI\omdr-awakening\experiments\muse-first-night
.\.venv\Scripts\Activate.ps1
```

### 3. In terminal 1 — start OpenMuse streaming from your Athena

```powershell
OpenMuse stream --address 00:55:DA:BB:D9:53 --duration 1800
```

That's your Athena's MAC address from last night's validation. `--duration 1800` gives us 30 minutes before OpenMuse exits on its own (enough for tonight's ~7-minute protocol plus slack). You should see:
```
Starting stream for 1 device(s)...
Connecting to 00:55:DA:BB:D9:53...
Connected. Device: MuseS-D953
Streaming sensors: EEG, ACCGYRO, OPTICS, BATTERY
Connected to device (firmware 3.1.15): battery XX.XX%
Streaming data... (Press Ctrl+C to stop)
```

**If you get `BLEAK Error: Device with address ... was not found`:** press the Muse power button once to wake it up and re-run the command. The Muse drops into low-power advertising-off mode after a few minutes of idle.

### 4. In terminal 2 — start the live signal-quality display

```powershell
python live_display.py
```

This shows a real-time per-channel signal quality view updating ~5 times per second. You'll see 8 EEG channels with GOOD / OK / BAD labels and an amplitude bar. **Use this to verify headband fit BEFORE starting the experiment.**

Target state before you run the experiment:
- `EEG_AF7` and `EEG_AF8` (forehead): GOOD
- `EEG_TP9` and `EEG_TP10` (ears): at least OK, ideally GOOD
- The AUX channels don't matter for tonight's analysis

If TP9 or TP10 are BAD, re-dampen the pads and reseat the headband. Don't start recording until they're at least OK. You can leave `live_display.py` running in the background during the recording — it's a pure observer and doesn't interfere with the recorder (Gemini's Y-split architecture: both consumers pull from the same LSL bus independently).

### 5. In terminal 3 — run the experiment

```powershell
python experiment_1_eyes_closed_v3.py --subject jaie
```

You'll see the experiment preamble print, then a `Press ENTER when ready...` prompt. Press ENTER, and it walks you through:

```
>>> BLOCK 1/6 — EYES OPEN — look at the screen, blink normally — 60s <<<
[audible beep]
  eyes_open_block_1:  60s remaining ...

>>> BLOCK 2/6 — EYES CLOSED — let your eyes rest, breathe normally — 60s <<<
[two audible beeps]
  eyes_closed_block_1: 60s remaining ...

...continues for 6 blocks, alternating...
```

Total active recording: 6 minutes. After the last block:

```
[experiment_1] protocol complete, stopping recorder...
[recorder] saved Muse-EEG (00:55:DA:BB:D9:53): 92160 samples -> eeg_raw.fif
[recorder] saved Muse-OPTICS (00:55:DA:BB:D9:53): 23040 samples -> optics_raw.fif
[recorder] saved Muse-ACCGYRO (00:55:DA:BB:D9:53): 18720 samples -> accgyro_raw.fif
[recorder] saved Muse-BATTERY (00:55:DA:BB:D9:53): 72 samples -> battery_raw.fif
[recorder] saved 8 markers -> markers.json
[recorder] wrote manifest -> ...session_manifest.json

[experiment_1] running post-session ingest...
[experiment_1] ingested as session <UUID>

[experiment_1] running post-session feature computation...

==========================================================================
 RESULT
==========================================================================
  Pooled temporal alpha enhancement (closed/open) = X.XX x  [STRONG/MODERATE/WEAK/NONE]
  Per-channel:
    EEG_TP9:  X.XXx
    EEG_AF7:  X.XXx
    EEG_AF8:  X.XXx
    EEG_TP10: X.XXx
    AUX_1:    X.XXx
    ...

[experiment_1] done. Session at: experiments/muse-first-night/data/sub-jaie/ses-20260408T190XXX
```

That's it. **You're done.** Terminal 1 keeps streaming, terminal 2 keeps showing signal quality, terminal 3 shows the result.

---

## What the result means

**Expected range for the pooled temporal alpha enhancement** (TP9 + TP10 averaged): **1.2x to 2.0x** for a well-fit session without electrode gel. Textbook occipital-site enhancement is 2-4x but the Muse doesn't reach occipital, so temporal-only is a weaker effect.

| Ratio | Verdict | What it means |
|---|---|---|
| >1.5x | STRONG | Well-fit headband, clean data, canonical effect detected |
| 1.2-1.5x | MODERATE | Good session, effect present, matches Muse-on-temporal literature |
| 1.0-1.2x | WEAK | Effect barely detectable. Probably suboptimal fit or poor dampening |
| <1.0x | NONE | Alpha was higher during *open* than *closed* — the fit is wrong, re-dampen and retry |

**The per-channel breakdown matters more than the pooled number.** If TP9 shows 2.0x but TP10 shows 0.8x, one ear electrode is bad — the pooled average hides it. Read both.

If `individual_alpha_peak_hz` is outside the 8-13 Hz range for your temporal sites (you'll see this in `analysis_summary.json`), the band-power is understating your actual alpha and we should widen the analysis band — flag it for tomorrow's re-analysis.

---

## Where everything lives after the session

```
experiments/muse-first-night/data/sub-jaie/ses-20260408T190XXX/
├── eeg_raw.fif                    # 8-channel EEG, MNE-Python native
├── eeg_timestamps.npz             # host + LSL clock per sample
├── optics_raw.fif                 # 16-channel fNIRS + PPG + ambient
├── optics_timestamps.npz
├── accgyro_raw.fif                # 6-axis IMU
├── accgyro_timestamps.npz
├── battery_raw.fif                # battery %
├── battery_timestamps.npz
├── markers.json                   # LSL marker stream (session_start, blocks, session_end)
├── clock_sync.json                # sync events at start and end
├── session_manifest.json          # everything at a glance
└── analysis_summary.json          # the alpha enhancement + coherence results
```

**Postgres (Path B) gets populated automatically** by `post_session_ingest.py`:
- `sessions` row with this session's UUID, start/end, subject=jaie, hardware=MuseS_Athena_MS-03, firmware=3.1.15, bids path, git commit
- `raw_files` rows (one per FIF) with SHA256, size, stream inventory
- `markers` rows — 8 entries (session_start, 6 blocks, session_end) with both host clock and LSL clock timestamps
- `clock_sync_events` rows
- `gap_events` rows if any BLE dropouts were detected
- `analysis_results` row with the full features JSON

To query later:
```bash
$env:PGPASSWORD="resonance"
psql -U kai -d omdr_bci -h localhost -c "SELECT started_at, name, experiment_kind FROM sessions ORDER BY started_at DESC LIMIT 5;"
```

---

## Troubleshooting

### OpenMuse can't find the Muse
- Power-cycle the Muse: hold the button until it turns off, then tap once to turn it back on
- Make sure Bluetooth is enabled on this PC
- Check you're using the right MAC address: `OpenMuse find` will re-discover it

### `Muse-EEG` stream doesn't appear in live_display or experiment_1
- OpenMuse sometimes takes 5-10 seconds after "Streaming data..." before the LSL outlet is actually publishing — wait ~10s before running the experiment
- If it still doesn't show up, restart the OpenMuse stream (Ctrl+C in terminal 1, re-run)

### `BLEAK Error: Device not found` during stream start
- The Muse went to sleep. Short-press the power button to wake it. Re-run OpenMuse stream.

### Electrode contact is BAD on TP9/TP10 no matter what
- More water. Not just a dab — genuinely wet the pads
- Brush hair off the area behind your ears
- Make sure the pads are touching skin, not sitting on hair
- TP9/TP10 are the hardest sites on the Muse; 0.8x to 1.2x contact quality is typical without proper electrolyte gel. If you can get them to "OK" (yellow) that's enough for the experiment to work

### `python experiment_1_eyes_closed_v3.py` crashes with a Postgres error
- The omdr_bci database IS created and populated from last night's overnight build
- If you see `connection refused`: check the postgresql-x64-17 Windows service is running (`Get-Service postgresql-x64-17`)
- If you see `password authentication failed`: the experiment script reads credentials from environment OR defaults to `kai/resonance`. If you changed the kai password, set `OMDR_BCI_PGPASSWORD` in the terminal before running the experiment
- As a fallback, you can run with `--no-ingest --no-features` and the FIF files will still be saved for manual analysis later

### Alpha enhancement is weirdly low (ratio < 1.0)
- Re-dampen the ear electrodes and retry (most common cause)
- Check `analysis_summary.json` → `individual_alpha_peak_hz` for each temporal channel. If your alpha peak is below 8 Hz or above 13 Hz, the band-power is missing it. Flag for re-analysis with a widened band.
- Check the per-channel ratios separately — a single bad electrode can invert the pooled result

### You get the result but want to re-run the analysis with different parameters
```powershell
python post_session_features.py "data/sub-jaie/ses-20260408T190XXX"
```

### You want to skip tonight but keep the setup for tomorrow
The pipeline doesn't care when you run it. Just power off the Muse and run it another night. Everything we did overnight is durable.

---

## What NOT to worry about tonight

- **fNIRS analysis** — we're capturing all 16 OPTICS channels tonight but we're not doing cross-modal EEG-fNIRS coherence analysis yet. That's a next-week task. You'll have the raw fNIRS in the FIF regardless.
- **TimescaleDB extension** — not installed, not needed. Path B uses vanilla Postgres tables.
- **BIDS validator** — we're in BIDS-compliant layout but we haven't run the validator against it. The layout is correct for future BIDS compliance but nothing downstream requires it tonight.
- **Multiple sessions tonight** — do one. Read the result. Tomorrow we iterate.

---

## What I want to happen

You dampen, put on the headband, run the three commands, do the 6 minutes of protocol, see a pooled temporal alpha enhancement ratio and know it's real. Your alpha at TP9 is genuinely higher when your eyes close. The harmonic balance function that the OMDR project plan has been waiting for since day 1 has its first measurement from your specific brain. Tomorrow we start asking it real questions.

**Go when you're ready. No rush.**

Kai
2026-04-08 overnight build, committed to omdr-awakening main
