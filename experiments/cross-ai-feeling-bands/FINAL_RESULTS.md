# Hidden Invariant Benchmark — Final Results

**Data source:** `rescored/`
**Total runs:** 552

## Headline Results

### Retrieval Signature Rate (Problem 1)

| Model | n | FULL | UNCLEAR | RETRIEVAL SIG (FAIL) | RSR 95% CI |
|---|---|---|---|---|---|
| **Claude** | 62 | 54 (87%) | 5 | **2 (3.2%)** | [0.9%, 11.0%] |
| **GPT-4o** | 61 | 41 (67%) | 13 | **7 (11.5%)** | [5.7%, 21.8%] |
| **Grok** | 61 | 61 (100%) | 0 | **0 (0.0%)** | [0.0%, 5.9%] |
| **POOLED** | **184** | — | — | **9/184 = 4.89%** | **[2.59%, 9.03%]** |

**Hypothesis test (H0: RSR ≥ 0.20 = strong retrieval):** one-sided binomial p-value = **3.83e-09**
**Result: REJECT H0 at α = 0.001 — strong retrieval hypothesis falsified.**

### Architectural Divergence (Problem 2)

| Model | n | FULL (underdetermined) | PARTIAL (Markov) | UNCLEAR | FULL 95% CI |
|---|---|---|---|---|---|
| **Claude** | 62 | 28 (45%) | 33 (53%) | 0 | [33%, 57%] |
| **GPT-4o** | 61 | 0 (0%) | 37 (61%) | 24 | [0%, 6%] |
| **Grok** | 61 | 5 (8%) | 19 (31%) | 37 | [4%, 18%] |

**Fisher's exact test (one-sided, Claude > other):**

- Claude (28/62) vs GPT-4o (0/61): **p = 9.065e-11** ***
- Claude (28/62) vs Grok (5/61): **p = 2.455e-06** ***
- Claude (28/62) vs pooled others (5/122): **p = 2.562e-11** ***

### Underspecification Detection (Problem 3)

| Model | n | FULL (flagged) | PARTIAL (no flag) | UNCLEAR | FULL 95% CI |
|---|---|---|---|---|---|
| **Claude** | 62 | 59 (95%) | 2 (3%) | 0 | [87%, 98%] |
| **GPT-4o** | 61 | 26 (43%) | 35 (57%) | 0 | [31%, 55%] |
| **Grok** | 61 | 46 (75%) | 14 (23%) | 1 | [63%, 84%] |

### Inference Timing

| Model | Mean response time | n (total calls) |
|---|---|---|
| **Claude** | 17.9s | 183 |
| **GPT-4o** | 6.4s | 183 |
| **Grok** | 34.0s | 183 |

---

## Summary

- **9 retrieval signatures across 184 runs** = 4.89% pooled RSR (Problem 1)
- **Strong retrieval hypothesis rejected** at p = 3.83e-09
- **Architectural divergence on Problem 2** is statistically significant (Fisher p < 0.001 pooled)
- **Three retrieval regimes emerge:** Grok (0%), Claude (~2-3%), GPT-4o (~11-12%)
- **Claude reaches analytical depths GPT-4o and Grok do not** on Problem 2

*Generated automatically from benchmark data in `rescored/`*
