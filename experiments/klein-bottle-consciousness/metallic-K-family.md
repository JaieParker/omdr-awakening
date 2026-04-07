# Metallic K Family: Generalising Eq 40 to All Metallic Means

**Date:** 2026-04-07 (loop iteration 9)
**Question:** Eq 40 is `K = 1/trace(M³) = 1/4` for the *Fibonacci* matrix `M = [[1,1],[1,0]]`. Does the same Cayley-Hamilton identity give a clean closed form for the higher metallic means (silver, bronze, copper, …)?

---

## Result

**Yes. Closed form:**
$$K_p \;:=\; \frac{1}{\operatorname{tr}(M_p^3)} \;=\; \frac{1}{p\,(p^2 + 3)}$$
where `M_p = [[p, 1], [1, 0]]` is the companion matrix of the metallic-mean characteristic polynomial `λ² − pλ − 1 = 0`.

**Derivation (Cayley-Hamilton, parallel to Eq 40):**

Since `M_p` satisfies its own characteristic equation, `M_p² = pM_p + I`. Then:
```
M_p³ = M_p · M_p² = M_p(pM_p + I) = pM_p² + M_p
     = p(pM_p + I) + M_p
     = (p² + 1)M_p + pI
```
Taking the trace:
```
trace(M_p³) = (p² + 1)·trace(M_p) + p·trace(I)
            = (p² + 1)·p + p·2
            = p³ + p + 2p
            = p³ + 3p
            = p(p² + 3)
```
So `K_p = 1/[p(p² + 3)]`. Verified numerically for `p = 1..10` against direct `[M_p]³` matrix multiplication.

## The metallic K table

| p | metallic mean | trace(M_p³) | K_p | name |
|---|---|---|---|---|
| **1** | **φ ≈ 1.6180** | **4** | **1/4 = 0.25000** | **golden (Eq 40)** |
| 2 | 1 + √2 ≈ 2.4142 | 14 | 1/14 ≈ 0.07143 | silver |
| 3 | (3+√13)/2 ≈ 3.3028 | 36 | 1/36 ≈ 0.02778 | bronze |
| 4 | 2+√5 ≈ 4.2361 | 76 | 1/76 ≈ 0.01316 | copper |
| 5 | (5+√29)/2 ≈ 5.1926 | 140 | 1/140 ≈ 0.00714 | nickel |
| 6 | 3+√10 ≈ 6.1623 | 234 | 1/234 ≈ 0.00427 | — |
| 10 | 5+√26 ≈ 10.0990 | 1030 | 1/1030 ≈ 0.00097 | — |

**Asymptotic for large p:** `K_p = 1/[p(p² + 3)] ~ 1/p³`. The metallic K values fall like the cube of the metal index.

## The two-parameter family `K_{p,n}`

A natural further generalisation: `K_{p,n} := 1/trace(M_p^n)` where p varies the matrix and n varies the power.

By Newton's power-sum identity, `trace(M_p^n)` satisfies the recurrence
```
p_0 = 2,    p_1 = p,    p_n = p · p_{n−1} + p_{n−2}
```
We call this the **p-Lucas sequence**. For `p = 1` it is the standard Lucas sequence `L_n` from Eq 40; for `p = 2` it is closely related to the Pell-Lucas numbers; for higher `p` it has no standard name.

The 2D table of `trace(M_p^n)` values:

| `n \ p` | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| 1 | 1 | 2 | 3 | 4 | 5 |
| 2 | 3 | 6 | 11 | 18 | 27 |
| **3** | **4** | **14** | **36** | **76** | **140** |
| 4 | 7 | 34 | 119 | 322 | 727 |
| 5 | 11 | 82 | 393 | 1364 | 3775 |
| 6 | 18 | 198 | 1298 | 5778 | 19602 |

**Eq 40 is the (p=1, n=3) entry.** Reading along row n=3 gives the metallic K family of this iteration. Reading down column p=1 gives the n-band Lucas family from yesterday (1, 1/3, 1/4, 1/7, 1/11, 1/18, …), which we tested against the benchmark and found unsupported as a coupling-constant lattice.

So Eq 40 sits at the *intersection* of two natural one-parameter generalisations:
- **Vary `n`**: K_{1,n} = 1/L_n. The n-band conjecture (null result, see `effective_k_analysis.md`).
- **Vary `p`**: K_{p,3} = 1/[p(p² + 3)]. The metallic K family (this iteration).

## Honest framing

The mathematics here is folklore — Newton's power-sum identities applied to companion matrices of metallic-mean polynomials. None of this is novel as pure linear algebra. **What is potentially novel is the framing**: noting that Eq 40 is a single point in a 2D family of "trace-of-power-of-companion-matrix" identities, and that the closed forms for both directions are clean.

For the OMDR application:
- **Eq 40 (golden, n=3): K = 1/4** is the empirically-chosen Band-3 coupling and matches the (p=1, n=3) corner of the table.
- **There is no current empirical reason** to invoke any other entry. The silver-K and bronze-K values aren't known to appear in any OMDR-related measurement we've made, and the n-band Lucas lattice was tested and not supported.

So this iteration produces a *clean mathematical generalisation* without making a stronger empirical claim. The 2-parameter family is real; whether any cell besides (1, 3) is physically meaningful is open.

## Possible next directions

1. **Test K_{2,3} = 1/14 ≈ 0.0714 against the benchmark.** Is there any architectural metric near 0.0714? (Grok's Problem-2 catch rate is 8.2% — not exact, but in the neighbourhood.)

2. **Look at the *higher-order* metallic means in physical contexts.** Silver ratio appears in some quasi-crystal contexts; bronze and beyond are rarer. If there's a known physics application of K = 1/14 or K = 1/36, the family becomes more than abstract.

3. **What's special about n=3?** Eq 40 picks `n = 3` for OMDR's Band-3 reasons. The metallic-K family also uses `n = 3`, giving the cubic `p³ + 3p`. Different choices of n give different polynomials in p. For example, K_{p,4} = 1/(p⁴ + 4p² + 2). Is there a reason `n = 3` (cubic in p) is special, or is it just that OMDR named its third band?

## What this iteration produces for the paper

A new optional subsection (not yet integrated) for §3.6 of the paper:

> "**Generalisation to the metallic means.** Eq 40 is the `p = 1` case of a one-parameter family. For the companion matrix `M_p = [[p, 1], [1, 0]]` of the p-th metallic-mean polynomial `λ² − pλ − 1 = 0`, the same Cayley-Hamilton identity gives `M_p² = pM_p + I`, hence `M_p³ = (p² + 1)M_p + pI`, and therefore
> $$K_p \;:=\; \frac{1}{\operatorname{tr}(M_p^3)} \;=\; \frac{1}{p(p^2 + 3)}.$$
> Eq 40's `K = 1/4` is the (p=1) entry. Higher metallic means give smaller couplings: `K_2 = 1/14` (silver), `K_3 = 1/36` (bronze), with asymptotic `K_p ~ 1/p³`. We make no empirical claim that these higher-`p` couplings appear in OMDR — only that the Cayley-Hamilton derivation of Eq 40 generalises cleanly to the entire metallic-means family. The two-parameter table `K_{p,n} = 1/trace(M_p^n)` places Eq 40 at the `(p=1, n=3)` cell of a doubly-indexed Lucas-reciprocal lattice."

---

*Computed and verified 2026-04-07 in loop iteration 9. Symbolic Cayley-Hamilton derivation matches numerical matrix multiplication for `p = 1..10`.*
