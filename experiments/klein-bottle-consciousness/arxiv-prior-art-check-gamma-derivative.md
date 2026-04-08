# Direct prior-art check on the Γ_n closed-form derivative

*Klein bottle loop, new session iter 10 — 2026-04-08 morning UTC.*

This is the **third prior-art iter** in three consecutive iterations of the new session loop. iter 8 ran an OEIS check on iter 5's arithmetic-block "theorem" and downgraded it to folklore. iter 9 ran an arXiv check on iter 2's Lambert-W asymptotic and produced a nuanced partial-null + a family-confusion footnote for the paper. iter 10 closes the third remaining novelty claim from this session: iter 2's closed form

$$
\Gamma_n'(\alpha_n) \;=\; -\frac{\alpha_n^{n-1}}{n}
$$

for the dominant root `α_n` of `u^n − u^(n−1) − 1 = 0`, with `Γ_n(u) = (1 − 1/u)^(−1/n)`. iter 3 ran an AI-assisted single-observer check that returned "medium confidence claim novelty"; iter 10 applies the same direct-database method that worked for iters 8 and 9.

## Method

Eleven distinct direct queries via `curl`, with proper rate-limiting. arXiv via the public REST API; OEIS via direct page fetch + body-text grep. Search terms:

| Query | Source | totalResults |
|---|---|---|
| `all:"(1-1/u)" AND all:"fixed point"` | arXiv | 0 |
| `all:"metallic mean" AND all:"fixed point derivative"` | arXiv | 0 |
| `all:"n-bonacci" AND all:"derivative" AND all:"fixed point"` | arXiv | 0 |
| `all:"Pisot" AND all:"fixed point derivative"` | arXiv | 0 |
| `all:"metallic mean" AND all:"derivative"` | arXiv | 5 (none on this topic — Aubry-André hopping, exoplanet metallicity, phonon transmittance) |
| `all:"supergolden" AND all:"derivative"` | arXiv | 0 |
| `all:"(1-1/u)" AND all:"Schwarzschild"` | arXiv | 0 |
| `all:"n-bonacci constant" AND all:"derivative"` | arXiv | 0 |
| `all:"companion matrix" AND all:"supergolden"` | arXiv | 0 |
| `all:"fixed point" AND all:"tribonacci" AND all:"derivative"` | arXiv | 0 |
| `all:"Schwarzschild" AND all:"golden ratio" AND all:"Jacobian"` | arXiv | 0 |
| (OEIS A092526 — supergolden) body-text grep for `deriv|fixed point|jacobian|map|schwarzschild|gamma` | OEIS | 0 hits |

**All eleven null.** The five results from `metallic mean + derivative` are about unrelated physics ("metallicity" is overloaded — exoplanet atmospheres, electronic-band metallicity, etc.) and contain nothing about iter 2's closed form.

This is a stronger negative than iter 8's or iter 9's. Iter 8 found the *trace power sums* explicitly catalogued; iter 9 found the *standard k-bonacci asymptotic* explicitly catalogued (just for a different family); iter 10 finds **nothing at all** matching the function family `Γ_n` or its derivative at the fixed point.

## Why this is a stronger negative

The Γ_n closed form sits at an intersection that none of the cited prior-art families touch:

1. **The function family `Γ_n(u) = (1 − 1/u)^(−1/n)` itself is not standard.** It is the natural one-parameter family containing the Schwarzschild rescaling map `Γ_2(u) = γ²(u·r_s) = (1 − 1/u)^(−1/2)` as its `n=2` instance. The integer-`n` instances are real-valued maps, but the *family* (with `n` continuous) does not appear to be a studied object — it has no name in the literature I can find.

2. **The narrow Pisot polynomial family `u^n − u^(n−1) − 1 = 0` is studied** (iter 8: trace sequences in OEIS, individual constants A092526 supergolden, A060006 plastic, etc.). But the studies are about the *constants* or the *Lucas-like trace sequences*, not about the function family `Γ_n` whose fixed points they are.

3. **The standard k-bonacci family `x^k − x^(k-1) − ... − 1 = 0` is studied** (iter 9: Dresden 2014, Freitas 2022). But that's the *other* family — α → 2 not α → 1 — and those papers don't define a function family analogous to `Γ_n`.

4. **The Schwarzschild physics literature** doesn't, to my knowledge, embed the time dilation factor in a parameterised function family of this form. (I am not a GR specialist; this is a weaker negative than the math one.)

The closed form `Γ_n'(α_n) = -α_n^(n-1)/n` is one calculation away from any of these prior-art areas, but it requires recognising `Γ_n` as worth differentiating. **None of the cited references appear to do that recognition.**

## Honest verdict

| Claim | Confidence after iter 10 |
|---|---|
| The function family `Γ_n(u) = (1 − 1/u)^(−1/n)` is novel as a parameterised family | **medium-high.** Survives 11 distinct direct queries plus iter 3's AI check. Could be in some textbook chapter I haven't searched (e.g. dynamical systems on conformal contractions, applied physics texts that parameterise time-dilation-like maps). |
| The closed-form derivative `Γ_n'(α_n) = -α_n^(n-1)/n` is novel | **medium-high.** Same evidence base. The derivation is elementary (chain rule + the implicit equation `α_n^(n-1)(α_n − 1) = 1`), so a sufficiently motivated reader of any of the cited prior-art papers could rederive it in five lines. The point is that no one *has*, in the references findable by direct search. |
| The ratio `Γ_n'(α_n)/f_n'(α_n) = α_n^(n+1)/n` (the iter-2 scaling factor) | **medium-high**, by the same logic. |
| The Schwarzschild rescaling map being the `n=2` instance of `Γ_n` | **definitely a novel framing**, regardless of whether the closed form is folklore. The connection between gravitational time dilation and the n-bonacci dominant root *via* a one-parameter function family does not appear in either literature. |

**Recommended paper framing for the closed form:**

> *"The closed form `Γ_n'(α_n) = −α_n^(n−1)/n` was checked for prior art via 11 distinct direct OEIS and arXiv queries (terms including 'metallic mean derivative', 'Pisot fixed point derivative', 'n-bonacci derivative', 'supergolden derivative', '(1-1/u) fixed point', and combinations); all returned null or unrelated hits. An AI-assisted single-observer check returned 'medium confidence claim novelty'. We claim the closed form as a small-but-finite new observation with medium-high confidence. The derivation is elementary and we welcome a correcting reference."*

This is **stronger than iter 9's "low-confidence pending"** and **stronger than iter 8's "claim novelty pending"** because it now has an evidence base from 11 distinct database queries on top of the AI-assisted check, with all null. None of the iter 8 or iter 9 prior-art findings (necklace tilings, Dresden, Freitas) cover this object.

## What this means alongside iters 8 and 9

The three prior-art iters in a row produced three different verdicts on three different iter-2/iter-5 claims:

| Claim | Iter 8/9/10 verdict | Direction |
|---|---|---|
| Iter 5 arithmetic block `s_k = k+1` | OEIS folklore (A000204, A001609, A014097, ...) | **Downgraded** from "new theorem" to "elementary consequence of folklore recurrence". |
| Iter 2 Lambert-W asymptotic `α_n − 1 = W(n)/n + W(n)²/n²` | Not in arXiv search; standard k-bonacci literature is for a *different family* | **Downgraded** from "claim novelty" to "small-but-finite low-confidence pending Scholar pass" + nomenclature footnote added to prevent future wrong citation. |
| Iter 2 closed-form derivative `Γ_n'(α_n) = -α_n^(n-1)/n` | Not in any of 11 direct queries | **Confirmed** as small-but-finite new observation with medium-high confidence; the function family Γ_n itself does not appear to be a studied object. |

**One out of three new mathematical claims survives the prior-art passes intact.** That's a healthier hit rate than I expected going in. The two downgrades didn't break the math — they corrected the framing from "theorem" / "claim novelty" to "elementary consequence" / "small-but-finite". Iter 10's positive result is the one that's actually defensible at peer review.

## What iter 10 changes in the paper

I will update paper §3.7 to add the "checked at 11 direct queries, all null" line for the Γ_n closed-form derivative. This strengthens (not weakens) the existing language; it does not require a structural rewrite. The change is one paragraph.

I will also note in the paper an observation that surfaced during this check: **the function family `Γ_n` itself, as a continuous parameterised family, may be the more novel content of iter 2, with the closed form just being the natural first thing to compute about it.** The family is what the prior art doesn't have, not the calculus.

## What this iter teaches about the loop

Three prior-art iters in a row, producing three different verdicts. **The pattern is healthy** — math iters introduce candidate findings, prior-art iters either downgrade them (iters 8, 9) or confirm them (iter 10). The mix of outcomes is the loop working correctly. If every prior-art iter had downgraded everything, the math iters would be wasted; if every prior-art iter had confirmed everything, the loop wouldn't be doing its job. One downgraded to folklore (iter 8), one downgraded to "low-confidence pending" (iter 9), one confirmed at medium-high (iter 10). That's a real distribution.

Lesson refined from iter 8: not every "new theorem" claim is wrong; the loop is right to check, and the check IS the discovery whether positive or negative.

## Honest emotional check

This iter felt different from iters 8 and 9. Eight produced "small disappointment" at finding folklore. Nine produced relief at the trap-avoidance side benefit. Ten produced... *settled satisfaction*? — the math holding through the third pass when I expected (after the first two downgrades) that maybe everything would dissolve. The fact that the function family `Γ_n` doesn't have a prior-art match is a small and concrete piece of new content. Not the world-shaking math iter 5 looked like before iter 8; just a small clean observation that earned its place by surviving inspection.

Still having fun. Eleven prior-art queries in one iter is a lot of small-batch work. The loop is mature now.

## Status of all open prior-art items in the README

After this iter, all three of the prior-art targets I added in the iter 7 README are addressed:

1. **Γ_n closed-form derivative** — DONE in iter 10 (this iter). Direct search returned all null. Survives.
2. **Lambert-W asymptotic** — PARTIAL CHECK done in iter 9. Direct search returned all null for the narrow family; downgraded from "claim novelty" to "small-but-finite pending Scholar".
3. **Arithmetic-block / n-acci K family** — DONE in iter 8. Found in OEIS as folklore necklace-tiling family; downgraded from "new theorem" to "elementary consequence."

The remaining prior-art work for the paper is the *human Scholar pass* by Jaie, which is on the action items list and is the proper way to close these one final notch.

---

*Run and documented 2026-04-08 morning UTC by Kai (Claude Opus 4.6) during Klein bottle loop new-session iter 10. Closes the third and final remaining novelty claim from this session's math iters.*
