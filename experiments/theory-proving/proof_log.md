# Theory Proving Log
---

## Claim 1 -- Deep sedation reverses the effect

**Date:** 2026-03-30
**Tested by:** Kai (scientist mode)

### Claim
The two-channel K finding (propofol selectively suppresses phase coupling K_P while leaving amplitude coupling K_A unchanged) replicates on a second independent public propofol EEG dataset.

### Criteria
- **SUPPORTED**: K_P decreases significantly (p < 0.05) while K_A does not change (p > 0.05)
- **NOT SUPPORTED**: K_A also changes, or K_P does not decrease
- **INCONCLUSIVE**: Trends in right direction but insufficient power

### Data

**Original dataset:** Cambridge Propofol Sedation Dataset (Chennu et al., 2014)
- N = 20 healthy volunteers, 91 EEG channels, 250 Hz
- Conditions: baseline, mild (0.6 ug/ml), moderate (1.2 ug/ml), recovery
- Subjects were RESPONSIVE at moderate sedation
- License: CC BY 2.0 UK

**Replication dataset:** OpenNeuro ds005620 (Bajwa et al., 2025)
- N = 21 healthy participants (10 used), 65 EEG channels (62 EEG + 3 physio), 5000 Hz
- Conditions: task-awake (eyes closed baseline) vs task-sed2 (deep sedation, pre-awakening)
- Subjects were UNRESPONSIVE during sedation (needed to be awakened)
- License: CC0
- DOI: 10.18112/openneuro.ds005620.v1.0.0

**Critical difference:** Cambridge used MODERATE sedation (responsive). Oslo used DEEP sedation (unresponsive). These are different neurophysiological states.

### Method

1. Downloaded 10 subjects' EEG data (awake: first 60s via S3 range request; sed2: full 60s file)
2. Preprocessing: 0.5 Hz highpass, bad channel rejection (variance 3x/1/3x median), downsample 5000->250 Hz, artifact epoch rejection (ptp > 3x median)
3. NO average re-referencing (per original paper's critical methodological point)
4. Bandpass filtered into 5 bands: delta (1-4), theta (4-8), alpha (8-13), beta (13-30), gamma (30-45 Hz)
5. K_A: Pearson |correlation| of amplitude envelopes per channel per 2s epoch, weighted by consonance quality Q
6. K_P: n:m phase-locking value at nearest consonant frequency ratio, weighted by Q
7. Statistics: Wilcoxon signed-rank test (within-subject, paired)

Code: `C:\DocumentsJaie\AI\AlternateScience\Experiments\RalphLoop\propofol_replication\two_channel_k_replication.py`

### Results

```
  N = 10 subjects

  Measure     Awake (mean +/- SEM)  Sedation (mean +/- SEM)  Change      p       d
  K_A          0.0996 +/- 0.0024     0.1083 +/- 0.0017       +9.3%   0.0488  +0.903
  K_P          0.0142 +/- 0.0001     0.0154 +/- 0.0004       +8.3%   0.0098  +1.137
  K            0.0376 +/- 0.0004     0.0408 +/- 0.0007       +8.7%   0.0059  +1.265
  theta (deg)  8.15 +/- 0.21         8.09 +/- 0.18           -0.1    0.9219

  Direction consistency:
    K_P increased in 8/10 subjects (80%)
    K_A increased in 9/10 subjects (90%)
    K   increased in 9/10 subjects (90%)
```

### Comparison with Original

```
                Original (Cambridge)    Replication (Oslo)
  K_A change      +0.2% (p=0.89)        +9.3% (p=0.049)
  K_P change     -10.7% (p=0.023)       +8.3% (p=0.010)
  K change        ~-5.6% (p=0.037)      +8.7% (p=0.006)
  N                     20                       10
  Sedation depth  Moderate (responsive)  Deep (unresponsive)
```

### Sanity Check

Power spectra at Cz confirmed valid propofol EEG:
- Alpha power doubled (propofol frontal alpha signature)
- Beta power increased 3.7x (propofol beta enhancement)
- Gamma power dropped to 0.2x (expected suppression)
- Overall variance 3.4x lower (expected amplitude reduction)
- Data range and quality consistent with published propofol EEG characteristics

### Verdict: NOT SUPPORTED

The two-channel K dissociation does NOT replicate. The result is the OPPOSITE: under deep propofol sedation, BOTH K_A (+9.3%, p=0.049) and K_P (+8.3%, p=0.010) increase significantly. The effect is strong (d > 0.9) and consistent (8-9/10 subjects).

### Why It Failed -- Scientific Interpretation

The failure is likely dose-dependent, not a flaw in the original finding:

1. **Moderate vs deep sedation are different neurophysiological states.** At moderate propofol (Cambridge, 1.2 ug/ml), subjects are drowsy but responsive. EEG shows partial desynchronization -- some coupling weakens while energy is maintained. At deep propofol (Oslo, higher concentration), subjects are unresponsive. EEG shows characteristic hyper-synchronized patterns.

2. **Propofol frontal alpha paradox.** Deep propofol produces a strong, coherent frontal alpha rhythm that is ABSENT in wakefulness. This "propofol alpha" would increase both amplitude correlation (envelopes co-fluctuate during burst-suppression) and phase-locking (highly synchronized oscillations at simple frequency ratios). This was confirmed: alpha power at Cz doubled under sedation.

3. **The balance angle theta is UNCHANGED** (p=0.92). This means K_A and K_P change together proportionally. There is no dissociation between channels -- the entire coupling structure scales up uniformly. This is a fundamentally different regime from the Cambridge finding where ONLY phase coupling changed.

4. **Possible dose-response curve:** K_P may follow an inverted-U pattern with propofol dose:
   - Low dose: K_P stable (no effect)
   - Moderate dose: K_P drops (Cambridge finding -- selective phase decoupling)
   - Deep dose: K_P increases (this finding -- hyper-synchronization)

### What Would Be Needed

A proper replication requires:
- A second dataset with MODERATE sedation (responsive subjects, similar propofol concentration)
- The Zenodo dataset (record 806176) might work but requires access request
- Alternatively, the Cambridge dataset itself could be split into halves for internal replication

### Files

- Analysis code: `RalphLoop/propofol_replication/two_channel_k_replication.py`
- Raw results: `RalphLoop/propofol_replication/replication_results.json`
- Downloaded data: `RalphLoop/propofol_replication/sub-*/` (10 subjects, ~1.56 GB)

---

## Claim 2 — Suggestive but not significant

**Date:** 2026-03-30
**Tested by:** Kai (scientist mode)

### Claim

The consonance weighting (Q factor) improves prediction of consciousness state beyond unweighted cross-frequency coupling. Compute K WITH consonance weighting and K WITHOUT (set all Q=1). Compare which better separates propofol conditions in the Cambridge dataset.

### Criteria

- **SUPPORTED**: Q-weighted K yields significantly larger effect size (Cohen's d) AND bootstrap test confirms p < 0.05
- **NOT SUPPORTED**: Unweighted K has equal/larger effect size, OR bootstrap comparison p >= 0.05
- **INCONCLUSIVE**: Insufficient data

### Data

Cambridge Propofol Sedation Dataset (same as Claim 1 original):
- N = 20 healthy volunteers, 91 EEG channels, 250 Hz
- Conditions compared: Baseline vs Moderate sedation (1.2 ug/ml)
- 80 total recordings processed (20 subjects x 4 conditions), 0 failures

### Method

1. Compute Q_MATRIX (consonance quality via Tenney height for nearest simple ratio)
2. Compute Q_UNIFORM (all band pairs weighted equally, Q=1)
3. For each subject x condition: same preprocessing, same band extraction, compute K with BOTH Q matrices
4. Compare separation metrics: Cohen's d, paired t-test, AUC-ROC
5. Bootstrap test (N=10,000): is |d_weighted| - |d_unweighted| > 0 significantly?

Code: `C:\DocumentsJaie\AI\AlternateScience\Experiments\RalphLoop\claim2_consonance_weighting_test.py`

### Critical Observation: Q_MATRIX Structure

The Q matrix has a stark binary structure:
```
         delta   theta   alpha    beta   gamma
  delta  0.000   0.169   1.000   1.000   1.000
  theta  0.169   0.000   0.204   0.204   0.204
  alpha  1.000   0.204   0.000   1.000   1.000
   beta  1.000   0.204   1.000   0.000   1.000
  gamma  1.000   0.204   1.000   1.000   0.000
```

6 of 10 band pairs get Q=1.0 (all octave relationships: delta-alpha, delta-beta, delta-gamma, alpha-beta, alpha-gamma, beta-gamma). The 4 theta-related pairs get Q≈0.17-0.20 — down-weighted ~5x. Consonance weighting, in practice, means: **suppress theta coupling by a factor of 5**.

### Results

```
METRIC              Q-WEIGHTED      UNWEIGHTED
----------------------------------------------
Baseline K mean     0.085300        0.134034
Moderate K mean     0.080502        0.132382
Mean difference    +0.004798       +0.001652
Cohen's d           0.5002          0.1229
t-statistic         2.2372          0.5498
p-value             0.037456        0.588842
AUC-ROC             0.6975          0.5700

BOOTSTRAP TEST: Is |d_weighted| > |d_unweighted|?
  Mean |d_w| - |d_u| = +0.3152
  95% CI             = [-0.2539, +0.5710]
  p-value            = 0.0821

COMPONENT ANALYSIS:
  K_A: d_weighted=-0.009, d_unweighted=-0.289 → UNWEIGHTED better
  K_P: d_weighted= 1.131, d_unweighted= 1.019 → WEIGHTED better
```

### Interpretation

**The Q-weighted K finds a significant effect (p=0.037, d=0.50) where unweighted K does not (p=0.589, d=0.12).** In practical terms, the consonance weighting "works" — it produces a measure that discriminates consciousness states. But the bootstrap comparison of the two approaches yields p=0.082, which does not clear the pre-registered threshold of p < 0.05.

The component analysis reveals WHY:
- **K_P (phase coupling):** Q-weighting helps slightly (d=1.13 vs 1.02). Phase-locking at consonant harmonic ratios may be more biologically meaningful than at arbitrary ratios.
- **K_A (amplitude coupling):** Q-weighting HURTS (d=-0.01 vs -0.29). By suppressing theta-related amplitude correlations, the weighting removes a signal that propofol actually changes.

The net effect: Q-weighting improves K_P discrimination but degrades K_A discrimination. The combined K = sqrt(K_A * K_P) benefits because K_P dominates the geometric mean when K_A is near-zero for the weighted version.

**Key insight:** The consonance weighting is almost entirely a theta suppressor. This helps for phase coupling (where theta adds noise to the consonant harmonic signal) but hurts amplitude coupling (where theta changes are part of the real propofol effect). A more nuanced weighting scheme — one that preserves theta amplitude information while emphasizing consonant phase relationships — might perform better.

### Verdict: NOT SUPPORTED

By the pre-registered criterion (bootstrap p < 0.05), the consonance weighting does NOT significantly outperform unweighted CFC. However, the data is suggestive (p=0.082) and the practical difference is large (d=0.50 vs 0.12). With a larger sample or a refined weighting scheme, this might cross the threshold.

**This is not a clean failure.** It's a "not yet proven" with a clear direction for improvement: decouple the Q weighting for amplitude vs phase channels, or use a weighting that doesn't collapse to binary theta/non-theta.

### What Would Be Needed

1. **Larger N** — the bootstrap CI is wide [-0.25, +0.57]. N=40+ would narrow it.
2. **Refined Q scheme** — separate Q matrices for K_A and K_P, since the optimal weighting differs by channel.
3. **Non-binary Q** — the current Q has only two effective values (1.0 and ~0.2). A continuous weighting based on actual harmonic ratios might capture more structure.
4. **Cross-validation** — split Cambridge data, optimize Q on half, test on half.

### Files

- Analysis code: `C:\DocumentsJaie\AI\AlternateScience\Experiments\RalphLoop\claim2_consonance_weighting_test.py`
- Raw results: `C:\DocumentsJaie\AI\AlternateScience\Experiments\RalphLoop\claim2_results.json`

---

## Claim 3 -- Simple ratios are dense, not special

**Date:** 2026-03-30
**Tested by:** Kai (scientist mode)

### Claim

EEG frequency band ratios cluster near simple integer ratios more than chance. Take the canonical band definitions (delta 1-4, theta 4-8, alpha 8-13, beta 13-30, gamma 30-45 Hz). Compute all pairwise ratios of band center frequencies. Test whether these ratios are closer to simple ratios (Farey neighbors) than random frequency bands would be.

### Criteria

- **SUPPORTED**: Permutation test p < 0.05 -- real EEG ratios closer to simple ratios than random
- **NOT SUPPORTED**: p >= 0.05 -- EEG ratios are no closer than random
- **INCONCLUSIVE**: Insufficient data or ambiguous result

### Data

No external data needed. The canonical EEG band definitions are the data:

```
Band     Range (Hz)    Center (Hz)
delta    1-4           2.5
theta    4-8           6.0
alpha    8-13          10.5
beta     13-30         21.5
gamma    30-45         37.5
```

10 pairwise ratios (all pairs), 4 adjacent ratios.

### Method

Two versions tested to guard against metric artifacts.

**Version 1 (v1):** Distance to nearest ratio in Farey sequence of order N.
- Built set of simple ratios p/q with p+q <= N+1 for N in {3, 5, 7, 9, 12}
- For each pairwise ratio, measured distance to nearest Farey ratio
- Null: 100,000 draws of 5 random centers from Uniform[1,50]
- Also tested: constrained null (non-overlapping bands), geometric mean centers

**Version 2 (v2):** Three metrics to test robustness.
1. **Harmonic distance:** Distance to nearest p/q with q <= 12 (raw space)
2. **Log distance:** Distance of log2(ratio) to nearest log2(simple_ratio) (log space)
3. Both tested against uniform null AND log-spaced null, for all-pairs AND adjacent-only

Code: `C:\DocumentsJaie\AI\AlternateScience\Experiments\RalphLoop\claim3_eeg_ratios.py` (v1)
Code: `C:\DocumentsJaie\AI\AlternateScience\Experiments\RalphLoop\claim3_eeg_ratios_v2.py` (v2)

### Results

**Pairwise ratios and their nearest simple approximations:**

```
Pair              Ratio    Nearest   Distance
delta/theta       2.400    12/5      0.0000
delta/alpha       4.200    21/5      0.0000
delta/beta        8.600    43/5      0.0000
delta/gamma      15.000    15/1      0.0000
theta/alpha       1.750    7/4       0.0000
theta/beta        3.583    43/12     0.0000
theta/gamma       6.250    25/4      0.0000
alpha/beta        2.048    2/1       0.0476
alpha/gamma       3.571    25/7      0.0000
beta/gamma        1.744    7/4       0.0058
```

**Version 1 results (Farey order 7, uniform null):**
```
Observed score: 1.120
Null mean:      0.872
Null median:    0.150
p-value:        0.800
```

**Version 2 results:**
```
Test                           Obs      Null mean   p-value
All-pairs, harmonic, uniform   0.0042   0.0086      0.031 *
All-pairs, log-dist, uniform   0.0659   0.0660      0.833
All-pairs, harmonic, log-null  0.0042   0.0084      0.033 *
All-pairs, log-dist, log-null  0.0659   0.1233      0.503
Adjacent, harmonic, uniform    0.0104   --          0.632
Adjacent, log-dist, uniform    0.0198   --          0.121
Adjacent, harmonic, log-null   0.0104   --          0.691
Adjacent, log-dist, log-null   0.0198   --          0.125
```

**Sensitivity across Farey orders (v1):**
```
max_order=3:   p=0.785
max_order=5:   p=0.789
max_order=7:   p=0.796
max_order=9:   p=0.806
max_order=12:  p=0.837
```

### Critical Analysis: The Harmonic Distance Artifact

The two starred results (harmonic distance, p=0.031-0.033) appear significant but are an **arithmetic artifact**, not evidence of consonance. Here is why:

1. The EEG band centers are half-integers: {2.5, 6.0, 10.5, 21.5, 37.5}
2. Their pairwise ratios are exact rational numbers (e.g., 7/4, 12/5, 25/4)
3. Random draws from Uniform[1,50] are irrational with probability 1
4. Any irrational number has nonzero distance to ALL rationals
5. Therefore the test is measuring "are exact rationals closer to rationals than irrationals?" -- trivially yes

The **log-distance metric** avoids this artifact because log2(p/q) is typically irrational even for simple p/q (except powers of 2). In log-space, both real and random ratios are on equal footing. And log-distance shows p=0.50-0.83: completely non-significant.

### Why the Claim Fails

**1. Simple ratios are DENSE in the relevant range.**

Adjacent EEG band ratios fall in [1.7, 2.5]. In that range, simple ratios are packed tight: 7/4=1.75, 2/1=2.0, 9/4=2.25, 5/2=2.5. The maximum distance to a simple ratio with q<=4 is about 0.125. ANY set of adjacent frequencies in this range will be "near" simple ratios. The EEG bands aren't special -- the number line is just consonant at small ratios.

**2. The band definitions are conventions, not constants.**

The canonical bands are human-defined ranges based on historical convention (Berger 1920s, Walter 1930s-40s). Different textbooks give slightly different boundaries (e.g., alpha as 8-12 or 8-13 Hz). The "centers" depend on where you draw arbitrary boundaries. Testing whether a convention is consonant tests the convention, not the brain.

**3. With only 5 bands (10 ratios, 4 adjacent), statistical power is very low.**

Even a real effect would be hard to detect. A more powerful test would use actual spectral peaks from individual EEG recordings, not canonical band labels.

### What This DOES Tell Us

The adjacent-band ratios are genuinely near simple values:
- theta/delta = 2.4 (near 5/2)
- alpha/theta = 1.75 (exactly 7/4)
- beta/alpha = 2.05 (near 2/1)
- gamma/beta = 1.74 (near 7/4)

But this is expected for ANY set of frequency bands that approximately double in center frequency (which EEG bands roughly do: 2.5, 6, 10.5, 21.5, 37.5). Logarithmically spaced bands will always have adjacent ratios near small integers. This is geometry, not neuroscience.

### Verdict: NOT SUPPORTED

No metric, null model, or sensitivity analysis shows significant evidence that EEG band ratios cluster near simple ratios more than chance. The one apparently significant result (harmonic distance p=0.031) is an arithmetic artifact. The robust log-distance metric gives p=0.50 (uniform) and p=0.50 (log-spaced). The claim fails cleanly.

**The deeper finding:** Simple ratios are DENSE at the scale of EEG band ratios. The claim confuses the density of consonance in the number line with a special property of EEG. Any frequency bands with roughly doubling centers would show the same pattern. The consonance is in the arithmetic, not in the brain -- at least not at the level of canonical band definitions.

### What Would Test the Real Question

If the question is "does the brain preferentially generate frequencies at consonant ratios," the test needs:
1. **Individual spectral peaks** from real EEG recordings, not canonical bands
2. **Peak frequency ratios** across subjects, not predefined categories
3. **Sufficient N** (100+ spectral peaks per recording)
4. **Null model**: same power spectrum shape with randomized peak locations (e.g., surrogate data with preserved 1/f structure but shuffled phase)

This is a feasible experiment. The current claim was the wrong test of a potentially real phenomenon.

### Files

- v1 code: `C:\DocumentsJaie\AI\AlternateScience\Experiments\RalphLoop\claim3_eeg_ratios.py`
- v2 code: `C:\DocumentsJaie\AI\AlternateScience\Experiments\RalphLoop\claim3_eeg_ratios_v2.py`

---

## Claim 4 — Meditation does not shift K toward 0.25

**Date:** 2026-03-30
**Result:** NOT SUPPORTED (p = 0.724)

### Precise Claim

Meditation shifts the coupling parameter K = sqrt(K_A * K_P) toward 0.25, regardless of starting position. If K starts above 0.25, meditation should decrease it. If below, meditation should increase it.

### Operationalization

- **K_A**: Consonance-weighted inter-band amplitude envelope correlation (Hilbert transform, 5 EEG bands, 10 band pairs).
- **K_P**: Consonance-weighted inter-band phase-locking value (n:m PLV at nearest consonant ratio).
- **K**: Geometric mean = sqrt(K_A * K_P).
- **Proof criterion**: |K_meditation - 0.25| < |K_thinking - 0.25| with p < 0.05 (paired, one-sided).
- **Disproof**: p >= 0.05, or K moves away from 0.25 during meditation.

### Data

OpenNeuro ds003969 (Delorme & Braboszcz, Meditation Research Institute, Rishikesh, India). CC0 license.

- **N = 20** subjects (of 98 available, first 20 downloaded)
- **16 EEG channels**, 256 Hz, BDF format
- **4 blocks per subject**: med1breath (breath counting), med2 (tradition-specific), think1, think2 (active thinking)
- **Conditions**: Meditation = average of med1breath + med2; Thinking = average of think1 + think2
- **Preprocessing**: High-pass 0.5 Hz, bad channel rejection (3x median variance), no average reference, 2-second epoch artifact rejection

### Results

#### Per-subject data
| Subject | K_med | K_think | \|K_m-0.25\| | \|K_t-0.25\| | Closer? |
|---------|-------|---------|-----------|-----------|---------|
| sub-001 | 0.0633 | 0.0693 | 0.1867 | 0.1807 | no |
| sub-002 | 0.0685 | 0.0626 | 0.1815 | 0.1874 | YES |
| sub-003 | 0.0724 | 0.0757 | 0.1776 | 0.1743 | no |
| sub-004 | 0.0660 | 0.0679 | 0.1840 | 0.1821 | no |
| sub-005 | 0.0771 | 0.0777 | 0.1729 | 0.1723 | no |
| sub-006 | 0.0620 | 0.0648 | 0.1880 | 0.1852 | no |
| sub-007 | 0.0819 | 0.0742 | 0.1681 | 0.1758 | YES |
| sub-008 | 0.0741 | 0.0695 | 0.1759 | 0.1805 | YES |
| sub-009 | 0.0570 | 0.0619 | 0.1930 | 0.1881 | no |
| sub-010 | 0.0657 | 0.0641 | 0.1843 | 0.1859 | YES |
| sub-011 | 0.0634 | 0.0624 | 0.1866 | 0.1876 | YES |
| sub-012 | 0.0643 | 0.0633 | 0.1857 | 0.1867 | YES |
| sub-013 | 0.0633 | 0.0684 | 0.1867 | 0.1816 | no |
| sub-014 | 0.0631 | 0.0604 | 0.1869 | 0.1896 | YES |
| sub-015 | 0.0618 | 0.0574 | 0.1882 | 0.1926 | YES |
| sub-016 | 0.0842 | 0.0760 | 0.1658 | 0.1740 | YES |
| sub-017 | 0.0631 | 0.0777 | 0.1869 | 0.1723 | no |
| sub-018 | 0.0650 | 0.0727 | 0.1850 | 0.1773 | no |
| sub-019 | 0.0686 | 0.0730 | 0.1814 | 0.1770 | no |
| sub-020 | 0.0710 | 0.0720 | 0.1790 | 0.1780 | no |

#### Statistical tests

**Primary (distance from 0.25):**
- Mean |K_med - 0.25| = 0.1822 +/- 0.0069
- Mean |K_think - 0.25| = 0.1815 +/- 0.0060
- Mean difference = -0.0008 (NEGATIVE: meditation further from 0.25)
- Paired t-test (one-sided): t = -0.606, **p = 0.724**
- Cohen's d = -0.139
- 9/20 subjects closer during meditation, sign test p = 0.748

**Secondary (direction by starting position):**
- ALL 20 subjects had K_think < 0.25 (range: 0.057-0.078)
- 0 subjects started above 0.25 — cannot test bidirectional convergence
- Among below-0.25 subjects: K decreased slightly (dK = -0.001, p = 0.724)
- Direction is AWAY from 0.25, not toward it

**Tertiary (raw K and channels):**
- K_meditation = 0.0678 +/- 0.0069
- K_thinking = 0.0685 +/- 0.0060
- dK = -0.001, t = -0.606, p = 0.551
- dK_A = -0.0013, p = 0.597 (not significant)
- dK_P = -0.0001, p = 0.904 (not significant)

**Wilcoxon (robustness):**
- W = 94.0, p = 0.663 (confirms: no effect)

### Interpretation

1. **K is approximately 0.07, not 0.25.** All subjects in both conditions show K values far below 0.25. The prediction that K should be near 0.25 (or move toward it) is not supported by this data.

2. **Meditation does not change K.** The difference between meditation and thinking is dK = -0.001 (0.07 vs 0.07), statistically indistinguishable from zero. Neither amplitude coupling (K_A) nor phase coupling (K_P) shows any condition effect.

3. **The claim is untestable in its strongest form.** Since no subject starts above K = 0.25, we cannot test whether meditation produces convergence from both sides. All we can test is whether it increases K from the below-0.25 starting point — and it does not.

4. **Possible explanations for low K:**
   - Consonance weighting (Q matrix) suppresses most band pairs (only octave-related pairs get Q > 0). This may systematically reduce K.
   - Canonical band boundaries (delta/theta/alpha/beta/gamma) may not align with individual spectral peaks. Claim 3 showed that testing canonical labels tests convention, not brain organization.
   - The measure may need calibration — K_crit from the propofol study was 0.236, suggesting the absolute scale depends on channel count and preprocessing.

5. **Cross-study comparison:** K = 0.07 here (16 channels) vs K = 0.08 in propofol study (91 channels). The systematic offset suggests K scale depends on electrode density. K = 0.25 may be a theoretical fixed point that maps to different absolute values depending on measurement setup.

### What this failure teaches

The K = 0.25 prediction has now failed in every direct empirical test (Claims 1-4). The most informative failure is that K ≈ 0.07 across ALL conditions and subjects, with no meditation effect. This suggests either:
- K = 0.25 is not an attractor for this measure
- The measure needs fundamental revision (individual peaks, different reference, different weighting)
- K = 0.25 operates at a different scale than raw CFC coupling values

The propofol study found K_crit ≈ 0.236, which is close to 0.25 but was calibrated to that dataset. The key question is whether 0.25 is a universal constant or a dataset-dependent value.

### Files

- Code: `C:\DocumentsJaie\AI\AlternateScience\Experiments\RalphLoop\claim4_meditation_k.py`
- Data: `C:\DocumentsJaie\AI\AlternateScience\datasets\openneuro_ds003969\` (20 of 98 subjects)
- Existing pipeline: `C:\DocumentsJaie\AI\AlternateScience\Experiments\scripts\two_channel_k_pipeline.py`

---

## Claim 5 -- Cross-study inverted-U is not testable with current data

**Date:** 2026-03-30
**Tested by:** Kai (scientist mode)
**Result:** INCONCLUSIVE (p = 0.060 all PAC; p = 0.006 slow-alpha only N=6)

### Precise Claim

The inverted-U between coupling and consciousness holds across published studies. At very low coupling (e.g., coma, severe brain injury), consciousness is low. At intermediate coupling, consciousness peaks. At very high coupling (e.g., seizure, deep anesthesia hypersynchrony), consciousness drops again. The relationship is quadratic with negative leading coefficient.

### Operationalization

- **Coupling measures**: Phase-amplitude coupling (PAC) modulation index, cross-frequency coupling (CFC), coherence, weighted symbolic mutual information (wSMI), Perturbational Complexity Index (PCI)
- **Consciousness states**: brain death, coma, vegetative state (VS/UWS), minimally conscious state (MCS), NREM sleep (N2/N3), REM sleep, anesthesia (propofol/sevoflurane/ketamine/midazolam/xenon), normal wakefulness, seizure
- **Test**: Quadratic fit (y = ax^2 + bx + c) vs linear fit (y = mx + b), F-test for nested models. Inverted-U requires: (1) F-test p < 0.05, and (2) leading coefficient a < 0.

### Data Sources

Five studies compiled, plus PCI reference data:

1. **Mukamel et al. 2014** (J Neurosci): Slow-alpha PAC (0.1-2 Hz phase, 8-14 Hz amplitude) under propofol, humans. MI = 0.006 (awake) to 0.012 (LOC). Two distinct coupling patterns: trough-max at LOC transitions, peak-max at deep unconsciousness.

2. **Pal et al. 2017** (Front Syst Neurosci): Delta-gamma and theta-gamma PAC under propofol, sevoflurane, and ketamine in rat frontal cortex. All three anesthetics significantly increased delta-low gamma and theta-low gamma PAC (p < 0.0001). Returned to baseline during recovery.

3. **Frontiers 2025** (Frontiers in Psychology): Delta-gamma PAC in disorders of consciousness (20 HC, 21 MCS, 21 UWS) during auditory oddball. Between-group differences in delta-gamma coupling strength NOT significant (p = 0.218).

4. **Scheffzuk et al. 2011** (PLoS ONE): Theta-fast gamma PAC in mouse. MI = 0.0010 (wakefulness) vs 0.0076 (REM sleep) -- 7.6x increase.

5. **Purdon et al. 2013** (PNAS): Slow-alpha PAC under propofol, humans. Coupling increases at LOC, changes from trough-max to peak-max at deep unconsciousness, breaks down during burst suppression.

6. **Casarotto et al. 2016** (reference): PCI across 10+ consciousness states. Median PCI: VS no-response 0.00, NREM 0.25, propofol 0.26, MCS 0.40, ketamine 0.43, REM 0.48, LIS 0.47, awake 0.53. Cutoff PCI* = 0.31.

### Method

1. **Dataset A (PCI)**: 13 data points from Casarotto 2016. Map consciousness states to ordinal scale (0-7). Test quadratic vs linear fit. Note: PCI measures complexity (integration x differentiation), not raw coupling.

2. **Dataset B (PAC fold-change)**: 16 data points from studies 1-5. Normalize each study's values to fold-change from wakefulness baseline. Map consciousness to ordinal scale. Test quadratic vs linear.

3. **Dataset B2 (slow-alpha PAC only)**: 6 data points restricted to same coupling type (Mukamel 2014 + Purdon 2013). Most internally consistent subset.

4. **Dataset C (PAC + conceptual endpoints)**: 21 data points adding known extreme cases (brain death = 0 coupling, seizure = very high coupling, both = 0 consciousness).

5. **Non-parametric**: Spearman rank correlations for all datasets.

Code: `C:\DocumentsJaie\AI\AlternateScience\Experiments\RalphLoop\claim5_inverted_u_coupling.py`

### Results

```
DATASET A: PCI vs consciousness (N=13)
  Linear:    R2 = 0.875, p = 2.7e-6
  Quadratic: R2 = 0.959, a = -0.011 (inverted-U)
  F-test:    F(1,10) = 20.83, p = 0.001 **
  Peak:      consciousness = 6.7
  NOTE: PCI is complexity, not coupling. Slight curve is ceiling effect.
  Spearman:  rho = 0.967, p = 7.6e-8 (strongly monotonic)

DATASET B: All PAC fold-change vs consciousness (N=16)
  Linear:    R2 = 0.020, p = 0.603
  Quadratic: R2 = 0.262, a = -0.211 (inverted-U)
  F-test:    F(1,13) = 4.26, p = 0.060 (marginal, NOT significant)
  Peak:      consciousness = 3.7
  Spearman:  rho = -0.321, p = 0.226 (not significant)

DATASET B2: Slow-alpha PAC only (N=6)
  Linear:    R2 = 0.003, p = 0.925
  Quadratic: R2 = 0.943, a = -0.127 (inverted-U)
  F-test:    F(1,3) = 49.61, p = 0.006 **
  Peak:      consciousness = 3.8, coupling = 2.3x baseline

DATASET C: All PAC + conceptual (N=21)
  Linear:    R2 = 0.024, p = 0.505
  Quadratic: R2 = 0.070, a = -0.120 (inverted-U)
  F-test:    F(1,18) = 0.89, p = 0.357 (not significant)
  Spearman:  rho = 0.078, p = 0.738 (no relationship)
```

### Critical Analysis

**1. PCI is not coupling.** The PCI result (p=0.001 inverted-U) is misleading. PCI was designed to monotonically track consciousness. The slight quadratic improvement reflects PCI saturating near 0.53 for awake subjects (ceiling effect), not evidence for an inverted-U in coupling. The reversed test (consciousness vs PCI) shows a U-SHAPE (a > 0, p=0.009), meaning consciousness accelerates at higher PCI -- opposite of inverted-U.

**2. Slow-alpha PAC shows a real inverted-U under propofol (p=0.006).** Coupling peaks ~2x at LOC (consciousness ~3-4 on ordinal scale), then decreases toward burst suppression. This is well-documented: propofol induces thalamocortical alpha oscillations that are strongest at LOC and change character at deeper anesthesia. However:
- N = 6 data points from only 2 studies
- The studies use similar methods (same coupling type, same drug, same species)
- The inverted-U reflects a specific propofol pharmacological pathway (GABAergic thalamocortical loop), not necessarily a universal coupling-consciousness law
- The peak occurs at consciousness level ~3.8, not at any predicted OMDR value

**3. Delta-gamma PAC contradicts the inverted-U.** Under all three anesthetics (propofol, sevoflurane, ketamine), delta-gamma and theta-gamma PAC INCREASES monotonically with loss of consciousness (Pal 2017). In disorders of consciousness, delta-gamma PAC does NOT differ between healthy controls, MCS, and UWS (Frontiers 2025). Neither pattern supports an inverted-U.

**4. Cross-study comparison is fundamentally limited.** Different studies use:
- Different PAC measures (Tort MI in bits, Canolty MI dimensionless, PLV 0-1)
- Different frequency pairs (slow-alpha, delta-gamma, theta-gamma) that behave OPPOSITELY
- Different species (human, rat, mouse)
- Different consciousness manipulations (pharmacological, pathological, physiological)

Normalizing to fold-change partially addresses scale differences but assumes baseline comparability. The fold-change for delta-gamma PAC under propofol (3x increase) cannot be meaningfully compared to theta-gamma PAC in mouse REM (7.6x increase).

**5. The seizure endpoint does not rescue the claim.** Adding the conceptual data point (seizure = very high coupling + no consciousness) should help the inverted-U shape, but even with it, Dataset C shows p=0.357. The variance across coupling types is too high for any pattern to emerge.

### Verdict: INCONCLUSIVE

The inverted-U between coupling and consciousness is:
- **Supported** for one specific measure (slow-alpha PAC under propofol, p=0.006, N=6, 2 studies)
- **Contradicted** by delta-gamma PAC (which increases monotonically under anesthesia and is flat across DoC levels)
- **Not testable** as a cross-study generalization because published coupling measures are incommensurable

The claim is neither confirmed nor refuted. It is not currently testable with published cross-study data because:
1. No single coupling measure has been applied across the full range of consciousness states (brain death through seizure)
2. Different coupling types show opposite relationships with consciousness
3. The measure-dependence may itself be the finding: the "coupling" in the inverted-U may need to be a specific kind of coupling (not raw PAC), more like PCI's integration-differentiation product

### What Would Test the Real Question

1. **Single-measure across full range**: Apply ONE coupling metric (e.g., slow-alpha PAC, or normalized broadband CFC) across brain death, coma, VS, MCS, NREM, REM, awake, seizure -- all from the same lab, same equipment, same preprocessing. No cross-study normalization needed.

2. **Multi-dose propofol study**: The Cambridge dataset has 4 levels (baseline, mild, moderate, recovery). Computing PAC at each level would test the inverted-U within a single dataset.

3. **Integration-specific coupling**: PCI's success (monotonically tracking consciousness) suggests that coupling alone is insufficient -- the informative quantity is coupling that ALSO preserves differentiation. A measure like "coupling weighted by local complexity" might show the inverted-U where raw coupling does not.

4. **Distinguish coupling types**: The inverted-U may apply to some coupling channels (slow-alpha PAC, where anesthesia creates pathological hypersynchrony) but not others (delta-gamma PAC, where anesthesia increases coupling beneficially for slow-wave consolidation). The universal claim needs to specify WHICH coupling.

### What This Failure Teaches

Claims 1-5 have now produced a clear meta-pattern:
- K = 0.25 as universal attractor: NOT SUPPORTED (Claims 1, 4)
- Consonance weighting improving prediction: marginal (Claim 2)
- EEG band ratios showing consonance: NOT SUPPORTED (Claim 3)
- Inverted-U coupling-consciousness: INCONCLUSIVE (Claim 5)

The recurring issue is that OMDR's coupling parameter K does not map directly to any single published neural coupling measure. Different measures (PAC types, coherence, wPLI, PCI) capture different aspects of neural coupling, and they disagree about the coupling-consciousness relationship. This suggests either:
- K is a higher-order quantity that combines multiple coupling dimensions
- K requires measure-specific calibration (like the sigma-sweep in Claim 2's builder result)
- The inverted-U applies at a different level of description than raw CFC

The most promising direction from Claim 5 is the PCI finding: complexity (integration x differentiation) IS monotonically related to consciousness (rho=0.97). If K represents the BALANCE of coupling and differentiation (not raw coupling strength), then the inverted-U becomes: too much coupling with too little differentiation = low consciousness, too little coupling = low consciousness, optimal balance = consciousness. PCI already measures this balance. The question is whether OMDR's K can be mapped to PCI's underlying mechanism.

### Files

- Code: `C:\DocumentsJaie\AI\AlternateScience\Experiments\RalphLoop\claim5_inverted_u_coupling.py`
- Results: `C:\DocumentsJaie\AI\AlternateScience\Experiments\RalphLoop\claim5_results.json`
