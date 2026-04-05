# Schwarzschild Black Hole Quasinormal Mode Frequencies: Phi Ratio Analysis

**Date:** 2026-04-04
**Computed with:** `qnm` Python package v0.4.4 (Stein 2019), Leaver continued fraction method
**Units:** omega * M (geometric units, G = c = 1)
**Perturbation type:** Gravitational (spin-weight s = -2)

---

## 1. Exact Numerical QNM Frequencies

### Table 1: l = 2

| n | Re(omega*M) | -Im(omega*M) |
|---|-------------|---------------|
| 0 | 0.3736716844 | 0.0889623157 |
| 1 | 0.3467109969 | 0.2739148753 |
| 2 | 0.3010534546 | 0.4782769832 |
| 3 | 0.2515049622 | 0.7051482024 |
| 4 | 0.2075145798 | 0.9468448909 |
| 5 | 0.1692994031 | 1.1956080541 |
| 6 | 0.1332523402 | 1.4479106262 |
| 7 | 0.0928223354 | 1.7038411718 |

### Table 2: l = 3

| n | Re(omega*M) | -Im(omega*M) |
|---|-------------|---------------|
| 0 | 0.5994432884 | 0.0927030479 |
| 1 | 0.5826438030 | 0.2812981134 |
| 2 | 0.5516849008 | 0.4790927510 |
| 3 | 0.5119619111 | 0.6903370960 |
| 4 | 0.4701740058 | 0.9156493925 |
| 5 | 0.4313864786 | 1.1521513621 |
| 6 | 0.3976595242 | 1.3959122427 |
| 7 | 0.3689922759 | 1.6438445284 |

### Table 3: l = 4

| n | Re(omega*M) | -Im(omega*M) |
|---|-------------|---------------|
| 0 | 0.8091783775 | 0.0941639610 |
| 1 | 0.7966315320 | 0.2843343494 |
| 2 | 0.7727095326 | 0.4799081751 |
| 3 | 0.7398367300 | 0.6839243190 |
| 4 | 0.7015155093 | 0.8982389718 |
| 5 | 0.6615724994 | 1.1229767535 |
| 6 | 0.6231088747 | 1.3566862683 |
| 7 | 0.5879088250 | 1.5971706806 |

**Cross-check:** The n=0 values agree with Kokkotas & Schmidt (1999) Table 2 to all reported digits:
- l=2: 0.37367 - 0.08896i (5 digits match)
- l=3: 0.59944 - 0.09270i (5 digits match)
- l=4: 0.80918 - 0.09416i (5 digits match)

**Note on units:** Berti's ringdown.info uses c = G = 2M = 1, so their frequencies are exactly 2x larger. E.g., their l=2 fundamental is 0.747343 - 0.177925i = 2 * (0.37367 - 0.08896i).

---

## 2. Consecutive l-Mode Ratios: Re(omega(l+1,n)) / Re(omega(l,n))

### Fundamental mode (n=0):

| Ratio | Value | Deviation from phi | Deviation from 3/2 |
|-------|-------|-------------------|---------------------|
| l=3/l=2 | **1.6041977849** | **0.855%** | 6.947% |
| l=4/l=3 | 1.3498831218 | 16.573% | 10.007% |

### All overtones:

| n | l=3/l=2 | phi diff | l=4/l=3 | phi diff |
|---|---------|----------|---------|----------|
| 0 | **1.6041977849** | **0.855%** | 1.3498831218 | 16.573% |
| 1 | 1.6804883845 | 3.860% | 1.3672702394 | 15.498% |
| 2 | 1.8325147655 | 13.256% | 1.4006356373 | 13.436% |
| 3 | 2.0355936779 | 25.810% | 1.4451011179 | 10.688% |
| 4 | 2.2657037028 | -- | 1.4920338015 | 7.787% |
| 5 | 2.5479093862 | -- | 1.5335958175 | 5.219% |
| 6 | 2.9842459849 | -- | 1.5669406535 | 3.158% |
| 7 | 3.9753279367 | -- | **1.5932821997** | **1.530%** |

---

## 3. Consecutive Overtone Ratios: Re(omega(l,n)) / Re(omega(l,n+1))

| n/n+1 | l=2 | l=3 | l=4 |
|-------|-----|-----|-----|
| 0/1 | 1.0778 | 1.0288 | 1.0157 |
| 1/2 | 1.1517 | 1.0561 | 1.0310 |
| 2/3 | 1.1970 | 1.0776 | 1.0444 |
| 3/4 | 1.2120 | 1.0889 | 1.0546 |
| 4/5 | 1.2257 | 1.0899 | 1.0604 |
| 5/6 | 1.2705 | 1.0848 | 1.0617 |
| 6/7 | 1.4356 | 1.0777 | 1.0599 |

**No overtone ratio is close to phi.** The overtone real frequencies decrease slowly for low n and more rapidly for high n. The ratios are all significantly below phi (closest: l=2, n=6/7 at 1.4356, still 11.3% off).

---

## 4. Eikonal Limit Analysis

In the eikonal (geometric optics) limit l >> 1 (Schutz & Will 1985):

    Re(omega*M) ~ (l + 1/2) * Omega_c

where Omega_c = 1/(3*sqrt(3)*M) = 0.19245... is the orbital frequency at the unstable photon orbit (r = 3M).

This predicts:
    Re(omega(l+1)) / Re(omega(l)) -> (l + 3/2) / (l + 1/2)

For l=2: eikonal ratio = 3.5/2.5 = 1.400

**The actual ratio (1.6042) exceeds the eikonal prediction by 14.6%.** The eikonal approximation is poorest at low l. The actual l=3/l=2 ratio sits 93.7% of the way from the eikonal value (1.400) to phi (1.618).

---

## 5. Phi Analysis: All Mode Combinations Within 2%

Searching ALL pairs of Re(omega) across l=2..14, n=0..7 (104 modes, 5356 unique pairs):

### Closest to phi (within 0.5%):

| Pair | Ratio | phi deviation |
|------|-------|---------------|
| (l=7,n=5) / (l=4,n=0) | 1.618095661 | **0.004%** |
| (l=13,n=2) / (l=8,n=2) | 1.617667736 | 0.023% |
| (l=12,n=4) / (l=8,n=7) | 1.617662108 | 0.023% |
| (l=8,n=4) / (l=5,n=3) | 1.617638995 | 0.024% |
| (l=13,n=6) / (l=8,n=4) | 1.617435578 | 0.037% |
| (l=10,n=4) / (l=6,n=1) | 1.617420431 | 0.038% |
| (l=14,n=4) / (l=9,n=6) | 1.618794369 | 0.047% |
| (l=13,n=4) / (l=8,n=3) | 1.619321849 | 0.080% |
| (l=7,n=3) / (l=5,n=6) | 1.619613734 | 0.098% |
| (l=12,n=7) / (l=7,n=1) | 1.619638889 | 0.099% |

### The physically most meaningful ratio within 2%:

| Pair | Ratio | phi deviation | Note |
|------|-------|---------------|------|
| **l=3/l=2, n=0** | **1.604198** | **0.855%** | Fundamental modes of lowest gravitational multipoles |
| l=4/l=3, n=7 | 1.593282 | 1.530% | High overtone |

---

## 6. Statistical Significance Assessment

Monte Carlo test: 1000 trials of 104 random values drawn uniformly from the same range [0.093, 2.773].

| Threshold | QNM actual | Random average | Enrichment |
|-----------|-----------|----------------|------------|
| 0.01% | 1 | 0.7 | 1.4x |
| 0.05% | 7 | 3.6 | 1.9x |
| 0.10% | 10 | 7.1 | 1.4x |
| 0.50% | 35 | 35.3 | 1.0x |
| 1.00% | 70 | 70.5 | 1.0x |
| 2.00% | 149 | 140.9 | 1.1x |

**Interpretation:** At the 0.5% and wider thresholds, the QNM spectrum shows NO statistically significant enrichment of phi-ratios compared to random numbers in the same range. The slight enrichment at very tight thresholds (0.01-0.05%) could be a small-number fluctuation.

This means: **the occurrence of phi-like ratios in QNM spectra is consistent with coincidence given the number of possible pairs examined (5356).** The spectrum is dense enough that many ratios are achievable.

---

## 7. The l=3/l=2 Fundamental Mode Ratio: Why It Is Close to Phi

The ratio Re(omega(l=3,n=0)) / Re(omega(l=2,n=0)) = 1.6042 is closest to the Fibonacci convergent **8/5 = 1.600** (within 0.26%), not exactly phi.

### Why the ratio exceeds the eikonal prediction:

The eikonal approximation assumes l >> 1. For l=2, the WKB/eikonal approach has large corrections. These corrections push the ratio from 1.400 (eikonal) toward larger values. The fact that the correction lands near phi is a consequence of:

1. The l=2 mode being maximally sensitive to curvature corrections (lowest allowed gravitational multipole)
2. The WKB correction series producing a ratio that happens to fall near 8/5

The exact ratio 77/48 = 1.604167 matches the computed value to 0.002%.

### Is this ratio universally phi?

No. The ratio:
- Is NOT exactly phi (1.6180...) -- it is 0.855% below
- Is closest to the rational approximant 8/5 (a Fibonacci ratio, but the 4th convergent, not phi itself)
- Changes for different perturbation types (scalar s=0 and vector s=1 give different ratios)
- Is a property of the Regge-Wheeler/Zerilli potential shape, not a universal constant

---

## 8. Existing Literature: Golden Ratio in Black Hole Physics

### Papers connecting phi to black holes (NOT to QNMs):

1. **Cruz, Olivares & Villanueva (2017)** - "The golden ratio in Schwarzschild-Kottler black holes" (EPJC 77, 123). The turning points of null geodesics with maximal radial acceleration are in the golden ratio. This is about geodesic orbits, not QNMs.

2. **Baez (2013)** - Blog post discussing a link between black holes and the golden ratio involving the Bekenstein-Hawking entropy and specific heat.

3. **Sigalotti & Mejias (2006)** - Golden ratio in special relativity kinematics.

4. **Sonnino & Nardone (2024)** - Golden ratio in extremal Kerr-Newman families.

5. **Parker (2026)** - Golden ratio fixed point in Schwarzschild time dilation: gamma(phi * r_s) = phi. Already in this repository at experiments/phi-time-dilation/.

### Papers connecting phi to QNM spectra:

**NONE FOUND.** An extensive literature search found no published papers analyzing or reporting phi-like ratios in quasinormal mode frequency spectra.

---

## 9. Summary and Honest Assessment

### What is true:
- The fundamental mode ratio Re(omega(l=3)) / Re(omega(l=2)) = 1.6042, within 0.86% of phi
- This is the closest integer-l ratio to phi in the fundamental mode spectrum
- The ratio 8/5 (Fibonacci convergent) matches even better (0.26%)
- Across all 5356 possible mode pairs, some ratios match phi to <0.01% (closest: 0.004%)

### What is NOT true:
- The QNM spectrum does NOT have a systematic phi structure
- The statistical occurrence of phi-like ratios is NOT significantly above random chance
- No consecutive overtone ratio approaches phi
- The l=3/l=2 ratio is NOT exactly phi -- it is 0.86% below
- The imaginary parts show no phi structure at all

### What would be worth publishing:
The l=3/l=2 fundamental mode ratio being within 1% of phi is a **numerical curiosity**, not a deep connection. It is explainable by the WKB correction structure at low l. However, combined with the phi-fixed-point in Schwarzschild time dilation (already published as a question on Physics Stack Exchange), it may be worth a brief note documenting the near-miss, explicitly stating it is NOT exact, and explaining the eikonal correction origin.

---

## References

1. Kokkotas, K.D. & Schmidt, B.G. (1999). "Quasi-Normal Modes of Stars and Black Holes." Living Reviews in Relativity, 2, 2. [gr-qc/9909058]
2. Berti, E., Cardoso, V. & Starinets, A.O. (2009). "Quasinormal modes of black holes and black branes." Class. Quantum Grav. 26, 163001. [arXiv:0905.2975]
3. Stein, L.C. (2019). "qnm: A Python package for calculating Kerr quasinormal modes." J. Open Source Softw. 4(42), 1683.
4. Schutz, B.F. & Will, C.M. (1985). "Black hole normal modes: a semianalytic approach." Astrophys. J. Lett. 291, L33.
5. Cruz, N., Olivares, M. & Villanueva, J.R. (2017). "The golden ratio in Schwarzschild-Kottler black holes." EPJC 77, 123.
6. Maggiore, M. (2008). "Physical Interpretation of the Spectrum of Black Hole Quasinormal Modes." Phys. Rev. Lett. 100, 141301.
