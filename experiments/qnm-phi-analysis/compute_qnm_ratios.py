"""
Compute Schwarzschild QNM frequencies and analyze phi ratios.

Requirements: pip install qnm
Source: qnm v0.4.4 (Stein 2019), Leaver continued fraction method
Units: omega * M (geometric units, G = c = 1)
Perturbation: gravitational (s = -2)

Usage: python compute_qnm_ratios.py
"""

import qnm
import warnings
import math
from fractions import Fraction

warnings.filterwarnings('ignore')

PHI = (1 + math.sqrt(5)) / 2  # 1.6180339887498949...


def compute_frequencies(l_range=range(2, 15), n_range=range(8)):
    """Compute QNM frequencies for given l and n ranges."""
    data = {}
    for l in l_range:
        data[l] = {}
        for n in n_range:
            try:
                mode = qnm.modes_cache(s=-2, l=l, m=0, n=n)
                omega, A, sep = mode(a=0)
                data[l][n] = omega
            except Exception:
                pass
    return data


def print_frequency_tables(data):
    """Print frequency tables for l=2,3,4."""
    print("=" * 90)
    print("SCHWARZSCHILD BLACK HOLE QUASINORMAL MODE FREQUENCIES")
    print("Gravitational perturbations (s=-2), units: omega * M")
    print("=" * 90)

    for l in [2, 3, 4]:
        if l not in data:
            continue
        print(f"\n--- l = {l} ---")
        for n in sorted(data[l].keys()):
            omega = data[l][n]
            print(f"  n={n}:  omega*M = {omega.real:+.10f} {omega.imag:+.10f}i")


def analyze_l_ratios(data):
    """Analyze consecutive l-mode ratios."""
    print("\n" + "=" * 90)
    print("CONSECUTIVE l-MODE RATIOS: Re(omega(l+1,n)) / Re(omega(l,n))")
    print("=" * 90)

    for n in range(8):
        hits = []
        for l in sorted(data.keys()):
            if l + 1 in data and n in data.get(l, {}) and n in data.get(l + 1, {}):
                r = data[l + 1][n].real / data[l][n].real
                pct = abs(r - PHI) / PHI * 100
                marker = " <-- WITHIN 2%" if pct < 2 else ""
                hits.append(f"    l={l + 1}/l={l}: {r:.10f}  (phi diff: {pct:.4f}%){marker}")
        if hits:
            print(f"\n  --- Overtone n={n} ---")
            for h in hits:
                print(h)


def analyze_overtone_ratios(data):
    """Analyze consecutive overtone ratios."""
    print("\n" + "=" * 90)
    print("CONSECUTIVE OVERTONE RATIOS: Re(omega(l,n)) / Re(omega(l,n+1))")
    print("=" * 90)

    for l in [2, 3, 4]:
        if l not in data:
            continue
        print(f"\n  --- l = {l} ---")
        for n in range(7):
            if n in data[l] and n + 1 in data[l]:
                r = data[l][n].real / data[l][n + 1].real
                pct = abs(r - PHI) / PHI * 100
                marker = " <-- WITHIN 2%" if pct < 2 else ""
                print(f"    n={n}/n={n + 1}: {r:.10f}  (phi diff: {pct:.4f}%){marker}")


def find_all_phi_ratios(data, threshold=2.0):
    """Find all mode pairs whose Re ratio is within threshold% of phi."""
    print("\n" + "=" * 90)
    print(f"ALL MODE PAIRS WITHIN {threshold}% OF PHI")
    print("=" * 90)

    all_modes = []
    for l in data:
        for n in data[l]:
            all_modes.append((l, n, data[l][n].real))

    results = []
    seen = set()
    for i in range(len(all_modes)):
        for j in range(i + 1, len(all_modes)):
            re1 = all_modes[i][2]
            re2 = all_modes[j][2]
            if re1 > 0 and re2 > 0:
                r = max(re1, re2) / min(re1, re2)
                pct = abs(r - PHI) / PHI * 100
                if pct < threshold:
                    if re1 > re2:
                        label = f"(l={all_modes[i][0]},n={all_modes[i][1]})/(l={all_modes[j][0]},n={all_modes[j][1]})"
                    else:
                        label = f"(l={all_modes[j][0]},n={all_modes[j][1]})/(l={all_modes[i][0]},n={all_modes[i][1]})"
                    key = f"{r:.8f}"
                    if key not in seen:
                        seen.add(key)
                        results.append((pct, label, r))

    for pct, label, r in sorted(results)[:20]:
        print(f"  {label}: {r:.12f}  (phi diff: {pct:.6f}%)")

    return len(results), len(all_modes)


def eikonal_analysis(data):
    """Compare with eikonal approximation."""
    print("\n" + "=" * 90)
    print("EIKONAL LIMIT COMPARISON")
    print("=" * 90)

    r_actual = data[3][0].real / data[2][0].real
    r_eikonal = 3.5 / 2.5

    print(f"\n  l=3/l=2 fundamental mode:")
    print(f"    Actual ratio:   {r_actual:.12f}")
    print(f"    Eikonal (l>>1): {r_eikonal:.12f}")
    print(f"    phi:            {PHI:.12f}")
    print(f"    8/5 (Fib):      {8 / 5:.12f}")
    print()
    print(f"    Distance eikonal -> actual:  {r_actual - r_eikonal:.10f}")
    print(f"    Distance eikonal -> phi:     {PHI - r_eikonal:.10f}")
    print(f"    Actual is {(r_actual - r_eikonal) / (PHI - r_eikonal) * 100:.1f}% of the way from eikonal to phi")
    print()

    f = Fraction(r_actual).limit_denominator(100)
    print(f"    Best rational approximant (denom <= 100): {f} = {float(f):.10f}")


def monte_carlo_test(data, n_trials=1000):
    """Test statistical significance of phi-ratios."""
    import random
    random.seed(42)

    print("\n" + "=" * 90)
    print(f"MONTE CARLO SIGNIFICANCE TEST ({n_trials} trials)")
    print("=" * 90)

    all_re = [data[l][n].real for l in data for n in data[l] if data[l][n].real > 0]
    N = len(all_re)
    min_re = min(all_re)
    max_re = max(all_re)

    # Count actual phi-ratios
    actual_count = 0
    total_pairs = 0
    for i in range(N):
        for j in range(i + 1, N):
            r = max(all_re[i], all_re[j]) / min(all_re[i], all_re[j])
            pct = abs(r - PHI) / PHI * 100
            total_pairs += 1
            if pct < 1.0:
                actual_count += 1

    # Monte Carlo
    mc_counts = []
    for _ in range(n_trials):
        rand_vals = [random.uniform(min_re, max_re) for _ in range(N)]
        count = 0
        for i in range(len(rand_vals)):
            for j in range(i + 1, len(rand_vals)):
                r = max(rand_vals[i], rand_vals[j]) / min(rand_vals[i], rand_vals[j])
                if abs(r - PHI) / PHI * 100 < 1.0:
                    count += 1
        mc_counts.append(count)

    avg_mc = sum(mc_counts) / len(mc_counts)
    print(f"\n  Modes: {N}, Total pairs: {total_pairs}")
    print(f"  Pairs within 1% of phi: actual={actual_count}, random avg={avg_mc:.1f}")
    print(f"  Enrichment factor: {actual_count / avg_mc:.2f}x" if avg_mc > 0 else "")


if __name__ == "__main__":
    data = compute_frequencies()
    print_frequency_tables(data)
    analyze_l_ratios(data)
    analyze_overtone_ratios(data)
    find_all_phi_ratios(data, threshold=0.5)
    eikonal_analysis(data)
    monte_carlo_test(data, n_trials=100)  # Reduced for speed
