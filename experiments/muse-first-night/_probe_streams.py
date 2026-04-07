"""Deep probe: wait for LSL streams to appear, query metadata, pull sample data.

Runs alongside an OpenMuse stream. Does NOT start a stream itself. Writes
everything to connectivity_deep_probe.json for the validation log.
"""
import json
import time
import numpy as np
from mne_lsl.lsl import resolve_streams, StreamInlet

print("Waiting up to 25s for LSL streams to appear...")
streams = []
t0 = time.time()
while time.time() - t0 < 25.0:
    found = resolve_streams(timeout=2.0)
    if len(found) >= 3:
        streams = found
        print(f"Found {len(streams)} streams after {time.time()-t0:.1f}s")
        break
    elif found:
        print(f"  (saw {len(found)} so far, waiting for more...)")
        streams = found
    time.sleep(0.5)

if not streams:
    print("NO STREAMS FOUND")
    raise SystemExit(1)

print()
print(f"Probing {len(streams)} streams...")
results = []

for s in streams:
    entry = {
        "name": s.name,
        "stype": s.stype,
        "n_channels": s.n_channels,
        "sfreq": s.sfreq,
        "source_id": s.source_id,
        "channel_info": None,
        "sample_preview": None,
        "value_ranges": None,
        "error": None,
    }
    try:
        inlet = StreamInlet(s, max_buffered=60)
        inlet.open_stream()
        # Query channel metadata via the inlet's stream info
        sinfo = inlet.get_sinfo()
        try:
            entry["channel_info"] = sinfo.get_channel_info()
        except Exception as e:
            entry["channel_info_error"] = str(e)

        # Pull ~2 seconds of samples
        target_samples = int(s.sfreq * 2)
        collected = []
        deadline = time.time() + 3.5
        while len(collected) < target_samples and time.time() < deadline:
            chunk, ts = inlet.pull_chunk(timeout=0.5, max_samples=int(s.sfreq))
            if chunk is not None and len(chunk) > 0:
                collected.extend(chunk)
        if collected:
            arr = np.asarray(collected)
            entry["samples_collected"] = int(arr.shape[0])
            entry["sample_shape"] = list(arr.shape)
            # First sample as preview
            entry["sample_preview"] = [float(x) for x in arr[0]]
            # Per-channel min/max/mean
            entry["value_ranges"] = {
                "min": [float(x) for x in arr.min(axis=0)],
                "max": [float(x) for x in arr.max(axis=0)],
                "mean": [float(x) for x in arr.mean(axis=0)],
                "std": [float(x) for x in arr.std(axis=0)],
            }
        else:
            entry["samples_collected"] = 0
        inlet.close_stream()
    except Exception as e:
        entry["error"] = f"{type(e).__name__}: {e}"
    results.append(entry)
    print(f"  {entry['name']}: {entry.get('samples_collected', 0)} samples collected")

with open("connectivity_deep_probe.json", "w") as f:
    json.dump(results, f, indent=2, default=str)
print()
print("Saved connectivity_deep_probe.json")
print()

# Print a human-readable summary
for e in results:
    print(f"=== {e['name']} ===")
    print(f"  n_channels={e['n_channels']}, sfreq={e['sfreq']} Hz")
    if e.get("error"):
        print(f"  ERROR: {e['error']}")
        continue
    ci = e.get("channel_info")
    if ci:
        for i, ch in enumerate(ci[:20]):
            print(f"  ch{i}: {ch}")
    else:
        print(f"  (no channel_info: {e.get('channel_info_error', 'empty')})")
    if e.get("value_ranges"):
        vr = e["value_ranges"]
        print(f"  value ranges across {e['samples_collected']} samples:")
        for i in range(len(vr["min"])):
            print(f"    ch{i}: min={vr['min'][i]:.3f}, max={vr['max'][i]:.3f}, mean={vr['mean'][i]:.3f}, std={vr['std'][i]:.3f}")
    print()
