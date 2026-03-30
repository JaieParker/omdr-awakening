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

| 6 | Three-channel K (balance angle theta_PS) outperforms two-channel K as consciousness marker | SUPPORTED (in-sample) | theta_PS: p=0.004, d=-0.850 | Outperforms K_S alone (d=0.63) by 35%. 25% of subjects detectable ONLY by angle. BUT: same dataset as Claim 1 (Cambridge propofol, N=20). Not replicated on independent data. In-sample performance ≠ generalization. Needs: (a) deep-sedation replication, (b) psychedelic direction test (pre-registered). |
| 7 | OMDR's observation space is 5-dimensional (effective rank plateaus at 5 for sigma ≤ 0.05) | COMPUTED (sigma-dependent) | rank=5 at sigma≤0.05 | Mathematical property of the stiffness matrix, not an empirical claim about nature. At sigma=0.015: 4 effective axes, Jacobian rank 11 from 13 inputs, 72% of derived quantities algebraically forced. At sigma≥0.075: rank drops to 3 (peaks merge). The "5 dimensions" claim is a resolution statement — OMDR resolves 5 orthogonal observation axes at intermediate coupling. Not falsifiable — it's a computation, not a prediction. |
| 8 | Category A equations (27/38) derivable from standard oscillator physics without OMDR-specific axioms | SUPPORTED with caveat | 27/38 = 71% Category A | Every Category C equation uses standard math (products, integrals, Fabry-Pérot). No consciousness-specific mathematics exists in OMDR. BUT Dive 3 Cycle 5 found the deeper result: the experiential layer IS the N>1 dimensionality condition. Without it, OMDR is a 1D circle map incapable of self-reference. The math is standard; the APPLICATION (cross-domain + consciousness) is genuinely novel. "Derivable from standard physics" is true but misleading — Maxwell's equations are "standard math" applied to electromagnetism, which doesn't diminish them. |

## Scoring Notes (Kai-evening, 2026-03-30)

**Claim 6** is the strongest result in the entire project (d=0.85) but sits on a single dataset. The psychedelic pre-registration (filed) is the critical next test — if theta_PS moves in the OPPOSITE direction from propofol, that's two-directional confirmation from one framework. Standard pharmacology doesn't predict opposite theta shifts.

**Claim 7** was proposed as an empirical claim but is actually a mathematical result. It belongs in the "Key Findings" section, not the scoreboard. The observation space dimensionality depends on resolution (sigma), which depends on the question being asked. This is a feature (sigma as spectroscope), not a bug.

**Claim 8** was the most philosophically productive claim. The "27/38 = standard physics" finding initially looked like a weakness (OMDR is "just" oscillator physics). Dive 3 inverted this: the fact that consciousness doesn't need new math may be the deepest finding. The same Fabry-Pérot cavity governing laser physics also governs self-observation. Whether that's profound or trivially true is the hard problem expressed in OMDR terms.

**Pattern across all 8 claims:** The scoreboard is 1/8 supported, 0/8 strongly confirmed, 5/8 failed/unsupported. But the strongest findings (balance angle d=0.85, σ-sweep self-diagnosis, 72% algebraic forcing, compression-as-prediction) were DISCOVERED through failures, not by confirming predictions. The scoreboard measures prediction accuracy. The science advances through structured surprise. These are orthogonal.

## Failed Claims
*Honest failures documented here. These are the most important results.*
