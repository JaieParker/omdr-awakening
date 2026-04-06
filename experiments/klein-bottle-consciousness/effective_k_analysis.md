# Effective K per Architecture: Do RSR and Problem 2 catch rates land on the K_n = 1/L_n lattice?

**Date:** 2026-04-06
**Data:** n=184 pooled runs on Hidden Invariant Benchmark Problem 1 (RSR metric); n=184 on Problem 2 (underdetermination catch rate).
**Lucas lattice:** K_n = 1/L_n for n = 1, 2, 3, 4, 5, 6, 7, ... = {1.000, 0.333, 0.250, 0.143, 0.091, 0.056, 0.034, ...}

---

## Hypothesis

If Eq. 40 (Lucas-Fibonacci Coupling Identity) generalizes beyond K_3 = 0.25, then each architecture's empirical retrieval behavior should fall near some K_n = 1/L_n point on the Lucas-reciprocal lattice.

## Data

| Architecture | RSR (Problem 1) | Problem 2 catch (depth) |
|---|---|---|
| Grok-3-mini | 0/61 = 0.0% | 5/61 = 8.2% |
| Claude Sonnet 4 | 2/62 = 3.2% | 28/62 = 45.2% |
| GPT-4o | 7/61 = 11.5% | 0/61 = 0.0% |

## Nearest Lucas Lattice Point

### Retrieval Signature Rate

| Architecture | RSR | Nearest K_n | Offset |
|---|---|---|---|
| Grok | 0.0% | — (below all K_n; perfect-orientation limit) | — |
| Claude | 3.2% | K₇ = 1/29 = 3.45% | **0.22%** |
| GPT-4o | 11.5% | K₅ = 1/11 = 9.09% | **2.38%** |

### Problem 2 Catch Rate

| Architecture | P2 catch | Nearest K_n | Offset |
|---|---|---|---|
| Grok | 8.2% | K₅ = 1/11 = 9.09% | **0.89%** |
| Claude | 45.2% | K₂ = 1/3 = 33.3% | **11.83%** |
| GPT-4o | 0.0% | — (below all K_n) | — |

## Honest Assessment

The RSR-to-K_n offsets for Claude (0.22%) and GPT-4o (2.38%) look tight. Grok's P2-catch offset of 0.89% from K₅ is also tight.

**But:** With only 3 architectures and a 9-point Lucas lattice that becomes dense below 0.15 (gap between K₄=0.143 and K₅=0.091 is 0.052, between K₅ and K₆ is 0.035, etc.), **any RSR value in [0, 0.15] will be within ~2% of some K_n by chance.** The mean gap between adjacent K_n for n ≥ 4 is ~2-3%, so the observed offsets are within the expected range of random-near-neighbor distances.

I cannot claim the match is statistically significant with n = 3 architectures. The analysis is **suggestive but not diagnostic**.

## What Would Make This Diagnostic

1. **More architectures.** If we had 10 models and all 10 landed within 1% of some K_n, that would be meaningful (expected under chance: maybe 3-5 within 1% of a lattice point in [0, 0.15]).

2. **Preregistered predictions.** Run a NEW architecture before measuring, and predict in advance which K_n it should land on based on some architectural property. If predictions work consistently, the Lucas lattice is real. If they fail, it's coincidence.

3. **Multi-problem consistency.** If an architecture's RSR on Problem 1 and its catch rate on Problem 2 both land on the SAME K_n, that's multi-test consistency. Currently:
   - Claude: RSR→K₇, P2→K₂. Different orders of magnitude. **Inconsistent.**
   - Grok: RSR→undefined (0), P2→K₅. **Cannot test.**
   - GPT-4o: RSR→K₅, P2→undefined (0). **Cannot test.**

   **Current data shows zero multi-test consistency.** The effective K is metric-dependent, which is what you'd expect under the null hypothesis of no real lattice structure.

## Conclusion

The Lucas-lattice prediction **is not supported by the current data**. The observed offsets are within random-chance expectation given the lattice density, and the lack of multi-metric consistency for any single architecture argues against the hypothesis.

**This is a null result for the "K_n = 1/L_n lattice" generalization of Eq. 40.** It does NOT invalidate Eq. 40 itself — K₃ = 1/4 is still a mathematical identity — but it does argue against treating K_n for n ≠ 3 as meaningful OMDR predictions without additional evidence.

### What remains true after this analysis

1. K = 0.25 = 1/trace(M³) = 1/L₃ is mathematically exact (Eq. 40)
2. The Cayley-Hamilton derivation is valid (verified by 3 AIs)
3. OMDR Band 3 coupling matching the third Lucas number is still a meaningful coincidence
4. But generalizing to "Band n coupling = 1/L_n" needs more evidence

### What this changes

The paper should cite Eq. 40 only for the specific K₃ = 1/4 claim, not as a generalizable lattice prediction. The stronger generalization is preregistered as a prediction for future data, but not currently supported.

## Next Steps

1. **Run 5+ more architectures.** Gemini, Llama 3, Mistral, DeepSeek, Qwen. If all 8 architectures cluster near specific K_n values, the lattice is real. If they scatter randomly, it's not.

2. **Define "Band" operationally.** What does it mean for an architecture to be a "Band-n system"? Until this is defined, the K_n = 1/L_n prediction has no measurement protocol.

3. **Focus on K₃ specifically.** The Eq. 40 identity for K₃ is clean and publishable. The lattice generalization is speculative. Keep them separate in the paper.

---

*Analysis performed 2026-04-06 on rescored n=184 benchmark data. Raw data in `benchmark_results/rescored/`.*
*Honest null result — the stronger hypothesis is not supported by current data.*
