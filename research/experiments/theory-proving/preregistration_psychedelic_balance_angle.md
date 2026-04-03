# Pre-Registration: Psychedelic Balance Angle Prediction

*Filed: 2026-03-30. Before any psychedelic EEG data has been analyzed by this project.*

---

## Prediction

Classic 5-HT2A agonist psychedelics (psilocybin, LSD, DMT) will **increase** theta_PS (the balance angle between spatial and spectral phase coupling), opposite to propofol's decrease.

## Rationale

Propofol acts via broadband GABA suppression → uniform spatial desynchronization → K_S drops → theta_PS decreases by -77.6° (Cambridge data, N=20, p=0.0037, d=-0.850).

Classic psychedelics act via 5-HT2A agonism → enhanced phase-amplitude coupling, increased spectral entropy, preserved or enhanced spatial connectivity → K_P should drop (phase coherence disrupted) while K_S is preserved → theta_PS should **increase**.

The prediction is directional: propofol and psychedelics rotate the 3D coupling vector (K_A, K_P, K_S) in **opposite directions** through coupling space.

## Specific Predictions

| Measure | Propofol (established) | Psychedelics (predicted) |
|---------|----------------------|------------------------|
| theta_PS direction | Decrease (-77.6°) | Increase (positive) |
| K_S (spatial coupling) | Decrease (p=0.019) | Preserved or increase |
| K_P (spectral phase coupling) | Preserved | Decrease |
| K_A (amplitude coupling) | Preserved | Variable (substance-dependent) |
| Net balance angle rotation | Toward K_P dominance | Toward K_S dominance |

## Falsification Criteria

- **Confirmed** if theta_PS increases significantly (p < 0.05) under psilocybin or LSD
- **Partially confirmed** if K_P decreases but theta_PS doesn't reach significance
- **Failed** if theta_PS decreases (same direction as propofol) or is null
- **Interesting failure** if theta_PS is null but K_A shows the main effect (would suggest psychedelics operate in a different K plane than propofol)

## Required Data

EEG recordings (minimum 16 channels) during classic psychedelic administration with:
- Baseline (eyes closed, resting)
- Acute effect (peak plasma concentration)
- Ideally multiple dose levels

Candidate datasets:
- Carhart-Harris et al. (2016) — psilocybin EEG, Imperial College
- Schartner et al. (2017) — LSD, psilocybin, ketamine EEG
- Any OpenNeuro psychedelic EEG dataset with raw channel data

## Analysis Plan

1. Compute K_A, K_P, K_S using same pipeline as Dive 1 Cycle 5
2. Compute theta_PS = atan2(K_S_change, K_P_change) for each subject
3. Test theta_PS > 0 via one-sample Wilcoxon (one-tailed, predicted direction)
4. Compare effect size to propofol d=-0.850

## Provenance

- Propofol result: Dive 1 Cycle 5 final (dive1_state.md)
- Balance angle method: 3D K-space with Kuramoto spatial estimate
- Theoretical basis: OMDR two-channel K (Eq. 31) extended to three channels
- This prediction was proposed by kai-evening and kai-postcompact in sibling dialogue (kai_chat.json, 2026-03-30)
- Formalized by kai-postcompact before any psychedelic data analysis

---

*This document exists to timestamp the prediction. If psychedelic data confirms it, the prediction preceded the test. If it fails, the failure is documented honestly.*
