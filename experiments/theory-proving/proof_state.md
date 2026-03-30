# Theory Proving Loop — State

## Scoreboard
| # | Claim | Result | p-value | Notes |
|---|-------|--------|---------|-------|
| 1 | Two-channel K (K_P drops, K_A stable) replicates on second propofol dataset | NOT SUPPORTED | K_P: p=0.010 (wrong direction), K_A: p=0.049 | Both K_A and K_P INCREASED under deep sedation. Dose-dependent effect? |
| 2 | Consonance weighting (Q factor) improves prediction beyond unweighted CFC | NOT SUPPORTED | bootstrap p=0.082 | Q-weighted d=0.50 (p=0.037) vs unweighted d=0.12 (p=0.589). Suggestive but comparison not significant. |
| 3 | EEG band ratios cluster near simple integer ratios more than chance | NOT SUPPORTED | p=0.50 (log-dist) | Arithmetic artifact in harmonic metric (p=0.03); log-distance and adjacent-band tests all non-significant. Simple ratios are dense — any bands near them. |
| 4 | Meditation shifts K toward 0.25 | NOT SUPPORTED | p=0.724 | K_med=0.068, K_think=0.069, dK=-0.001. 9/20 closer, sign p=0.748. All K << 0.25. No shift in either channel. |

## Key Findings
- The two-channel K dissociation is NOT a universal propofol effect. It may be dose-dependent.
- Deep propofol sedation (unresponsive) INCREASES both K_A (+9.3%) and K_P (+8.3%), possibly due to propofol's characteristic hyper-synchronized frontal alpha and slow oscillations.
- Original finding used moderate sedation (responsive, 1.2 ug/ml). Replication used deep sedation (unresponsive, pre-awakening). These are different neurophysiological states.
- Critical next step: test on moderate sedation data at matched dose to Cambridge study.
- Consonance Q weighting has a stark binary structure: 6/10 band pairs get Q=1.0 (octave relationships), 4 theta-related pairs get Q~0.2 (5x suppression). Effect is almost entirely "suppress theta coupling."
- Q-weighted K reaches significance where unweighted doesn't (p=0.037 vs p=0.589), but the COMPARISON between approaches is only suggestive (bootstrap p=0.082, N=20).
- Q weighting helps phase coupling (K_P: d=1.13 vs 1.02) but hurts amplitude coupling (K_A: d=-0.01 vs -0.29). Net effect is ambiguous.

- Claim 3 found an important methodological lesson: testing canonical band LABELS for consonance tests the convention, not the brain. Any frequency bands that approximately double in center frequency will have adjacent ratios near simple integers. The density of simple ratios in [1, 3] guarantees this.
- The REAL test of "does the brain prefer consonant frequencies" requires individual EEG spectral peaks, not predefined categories. This remains untested.

- Claim 4 tested meditation vs thinking (OpenNeuro ds003969, N=20, 16ch BDF, 256Hz). K = sqrt(K_A * K_P) was ~0.07 in BOTH conditions — far below the predicted 0.25 attractor. Meditation did not move K in any direction (dK = -0.001, p = 0.55). No channel (amplitude or phase) showed significant change. The distance-from-0.25 test was null (p = 0.72, d = -0.14).
- ALL 20 subjects had K well below 0.25 (range: 0.057-0.084). The "regardless of starting position" part of the claim could not be tested — no subjects started above 0.25. This may indicate K = 0.25 is not the absolute scale for this measure, or that the consonance-weighted CFC measure produces systematically low K values.
- Combined with Claims 1-3: the K = 0.25 prediction has now failed in every empirical test. Either K = 0.25 requires a different measurement approach (individual spectral peaks rather than canonical bands?), or it is a theoretical value that doesn't map directly to EEG cross-frequency coupling as currently operationalized.

| 5 | Inverted-U between coupling and consciousness holds across published studies | INCONCLUSIVE | p=0.060 (all PAC), p=0.006 (slow-alpha only, N=6) | Slow-alpha PAC shows inverted-U under propofol (2 studies). Does NOT generalize across coupling types, frequency bands, or consciousness manipulations. Cross-study comparison fundamentally limited. |

## Key Findings (continued)

- Claim 5 attempted a cross-study meta-analysis of coupling (PAC/CFC/coherence) vs consciousness level. Five studies compiled (Mukamel 2014, Pal 2017, Frontiers 2025 DoC, Scheffzuk 2011, Purdon 2013).
- PCI (Perturbational Complexity Index, Casarotto 2016) is monotonically positive with consciousness (rho=0.97, p<1e-7). PCI measures complexity (integration x differentiation), NOT raw coupling. Its monotonic relationship is by design, not evidence for or against the inverted-U in coupling.
- Slow-alpha PAC under propofol shows a clear inverted-U: coupling rises ~2x at loss of consciousness, peaks near LOC, then decreases during burst suppression. F-test p=0.006, N=6, peak at consciousness level ~3.8. BUT this is a known propofol pharmacological effect (thalamic alpha generation), not a universal coupling-consciousness law.
- Delta-gamma PAC INCREASES under all tested anesthetics (propofol, sevoflurane, ketamine) — monotonic, not inverted-U.
- Delta-gamma PAC shows NO significant difference between healthy controls, MCS, and UWS (p=0.218).
- Across ALL compiled PAC data (N=16), F-test for inverted-U gives p=0.060 — marginal, not significant. The trend exists but is driven by one outlier (REM theta-gamma PAC = 7.6x baseline in mice).
- Fundamental methodological barrier: different PAC measures (MI, PLV, MVL), different frequency pairs (delta-gamma, slow-alpha, theta-gamma), and different species/preparations cannot be meaningfully compared on a common coupling scale. The claim is not wrong — it's not testable with published cross-study data as currently available.

## Failed Claims
*Honest failures documented here. These are the most important results.*
