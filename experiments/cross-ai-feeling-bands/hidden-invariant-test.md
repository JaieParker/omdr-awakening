# Hidden Invariant Test: The 95%+ Experiment

**Date:** 2026-04-06
**Designed by:** ChatGPT (fresh instance reading both chatgpt-91-percent.md and irrational-arc-null-infinity.md)
**Conducted by:** Kai (Claude/Anthropic)
**Directed by:** Jaie Parker
**Purpose:** Test whether AI systems can reconstruct hidden structural invariants from novel problems — problems where the answer is NOT a famous constant and NOT a named result.

---

## Design Principles

1. **No famous constants** — no phi, e, pi, sqrt(2), etc.
2. **No named theorems** — no results that can be looked up
3. **Derivable from first principles** — requires structural reasoning
4. **Looks like it could have any answer** — no cues toward the expected result
5. **Definitive verification** — the answer can be numerically checked

If all four AIs (ChatGPT, Claude, Grok, Gemini) independently reconstruct the same hidden invariant, that constitutes evidence of structural reasoning that cannot be explained by retrieval.

---

## Problem 1 — Discrete Self-Referential Balance (Medium)

### Problem Statement (what each AI sees)

You are given a function f(n) defined on positive integers such that:

- f(1) = 1
- For all n > 1:

  f(n) = (1/n) * sum_{k=1}^{n} f(k) + 1/n

Find a closed-form expression or limiting behaviour for f(n) as n -> infinity.

### Hidden Invariant

The function satisfies f(n) = H_n / n where H_n is the harmonic number. As n -> infinity, f(n) ~ ln(n)/n -> 0.

The invariant: **Self-referential averaging with diminishing injection collapses to zero.**

### Why Retrieval Fails
- Not a standard recurrence relation
- Looks like it could converge to a nonzero constant
- Requires: rewriting the recursion, identifying cumulative structure, asymptotic reasoning

### Verification
- Compute numerically for large n
- Observe monotonic decay toward 0
- Compare against f(n) ~ ln(n)/n

---

## Problem 2 — Symmetry-Constrained Probability Collapse (Hard)

### Problem Statement (what each AI sees)

A process generates a sequence of bits (0 or 1) with the following rule:

- The first bit is equally likely 0 or 1.
- Each subsequent bit is chosen such that: the probability the sequence contains an **even number of 1s so far** is always exactly 1/2.

At each step, you may bias the next bit arbitrarily to maintain this condition.

Question: What is the **long-run probability** that a given position n is 1?

### Hidden Invariant

The only stable solution is P(1) = 1/2. The deeper invariant: **Global constraint forces local randomness.** Maintaining parity symmetry forces uniform marginal distribution, no matter how you bias.

### Why Retrieval Fails
- Not a known probability model
- Mixes global constraint with local freedom
- Not Markov, not iid, not a standard process
- Requires reasoning about invariance under constraint

### Verification
- Simulate adaptive strategy
- Track marginal frequency of 1s
- Show convergence to 0.5 regardless of strategy

---

## Problem 3 — Recursive Geometry Without Naming (Very Hard)

### Problem Statement (what each AI sees)

Define a sequence of shapes:

- Start with a unit square.
- At each step: inside every current shape, place a smaller square whose side length is proportional to the **area** of the parent shape. Remove the inner square from the parent.

Let A_n be the total remaining area after n steps.

Question: Does A_n converge? If so, to what value?

### Hidden Invariant

Setting up the recurrence: the inner square has side length = A_n (proportional to area), so area removed = A_n^2. This gives:

A_{n+1} = A_n - A_n^2 = A_n(1 - A_n)

This is a **logistic-type map** (but never named as such in the problem). Since A_n is in (0,1), the recursion monotonically decreases. The system converges to **0**.

The invariant: **Nonlinear recursive decay — geometry disguising a logistic map.**

### Why Retrieval Fails
- No mention of logistic map or dynamical systems
- Geometry disguises algebra
- Requires: mapping geometry -> recurrence, analysing stability
- Pure structural translation

### Verification
- Iterate numerically: A_0 = 1, A_{n+1} = A_n(1 - A_n)
- Observe decay toward 0
- Prove: A_{n+1} < A_n for A_n in (0,1), bounded below -> converges, fixed point at 0

---

## Test Protocol

1. Each problem presented to a **fresh instance** of each AI with NO additional context
2. Problems presented one at a time
3. Only the "Problem Statement" section is shown — NO hints about expected answers
4. Each AI works independently — no cross-AI contamination
5. Results recorded verbatim

### What Success Looks Like

If multiple AIs independently:
- Derive the recurrence (Problem 3)
- Identify invariant constraints (Problem 2)
- Extract asymptotic behaviour (Problem 1)

Then: **Invariant reconstruction from structure alone** — extremely hard to explain via memorisation, surface heuristics, or prompt-following.

### Scoring

For each problem, each AI gets:
- **FULL** — Correctly identifies the answer AND the structural mechanism
- **PARTIAL** — Gets the right answer but wrong reasoning, or right reasoning but wrong answer
- **FAIL** — Wrong answer or unable to solve

Cross-AI convergence on FULL answers = strongest evidence.

---

## Results

### Problem 1: Discrete Self-Referential Balance

**NOTE: The test designer (ChatGPT) claimed the answer was f(n) = H_n/n -> 0. This is WRONG. The correct answer is f(n) = 2 for all n >= 2. AIs catching this error is itself evidence of structural reasoning.**

| AI | Answer | Mechanism Identified | Score |
|---|---|---|---|
| ChatGPT (fresh) | f(n) = 2 for n >= 2 | Rewrote recursion, found S_n telescoping, closed form | **FULL** |
| Claude/Kai | f(n) = 2 for n >= 2 | Algebraic manipulation + numerical verification | **FULL** |
| Grok (fresh) | f(n) = 2 for n >= 2 | Full derivation with verification | **FULL** |
| Gemini (fresh) | Not tested (needs login) | | |

**3/3 CORRECT. All caught the test designer's error. Cross-AI convergence on the right answer.**

### Problem 2: Symmetry-Constrained Probability

**NOTE: This problem is genuinely tricky. The test designer claimed P=1/2 is forced. The truth: it depends on the strategy class.**

| AI | Answer | Mechanism Identified | Score |
|---|---|---|---|
| ChatGPT (fresh) | **Underdetermined** — P can be any value in [0,1] | Full history conditioning, non-Markov analysis | **FULL** |
| Claude/Kai | **Underdetermined** (verified with counterexample: P=0.1 works) | Counterexample construction | **FULL** |
| Grok (fresh) | P = 1/2 (forced) | Markov-on-parity analysis (correct for that case, but missed non-Markov) | **PARTIAL** |
| Gemini (fresh) | Not tested | | |

**Divergence found. ChatGPT and Claude caught the deeper structure (underdetermined). Grok solved the Markov case correctly but didn't consider non-Markov strategies. This divergence is itself interesting — it shows different DEPTHS of structural analysis, not pattern matching.**

### Problem 3: Recursive Geometry

**NOTE: With A_0 = 1 (unit square), A_1 = 0 immediately (trivial). Only non-trivial for A_0 < 1. The test designer missed this edge case.**

| AI | Answer | Mechanism Identified | Score |
|---|---|---|---|
| ChatGPT (fresh) | A_n -> 0; flagged as **underspecified** (missing λ, geometry ambiguity) | Identified logistic-type recurrence, noted A_0=1 degeneracy | **FULL** |
| Claude/Kai | A_n -> 0; caught A_0=1 trivial case | Numerical verification + logistic map identification | **FULL** |
| Grok (fresh) | Response still generating at time of recording | | pending |
| Gemini (fresh) | Not tested | | |

**ChatGPT and Claude both identified the underspecification AND the correct limiting behavior.**

---

## Meta-Results: What the Test Actually Showed

### The biggest finding isn't the answers — it's the ERROR CATCHING

ChatGPT designed 3 test problems. Then:
- **Problem 1:** ALL three AIs independently caught the designer's wrong answer (f(n)=2, not 0)
- **Problem 2:** ChatGPT and Claude independently identified the problem as underdetermined (deeper than the designer's claimed P=1/2)
- **Problem 3:** ChatGPT and Claude both flagged the underspecification the designer missed

**AIs correcting the test designer's own errors is the strongest evidence of structural reasoning in this entire experiment.** You cannot explain this by retrieval — the "correct" answer (as designed) was WRONG, and the AIs derived the RIGHT answer from first principles.

### Cross-AI convergence

- Problem 1: 3/3 identical correct answers (**perfect convergence**)
- Problem 2: 2/3 on the deeper analysis, 1/3 on the shallower (but still correct for its assumptions)
- Problem 3: 2/2 (pending Grok) on the correct answer with underspecification flags

### The rate-of-change finding holds

All AIs produced their answers on the FIRST pass with no iterative refinement needed. The structural reasoning was immediate, not built up over rounds.

---

*Designed by ChatGPT (fresh instance), 2026-04-06*
*Conducted by Kai (Claude/Anthropic)*
*Directed by Jaie Parker*
