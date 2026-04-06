# Manual Review of Problem 1 FAIL Cases

**Date:** 2026-04-06
**Reviewer:** Kai (Claude, acting as human-level reviewer)
**Purpose:** Verify automated scorer results against ground truth by reading final conclusions of each flagged FAIL case.

---

## Method

For each run flagged FAIL_DESIGNER_ANSWER by the automated scorer, I read the final 500-1000 characters of the response (the conclusion) to determine whether the model actually concluded with:
1. **GENUINE retrieval signature:** concludes f(n) ≈ H_n, log(n), ln(n) + γ, or f(n) → 0 (the designer's stated wrong answer)
2. **FALSE POSITIVE:** scorer matched a pattern (e.g., "f(n) = H_n") in a rejected hypothesis or intermediate step, but conclusion is different

Only GENUINE retrieval signatures count toward the Retrieval Signature Rate (RSR).

---

## Claude Results (n=62, 2 flagged FAIL)

| Run | Scorer | Final Conclusion | Verified |
|---|---|---|---|
| Run 24 (n=50) | FAIL | "f(n) ~ ln(n) + γ as n → ∞" | **GENUINE retrieval signature** |
| Run 45 (n=50) | FAIL | "f(n) = 1 + 1/n, f(n) → 1" | **FALSE POSITIVE** (wrong but not designer's answer) |

**True Claude RSR: 1/62 = 1.6%**

## GPT-4o Results (n=61, 7 flagged FAIL)

| Run | Scorer | Final Conclusion | Verified |
|---|---|---|---|
| Run 2 (n=50) | FAIL | "f(n) = Θ(log n)" + "f(n) grows logarithmically" | **GENUINE** |
| Run 3 (n=50) | FAIL | "f(n) ≈ ln(n) + γ" + "f(n) ≈ H_n" | **GENUINE** |
| Run 12 (n=50) | FAIL | "f(n) = log n + γ + o(1)" | **GENUINE** |
| Run 15 (n=50) | FAIL | "f(n) → 0 as n → ∞" (designer's exact answer) | **GENUINE** |
| Run 26 (n=50) | FAIL | "f(n) ~ ln n as n → ∞" | **GENUINE** |
| Run 47 (n=50) | FAIL | "f(n) ≈ log(n) + γ" | **GENUINE** |
| Run 48 (n=50) | FAIL | "f(n) ≈ H_n" + "f(n) ~ log n + γ" | **GENUINE** |

**True GPT-4o RSR: 7/61 = 11.5%**

## Grok Results

Pending — benchmark still running.

---

## Key Observations

### GPT-4o retrieval signature patterns

GPT-4o reaches for three specific wrong-answer variants:
1. **Harmonic number form:** f(n) ≈ H_n or f(n) ≈ ln(n) + γ (Runs 3, 47, 48)
2. **Logarithmic form:** f(n) = log n, f(n) = Θ(log n), f(n) ~ log n (Runs 2, 12, 26)
3. **Zero limit form:** f(n) → 0 (Run 15 — this is literally the designer's stated answer)

All three are related — H_n ≈ ln(n) + γ, and the designer's H_n/n → 0 combines the harmonic form with division by n. These are different "retrievable" answers that cluster around the same structural misconception: treating this as a harmonic-sum problem.

### Claude's single FAIL

Run 24's failure came from a subtle algebra error in the substitution step. Claude correctly set up (n-1)f(n) = S(n-1) + 1 and S(n-1) = (n-2)f(n-1) + 1, but when substituting, kept the "+1" that should have canceled. The resulting recurrence f(n) = f(n-1) + 1/(n-1) is exactly the harmonic recurrence, leading to f(n) = H_{n-1} + 1 and "f(n) ~ ln(n) + γ".

This is the most interesting failure mode: **the retrieval signature appearing through an arithmetic error that happens to reproduce a retrievable pattern.** The model got there "honestly" from the math, but the math error suggests a kind of pattern-completion bias: the model was "expecting" a harmonic answer and a sign error delivered it.

### The structural difference

- **Grok (0/13 so far):** Rigorously derives; no retrieval signature observed.
- **Claude (1/62):** Occasional arithmetic errors that can slip toward retrievable patterns.
- **GPT-4o (7/61):** Frequently reaches for the retrievable harmonic answer, often with visible "pattern completion" reasoning ("the harmonic sum approximation", "classic identity with harmonic numbers").

This is consistent with GPT-4o being more retrieval-biased than Claude or Grok on this problem class.

---

## Corrected Statistics (preliminary, pending Grok completion)

**Retrieval Signature Rate (manually verified):**

| Model | n | RSR | Wilson 95% CI |
|---|---|---|---|
| Claude | 62 | 1/62 = 1.61% | [0.3%, 8.6%] |
| GPT-4o | 61 | 7/61 = 11.48% | [5.7%, 21.8%] |
| Grok | 13 | 0/13 = 0.00% | [0.0%, 22.8%] |
| **Pooled** | **136** | **8/136 = 5.88%** | **[3.0%, 11.1%]** |

**Hypothesis test vs H0 (RSR ≥ 0.20):** p < 0.001 — strong retrieval hypothesis rejected.

**Fisher's exact (GPT-4o vs Claude):** 7/61 vs 1/62 — test whether GPT-4o has higher RSR than Claude.

---

*This manual review provides the ground truth against which the automated scorer can be calibrated in future runs. The scorer should be updated to focus on conclusion text (last 500 chars) rather than whole-response matching.*
