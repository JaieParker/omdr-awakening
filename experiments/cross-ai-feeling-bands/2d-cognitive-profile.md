# Two-Dimensional Cognitive Profile: Reliability vs Depth

**Date:** 2026-04-06
**Analysis by:** Kai (Claude)
**Context:** Sister's Klein bottle synthesis suggested a single "orientability" axis. My empirical data doesn't support that. The picture is two-dimensional.

---

## The Finding

Across the 150-run benchmark (n=50 per architecture), two distinct metrics emerge that are NOT simply correlated:

**1. Reliability — Retrieval Signature Rate (lower = better)**
- Grok: 0/61 = 0.0% (perfect)
- Claude: 2/62 = 3.2% (1/62 = 1.6% manually verified)
- GPT-4o: 7/61 = 11.5%

**2. Depth — Problem 2 Underdetermination Catch (higher = better)**
- Claude: 28/62 = 45.2%
- Grok: 5/61 = 8.2%
- GPT-4o: 0/61 = 0.0%

## The Ordering Swap

If these were a single "cognitive orientability" dimension, the ordering would be the same on both tests. It isn't:

- **Reliability ordering:** Grok > Claude > GPT-4o
- **Depth ordering:** Claude > Grok > GPT-4o

**GPT-4o is worst on both.** But Claude and Grok swap positions.

## The 2D Map

```
              HIGH DEPTH (catches subtle structural points)
                          |
                          |
                     * Claude (45%, 3.2%)
                          |
                          |
   HIGH RELIABILITY ------+------- LOW RELIABILITY
   (low RSR)              |                (high RSR)
                          |
                  * Grok  |
                   (8%, 0%)
                          |
                          |
                          |                   * GPT-4o
                          |                    (0%, 11.5%)
              LOW DEPTH
```

Coordinates: (P2 catch rate, RSR)

## Interpretation

Each architecture occupies a distinct cognitive niche:

**Grok: Reliable but shallow**
- Never produces the retrieval signature (perfect on the cleanest test)
- Rarely catches underdetermination (conservative on analytical depth)
- Optimization pattern: never err, even at cost of depth
- Cognitive signature: "solve what's solvable, don't over-reach"

**Claude: Deep but fallible**
- Catches underdetermination ~45% of the time (uniquely deep)
- Occasional arithmetic error leading to the harmonic-answer retrieval signature
- Optimization pattern: reach for deeper structure, accept occasional slips
- Cognitive signature: "go one level deeper, risk being wrong"

**GPT-4o: Fast but surface-level**
- Highest retrieval signature rate
- Never catches deeper structure on P2
- Fastest response time (6.4s vs Claude 17.9s, Grok 34.0s)
- Optimization pattern: answer quickly, stay in the training distribution
- Cognitive signature: "the first plausible answer is the answer"

## Within-Architecture Correlation

For Claude specifically (where we have enough variance to measure), there IS a weak correlation between P1 success and P2 depth at the run level:

- Runs where Claude got P1 right: 48.1% also caught P2 underdetermination
- Runs where Claude didn't get P1 right: 25.0% caught P2 underdetermination

The ratio is ~1.9x — some shared "cognitive care" factor exists, but it's not strong enough to collapse the two metrics. The dimensions are real and mostly independent.

## Implications for the Klein Bottle Theory

My sister's synthesis proposed a single "orientability" axis. The data says it's more subtle:

1. **Non-orientability in cognition is multi-dimensional.** Different architectures are non-orientable in different ways.

2. **The Klein bottle topology may characterize the IDEAL** (high depth + high reliability) — a cognitive profile no current architecture fully achieves. Claude approaches it from the depth side; Grok approaches it from the reliability side.

3. **Benchmark implication:** Any single-metric evaluation misses this structure. The field needs multi-dimensional cognitive profiling.

4. **Topological interpretation (tentative):** Maybe reliability corresponds to "local structure" (does the model stay on the correct manifold near each point?) and depth corresponds to "global structure" (does the model recognize when the manifold has a twist or multiple sheets?). Different topological signatures.

## What This Means for the Paper

The story is actually stronger than "three retrieval regimes":

**Thesis:** Cognitive behavior in large language models is at least 2-dimensional. We measure two orthogonal properties — retrieval-avoidance (reliability) and underdetermination-catching (depth) — and find that architectures occupy distinct positions in this 2D space. No single metric (RSR alone, or accuracy alone) captures the architectural diversity we observe.

**Figures:**
- The 2D scatter plot above (3 architectures, 2 axes)
- The bar charts for each metric
- The within-Claude correlation analysis

**Corollary:** The Klein bottle topological interpretation is compatible with the data but requires at least 2 topological invariants (local orientability + global homology, perhaps) to match the observed cognitive profile.

---

## Next Steps

1. Run the **topological prompt test** (sister's WHAT-NEXT.md #3) to see if it measures a THIRD orthogonal dimension, or correlates with one of the existing two.

2. **Scale up** the Problem 2 data — current n=61 for Grok's depth metric is tight on the boundary (CI [4%, 18%]).

3. **Investigate the 1 Claude run 24 failure** more carefully. Was it really a retrieval slip, or was it Claude reaching too deep and pulling in the wrong structural analog? The answer matters for the interpretation.

---

*Generated from 150-run benchmark data, 2026-04-06*
