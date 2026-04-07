"""Mock Mind Monitor OSC sender for end-to-end testing without a Muse.

Generates synthetic 4-channel EEG at 256 Hz, plus the slower band-power and
horseshoe streams Mind Monitor sends, and emits them over UDP/OSC. The synthetic
data deliberately injects more alpha (10 Hz sine) into the "eyes-closed" portion
of the run so that downstream analysis CAN detect the alpha-enhancement effect
if the pipeline is correct. If our alpha-enhancement script can't see the effect
in mock data, it can't see it in real data either.

Usage:
    # Default: 60 seconds of mock data, eyes-open for first 30s, eyes-closed for last 30s
    python mock_sender.py

    # Match a specific port (must match receiver's --port)
    python mock_sender.py --port 5000

    # Custom timing
    python mock_sender.py --duration 240 --closed-start 60 --closed-end 180
"""
from __future__ import annotations

import argparse
import math
import random
import time

import numpy as np
from pythonosc.udp_client import SimpleUDPClient

SAMPLE_RATE = 256        # Hz, raw EEG
BAND_RATE = 10           # Hz, Mind Monitor sends band powers ~10 Hz
HORSESHOE_RATE = 1       # Hz
ACC_RATE = 50            # Hz


def alpha_amplitude(t: float, closed_start: float, closed_end: float) -> float:
    """Higher alpha during the eyes-closed window (10 Hz sine), low otherwise."""
    if closed_start <= t <= closed_end:
        return 35.0  # microvolts
    return 5.0


def gen_eeg_sample(t: float, closed_start: float, closed_end: float) -> tuple[float, float, float, float]:
    """Generate one 4-channel sample (TP9, AF7, AF8, TP10) at time t (seconds)."""
    # Base 1/f-ish brown noise
    noise = lambda: random.gauss(0, 8)
    # 10 Hz alpha component, modulated by closed-eyes window
    alpha = alpha_amplitude(t, closed_start, closed_end) * math.sin(2 * math.pi * 10 * t)
    # 20 Hz beta component, fixed
    beta = 6.0 * math.sin(2 * math.pi * 20 * t)
    # 6 Hz theta component, fixed
    theta = 4.0 * math.sin(2 * math.pi * 6 * t)
    # 50 Hz mains hum (small)
    mains = 2.0 * math.sin(2 * math.pi * 50 * t)
    # Combine and add per-channel noise + slight phase variation
    base = alpha + beta + theta + mains
    return (
        base + noise(),                                                                       # TP9
        base * 0.9 + noise() + 1.5 * math.sin(2 * math.pi * 10 * t + 0.3),                   # AF7
        base * 0.9 + noise() + 1.5 * math.sin(2 * math.pi * 10 * t - 0.3),                   # AF8
        base + noise(),                                                                       # TP10
    )


def gen_band_powers(t: float, closed_start: float, closed_end: float) -> dict[str, list[float]]:
    """Crude band-power estimates (per channel) — just for streaming sanity."""
    alpha_lvl = alpha_amplitude(t, closed_start, closed_end)
    in_closed = closed_start <= t <= closed_end
    return {
        "alpha": [alpha_lvl / 10] * 4 if not in_closed else [(alpha_lvl / 10) + 0.6] * 4,
        "beta":  [0.3 + random.gauss(0, 0.05)] * 4,
        "theta": [0.4 + random.gauss(0, 0.05)] * 4,
        "gamma": [0.1 + random.gauss(0, 0.02)] * 4,
        "delta": [0.5 + random.gauss(0, 0.05)] * 4,
    }


def main():
    parser = argparse.ArgumentParser(description="Mock Mind Monitor OSC sender for testing")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--duration", type=float, default=60.0, help="Total run duration (seconds)")
    parser.add_argument("--closed-start", type=float, default=30.0, help="Eyes-closed window start (seconds)")
    parser.add_argument("--closed-end", type=float, default=60.0, help="Eyes-closed window end (seconds)")
    parser.add_argument("--good-contact", action="store_true", default=True, help="Send good horseshoe values")
    args = parser.parse_args()

    client = SimpleUDPClient(args.host, args.port)
    print(f"[mock_sender] streaming to {args.host}:{args.port} for {args.duration:.0f}s")
    print(f"[mock_sender] eyes-closed window: {args.closed_start:.0f}s -> {args.closed_end:.0f}s (alpha boosted)")

    start = time.time()
    next_eeg = start
    next_band = start
    next_horseshoe = start
    next_acc = start
    eeg_dt = 1.0 / SAMPLE_RATE
    band_dt = 1.0 / BAND_RATE
    horseshoe_dt = 1.0 / HORSESHOE_RATE
    acc_dt = 1.0 / ACC_RATE

    sent_eeg = sent_band = sent_horseshoe = 0

    try:
        while True:
            now = time.time()
            t = now - start
            if t >= args.duration:
                break

            if now >= next_eeg:
                tp9, af7, af8, tp10 = gen_eeg_sample(t, args.closed_start, args.closed_end)
                client.send_message("/muse/eeg", [tp9, af7, af8, tp10])
                sent_eeg += 1
                next_eeg += eeg_dt

            if now >= next_band:
                bands = gen_band_powers(t, args.closed_start, args.closed_end)
                for name, vals in bands.items():
                    client.send_message(f"/muse/elements/{name}_absolute", vals)
                sent_band += 1
                next_band += band_dt

            if now >= next_horseshoe:
                client.send_message("/muse/elements/horseshoe", [1, 1, 1, 1] if args.good_contact else [2, 4, 1, 2])
                sent_horseshoe += 1
                next_horseshoe += horseshoe_dt

            if now >= next_acc:
                client.send_message("/muse/acc", [random.gauss(0, 0.05), random.gauss(0, 0.05), random.gauss(1, 0.05)])
                next_acc += acc_dt

            time.sleep(0.0005)  # avoid pegging the CPU
    except KeyboardInterrupt:
        print("\n[mock_sender] interrupted")

    print(f"[mock_sender] done. sent {sent_eeg} eeg, {sent_band} band, {sent_horseshoe} horseshoe packets")


if __name__ == "__main__":
    main()
