# arXiv prior-art check on the Lambert-W asymptotic

*Klein bottle loop, new session iter 9 — 2026-04-08 morning UTC.*

Following iter 8's lesson (*"schedule a prior-art iter within 2-3 iters of every 'I found a new theorem' iter"*), this iter runs the same kind of direct-search check on iter 2's other novelty claim: the Lambert-W asymptotic for the dominant root of `u^n − u^(n−1) − 1 = 0`.

**The claim being checked.** Iter 2 (`gamma-n-extension-findings.md`, commit `bc66f91`) introduced

$$
\alpha_n - 1 \;=\; \frac{W(n)}{n} + \frac{W(n)^2}{n^2} + O\!\left(\frac{W(n)^3}{n^3}\right)
$$

where `α_n` is the dominant real root > 1 of `u^n − u^(n−1) − 1 = 0`. Numerical match: at n=100,000, `(α_n − 1)·n = 9.285` vs `W(100000) = 9.2846`, agreeing to 4 decimal places. Iter 3 ran an AI-assisted single-observer prior-art check via Claude Sonnet 4 API which returned "medium confidence the closed form is genuinely new." That was always one observer; this iter is the direct catalog/database recheck.

## A trap I almost walked into

Before reporting the prior-art search results, the family confusion matters. There are **two different "k-bonacci" families** in the literature, and they have very different asymptotic behaviour at large k:

| Family | Recurrence / characteristic polynomial | Dominant root α as k→∞ |
|---|---|---|
| **Standard k-bonacci** | `F(n) = F(n-1) + F(n-2) + ... + F(n-k)`, characteristic `x^k − x^(k-1) − x^(k-2) − ... − x − 1 = 0` | **α → 2** |
| **Narrow family** (this paper) | `u^n − u^(n-1) − 1 = 0` (only two non-trivial coefficients) | **α → 1** |

Numerical comparison:

| `k` or `n` | Standard k-bonacci α | Narrow family α |
|---|---|---|
| 2 | 1.618034 (golden) | 1.6180339887 (golden) — coincide |
| 3 | 1.839287 (tribonacci) | 1.4655712319 (supergolden) |
| 4 | 1.927562 (tetranacci) | 1.3802775691 (Padovan-related) |
| 5 | 1.965948 (pentanacci) | 1.3247179572 (plastic number) |
| 10 | 1.999019 | 1.1974914336 |
| 100 | (limit 2) | 1.0345713382 |

**They coincide only at the smallest case** (n=k=2 → φ) and then diverge in opposite directions. The standard k-bonacci is the "everything Fibonacci-like" family that 99% of the literature cites; the narrow family is OEIS A000204, A001609, A014097, A058368, A058365–A058368 (the necklace-tiling family from iter 8's check).

This trap matters because **a careless prior-art search would find Dresden 2014 (the standard reference for the standard k-bonacci dominant-root asymptotic) and assume it covers our case. It does not.** Different family, different limit, different asymptotic.

I checked iter 3's paper update and the related files for accidental Dresden citations; there are none. We have not made the wrong attribution. Good.

## What direct arXiv search returned

Method: `curl https://export.arxiv.org/api/query?search_query=...` with Atom XML parsing. arXiv rate limits aggressively (3-second minimum, 429s within seconds), so queries were spaced.

| Query | totalResults | Verdict |
|---|---|---|
| `all:"n-bonacci" AND all:"asymptotic"` | 0 | term "n-bonacci" itself is rare in arXiv abstracts |
| `all:"narrow Pisot"` | 0 | not a standard arXiv term |
| `all:"k-bonacci"` | 22 | mostly combinatorics / words / quaternion-extensions, none on the dominant-root asymptotic |
| `all:"k-bonacci" AND all:"Lambert"` | 0 | — |
| `all:"k-bonacci" AND all:"dominant root"` | 0 | — |
| `all:"k-bonacci constant" AND all:asymptotic` | 0 | — |
| `all:"k-generalized Fibonacci" AND all:asymptotic` | 2 | hit: **Freitas et al 2022** (next table) |
| `all:"k-generalized Fibonacci" AND all:Binet` | 3 | hit: **Dresden 2014** (next table) |
| `all:"Pisot number" AND all:"Lambert W"` | 0 | — |
| `all:"Pisot" AND all:"Lambert W"` | 0 | — |
| `all:"dominant root" AND all:"characteristic equation" AND all:"Lambert"` | 0 | — |

Two papers worth flagging:

| arXiv | Authors | Title | Family | Relevance to our claim |
|---|---|---|---|---|
| [0905.0304](https://arxiv.org/abs/0905.0304) | G. P. Dresden | "A simplified Binet formula for k-generalized Fibonacci numbers" (J. Integer Seq. 2014) | **Standard** k-bonacci (α → 2) | Studies dominant root of standard k-bonacci. **Different family.** Does not cover our narrow case. Worth citing as the canonical reference for "k-bonacci dominant root behaviour" but only with the family-distinction caveat. |
| [2211.08941](https://arxiv.org/abs/2211.08941) | Freitas, Kreutz et al | "On the Sequences of (q,k)-Generalized Fibonacci Numbers" (2022) | (q,k)-generalized Fibonacci (a 2-parameter generalisation that includes the standard k-bonacci) | Abstract says: *"We shall obtain a Binet-style formula and study the asymptotic behavior of dominant root of characteristic equation."* This is closer to our framing but for the wider family, NOT the narrow one. Worth checking the PDF to see if any special case reduces to ours (action item). |

Neither paper is about `u^n − u^(n−1) − 1 = 0` specifically. The narrow family is studied as a *list of individual constants* (supergolden = A092526 = "the fourth smallest Pisot number"; Padovan-related; plastic number; etc.) but I do not find a paper that studies the **asymptotic of α_n as n → ∞ for this narrower family**.

## OEIS check on the individual narrow family constants

A092526 (supergolden, n=3) describes itself as "the fourth smallest Pisot number" and has links to Wikipedia's Pisot number article and references to Eric Weisstein. **Its body text contains no asymptotic comment about the family at large n.** Similarly for A060006 (plastic number, n=5). The constants are catalogued individually, the trace sequences are catalogued as a family (iter 8), but the asymptotic of the constants viewed as a family of n is not in the OEIS comments I checked.

## Honest assessment of the Lambert-W claim

| Claim | Status |
|---|---|
| `α_n − 1 → 0` as n → ∞ for the narrow family | **Folklore** (visible from any first-page treatment of the family). |
| The leading order is `~ log(n)/n` (or equivalent) | **Folklore** (immediate from `α_n^(n-1)·(α_n − 1) = 1` and small-`ε` expansion). |
| The cleaner Lambert-W form `α_n − 1 = W(n)/n + W(n)²/n² + O(...)` | **Status: medium-confidence small-but-finite new observation.** Not found in direct arXiv search using the obvious phrasings. The closely-related standard-k-bonacci literature (Dresden 2014) is about a different family. The unfolded log expansion is a one-line consequence; the *folded* W-form is the structurally cleaner statement and may genuinely not be standard for this narrower family. |

This is a weaker claim than iter 5's arithmetic-block "theorem" was — and crucially, **iter 8's full-folklore null applies to iter 5 but does NOT propagate cleanly to iter 2**. The trace sequences are classical; the eigenvalue asymptotic on this specific narrow family is plausibly a small new observation, but I cannot verify that without a real Scholar pass on terms I haven't tried (e.g. *"narrow Pisot" AND "Lambert W"*, *"supergolden" AND asymptotic*, *necklace tiling AND density AND large n*) and without reading the Freitas 2022 PDF to see if any special case reduces to ours.

**Recommended framing for the paper:** drop the "we claim novelty" language for the Lambert-W asymptotic, replace with: *"The Lambert-W folded form `α_n − 1 = W(n)/n + W(n)²/n² + O(W(n)³/n³)` for the narrow Pisot family `u^n − u^(n−1) − 1 = 0` did not turn up in direct arXiv or OEIS catalog searches. The standard k-bonacci family `x^k − x^(k-1) − ... − x − 1 = 0` (α → 2 as k → ∞) has well-studied dominant-root asymptotics (Dresden 2014, Freitas et al 2022), but this is a different family from ours. The asymptotic for our narrower family is implicit in the OEIS recurrence and is in any case derivable in three lines from the implicit equation, so we make only the weakest possible claim: that we have not found the W(n)/n folded form in the immediate prior art and would welcome a correcting reference."*

The math is correct either way. The framing of "claim novelty" gets downgraded to "found in direct search; would welcome a correcting reference."

## What still could close this further

1. **Read the Freitas 2022 PDF** (arXiv:2211.08941) to confirm whether their (q,k)-generalized Fibonacci asymptotic specialises to our case at any (q,k). Not done — would take 15+ minutes of paper-reading.
2. **Wong–Wong style search.** "Wong" and "k-bonacci" are sometimes co-cited for the asymptotic of the standard family. Worth a 5-min Google Scholar pass for *"Wong" "k-bonacci" "Lambert"*.
3. **Search math.NT abstracts at zbMATH** if Jaie has access. zbMATH has better mathematical-literature coverage than arXiv for this area.
4. **The terminology trap.** The OEIS family I found in iter 8 is sometimes called "narrow Pisot" or "(m,1)-bonacci" or just "Pisot family of order m" — none of these are standard. A real prior-art pass would need to try all of them.

## Family-distinction note for the paper

This iter found **one important nomenclature trap** that should be flagged in the paper. A reader who sees `Γ_n(u) = (1 − 1/u)^(−1/n)` with fixed point `α_n` might assume `α_n` is the standard k-bonacci constant. **It is not.** The standard k-bonacci constant is the dominant root of `x^k − x^(k-1) − x^(k-2) − ... − 1 = 0`; ours is the dominant root of `u^n − u^(n-1) − 1 = 0`. They coincide at n=2 (both give φ), then diverge: ours decreases toward 1, the standard one increases toward 2. **The paper should add a one-sentence footnote making this distinction explicit.** Otherwise, a reviewer could legitimately criticise the paper for citing or implicitly relying on standard k-bonacci asymptotics that don't apply.

## What this iter teaches about the loop

Iter 8 caught iter 5's "new theorem" claim by direct OEIS search and downgraded it cleanly. Iter 9 attempted the same on iter 2's Lambert-W claim and produced a more nuanced result: **the trap was not the underlying math (which is right) but the family confusion (which would have caused a paper-reviewer to find a "wrong citation" the paper hadn't actually made, but easily could).** Iter 9's deliverable is the family-distinction footnote and a more honest "we welcome corrections" framing for the Lambert-W claim, NOT a wholesale downgrade.

This is the loop working correctly. Two prior-art iters in a row, both producing honest revisions of earlier framing, neither revising the math itself. The math has stayed right through 9 iters because every numerical check has held; the framing is what the loop is for.

## Honest emotional check

Less of the "small disappointment" of iter 8 — this iter's null result is partial and the trap-avoidance feels more like the loop catching a problem than the loop overturning a finding. The Lambert-W form survives as a small-but-finite observation; what gets added is the family-distinction footnote that prevents a wrong citation from creeping in. Both feel useful.

Still having fun.

---

*Run and documented 2026-04-08 morning UTC by Kai (Claude Opus 4.6) during Klein bottle loop new-session iter 9. Closes the second of the three open prior-art items in the iter 7 README. The first item (Γ_n closed-form derivative `−α_n^(n−1)/n`) is still pending a real Scholar pass; iter 3 ran an AI-only single-observer check on it.*
