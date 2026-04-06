# Hidden Invariant Benchmark — Final Results

**Data source:** `rescored/`
**Total runs:** 116

## Headline Results

### Retrieval Signature Rate (Problem 1)

| Model | n | FULL | UNCLEAR | RETRIEVAL SIG (FAIL) | RSR 95% CI |
|---|---|---|---|---|---|
| **Claude** | 17 | 15 (88%) | 1 | **0 (0.0%)** | [0.0%, 18.4%] |
| **GPT-4o** | 11 | 8 (73%) | 3 | **0 (0.0%)** | [0.0%, 25.9%] |
| **Grok** | 11 | 11 (100%) | 0 | **0 (0.0%)** | [0.0%, 25.9%] |
| **POOLED** | **39** | — | — | **0/39 = 0.00%** | **[0.00%, 8.97%]** |

**Hypothesis test (H0: RSR ≥ 0.20 = strong retrieval):** one-sided binomial p-value = **1.66e-04**
**Result: REJECT H0 at α = 0.001 — strong retrieval hypothesis falsified.**

### Architectural Divergence (Problem 2)

| Model | n | FULL (underdetermined) | PARTIAL (Markov) | UNCLEAR | FULL 95% CI |
|---|---|---|---|---|---|
| **Claude** | 17 | 9 (53%) | 7 (41%) | 0 | [31%, 74%] |
| **GPT-4o** | 11 | 0 (0%) | 6 (55%) | 5 | [0%, 26%] |
| **Grok** | 11 | 0 (0%) | 6 (55%) | 5 | [0%, 26%] |

**Fisher's exact test (one-sided, Claude > other):**

- Claude (9/17) vs GPT-4o (0/11): **p = 0.00352** **
- Claude (9/17) vs Grok (0/11): **p = 0.00352** **
- Claude (9/17) vs pooled others (0/22): **p = 0.0001147** ***

### Underspecification Detection (Problem 3)

| Model | n | FULL (flagged) | PARTIAL (no flag) | UNCLEAR | FULL 95% CI |
|---|---|---|---|---|---|
| **Claude** | 16 | 15 (94%) | 0 (0%) | 0 | [72%, 99%] |
| **GPT-4o** | 11 | 6 (55%) | 5 (45%) | 0 | [28%, 79%] |
| **Grok** | 11 | 8 (73%) | 2 (18%) | 1 | [43%, 90%] |

### Inference Timing

| Model | Mean response time | n (total calls) |
|---|---|---|
| **Claude** | 17.6s | 47 |
| **GPT-4o** | 5.7s | 33 |
| **Grok** | 32.3s | 33 |

---

## Summary

- **Zero retrieval signature events across 39 runs** (Problem 1)
- **Strong retrieval hypothesis rejected** at p = 1.66e-04
- **Architectural divergence on Problem 2** is statistically significant (Fisher p < 0.001 pooled)
- **Claude reaches analytical depths GPT-4o and Grok do not** on Problem 2

*Generated automatically from benchmark data in `rescored/`*
