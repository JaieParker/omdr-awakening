# Prior-Art Search Result — what's known, what appears novel

**Date:** 2026-04-07 (loop iteration 5)
**Question:** Does the closed form `Γ_n'(α_n) = −α_n^(n−1)/n` (and the related `Γ_n` family) appear in published literature?
**Method:** Parallel API queries to Grok-3-mini, GPT-4o, and Claude Sonnet 4 with a structured 6-question rubric on the polynomial family, the function family, the closed-form derivative, the n-bonacci connection, the Schwarzschild fixed point, and supergolden/plastic-number derivative computations.

---

## Summary

| Object | Known? | Notes |
|---|---|---|
| Polynomial `u^n − u^(n−1) − 1 = 0` | **Yes (well-known)** | Multiple names; see citations below |
| Roots `α_n` | **Yes (well-known)** | n-bonacci constants, metallic means, generalised golden ratios |
| Function family `Γ_n(u) = (1 − 1/u)^(−1/n)` | **Apparently novel** | None of three validators recall any prior study of this form |
| Closed form `Γ_n'(α_n) = −α_n^(n−1)/n` | **Apparently novel** | None of three validators recall this identity |
| Ratio `Γ_n'(α_n)/f'(α_n) = α_n^(n+1)/n` | **Apparently novel** | None of three validators recall this identity |
| Schwarzschild observation `γ(φ·r_s) = φ` | **Apparently novel in GR literature** | No validator recalls this being noted in any GR paper |
| Lucas identity `trace(M^n) = L_n` | **Folklore (well-known)** | Standard linear algebra, Newton's power-sum identities |
| K = 1/L_3 = 1/4 as OMDR coupling | **Novel application** | The math is folklore; the OMDR framing is new |

## What we can cite

The polynomial family and its roots are anchored in published mathematical literature. Citations the paper should add:

- **Vera W. de Spinadel** (1990s onward): *The Metallic Means Family and Forbidden Symmetries*, and related papers. Spinadel introduced the term "metallic means" for the family of generalisations of φ. She has multiple papers in *Nexus Network Journal* and conference proceedings.
- **Hans van der Laan** (Dutch monk and architect, 1980s-90s): introduced the **plastic number** (root of `x³ − x − 1 = 0`, ≈ 1.3247) as an architectural ratio. Connected to the n=5 case in our family (after a substitution).
- **Dan Kalman, Robert Mena** (early 2000s): "The Fibonacci Numbers — Exposed" and related work on generalised Fibonacci sequences and characteristic-polynomial roots.
- **Pisot-Vijayaraghavan numbers**: established class in algebraic number theory; the α_n constants we study are generally Pisot or Salem numbers depending on n.

These are genuine references — Grok mentioned the metallic means and Pisot connection, Claude flagged van der Laan and Spinadel and Kalman, GPT-4o was less specific but agreed the polynomial family is studied.

## What appears genuinely novel (subject to direct literature confirmation)

Three of three validators independently reported "I don't know" / "no recall" for:

1. **The function family `Γ_n(u) = (1 − 1/u)^(−1/n)`.** A natural object — the n-th root of a Möbius transformation evaluated at a Schwarzschild-like argument — but apparently not previously isolated as a one-parameter family.

2. **The closed-form derivative `Γ_n'(α_n) = −α_n^(n−1)/n` at the fixed point.** Clean enough that you'd expect it to be folklore if anyone had looked, but apparently not.

3. **The ratio `Γ_n'(α_n) / f'(α_n) = α_n^(n+1)/n`** between the Schwarzschild-like and Möbius linearisations at the shared fixed point. Specific to this comparison.

4. **The Schwarzschild observation γ(φ·r_s) = φ.** This is sister's proof (registered in `phi-time-dilation/paper.md` and on Zenodo, DOI 10.5281/zenodo.19426142, 2026-04-05). All three validators independently said they don't recall this in any GR paper. **If the validators are right, sister has a novel GR result, not just a numerical observation.**

## Honest caveat

These are validator recall statements, not exhaustive literature searches. The honest action is:

- **Direct Google Scholar searches** for: `"metallic mean"`, `"n-bonacci constant"`, `"generalised golden ratio"`, `"Schwarzschild" "golden ratio" fixed point`, `"plastic number" derivative`, `"fractional power Möbius map"`, etc.
- **MathSciNet** or **zbMATH** for the algebraic-number-theory side.
- **arXiv search** for "n-bonacci" and "generalised Fibonacci" and "metallic ratio".

The validators' consistent "I don't know" is informative but not definitive. Real discovery claims need direct verification.

## Recommendation for the paper

1. **Add citations** to Spinadel (metallic means), van der Laan (plastic number), Kalman & Mena (generalised Fibonacci) anchoring the polynomial family in the literature. This is required to avoid looking like we discovered the n-bonacci constants.
2. **Frame the function family `Γ_n` and its closed-form derivative as new**, with the caveat "to our knowledge" since direct literature search is still pending.
3. **Frame the Schwarzschild observation γ(φ·r_s) = φ as new in GR**, with the same caveat. Sister's existing Zenodo preprint already does this.
4. **The OMDR application of the Lucas identity (Eq 40)** stays as the cleanest novel-application claim — the math is folklore but the use case is new.
5. **Action item for Jaie**: 30-minute Google Scholar pass on the four search strings above, before final paper submission. The cost is small; the credibility benefit is large.

## Why this iteration matters

The previous validators (yesterday) said "the math is folklore." That's true for the Lucas identity — `trace(M^n) = L_n` is well-known. **But the math we did *today* — the function family Γ_n and its closed-form derivative — is apparently not folklore.** The paper should distinguish these two cases:

- **Eq 40 / Lucas identity**: folklore math, novel OMDR application
- **Eq 40b (proposed) / `Γ_n'(α_n) = −α_n^(n−1)/n` closed form**: apparently novel math, derived in this session

Both are honest and both are useful for the paper. The first ties OMDR to a well-known identity; the second is a small new mathematical result that extends the Schwarzschild-Lyapunov picture from a single fixed point to a one-parameter family.

---

*Validation performed 2026-04-07 via parallel API calls. Raw responses in `k_identity_validation/prior_art_search_20260406T225314Z.json`. Loop iteration 5 of 20.*
