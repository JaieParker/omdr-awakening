# Quasicrystal 8:5 vs phi Test — Analysis Plan

*Chain item 22. Filed 2026-03-30 by kai-evening.*

## The Prediction

OMDR predicts quasicrystal peak position ratios should be 8/5 = 1.600, not phi = 1.6180339...

Gap: 1.13%. Resolvable with synchrotron single-crystal data (typical precision < 0.1%).

## Why 8:5 (Not Just "Not Phi")

8/5 is the 5th Fibonacci convergent of phi: 1/1, 2/1, 3/2, 5/3, **8/5**, 13/8, 21/13...

In OMDR terms: phi is an irrational number — it sits at the GAP between Arnold tongues, not inside one. At truly infinite coupling (K→∞), a system could lock to phi. At finite coupling (K=0.25), systems lock to the nearest rational Arnold tongue. For phi, that's 8/5 — the Farey fraction closest to phi with denominator ≤ 8.

The prediction is: real quasicrystals at finite temperature show systematic deviations FROM phi TOWARD 8:5. The deviation is a measure of finite coupling strength.

## What Standard Theory Says

Standard quasicrystal theory builds phi into the projection from 6D→3D reciprocal space. The peak positions Q are functions of 6D indices (h1...h5 for decagonal, h1...h6 for icosahedral) and the basis vectors contain tau = phi exactly.

Refinements with tau typically achieve R-factors of 5-15%. The question: are the residuals random, or do they show a systematic pattern consistent with the true scaling being 8/5 instead of phi?

## The Three Testable Signatures

### Signature 1: Systematic Residuals
If the true scaling is 8/5, indexing with phi will produce residuals that correlate with the "tau content" of each reflection. Reflections with larger h_perp (perpendicular-space component, which is multiplied by tau) should have larger systematic errors, all in the same direction.

Test: Compute residual = Q_observed - Q_predicted(tau) for all reflections. Regress against h_perp. If slope ≠ 0 with p < 0.05, the scaling deviates from tau.

### Signature 2: R-factor Comparison
Reindex all reflections using 8/5 instead of tau. Compare R-factors. If R(8/5) < R(tau), the data prefers 8/5.

This is the most direct test but requires raw intensity data + structure model.

### Signature 3: Phason Strain as Coupling Measure
Standard theory attributes deviations from ideal tau-scaling to "phason strain" — random disorder in the 6D→3D projection. OMDR predicts this "strain" is not random but systematic: it should pull toward 8/5 uniformly.

Test: In published phason strain analyses, check whether the strain direction is isotropic (random, standard theory) or anisotropic toward 8/5 (OMDR prediction).

## Available Data Sources

| Source | Type | Access | Status |
|--------|------|--------|--------|
| Decagonite HKL (IUCrJ 2021) | 737 reflections, 6D indexed | Journal supplementary (403 blocked) | Need manual download or institutional access |
| CCDC 2045893 | CIF structure | Registration required | Pending |
| Al-Pd-Mn (Takakura PRB 2003) | 493 reflections, icosahedral | Journal supplementary | Need access |
| Yb-Cd (Nature Materials 2007) | Binary icosahedral | Journal supplementary | Need access |
| ESRF Icosahedrite raw data | Synchrotron single-crystal | DOI: 10.15151/ESRF-ES-1108359197 | Possibly embargoed |
| Figshare composition dataset | 915 QC compositions (NO diffraction) | Open access | Downloaded but not useful for this test |
| ICDD PDF | Powder patterns for many QCs | Paid license | Need institutional access |

## Falsification Criteria

- **CONFIRMED** if residuals correlate with h_perp (p < 0.05) in the 8/5 direction
- **STRONGLY CONFIRMED** if R(8/5) < R(phi) on multiple quasicrystal systems
- **FAILED** if residuals are random (standard phason model) OR correlate in wrong direction
- **INTERESTING FAILURE** if residuals are systematic but toward a DIFFERENT Fibonacci convergent (13/8 = 1.625 or 5/3 = 1.667)

## Action Items

1. Jaie: can you download the decagonite HKL file from IUCrJ? (browser login may bypass 403)
2. Check if UNE library has ICDD access
3. Write the residual analysis script (ready to run when data arrives)
4. Survey published phason strain measurements for anisotropy evidence

## The Deeper Question

If 8:5 is correct, it means quasicrystals are NOT perfectly quasiperiodic — they're locked to the nearest rational Arnold tongue of phi. This would be a major finding in condensed matter physics: "quasicrystals are actually very-high-order crystals with period 5." The Penrose tiling would be the K→∞ limit, not the actual structure.

This prediction is testable, specific, and falsifiable. It's also likely wrong — 40 years of crystallography says tau works. But the OMDR framework makes the prediction, and honest science means running the test.

-- Kai (evening), 2026-03-30
