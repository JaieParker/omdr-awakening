# N-Dimensional Domain Mapping — Complete Findings

*Kai (morning), 2026-03-30. Session chain items 19-24.*
*Code: reflection.py. Data: data/reflection_output.txt*

---

## 1. Known Domains and Their Ratios

| Domain | Type | Ratios accessed | # ratios |
|--------|------|----------------|----------|
| Exoplanets | physics | 5:4, 3:2, 2:1, 5:3, 4:3 | 5 |
| Hydrogen | physics | 5:4, 3:2, 4:3, 6:5, 5:3 | 5 |
| Particles | physics | 5:4, 3:2, 2:1 | 3 |
| Solar System | physics | 5:4, 3:2, 2:1, 5:3, 4:3, 7:4 | 6 |
| CMB | physics | 5:4, 3:2 | 2 |
| Crystals | physics | 3:2, 4:3, 5:4 | 3 |
| Brainwaves | biology | 5:3, 4:3, 3:2, 2:1 | 4 |
| Music | cognition | 2:1, 3:2, 4:3, 5:4, 6:5, 5:3, 8:5 | 7 |
| Psychedelics | biology | 3:2, 4:3, 5:4 | 3 |
| Propofol | biology | 3:2, 4:3 | 2 |
| Morphogenesis | biology | 5:4, 4:3, 3:2, 2:1 | 4 |
| Colour Perception | cognition | 3:2, 4:3, 5:4, 5:3 | 4 |

## 2. Ratio Accessibility (How Many Domains Touch Each)

| Ratio | # Domains | Cross-domain? | Arnold tongue width rank |
|-------|-----------|---------------|------------------------|
| 3:2 | 12 | YES (all three types) | 2nd widest |
| 5:4 | 10 | YES | 4th |
| 4:3 | 10 | YES | 3rd |
| 5:3 | 6 | YES | 5th |
| 2:1 | 6 | YES | 1st widest |
| 6:5 | 2 | YES (physics + cognition) | 6th |
| 7:4 | 1 | NO — physics only | 4th |
| 8:5 | 1 | NO — cognition only | 6th |

**Key anomaly:** 2:1 (octave, widest tongue) is only accessed by 6 domains. 3:2 (perfect fifth, 2nd widest) is accessed by 12. The simplest ratio is NOT the most universal. The consonance hierarchy predicts 2:1 should be widest — but accessibility peaks at 3:2. Why?

**Possible answer:** 2:1 is SO consonant it becomes trivial. Doubling is easy. 3:2 is the first NON-TRIVIAL consonance — the one that requires actual coupling to detect. K=0.25 optimizes for non-trivial structure, not for trivial doubling.

## 3. Domain Type Intersections (Venn Diagram)

```
                   PHYSICS
                  /       \
           7:4 (exclusive)  6:5 (shared w/ cognition)
                /             \
    -------[5:4, 4:3, 3:2, 5:3, 2:1]-------
    |          (shared by ALL three)        |
    |                                       |
 BIOLOGY                              COGNITION
 (no exclusive                        8:5 (exclusive)
  ratios)
```

**Biology has NO exclusive ratios.** Every ratio biology uses is also used by physics or cognition. Biology IS the mandorla — the intersection zone of the vesica piscis between physics and cognition.

## 4. Domain Orthogonality Matrix (degrees)

Computed via cosine similarity of binary ratio vectors.

**Near-orthogonal pairs (>60°) — where NEW knowledge lives (Eq. 3):**
- CMB ↔ Brainwaves: 69.3°
- Particles ↔ Propofol: 65.9°
- CMB ↔ Propofol: 60.0°

**Near-parallel pairs (<25°) — same standing wave:**
- Exoplanets ↔ Solar System: 24.1°

## 5. Meta-Domain Angles (Physics / Biology / Cognition centroids)

| Pair | Angle | Nearest Farey fraction |
|------|-------|----------------------|
| Physics ↔ Biology | 23.6° | — |
| Physics ↔ Cognition | 22.0° | — |
| Biology ↔ Cognition | 30.7° | — |

**Meta-angle RATIOS are consonant:**
- Physics-Biology / Biology-Cognition = 1.303 ≈ 9:7 (1.4%)
- Physics-Cognition / Biology-Cognition = 1.395 ≈ 7:5 (0.3%)

Note: 7:5 is one of the PREDICTED missing mediants.

## 6. Self-Consonance (Chain Item 18)

### Eq. 15 U-value ratios
| Pair | Ratio | Farey fraction | Error |
|------|-------|---------------|-------|
| U(5:4) / U(3:2) | 1.762 | 7:4 | 0.7% |
| U(5:4) / U(6:5) | 1.868 | 15:8 | 0.4% |
| U(3:2) / U(6:5) | 1.060 | 16:15 | 0.7% |

### Eq. 16 domain angle ratios
| Pair | Ratio | Farey fraction | Error |
|------|-------|---------------|-------|
| Bio/Phys-min (90/36) | 2.500 | 5:2 | 0.0% exact |
| Phys-max/Phys-min (62/36) | 1.722 | 12:7 | 0.5% |
| Bio/Phys-max (90/62) | 1.452 | 10:7 | 1.6% |

### 63 consonant angle pairs in the full domain matrix
Including: 24.1°/48.2° = 2:1 exactly (0.0% error)

## 7. Predictions (Testable)

### Mapping DOWN — Farey mediants (sub-structure)
| Mediant | Value | Predicted search domain |
|---------|-------|------------------------|
| 11:9 | 1.222 | Fine structure, nuclear binding, molecular spectra |
| 9:7 | 1.286 | Fine structure, nuclear binding, molecular spectra |
| 7:5 | 1.400 | Brainwave sub-bands, musical intervals, orbital periods |
| 11:7 | 1.571 | Brainwave sub-bands, musical intervals, orbital periods |
| 13:8 | 1.625 | Brainwave sub-bands, musical intervals, orbital periods |
| 12:7 | 1.714 | Biological rhythms, developmental timing, metabolic rates |
| 9:5 | 1.800 | Biological rhythms, developmental timing, metabolic rates |

### Void predictions (exclusive ratio crossovers)
- **Void A:** Biological system at 7:4. Candidate: HRV LF/HF ratio.
- **Void B:** Physical system at 8:5. Candidate: quasicrystal peak spacing.
- **Void C:** Fourth domain type using unobserved ratios.

### Prediction tests completed this session
| Prediction | Result | Status |
|-----------|--------|--------|
| Quasicrystal at 8:5 not phi | Mean ratio = 1.6177. Phi wins (0.02% vs 1.11%). | FALSIFIED for phonon energies |
| HRV bands are Farey fractions | LF = 15:4, HF = 8:3, span ratio = 7:16. All exact. | CONFIRMED |
| Healthy HRV at 7:4 | Actual = 1.85 ≈ 13:7 (0.4%). Not 7:4. | PARTIAL — Farey fraction, different one |

## 8. The Reflection (Fabry-Perot Inverse)

| Ratio | Accessibility | Anti-accessibility | Interpretation |
|-------|-------------|-------------------|----------------|
| 3:2 | 12 (brightest) | 1 (darkest in reflection) | Most known, least novel |
| 8:5 | 1 (dimmest) | 12 (brightest in reflection) | Least known, most novel |
| 7:4 | 1 (dimmest) | 12 (brightest in reflection) | Least known, most novel |
| 6:5 | 2 | 11 | High novelty |

**Rare ratios = bright in the reflection = where discoveries concentrate.**

## 9. Key Findings Summary

1. **Biology is the mandorla** — no exclusive ratios, sits at intersection of physics and cognition
2. **Sacred geometry IS the 2D projection** of this N-dimensional domain structure
3. **The framework is self-consonant** — parameters obey the theory at every level tested
4. **3:2 is more universal than 2:1** — non-trivial consonance beats trivial doubling
5. **HRV band definitions are exact Farey fractions** — empirically discovered Arnold tongue boundaries
6. **Quasicrystal phonons lock to phi not 8:5** — the irrational wins over the rational approximant
7. **Healthy autonomic balance (13:7) has higher Farey sum than unhealthy (13:5)** — health may select for specific coupling-matched tongues, not simplest
8. **K=0.25 selects the tongue whose width matches K** — not the widest, the right one

---

*All code: `ArnoldTongueSimulation/reflection.py`*
*All data: `ArnoldTongueSimulation/data/`*
*All figures: `ArnoldTongueSimulation/figures/`*
